#!/usr/bin/env python3

from tkinter import *
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
from numpy import array
from inspect import getsourcefile
from os.path import abspath, splitdrive
import skimage.draw, subprocess, time, DSP

class ImageSoundGUI:
    NUM_TABS = 16
    NUM_PARTIALS = 128
    COLORS = ('#FF0000', '#FF9900', '#FFBB00', '#FFFF00', '#99FF00', '#00FF00', '#00FF99', '#00FFCC',
              '#00CCFF', '#0099FF', '#0000FF', '#9900FF', '#CC00FF', '#FF00FF', '#FF0099', '#FF9999')
    MODE_OPT = ['All', 'Even', 'Odd', 'Skip 2', 'Skip 3', 'Skip 4', 'Primes',
                'Sub All', 'Sub Even', 'Sub Odd', 'Sub Skip 2', 'Sub Skip 3', 'Sub Skip 4', 'Sub Primes',
                'Inc 100 Hz', 'Inc 250 Hz', 'Inc 500 Hz', 'Inc 1000 Hz', 'Random', 'Random Hz']
    labels = []  # tkinter widget IDs for all labels
    harm_count = []  # tkinter widget IDs for all Harmonics Count spinboxes
    harm_count_val = []  # tkinter widget actual value for all Harmonics Count spinboxes
    baseline_freq = []  # tkinter widget IDs for all Baseline spinboxes
    delay_time = []  # tkinter widget IDs for all Delay Time spinboxes
    read_speed = []  # tkinter widget IDs for all Read Speed spinboxes
    harm_mode = []  # tkinter widget IDs for all Harmonic Mode dropdown menus
    harm_mode_var = [] # tkinter widget IDs for the actual value selected from Harmonic Mode dropdown menus
    is_img_loaded = 0
    drawn = None
    objectId = None
    imag = None
    imgsize = []
    seg = {}
    textid = 0
    was_previewed = False

    def __init__(self):
        # root window of the whole program
        self.root = Tk()
        self.root.title('ImageSound')
        self.root.minsize(617, 600)
        # root window dimensions and positioning
        self.ws = self.root.winfo_screenwidth()
        self.wh = self.root.winfo_screenheight()
        self.w = self.ws * 0.5
        self.h = self.wh * 0.75
        self.x = (self.ws / 2) - (self.w / 2)
        self.y = (self.wh / 2) - (self.h / 2)
        self.root.geometry('617x600+%d+%d' % (self.x, self.y-50))

        # Options menu variable
        self.SRselect = StringVar()
        self.ImPreview = StringVar()
        self.AntiAlias = StringVar()

        # main menu
        main_menu = Menu(self.root)
        menu_file = Menu(main_menu, tearoff=0)
        menu_file.add_command(label='Open Image...',
                              accelerator='Ctrl+O',
                              underline=0,
                              command=self.OpenFile)
        menu_file.add_command(label='Close Image...',
                              accelerator='Ctrl+Q',
                              underline=0,
                              command=self.CloseFile)
        menu_file.add_command(label='Preview Audio',
                              accelerator='Ctrl+P',
                              underline=0,
                              command=self.PreviewAudio)
        menu_file.add_command(label='Render To File...',
                              accelerator='Ctrl+R',
                              underline=0,
                              command=self.RenderToFile)
        menu_file.add_command(label='Clear All Lines',
                              accelerator='Ctrl+A',
                              underline=8,
                              command=self.ClearAllLines)
        menu_file.add_separator()
        menu_file.add_command(label='Exit',
                              accelerator='Alt+F4',
                              command=self.OnProgramQuit,
                              underline=1)
        menu_options = Menu(main_menu, tearoff=0)
        menu_options.add_command(label='Sample Rate:', state=DISABLED)
        menu_options.add_radiobutton(label='44.1 kHz',
                                     underline=3,
                                     value=1,
                                     command=self.ChangeSR,
                                     variable=self.SRselect)
        menu_options.add_radiobutton(label='48 kHz',
                                     value=2,
                                     underline=1,
                                     command=self.ChangeSR,
                                     variable=self.SRselect)
        menu_options.add_radiobutton(label='88.2 kHz',
                                     value=3,
                                     underline=3,
                                     command=self.ChangeSR,
                                     variable=self.SRselect)
        menu_options.add_radiobutton(label='96 kHz',
                                     value=4,
                                     underline=1,
                                     command=self.ChangeSR,
                                     variable=self.SRselect)
        menu_options.add_radiobutton(label='176.4 kHz',
                                     value=5,
                                     underline=4,
                                     command=self.ChangeSR,
                                     variable=self.SRselect)
        menu_options.add_radiobutton(label='192 kHz',
                                     value=6,
                                     underline=1,
                                     command=self.ChangeSR,
                                     variable=self.SRselect)
        menu_options.add_command(label='Image Preview:', state=DISABLED)
        menu_options.add_radiobutton(label='Original',
                                     value=1,
                                     underline=0,
                                     command=self.ImPreviewMode,
                                     variable=self.ImPreview)
        menu_options.add_radiobutton(label='Luminance',
                                     value=2,
                                     underline=0,
                                     command=self.ImPreviewMode,
                                     variable=self.ImPreview)
        menu_options.add_command(label='Antialiasing:', state=DISABLED)
        menu_options.add_radiobutton(label='Disabled', value=1, underline=0, command=self.AAMode, variable=self.AntiAlias)
        menu_options.add_radiobutton(label='Enabled', value=2, underline=0, command=self.AAMode, variable=self.AntiAlias)
        menu_help = Menu(main_menu, tearoff=0)
        menu_help.add_command(label='Documentation',
                              accelerator='F1',
                              underline=0,
                              command=self.Docs)
        menu_help.add_command(label='About ImageSound',
                              accelerator='F12',
                              underline=0,
                              command=self.About)
        main_menu.add_cascade(label='File', underline=0, menu=menu_file)
        main_menu.add_cascade(label='Options', underline=0, menu=menu_options)
        main_menu.add_cascade(label='Help', underline=0, menu=menu_help)
        self.root.config(menu=main_menu)

        # canvas/viewport for displaying the image and drawing vectors on it
        self.viewport = Canvas(self.root, bd=2, relief='ridge', highlightthickness=0)

        # define master buttons for audio preview, render to file and clear all vectors
        self.btn_preview = Button(self.root, text='Preview', state=DISABLED, command=self.PreviewAudio)
        self.btn_render = Button(self.root, text='Render', state=DISABLED, command=self.RenderToFile)
        self.btn_clear = Button(self.root, text='Clear All', command=self.ClearAllLines)

        # define a notebook for vector properties
        self.tabs = ttk.Notebook(self.root)
        self.tabs.bind('<<NotebookTabChanged>>', self.GetCurrentTab)

        # registering input validation command
        self.vldt_ifnum_cmd = (self.root.register(self.ValidateIfNum), '%P', '%S', '%W')

        # creating controls within each tab
        for i in range(self.NUM_TABS):
            frame = Frame()
            frame.config(relief='ridge', highlightthickness=4, highlightcolor=self.COLORS[i], highlightbackground=self.COLORS[i])
            self.tabs.add(frame, text='  ' + str(i + 1) + '  ')
            label = Label(frame, text='Harmonics Count:')
            label.grid(row=0, padx=10, pady=5, sticky=E)
            self.labels += [label]
            self.harm_count += [Spinbox(frame, command=self.AdjustLineWidth, from_=1, to=self.NUM_PARTIALS, width=5,
                                        justify='right', validate='all', validatecommand=self.vldt_ifnum_cmd)]
            self.harm_count[i].insert(0, 8)
            self.harm_count[i].delete(1, 'end')
            self.harm_count[i].grid(padx=5, pady=10, row=0, column=1, sticky=W)
            self.harm_count[i].bind('<MouseWheel>', self.OnMouseWheel)
            self.harm_count_val.append(int(self.harm_count[i].get()))
            label = Label(frame, text='Base Note (MIDI):')
            label.grid(padx=10, pady=5, row=0, column=2, sticky=E)
            self.labels += [label]
            self.baseline_freq += [Spinbox(frame, from_=21, to=108, width=6, justify='right', validate='all',
                                           validatecommand=self.vldt_ifnum_cmd)]
            # setting the default value to 69 by invoking button presses of the spinbox. hacky, but works. needs to be like this!
            for j in range(48):
                self.baseline_freq[i].invoke('buttonup')
            self.baseline_freq[i].grid(padx=5, pady=5, row=0, column=3, sticky=W)
            self.baseline_freq[i].bind('<MouseWheel>', self.OnMouseWheel)
            label = Label(frame, text='Read Speed (ms):')
            label.grid(padx=10, pady=5, row=0, column=4, sticky=E)
            self.labels += [label]
            self.read_speed += [Spinbox(frame, from_=100, to=60000, width=6, increment=10, justify='right', validate='all',
                                               validatecommand=self.vldt_ifnum_cmd)]
            self.read_speed[i].insert(1, 0)
            self.read_speed[i].grid(padx=5, pady=5, row=0, column=5, sticky=W)
            self.read_speed[i].bind('<MouseWheel>', self.OnMouseWheel)
            self.read_speed[i].bind('<Control-MouseWheel>', self.OnMouseWheelCtrl)
            label = Label(frame, text='Harmonics Mode:')
            label.grid(padx=10, row=1, column=0, sticky=E)
            self.labels += [label]
            self.harm_mode_var += [StringVar()]
            self.harm_mode_var[i].set(self.MODE_OPT[0])
            self.harm_mode += [OptionMenu(frame, self.harm_mode_var[i], *self.MODE_OPT)]
            self.harm_mode[i].config(width=10, justify='left')
            self.harm_mode[i].grid(row=1, column=1, sticky=W)
            label = Label(frame, text='Delay Time (ms):')
            label.grid(padx=10, row=1, column=4, sticky=E)
            self.labels += [label]
            self.delay_time += [Spinbox(frame, from_=0, to=60000, width=6, increment=10, justify='right', validate='all',
                                               validatecommand=self.vldt_ifnum_cmd)]
            self.delay_time[i].grid(padx=5, pady=10, row=1, column=5, sticky=W)
            self.delay_time[i].bind('<MouseWheel>', self.OnMouseWheel)
            self.delay_time[i].bind('<Control-MouseWheel>', self.OnMouseWheelCtrl)

        # layout managing
        self.viewport.grid(columnspan=3, padx=5, pady=5, sticky=N+S+W+E)
        self.btn_preview.grid(row=1, padx=58, pady=10, ipadx=5, ipady=5, sticky=W)
        self.btn_render.grid(row=1, padx=162, pady=10, ipadx=5, ipady=5, sticky=W)
        self.btn_clear.grid(row=1, padx=272, pady=10, ipadx=5, ipady=5, sticky=W)
        self.tabs.grid(row=2, padx=5, pady=5, ipadx=5, ipady=2, sticky=W)

        # weights of rows and columns
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=1)

        # bind keyboard shortcuts
        self.root.bind('<Control-o>', self.OpenFile)
        self.root.bind('<Control-q>', self.CloseFile)
        self.root.bind('<Control-p>', self.PreviewAudio)
        self.root.bind('<Control-r>', self.RenderToFile)
        self.root.bind('<Control-a>', self.ClearAllLines)
        self.root.bind('<F1>', self.Docs)
        self.root.bind('<F12>', self.About)

        # protocol for exiting the program
        self.root.protocol('WM_DELETE_WINDOW',self.OnProgramQuit)

        # bind mouse actions for the canvas
        self.viewport.bind('<Button-1>', self.StartLineOrLoadPic)
        self.viewport.bind('<B1-Motion>', self.GrowLine)
        self.viewport.bind('<Configure>', self.ResizeCanvas)

        # create DSP object
        self.dsp = DSP.Dsp(gui=self)

        # loading values for options from the INI file, or defaults if INI not found
        try:
            optionsfile = open('ImageSound.ini','r')
            sr  = optionsfile.readline()
            imp = optionsfile.readline()
            aa  = optionsfile.readline()
            self.SRselect.set(sr[12])
            self.ImPreview.set(imp[12])
            self.AntiAlias.set(aa[13])
            optionsfile.close()
        except IOError:
            self.SRselect.set(1)
            self.ImPreview.set(1)
            self.AntiAlias.set(1)
        self.ChangeSR()
        self.AAMode()

    def ChangeSR(self, event=None):
        sel_value = self.SRselect.get()
        if sel_value == '1':
            DSP.SAMPLE_RATE = 44100
        elif sel_value == '2':
            DSP.SAMPLE_RATE = 48000
        elif sel_value == '3':
            DSP.SAMPLE_RATE = 88200
        elif sel_value == '4':
            DSP.SAMPLE_RATE = 96000
        elif sel_value == '5':
            DSP.SAMPLE_RATE = 174200
        elif sel_value == '6':
            DSP.SAMPLE_RATE = 192000

    def AAMode(self, event=None):
        sel_value = self.AntiAlias.get()
        if sel_value == '1':
            DSP.ANTIALIASING = 0
        elif sel_value == '2':
            DSP.ANTIALIASING = 1

    def ImPreviewMode(self, event=None):
        if self.is_img_loaded != 0:
            sel_value = self.ImPreview.get()
            self.viewport.delete('image')
            if sel_value == '1':
                self.viewport.create_image((4, 4), anchor=NW, image=im_tk, tag='image')
            else:
                self.viewport.create_image((4, 4), anchor=NW, image=im_lum_tk, tag='image')
            self.viewport.tag_lower('image')

    def ResizeCanvas(self, event=None):
        if self.is_img_loaded == 0:
            if self.textid != 0:
                self.viewport.delete('openfiletext')
            # position text on canvas to notify user he can load the image by clicking it
            textpos = (self.viewport.winfo_width(), self.viewport.winfo_height())
            self.textid = self.viewport.create_text(textpos[0] / 2, textpos[1] / 2, text="Click here to load an image!",
                                                    justify='center', font='arial 20 bold', tag='openfiletext')

    def ClearAllLines(self, event=None):
        if self.is_img_loaded != 0:
            self.btn_preview.config(state=DISABLED)
            self.btn_render.config(state=DISABLED)
            self.was_previewed = False
            self.seg.clear()
            for i in range(self.NUM_TABS):
                self.viewport.delete('line' + str(i))

    def CustomLine(self, x0, y0, x1, y1, width, color, name, canvas):
        try:
            slope = (y1 - y0) / (x1 - x0)
        except ZeroDivisionError:
            slope = 1000    # slope is undefined for vertical lines, so just use some positive number > 1 to be able to draw it

        tmp_list = list()
        for i in range(width):
            if -1 <= slope <= 1:
                obj = canvas.create_line(x0, y0 + i, x1, y1 + i, fill=color, tag=name)
                rr, cc = skimage.draw.line(y0 + i - 4, x0 - 4, y1 + i - 4, x1 - 4)
            else:
                obj = canvas.create_line(x0 + i, y0, x1 + i, y1, fill=color, tag=name)
                rr, cc = skimage.draw.line(y0 - 4, x0 + i - 4, y1 - 4, x1 + i - 4)
            try:
                tmp_list.append(self.imag[cc, rr])
                self.harm_count_val[self.current_tab] = int(self.harm_count[self.current_tab].get())
            except:
                self.harm_count_val[self.current_tab] = i
                break
        self.seg[self.current_tab] = tmp_list

    def StartLineOrLoadPic(self, event):
        if self.is_img_loaded != 0:
            self.start = event
            self.drawn = None
        else:
            self.OpenFile()

    def GrowLine(self, event):
        if self.is_img_loaded != 0:
            if self.btn_preview.cget('state') == DISABLED:
                self.btn_preview.config(state=NORMAL)
                self.btn_render.config(state=NORMAL)
            if self.objectId != 0:
                event.widget.delete('line' + str(self.current_tab))
            viewport = event.widget
            if self.drawn:
                viewport.delete(self.drawn)
            try:
                # limit the draggable mouse area to just the image dimensions
                if event.x < 4:
                    currentx = 4
                elif event.x > self.imgsize[0]:
                    currentx = self.imgsize[0]
                else:
                    currentx = event.x
                if event.y < 4:
                    currenty = 4
                elif event.y > self.imgsize[1]:
                    currenty = self.imgsize[1]
                else:
                    currenty = event.y
                # draw the vector
                objectId = 1
                self.CustomLine(self.start.x, self.start.y, currentx, currenty, width=int(self.harm_count[self.current_tab].get()),
                                color=self.COLORS[self.current_tab], name='line' + str(self.current_tab), canvas=self.viewport)
                self.drawn = objectId
            except:
                raise

    def AdjustLineWidth(self):
        tag = 'line' + str(self.current_tab)
        if self.viewport.find_withtag(tag):
            linecoords = self.viewport.coords(tag)
            self.viewport.delete(tag)
            self.CustomLine(int(linecoords[0]), int(linecoords[1]), int(linecoords[2]), int(linecoords[3]),
                            width=int(self.harm_count[self.current_tab].get()), color=self.COLORS[self.current_tab],
                            name='line' + str(self.current_tab), canvas=self.viewport)
            self.harm_count_val[self.current_tab] = int(self.harm_count[self.current_tab].get())

    def CloseFile(self, event=None):
        self.viewport.delete('image')
        self.viewport.grid(sticky=N+S+W+E)
        self.ClearAllLines(event=None)
        self.ResizeCanvas(event=None)
        self.is_img_loaded = 0

    def OpenFile(self, event=None):
        try:
            # keeps the reference to loaded image in this variable
            global im_tk
            global im_lum_tk
            # open file dialog
            imgfile = filedialog.askopenfilename(title='Open Image',
                                                 filetypes=[('All supported files', '.bmp .eps .gif .jpg .jpeg .png .pbm .pgm .ppm .tif .tiff'),
                                                            ('Bitmap files', '.bmp'),
                                                            ('EPS files', '.eps'),
                                                            ('GIF files', '.gif'),
                                                            ('JPEG files', '.jpg .jpeg'),
                                                            ('PNG files', '.png'),
                                                            ('PPM files', '.pbm .pgm .ppm'),
                                                            ('TIFF files', '.tif .tiff')])
            # open the image, convert to grayscale
            im = Image.open(imgfile)
            im_tk = ImageTk.PhotoImage(im)
            im_lum = im.convert('L')
            im_lum_tk = ImageTk.PhotoImage(im_lum)
            # convert the image to a numpy array
            self.imag = array(im)
            self.imag = self.imag.swapaxes(1,0) # swap the axes, numpy reads Y first, then X, for some reason
            # reference the numpy array in the DSP script
            self.dsp.set_img(self.imag)
            # show the image on GUI
            self.ClearAllLines()
            self.viewport.grid(sticky=N+W)
            self.viewport.config(width=im.size[0] + 4, height=im.size[1] + 4)
            self.imgsize = (int(self.viewport.cget('width')) - 1,int(self.viewport.cget('height')) - 1)
            self.is_img_loaded = im_tk
            self.ImPreviewMode()
            self.viewport.delete('openfiletext')
        except:
            pass

    def PreviewAudio(self, event=None):
        if self.btn_preview.cget('state') != DISABLED:
            self.was_previewed = True
            self.dsp.render_segments(self.seg, preview=True, filename=None)

    def RenderToFile(self, event=None):
        if self.btn_render.cget('state') != DISABLED:
            outfile = filedialog.asksaveasfilename(title='Render To File...', filetypes=[('WAV files', '.wav')], defaultextension='.wav')
            if outfile != '':
                # just write the file if it was already previewed, don't recalculate it
                if self.was_previewed:
                    self.dsp.generate_sample(out_buffer=None, preview=False, filename=outfile, was_previewed=True)
                else:
                    self.dsp.render_segments(self.seg, preview=False, filename=outfile)
            else:
                return

    def About(self, event=None):
        aboutscreen = Toplevel()
        aboutscreen.title('About ImageSound')
        info = Label(aboutscreen, justify='left', text='Programmed by Mario Krušelj\n\n\nMaster\'s Degree Thesis\n\n' +
                    'Converting Digital Image to Sound\nUsing Superposed and Parameterized\nVectors and Additive Synthesis\n\n\n' +
                    'Faculty of Electrical Engineering\nJosip Juraj Strossmayer University of Osijek\n\n\n © 2015-20xx')
        info.grid(padx=10, pady=10, sticky=N)
        # if the program is loaded from within ImageSound.data folder
        try:
            pic = ImageTk.PhotoImage(Image.open('images/author.png'))
        # if it's not, it's ran via BAT file, fix the path!
        except:
            pic = ImageTk.PhotoImage(Image.open('ImageSound.data/images/author.png'))
        logo = Label(aboutscreen, image=pic)
        logo.grid(row=0, column=1, padx=10, pady=10)
        closeabout = Button(aboutscreen, text='Close', padx=5, pady=5, command=aboutscreen.destroy)
        closeabout.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        closeabout.focus_force()
        aboutscreen.bind('<Escape>', lambda close: aboutscreen.destroy())
        aboutscreen.bind('<Return>', lambda close: aboutscreen.destroy())
        self.ModalPopup(aboutscreen)

    def Docs(self, event=None):
        root = splitdrive(abspath(getsourcefile(lambda:0)))[0]
        try:
            proc = subprocess.Popen('Mario Krušelj - Pretvorba digitalne slike u zvuk superponiranjem i parametrizacijom vektora.pdf', shell=True)
        except:
            proc = subprocess.Popen('explorer ' + root, shell=True)

    def ModalPopup(self, wnd):
        time.sleep(0.1)
        # hide it so you don't see it moving across the screen
        wnd.attributes('-alpha', 0.0)
        wnd.update_idletasks()
        w = wnd.winfo_screenwidth()
        h = wnd.winfo_screenheight()
        size = tuple(int(_) for _ in wnd.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        wnd.geometry("%dx%d+%d+%d" % (size + (x, y - 50)))
        wnd.resizable(width=False, height=False)
        # now we can show it, nicely centered
        wnd.attributes('-alpha', 1.0)
        # make it modal!
        wnd.focus_set()
        wnd.transient(self.root)
        wnd.grab_set()
        self.root.wait_window(wnd)

    def GetCurrentTab(self, event):
        self.current_tab = event.widget.index('current')

    def OnProgramQuit(self):
        if messagebox.askokcancel('Quit ImageSound','Do you really want to quit ImageSound?'):
            try:
                ini = open('ImageSound.ini','w+')
                ini.write('sample_rate=' + self.SRselect.get() + '\n')
                ini.write('img_preview=' + self.ImPreview.get() + '\n')
                ini.write('antialiasing=' + self.AntiAlias.get() + '\n')
                ini.close()
            except:
                pass
            self.root.destroy()

    def OnMouseWheel(self, event):
        # check if the user scrolls up (positive) or down (negative)
        if event.delta > 0:
            event.widget.invoke('buttonup')
        else:
            event.widget.invoke('buttondown')

    def OnMouseWheelCtrl(self, event):
        # check if the user scrolls up (positive) or down (negative)
        if event.delta > 0:
            for i in range(10):
                event.widget.invoke('buttonup')
        else:
            for i in range(10):
                event.widget.invoke('buttondown')

    def ValidateIfNum(self, new_value, user_input, widget_name):
        # disallow anything but numbers in the input
        valid = user_input == '' or user_input.isdigit()
        if not valid:
            self.root.bell()
        return valid

if __name__ == '__main__':
    mainwindow = ImageSoundGUI()
    mainloop()
