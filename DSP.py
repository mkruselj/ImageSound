from numpy import linspace,sin,pi,int16,int32,array,append,interp,arange,logical_not
from numpy import multiply
from scipy.io.wavfile import write
from scipy.interpolate import interp1d, UnivariateSpline
# from pylab import plot,show,axis
from midinotes import generate_midi_dict
import matplotlib.pyplot as plt

MAX_AMPLITUDE = 30000

class Dsp(object):
    def __init__(self,img=None,gui=None):
        self.img = img
        self.gui = gui
        self.midi_notes = generate_midi_dict()

        # helper stuff
        self.odds = [x for x in range(128) if x % 2]
        self.evens = [x for x in range(128) if not x % 2]

    def set_img(self,img):
        self.img = img

    def note(self,freq, len, amp=1, rate=44100):
        t = linspace(0,len,len*rate)
        data = sin(2*pi*freq*t)*amp
        # print(data)
        return data.astype(int16) # two byte integers
        # return data.astype(int32) # four byte integers

    def render_segments(self,segs):
        print("[ * ] Rendering segments...")
        buffs = []
        for k in segs.keys():
            print("[ * ] %s" % k)
            buffs.append(self.render_segment(segs[k],k))

        self.sum_buffers(buffs)

    def render_segment(self,seg, key):
        print("[ * ] Rendering individual segment...")

        # get length of buffer for segment
        buffer_length = int(self.gui.read_speed[key].get())
        midi_note_number = self.gui.baseline_freq[key].get()
        harm_mode = self.gui.harm_mode_var[key].get()
        harm_count = self.gui.harm_count[key].get()
        base_freq = self.midi_notes[int(midi_note_number)]

        print("[ * ] Buffer length: %s" % buffer_length)
        print("[ * ] MIDI Note: %s" % midi_note_number)
        print("[ * ] Harmonic Mode: %s" % harm_mode)
        print("[ * ] Harmonic Count: %s" % harm_count)
        print("[ * ] Base Frequency: %s" % base_freq)

        # handle harmonic settings
        harmonics = []
        harmonics.append(base_freq)

        # we only can handle first harmonic right now
        # so override anything from interface
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
                elif harm_mode == 'Prime':
                    pass
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
                elif harm_mode == 'Sub Prime':
                    pass

        # generate sine wave
        sine = self.note(base_freq,buffer_length/1000, amp=1.1)
        plt.plot(sine,'b',lw=3 )
        plt.show()

        # generate the amplitude buffer to be same size as sine
        # amplitude_buff_space = arange(0,(buffer_length/1000)*44100)
        # luminosity_buff_space = linspace(0,buffer_length/1000,buffer_length*44100)
        luminosity_values = []

        # get img pixel luminosity data
        # this will work for 1d arrays, but not nd arrays
        x,y = seg.shape
        for i in range(x):
            r,g,b = seg[i,0], seg[i,1], seg[i,2]
            luminosity = (r+r+b+g+g+g)/6
            # print luminosity
            luminosity_values.append(luminosity)

        # now interpolate the values with the amplitude buffer
        luminosity_values = array(luminosity_values)

        luminosity_x = linspace(0,1,len(luminosity_values))
        # plt.plot(luminosity_x,luminosity_values,'ro',ms=5)
        # plt.show()
        spl = UnivariateSpline(luminosity_x,luminosity_values,k=1)
        spl.set_smoothing_factor(0.5)
        amplitude_buff_space = linspace(0,1,(buffer_length/1000)*44100)

        # plt.plot(amplitude_buff_space, spl(amplitude_buff_space),'g',lw=3)
        # plt.show()



        # now return note * amplitude_buff
        print("[ * ] Modulating sine wav")
        rendered = sine *  spl(amplitude_buff_space)
        print(rendered)
        plt.plot(arange(0,len(rendered)),rendered,'r',lw=3)
        plt.show()
        return rendered

    def sum_buffers(self,buffs):
        print("[ * ] Summing buffers...")
        max_len = 0
        for buff in buffs:
            if len(buff) > max_len:
                max_len = len(buff)
        out_buff = [0]*max_len
        for buff in buffs:
            for i in range(len(buff)):
                out_buff[i] += buff[i]
        self.generate_sample(out_buff)

    def generate_sample(self,ob):
        print("[ * ] Generating sample...")

        # plt.plot(arange(0,len(ob)),ob,'g',lw=3)
        # plt.show()
        
        tone_out = array(ob,dtype=int16)
        tone_out *= MAX_AMPLITUDE

        # plt.plot(arange(0,len(tone_out)),tone_out,'g',lw=3)
        # plt.show()

        write('ImageSound.wav',44100,tone_out)
        print("[ * ] Wrote audio file")


if __name__ == '__main__':
    # A tone, 2 seconds, 44100 samples per second
    dsp = Dsp()
    tone = dsp.note(440,2,amp=10000)
    write('440hzAtone.wav',44100,tone) # writing the sound to a file
    plt.plot(linspace(0,2,2*44100),tone,'b',lw=3)
    plt.show()
