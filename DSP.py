from numpy import linspace,sin,pi,int16,array,append,arange,multiply
from scipy.io.wavfile import write
from scipy.interpolate import interp1d, UnivariateSpline
import matplotlib.pyplot as plt
import pyaudio

CHUNK = 1024
MAX_AMPLITUDE = 32767
SAMPLE_RATE = 48000			# processing sample rate
OUTPUT_SAMPLE_RATE = 48000	# output file sample rate

class Dsp(object):
    def __init__(self, img=None, gui=None):
        self.img = img
        self.gui = gui
        self.midi_notes = self.generate_midi_dict()

        # helper stuff
        self.odds = [x for x in range(128) if x % 2]
        self.evens = [x for x in range(128) if not x % 2]

    # http://subsynth.sourceforge.net/midinote2freq.html
    def generate_midi_dict(self):
        midi = {}
        a = 440;
        for x in range(128):
           midi[x] = (a / 32) * (pow(2,((x - 9) / 12)))
        return midi

    def set_img(self, img):
        self.img = img

    def note(self, freq, len, amp=1, rate=SAMPLE_RATE):
        t = linspace(0,len,len * rate)
        data = sin(2 * pi * freq * t) * amp
        return data.astype(int16)

    def render_segments(self, segs, preview, filename):
        print("* Rendering vectors...")
        buffs = []
        for k in segs.keys():
            buffs.append(self.render_segment(segs[k],k))
        self.sum_buffers(buffs, preview, filename)

    def render_segment(self, seg, key):
        print("  * Vector %d:" % (key + 1))

        harm_mode = self.gui.harm_mode_var[key].get()
        harm_count = self.gui.harm_count[key].get()
        buffer_length = int(self.gui.read_speed[key].get())
        delay_buffer_length = int(self.gui.delay_time[key].get())
        midi_note_number = self.gui.baseline_freq[key].get()
        base_freq = self.midi_notes[int(midi_note_number)]

        print("    * Harmonic Mode: %s" % harm_mode)
        print("    * Harmonic Count: %s" % harm_count)
        print("    * MIDI Note: %s" % midi_note_number)
        print("    * Base Frequency: %s Hz" % base_freq)
        print("    * Buffer length: %s ms" % buffer_length)
        print("    * Delay time: %s ms" % delay_buffer_length)

        # handle harmonics settings
        harmonics = []
        harmonics.append(base_freq)

        # we only can handle first harmonic right now so override anything from interface
        harm_count = 1

        if harm_count > 1:
            for h in range(1,len(int(harm_count))):
                if harm_mode == 'All':
                    freq = base_freq * h
                    harmonics.append(freq)
                elif harm_mode == 'Even':
                    freq = base_freq * (h * 2)
                    harmonics.append(freq)
                elif harm_mode == 'Odd':
                    freq = base_freq * ((h * 2) + 1)
                    harmonics.append(freq)
                elif harm_mode == 'Skip 2':
                    freq = base_freq * self.odds[h]
                    harmonics.append(freq)
                elif harm_mode == 'Skip 3':
                    freq = base_freq * (self.odds[h] + h)
                    harmonics.append(freq)
                elif harm_mode == 'Skip 4':
                    freq = base_freq * (self.odds[h] + h + h)
                    harmonics.append(freq)
                elif harm_mode == 'Sub All':
                    freq = base_freq / h
                    harmonics.append(freq)
                elif harm_mode == 'Sub Even':
                    freq = base_freq / (h * 2)
                    harmonics.append(freq)
                elif harm_mode == 'Sub Odd':
                    freq = base_freq / ((h * 2) + 1)
                    harmonics.append(freq)
                elif harm_mode == 'Sub Skip 2':
                    freq = base_freq / self.odds[h]
                    harmonics.append(freq)
                elif harm_mode == 'Sub Skip 3':
                    freq = base_freq * (self.odds[h] + h)
                    harmonics.append(freq)
                elif harm_mode == 'Sub Skip 4':
                    freq = base_freq * (self.odds[h] + h + h)
                    harmonics.append(freq)

        # generate empty buffer for delay time
        dly = self.note(1,delay_buffer_length / 1000, amp=0)

        # generate sine wave
        sine = self.note(base_freq,buffer_length / 1000, amp=MAX_AMPLITUDE)

        # get pixel luminosity data
        # this will work for 1d arrays, but not nd arrays
        luminosity_values = []
        x,y = seg.shape
        for i in range(x):
            r,g,b = int(seg[i,0]), int(seg[i,1]), int(seg[i,2])
            luminosity = (r + r + b + g + g + g) / 1530.0
            luminosity_values.append(luminosity)

        # now interpolate the values with the amplitude buffer
        luminosity_values = array(luminosity_values)
        luminosity_x = linspace(0,1,len(luminosity_values))
        spl = UnivariateSpline(luminosity_x, luminosity_values, k=1, s=0)
        amplitude_buff_space = linspace(0,1,(buffer_length / 1000) * SAMPLE_RATE)

        print("  * Applying luminosity values to sine wave amplitudes")
        waveform = sine * spl(amplitude_buff_space)

        # merge the delay time with the generated waveform
        rendered = append(dly,waveform)

        return rendered

    def sum_buffers(self, buffs, preview, filename):
        print("* Summing vector buffers...")
        max_len = 0
        for buff in buffs:
            if len(buff) > max_len:
                max_len = len(buff)
        out_buff = [0] * max_len
        for buff in buffs:
            for i in range(len(buff)):
                out_buff[i] += buff[i] / len(buffs) # dividing with number of vectors used to prevent clipping
        self.generate_sample(out_buff, preview, filename)

    def generate_sample(self, ob, preview, filename):
        print("* Generating sample...")
        tone_out = array(ob, dtype=int16)

        if preview:
            print("* Previewing audio file...")

            bytestream = tone_out.tobytes()
            pya = pyaudio.PyAudio()
            stream = pya.open(format=pya.get_format_from_width(width=2), channels=1, rate=OUTPUT_SAMPLE_RATE, output=True)
            stream.write(bytestream)
            stream.stop_stream()
            stream.close()

            pya.terminate()
            print("* Preview completed!")
        else:
            write(filename, OUTPUT_SAMPLE_RATE, tone_out)
            print("* Wrote audio file!")
