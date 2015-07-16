from numpy import linspace,sin,pi,int16,int32,array,append
from scipy.io.wavfile import write
from pylab import plot,show,axis

class Dsp(object):
    def __init__(self,img=None):
        self.img = img

    def set_img(self,img):
        self.img = img

    def note(self,freq, len, amp=1, rate=44100):
        t = linspace(0,len,len*rate)
        data = sin(2*pi*freq*t)*amp
        return data.astype(int16) # two byte integers

    def render_segments(self,segs):
        buff = []
        for s in segs.keys():
            buff.append(self.render_segment(segs[s]))
        self.sum_buffers(buff)

    def render_segment(self,seg):
        # print seg
        buff = []
        # get img pixel data
        x,y = seg.shape
        for i in range(x):
            r = seg[i,0]
            # print r
            g = seg[i,1]
            # print g
            b = seg[i,2]
            # print b
            # print "R: %d, G:%d, B:%d" % (r,g,b)
            luminosity = (r+g+b)/3
            # print luminosity
            buff.append(luminosity)
        return buff

    def sum_buffers(self,buffs):
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
        interpol = 44100/len(ob)
        tone = array([])
        for amp in ob:
            tone = append(tone,self.note(440,interpol,amp*100))
        print(tone)
        tonend = ndarray(tone,int16)
        write('ImageSound.wav',44100,tonend)


if __name__ == '__main__':
     # A tone, 2 seconds, 44100 samples per second
    tone = note(440,2,amp=10000)

    write('440hzAtone.wav',44100,tone) # writing the sound to a file

    plot(linspace(0,2,2*44100),tone)
    axis([0,0.4,15000,-15000])
    show()
