#!/usr/bin/env python3

from numpy import linspace, sin, pi, int16, array, append, multiply
from scipy.io.wavfile import write as writewav
from scipy.interpolate import UnivariateSpline as interpolate
from math import sqrt
import random
import pyaudio

MAX_AMPLITUDE = 32767
SAMPLE_RATE = 44100
ANTIALIASING = 1

class Dsp(object):
    output = 0

    def __init__(self, img=None, gui=None):
        self.img = img
        self.gui = gui
        self.midi_notes = self.generate_midi_dict()

        # precompute sequential odd numbers
        self.odds = [x for x in range(512) if x % 2]
        # precompute first 128 prime numbers
        N = 720    # 128th prime number is 719, this is the top limit
        a = [1] * N
        x = range
        for i in x(2, N):
            if a[i]:
                for j in x(i * i, N, i) : a[j] = 0
        self.primes = [i for i in x(len(a)) if a[i] == 1][2:]

    def set_img(self, img):
        self.img = img

    # http://subsynth.sourceforge.net/midinote2freq.html
    def generate_midi_dict(self):
        midi = {}
        a = 440;
        for x in range(145):
           midi[x] = (a / 32) * (pow(2,((x - 9) / 12)))
        return midi

    def generate_sample(self, out_buffer, preview, filename, was_previewed=None):
        if not was_previewed:
            print("* Generating audio...")
            self.output = array(out_buffer, dtype=int16)

        if preview:
            print("* Previewing audio...")

            bytestream = self.output.tobytes()
            pya = pyaudio.PyAudio()
            stream = pya.open(format=pya.get_format_from_width(width=2), channels=1, rate=SAMPLE_RATE, output=True)
            stream.write(bytestream)
            stream.stop_stream()
            stream.close()

            pya.terminate()
            print("* Audio preview completed!")
        else:
            writewav(filename, SAMPLE_RATE, self.output)
            print("* Wrote audio to %s!" % filename)

    def note(self, freq, length, amp, rate=SAMPLE_RATE):
        t = linspace(0,length,length * rate)
        data = sin(2 * pi * freq * t) * amp
        return data.astype(int16)

    def render_segment(self, seg, key):
        print("  * Vector %d:" % (key + 1))

        harm_mode = self.gui.harm_mode_var[key].get()
        harm_count = self.gui.harm_count_val[key]
        midi_note_number = int(self.gui.baseline_freq[key].get())
        read_time = int(self.gui.read_speed[key].get())
        delay_time = int(self.gui.delay_time[key].get())
        base_freq = self.midi_notes[midi_note_number]

        # handle harmonics settings
        harmonic_freqs = []
        harmonic_freqs.append(base_freq)

        # create random harmonics
        rnd_list = random.sample(range(2,256),128)
        rnd_list_hz = random.sample(range(int(base_freq) + 10,SAMPLE_RATE // (ANTIALIASING + 1)),128)

        for h in range(1,harm_count):
            if harm_mode == 'All':
                freq = base_freq * (h + 1)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Even':
                freq = base_freq * (h * 2)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Odd':
                freq = base_freq * self.odds[h]
                harmonic_freqs.append(freq)
            elif harm_mode == 'Skip 2':
                freq = base_freq * (self.odds[h] + h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Skip 3':
                freq = base_freq * (self.odds[h] + h + h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Skip 4':
                freq = base_freq * (self.odds[h] + h + h + h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Primes':
                freq = base_freq * self.primes[h]
                harmonic_freqs.append(freq)
            elif harm_mode == 'Sub All':
                freq = base_freq / (h + 1)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Sub Even':
                freq = base_freq / (h * 2)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Sub Odd':
                freq = base_freq / self.odds[h]
                harmonic_freqs.append(freq)
            elif harm_mode == 'Sub Skip 2':
                freq = base_freq / (self.odds[h] + h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Sub Skip 3':
                freq = base_freq / (self.odds[h] + h + h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Sub Skip 4':
                freq = base_freq / (self.odds[h] + h + h + h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Sub Primes':
                freq = base_freq / self.primes[h]
                harmonic_freqs.append(freq)
            elif harm_mode == 'Inc 100 Hz':
                freq = base_freq + (100 * h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Inc 250 Hz':
                freq = base_freq + (250 * h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Inc 500 Hz':
                freq = base_freq + (500 * h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Inc 1000 Hz':
                freq = base_freq + (1000 * h)
                harmonic_freqs.append(freq)
            elif harm_mode == 'Random':
                freq = base_freq * rnd_list[h]
                harmonic_freqs.append(freq)
            elif harm_mode == 'Random Hz':
                freq = rnd_list_hz[h]
                harmonic_freqs.append(freq)

        # list with all the harmonics to be generated
        harmonics = list()

        # generate sine waves
        for j, harm in enumerate(harmonic_freqs):
            # check if harmonic goes beyond Nyquist and stop processing, if antialiasing enabled
            if harm > SAMPLE_RATE / 2 and ANTIALIASING == 1:
                break
            print("    * Processing harmonic #" + str(j+1) + ', ' + str(harm) + ' Hz')
            sine = self.note(freq=harm, length=read_time / 1000, amp=MAX_AMPLITUDE / harm_count, rate=SAMPLE_RATE)
            # get pixel luminosity data
            luminosity_values = []
            x, y = seg[j].shape
            for i in range(x):
                R, G, B = int(seg[j][i,0]), int(seg[j][i,1]), int(seg[j][i,2])
                luminosity = sqrt(0.299 * R * R + 0.587 * G * G + 0.114 * B * B) / 255
                luminosity_values.append(luminosity)

            # now interpolate the values with the amplitude buffer
            luminosity_x = linspace(0,1,len(luminosity_values))
            luminosity_values = array(luminosity_values)
            spl = interpolate(luminosity_x, luminosity_values, k=1, s=0)
            amplitude_buff_space = linspace(0,1,(read_time / 1000) * SAMPLE_RATE)

            harmonics.append(sine * spl(amplitude_buff_space))

        waveform = sum(harmonics)

        # generate empty buffer for delay time
        dly = self.note(1,delay_time / 1000, amp=0, rate=SAMPLE_RATE)

        # merge the delay time with the generated waveform
        rendered = append(dly,waveform)

        return rendered

    def render_segments(self, vectors, preview, filename):
        print("* Rendering vectors...")
        buffers = []
        for k in vectors.keys():
            buffers.append(self.render_segment(vectors[k], k))
        self.sum_buffers(buffers, preview, filename)

    def sum_buffers(self, buffers, preview, filename):
        print("* Summing vector buffers...")
        max_len = 0
        for buff in buffers:
            if len(buff) > max_len:
                max_len = len(buff)
        out_buffer = [0] * max_len
        for buff in buffers:
            for i in range(len(buff)):
                out_buffer[i] += buff[i] / len(buffers) # dividing with number of vectors used to prevent clipping
        self.generate_sample(out_buffer, preview, filename)
