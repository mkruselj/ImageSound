from numpy import linspace,sin,pi,int16,array,append,arange,multiply
from scipy.io.wavfile import write
from scipy.interpolate import interp1d, UnivariateSpline
import matplotlib.pyplot as plt

MAX_AMPLITUDE = 32767
SAMPLE_RATE = 44100

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
        a = 440;    # A is 440 Hz...
        for x in range(128):
           midi[x] = (a / 32) * (pow(2,((x - 9) / 12)))
        return midi

    def set_img(self, img):
        self.img = img

    def note(self, freq, len, amp=1, rate=SAMPLE_RATE):
        t = linspace(0,len,len*rate)
        data = sin(2*pi*freq*t)*amp
        return data.astype(int16)

    def render_segments(self, segs, preview):
        print("* Rendering vectors...")
        buffs = []
        for k in segs.keys():
            buffs.append(self.render_segment(segs[k],k))
        self.sum_buffers(buffs, preview)

    def render_segment(self, seg, key):
        print("  * Vector %d:" % (key+1))

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

        # handle harmonic settings
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
        dly = self.note(1,delay_buffer_length/1000, amp=0)

        # generate sine wave
        sine = self.note(base_freq,buffer_length/1000, amp=MAX_AMPLITUDE)
        # plt.plot(sine,'b',lw=3 )
        # plt.show()

        # get img pixel luminosity data
        # this will work for 1d arrays, but not nd arrays
        luminosity_values = []
        x,y = seg.shape
        for i in range(x):
            r,g,b = int(seg[i,0]), int(seg[i,1]), int(seg[i,2])
            luminosity = (r+r+b+g+g+g)/1530.0
            luminosity_values.append(luminosity)

        # now interpolate the values with the amplitude buffer
        luminosity_values = array(luminosity_values)
        luminosity_x = linspace(0,1,len(luminosity_values))

        # plt.plot(luminosity_x,luminosity_values,'ro',ms=5)
        # plt.show()

        spl = UnivariateSpline(luminosity_x, luminosity_values, k=1, s=0)
        amplitude_buff_space = linspace(0,1,(buffer_length/1000)*SAMPLE_RATE)

        # plt.plot(amplitude_buff_space, spl(amplitude_buff_space),'g',lw=3)
        # plt.show()

        # now return note * amplitude_buff
        print("  * Applying luminosity to sine wave amplitude")
        rendered = sine * spl(amplitude_buff_space)

        # plt.plot(arange(0,len(rendered)),rendered,'r',lw=3)
        # plt.show()

        return rendered

    def sum_buffers(self, buffs, preview):
        print("* Summing vector buffers...")
        max_len = 0
        for buff in buffs:
            if len(buff) > max_len:
                max_len = len(buff)
        out_buff = [0]*max_len
        for buff in buffs:
            for i in range(len(buff)):
                out_buff[i] += buff[i] / len(buffs) # dividing with number of vectors used to prevent clipping
        self.generate_sample(out_buff, preview)

    def generate_sample(self, ob, preview):
        print("* Generating sample...")
        tone_out = array(ob, dtype=int16)

        # plt.plot(arange(0,len(tone_out)),tone_out,'g',lw=3)
        # plt.show()

        if preview:
            print("* Previewing audio file...")
        else:
            write('ImageSound.wav',SAMPLE_RATE,tone_out)
            print("* Wrote audio file!")

'''
if __name__ == '__main__':
    # A tone, 2 seconds, SAMPLE_RATE samples per second
    dsp = Dsp()
    tone = dsp.note(440,2,amp=10000)
    write('440hzAtone.wav',SAMPLE_RATE,tone) # writing the sound to a file
    plt.plot(linspace(0,2,2*SAMPLE_RATE),tone,'b',lw=3)
    plt.show()
'''