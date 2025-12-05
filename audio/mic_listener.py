
import pyaudio
import numpy as np
import wave
import time

def listen_for_human_turn(
    device_name = "USB PnP Audio Device",
    sample_rate = 16000,
    channels = 1,
    frames_per_buffer = 320,
    threshold = 1000,
    initial_timeout = 5.0,
    end_silence = 3.0,
    output_path = "human_turn.wav"
):
    
    pa = pyaudio.PyAudio()
    
    device_index = None
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info.get("maxInputChannels", 0) > 0 and device_name in info["name"]:
            device_index = i
            break
    
    print(f"[Mic] Using device index: {device_index}")
    
    stream = pa.open(
        format = pyaudio.paInt16,
        rate = sample_rate,
        channels = channels,
        input = True,
        frames_per_buffer = frames_per_buffer,
        input_device_index = device_index
    )
    
    print("[Mic] Listening for human speech...")
    
    audio_frames = []
    human_present = False
    silence_time = 0.0
    start_time = time.time()
    
    frame_duration = frames_per_buffer / sample_rate
    
    while True:
        chunk = stream.read(frames_per_buffer, exception_on_overflow = False)
        
        samples = np.frombuffer(chunk, dtype = np.int16)
        volume = np.abs(samples).mean()
        
        if not human_present:
            if volume > threshold:
                human_present = True
                print("[Mic] Human speech detected, starting to record ...")
                audio_frames.append(chunk)
                silence_time = 0.0
            else:
                if time.time() - start_time > initial_timeout:
                    print("[Mic] No human speech detected with initial timeout.")
                    stream.stop_stream()
                    stream.close()
                    pa.terminate()
                    return None
                continue
        else:
            audio_frames.append(chunk)
            
            if volume < threshold:
                silence_time += frame_duration
            else:
                silence_time = 0.0
            
            if silence_time >= end_silence:
                print("[Mic] End of human turn detected")
                break
        
    stream.stop_stream()
    stream.close()
    pa.terminate()
    
    with wave.open(output_path, "wb") as wave_file:
        wave_file.setnchannels(channels)
        wave_file.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(sample_rate)
        for audio_frame in audio_frames:
            wave_file.writeframes(audio_frame)
    
    print(f"[Mic] Saved human turn to: {output_path}")
    return output_path
                