from numpy import linspace,sin,pi,int16,int32,array,append
from scipy.io.wavfile import write
# from pylab import plot,show,axis

MAX_AMPLITUDE = 30000

class Dsp(object):
    def __init__(self,img=None,gui=None):
        self.img = img
        self.gui = gui

    def set_img(self,img):
        self.img = img

    def note(self,freq, len, amp=1, rate=44100):
        t = linspace(0,len,len*rate)
        data = sin(2*pi*freq*t)*amp
        return data.astype(int16) # two byte integers

    def render_segments(self,segs):
        print("[ * ] Rendering segments...")
        buffs = []
        for s in segs.keys():
            buffs.append(self.render_segment(segs[s]))

        self.sum_buffers(buffs)

    def render_segment(self,seg):
        print("[ * ] Rendering individual segment...")
        # print seg
        buff = []
        # get img pixel data
        x,y = seg.shape
        for i in range(x):
            r,g,b = seg[i,0], seg[i,1], seg[i,2]
            # print r
            # g = seg[i,1]
            # # print g
            # b = seg[i,2]
            # # print b
            # print "R: %d, G:%d, B:%d" % (r,g,b)
            luminosity = (r+g+b)/3
            # print luminosity
            buff.append(luminosity)
        return buff

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
        interpol = 44100/len(ob)
        
        interpol = 4

        print("[ * ] Length %d samples" % interpol)

        tone = []
        first = True
        for amp in ob:
            if(first):
                new_note = self.note(440,interpol,amp*MAX_AMPLITUDE)
            else:
                new_note += self.note(440,interpol,amp*MAX_AMPLITUDE)
            shapesize = new_note.shape
            print("[ * ] Note length %d " % shapesize)
            tone.extend(new_note)
        # print tone
        tonend = array(tone,int16)

        write('ImageSound.wav',44100,tonend)
        print("[ * ] Wrote audio file")


if __name__ == '__main__':
     # A tone, 2 seconds, 44100 samples per second
    tone = note(440,2,amp=10000)

    write('440hzAtone.wav',44100,tone) # writing the sound to a file

    # plot(linspace(0,2,2*44100),tone)
    # axis([0,0.4,15000,-15000])
    # show()
