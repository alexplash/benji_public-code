
import threading
import pyaudio
import numpy as np

class PendingSoundPlayer:
    def __init__(self, audio_path = "audio/sounds/pending.pcm", gain = 0.3, channels = 1, sample_rate = 16000, frames_per_buffer = 320):
        self.audio_path = audio_path
        self.gain = gain
        self.channels = channels
        self.sample_rate = sample_rate
        self.frames_per_buffer = frames_per_buffer
        self._stop = False
        self._thread = None
        self.stream = None
        self.pa = None
        
    
    def _loop_sound(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            format = pyaudio.paInt16,
            channels = self.channels,
            rate = self.sample_rate,
            frames_per_buffer = self.frames_per_buffer,
            output = True
        )
        
        try:
            while not self._stop:
                with open(self.audio_path, "rb") as audio_file:
                    data = audio_file.read(self.frames_per_buffer * 2)
                    while data and not self._stop:
                        samples = np.frombuffer(data, dtype = np.int16)
                        samples = np.clip(samples * self.gain, -32768, 32767).astype(np.int16)
                        self.stream.write(samples.tobytes())
                        data = audio_file.read(self.frames_per_buffer * 2)
        
        finally:
            try:
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
                if self.pa:
                    self.pa.terminate()
                    self.pa = None
            except:
                pass
    
    def start(self):
        if self._thread is not None:
            return
        
        self._stop = False
        self._thread = threading.Thread(target = self._loop_sound, daemon = True)
        self._thread.start()
    
    def stop(self):
        self._stop = True
        
        self._thread = None