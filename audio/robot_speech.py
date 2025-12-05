

import pyaudio
import numpy as np
import threading
import wave

class RobotSpeech:
    
    def __init__(self, device_name = "USB PnP Audio Device", gain = 2.5, channels = 1, sample_rate = 16000, frames_per_buffer = 320, interruption_threshold = 8000, end_speech_threshold = 1000, end_silence = 3.0, interrupted_output_path = "interrupted_human_turn.wav"):
        self.device_name = device_name
        self.gain = gain
        self.channels = channels
        self.sample_rate = sample_rate
        self.frames_per_buffer = frames_per_buffer
        self.interruption_threshold = interruption_threshold
        self.max_allowed_output = interruption_threshold - 1000
        self.end_speech_threshold = end_speech_threshold
        self.end_silence = end_silence
        self.interrupted_output_path = interrupted_output_path
        self.device_index = None
        
        pa = pyaudio.PyAudio()
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0 and self.device_name in info["name"]:
                self.device_index = i
                break
        pa.terminate()
        pa = None
    
    def uninterruptible_audio(self, audio_path):
        
        pa = pyaudio.PyAudio()
        
        stream = pa.open(
            format = pyaudio.paInt16,
            channels = self.channels,
            rate = self.sample_rate,
            frames_per_buffer = self.frames_per_buffer,
            output = True
        )
        
        with open(audio_path, 'rb') as audio_file:
            while True:
                chunk = audio_file.read(self.frames_per_buffer * 2)
                if not chunk:
                    break
                
                samples = np.frombuffer(chunk, dtype = np.int16)
                samples = np.clip(samples * self.gain, -32768, 32767).astype(np.int16)
                stream.write(samples.tobytes())
        
        stream.stop_stream()
        stream.close()
        pa.terminate()


    def interruptible_audio(self, audio_path):
        
        pa = pyaudio.PyAudio()
        
        input_stream = pa.open(
            format = pyaudio.paInt16,
            channels = self.channels,
            rate = self.sample_rate,
            frames_per_buffer = self.frames_per_buffer,
            input = True,
            input_device_index = self.device_index
        )
        
        output_stream = pa.open(
            format = pyaudio.paInt16,
            channels = self.channels,
            rate = self.sample_rate,
            frames_per_buffer = self.frames_per_buffer,
            output = True
        )
        
        interrupted = False
        stop_listening = False
        
        def listen_for_interruption():
            nonlocal interrupted, stop_listening
            
            while not interrupted and not stop_listening:
                try:
                    data = input_stream.read(self.frames_per_buffer, exception_on_overflow = False)
                except:
                    break
                
                samples = np.frombuffer(data, dtype = np.int16)
                volume = np.abs(samples).mean()
                
                if volume > self.interruption_threshold:
                    print("[INTERRUPTION] robot speech interrupted")
                    interrupted = True
                    return
        
        listener_thread = threading.Thread(target = listen_for_interruption, daemon = True)
        listener_thread.start()
        
        try:
            with open(audio_path, 'rb') as audio_file:
                while True:
                    if interrupted:
                        break
                    
                    chunk = audio_file.read(self.frames_per_buffer * 2)
                    if not chunk:
                        break
                    
                    samples = np.frombuffer(chunk, dtype = np.int16)
                    samples = np.clip(samples * self.gain, -self.max_allowed_output, self.max_allowed_output).astype(np.int16)
                    output_stream.write(samples.tobytes())
        finally:
            stop_listening = True
            listener_thread = None
            
            # record user audio if interrupted
            # ---------------------------------
            if interrupted:
                interrupted_audio_frames = []
                silence_time = 0.0
                frame_duration = self.frames_per_buffer / self.sample_rate  
                while True:
                    try:
                        data = input_stream.read(self.frames_per_buffer, exception_on_overflow = False)
                    except:
                        break
                    
                    samples = np.frombuffer(data, dtype = np.int16)
                    volume = np.abs(samples).mean()
                    
                    interrupted_audio_frames.append(data)
                    
                    if volume < self.end_speech_threshold:
                        silence_time += frame_duration
                    else:
                        silence_time = 0.0
                    
                    if silence_time >= self.end_silence:
                        print("[Mic] End of human turn detected")
                        break
            # ---------------------------------
            
            input_stream.stop_stream()
            input_stream.close()
            
            output_stream.stop_stream()
            output_stream.close()
            
            pa.terminate()
            
            # save interrupted audio if detected
            if interrupted and len(interrupted_audio_frames) > 0:
                with wave.open(self.interrupted_output_path, 'wb') as wave_file:
                    wave_file.setnchannels(self.channels)
                    wave_file.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                    wave_file.setframerate(self.sample_rate)
                    for audio_frame in interrupted_audio_frames:
                        wave_file.writeframes(audio_frame)
                
                print(f"[INTERRUPTION] Saved interrupted human audio → {self.interrupted_output_path}")
                return self.interrupted_output_path

            return None
                    
                
        
        