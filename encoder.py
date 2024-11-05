import time
import cv2
import math
import wave
import struct
import numpy as np

def mapping_nums(value, value_min, value_max, output_min, output_max):
    return (value - value_min) * (output_max - output_min) / (value_max - value_min) + output_min

class SourceImage:
    def __init__(self, image_path: str) -> None:
        self.path = image_path
        self.image_data = cv2.imread(image_path, 1)
        self.width = len(self.image_data[0])
        self.height = len(self.image_data)

class SoundSSTV:
    def __init__(self, object: SourceImage):
        self.audio = []
        self.sample_rate = 44100.0
        self.pixel_time = 1
        self.last_phase = 0
        self.object = object
    
    def _add_beep(self, freq: int, duration: int) -> None:
        num_samples = int(duration * (self.sample_rate / 1000.0))
        t = np.arange(num_samples) / self.sample_rate
        samples = np.sin(2 * math.pi * freq * t + self.last_phase)
        self.audio.extend(samples.tolist())
        self.last_phase = (2 * math.pi * freq * num_samples / self.sample_rate + self.last_phase) % (2 * math.pi)

    def _beeps_from_list(self, beeps: list[list[float | int, float | int]]) -> None:
        for beep in beeps:
            self._add_beep(beep[0], beep[1])
            
    def _sound_separator(self) -> None:
        self._add_beep(1200, 20)
        self._add_beep(1400, 50)
        
    def _sound_next_line(self) -> None:
        self._add_beep(1300, 10)
        self._add_beep(1500, 50)
    
    def _sstv_header(self) -> None:
        sstv_vox = [1900, 1500, 1900, 1500, 2300, 1500, 2300, 1500]
        for vox in sstv_vox: self._add_beep(vox, 100)        
        calibration = [[1900, 300], [1200, 10], [1900, 300]]
        self._beeps_from_list(calibration)
        
        self._sound_separator()

        if isinstance(self.object, SourceImage):
            image_typing = [[1700, 50], [1800, 100]]
            self._beeps_from_list(image_typing)
            self._sound_separator()
            
            bytes_width = [int(i) for i in list(bin(self.object.width)[2:])]
            bytes_height = [int(i) for i in list(bin(self.object.height)[2:])]
            
            for num in bytes_width:
                self._add_beep(1500 if num == 0 else 1700, 30)
            
            self._sound_separator()
            
            for num in bytes_height:
                self._add_beep(1500 if num == 0 else 1700, 30)
        
        self._sound_separator()

    def _encoding_image(self):
        image = self.object
        freqs = mapping_nums(image.image_data[:, :, ::-1].astype(float), 0, 255, 1400, 2424)
        for line in freqs:
            self._sound_next_line()
            for freq in line.flatten():
                self._add_beep(freq, self.pixel_time)
                 
    def encode_object(self, debug_mode: bool = True):
        avaliable_object_type = [SourceImage]
        if type(self.object) not in avaliable_object_type:
            raise TypeError(f"Cannot encode object: Object type ({type(self.object)}) was wrong")
            
        print("adding header...")
        self._sstv_header()
        
        print("encoding object...")
        if isinstance(self.object, SourceImage):
            self._encoding_image()
    
        self._add_beep(500, 1000)
    
    def save_wav(self, file_path: str) -> None:
        wav_file = wave.open(file_path, "w")
        nchannels = 1
        sampwidth = 2
        nframes = len(self.audio)
        comptype = "NONE"
        compname = "not compressed"
        wav_file.setparams((nchannels, sampwidth, self.sample_rate, nframes, comptype, compname))
        audio_np = (np.array(self.audio) * 32767.0).astype(np.int16)
        wav_file.writeframes(audio_np.tobytes())
        wav_file.close()

start = time.time()

image = SourceImage("tester.png")
sstv = SoundSSTV(image)
sstv.encode_object()
sstv.save_wav("output.wav")

end = time.time()
print(f"done in {round((end-start)*1000, 2)}ms")
