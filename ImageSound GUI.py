try:
    from Tkinter import *
    import tkFileDialog as filedialog
    import ttk
except ImportError:
    from tkinter import *
    from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import numpy as np
from scipy import misc
import time
import sys
import DSP


class ImageSoundGUI:
    NUM_TABS = 16
    NUM_PARTIALS = 128
    COLORS = ('#FF0000', '#FF9900', '#FFBB00', '#FFFF00', '#99FF00', '#00FF00', '#00FF99', '#00FFCC',
              '#00CCFF', '#0099FF', '#0000FF', '#9900FF', '#CC00FF', '#FF00FF', '#FF0099', '#FF9999')
    MODE_OPT = ['All', 'Even', 'Odd', 'Skip 2', 'Skip 3', 'Skip 4', 'Sub All',
                'Sub Even', 'Sub Odd', 'Sub Skip 2', 'Sub Skip 3', 'Sub Skip 4']
    labels = []  # tkinter widget IDs for all labels
    harm_count = []  # tkinter widget IDs for all Harmonics Count spinboxes
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

    def __init__(self):
        # root window of the whole program
        self.root = Tk()
        self.root.title('ImageSound')
        self.root.minsize(800, 600)
        # root window dimensions and positioning
        self.ws = self.root.winfo_screenwidth()
        self.wh = self.root.winfo_screenheight()
        self.w = self.ws * 0.5
        self.h = self.wh * 0.75
        self.x = (self.ws / 2) - (self.w / 2)
        self.y = (self.wh / 2) - (self.h / 2)
        self.root.geometry('800x600+%d+%d' % (self.x-25, self.y))

        # maximize the window on program open
        # self.root.state('zoomed')

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
                              accelerator='Ctrl+L',
                              underline=8,
                              command=self.ClearAllLines)
        menu_file.add_separator()
        menu_file.add_command(label='Exit',
                              accelerator='Alt+F4',
                              command=self.root.quit,
                              underline=1)
        menu_help = Menu(main_menu, tearoff=0)
        menu_help.add_command(label='About...',
                              accelerator='F12',
                              underline=0,
                              command=self.About)
        main_menu.add_cascade(label='File', underline=0, menu=menu_file)
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
            self.tabs.add(frame, text='  ' + str(i+1) + '  ')
            label = Label(frame, text='Harmonics Count:')
            label.grid(row=0, padx=10, pady=5, sticky=E)
            self.labels += [label]
            self.harm_count += [Spinbox(frame, command=self.AdjustLineWidth, from_=1, to=self.NUM_PARTIALS, width=5, justify='right', validate='all', validatecommand=self.vldt_ifnum_cmd)]
            self.harm_count[i].insert(0, 8)
            self.harm_count[i].delete(1, 'end')
            self.harm_count[i].grid(padx=5, pady=10, row=0, column=1, sticky=W)
            self.harm_count[i].bind('<MouseWheel>', self.OnMouseWheel)
            self.harm_count[i].bind('<Control-c>', lambda e: 'break')
            self.harm_count[i].bind('<Control-v>', lambda e: 'break')
            self.harm_count[i].bind('<Control-x>', lambda e: 'break')
            label = Label(frame, text='Baseline (MIDI Note):')
            label.grid(padx=10, pady=5, row=0, column=2, sticky=E)
            self.labels += [label]
            self.baseline_freq += [Spinbox(frame, from_=21, to=108, width=6, justify='right', validate='all', validatecommand=self.vldt_ifnum_cmd)]
            # setting the default value to 69 by invoking button presses of the spinbox. hacky, but works. needs to be like this!
            for j in range(48):
                self.baseline_freq[i].invoke('buttonup')
            self.baseline_freq[i].grid(
                padx=5, pady=5, row=0, column=3, sticky=W)
            self.baseline_freq[i].bind('<MouseWheel>', self.OnMouseWheel)
            self.baseline_freq[i].bind('<Control-c>', lambda e: 'break')
            self.baseline_freq[i].bind('<Control-v>', lambda e: 'break')
            self.baseline_freq[i].bind('<Control-x>', lambda e: 'break')
            label = Label(frame, text='Read Speed (ms):')
            label.grid(padx=10, pady=5, row=0, column=4, sticky=E)
            self.labels += [label]
            self.read_speed += [Spinbox(frame, from_=1000, to=60000, width=6, increment=10, justify='right', validate='all', validatecommand=self.vldt_ifnum_cmd)]
            self.read_speed[i].grid(padx=5, pady=5, row=0, column=5, sticky=W)
            self.read_speed[i].bind('<MouseWheel>', self.OnMouseWheel)
            self.read_speed[i].bind('<Control-MouseWheel>', self.OnMouseWheelCtrl)
            self.read_speed[i].bind('<Control-c>', lambda e: 'break')
            self.read_speed[i].bind('<Control-v>', lambda e: 'break')
            self.read_speed[i].bind('<Control-x>', lambda e: 'break')
            label = Label(frame, text='Harmonics Mode:')
            label.grid(padx=10, row=1, column=0, sticky=E)
            self.labels += [label]
            self.harm_mode_var += [StringVar()]
            self.harm_mode_var[i].set(self.MODE_OPT[0])
            self.harm_mode += [OptionMenu(frame, self.harm_mode_var[i], *self.MODE_OPT)]
            self.harm_mode[i].config(width=6, justify='left')
            self.harm_mode[i].grid(row=1, column=1, sticky=W)
            label = Label(frame, text='Delay Time (ms):')
            label.grid(padx=10, row=1, column=4, sticky=E)
            self.labels += [label]
            self.delay_time += [Spinbox(frame, from_=0, to=60000, width=6, increment=10, justify='right', validate='all', validatecommand=self.vldt_ifnum_cmd)]
            self.delay_time[i].grid(padx=5, pady=10, row=1, column=5, sticky=W)
            self.delay_time[i].bind('<MouseWheel>', self.OnMouseWheel)
            self.delay_time[i].bind('<Control-MouseWheel>', self.OnMouseWheelCtrl)
            self.delay_time[i].bind('<Control-c>', lambda e: 'break')
            self.delay_time[i].bind('<Control-v>', lambda e: 'break')
            self.delay_time[i].bind('<Control-x>', lambda e: 'break')

        # layout managing
        self.viewport.grid(columnspan=3, padx=5, pady=5, sticky=N+S+W+E)
        self.btn_preview.grid(row=1, padx=85, pady=10, ipadx=5, ipady=5, sticky=W)
        self.btn_render.grid(row=1, padx=200, pady=10, ipadx=5, ipady=5, sticky=W)
        self.btn_clear.grid(row=1, padx=305, pady=10, ipadx=5, ipady=5, sticky=W)
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
        self.root.bind('<Control-l>', self.ClearAllLines)
        self.root.bind('<F12>', self.About)

        # bind mouse actions for the canvas
        self.viewport.bind('<Button-1>', self.StartLineOrLoadPic)
        self.viewport.bind('<B1-Motion>', self.GrowLine)
        self.viewport.bind('<Configure>', self.ResizeCanvas)

        # create DSP object
        self.dsp = DSP.Dsp(gui=self)

    def ResizeCanvas(self, event):
        if self.is_img_loaded == 0:
            if self.textid != 0:
                self.viewport.delete('openfiletext')
            # position text on canvas to notify user he can load the image by clicking it
            textpos = (self.viewport.winfo_width(), self.viewport.winfo_height())
            self.textid = self.viewport.create_text(textpos[0] / 2, textpos[1] / 2, text="Click here to load an image!", justify='center', font='arial 20 bold', tag='openfiletext')

    def ClearAllLines(self, event=None):
        if self.is_img_loaded != 0:
            self.btn_preview.config(state=DISABLED)
            self.btn_render.config(state=DISABLED)
            self.seg.clear()
            for i in range(self.NUM_TABS):
                self.viewport.delete('line' + str(i))

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
                objectId = self.viewport.create_line(self.start.x, self.start.y, currentx, currenty,
                                                     width=self.harm_count[self.current_tab].get(),
                                                     fill=self.COLORS[self.current_tab],
                                                     stipple='gray75', tag='line' + str(self.current_tab))
                length = int(np.hypot(currenty-self.start.y, currentx-self.start.x))
                x, y = np.linspace(self.start.x - 4, currentx - 4, length), np.linspace(self.start.y - 4, currenty - 4, length)
                self.seg[self.current_tab] = self.imag[x.astype(np.int), y.astype(np.int)]
                self.drawn = objectId
            except:
                raise

    def AdjustLineWidth(self):
        tag = 'line' + str(self.current_tab)
        if self.viewport.find_withtag(tag):
            self.viewport.itemconfig(tag,width=self.harm_count[self.current_tab].get())

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
            imgfile = filedialog.askopenfilename(title='Open Image',
                                                 filetypes=[('All supported files', '.bmp .jpg .jpeg .png'),
                                                            ('Bitmap files', '.bmp'),
                                                            ('JPEG files', '.jpg .jpeg'),
                                                            ('PNG files', '.png')])
            im = Image.open(imgfile)
            im_tk = ImageTk.PhotoImage(im)
            self.imag = np.array(im)
            self.imag = self.imag.swapaxes(1,0) # swap first two axes, numpy goes Y then X for some reason when importing image
            self.dsp.set_img(self.imag)
            self.ClearAllLines()
            self.viewport.grid(sticky=N+W)
            self.viewport.config(width=im.size[0] + 4, height=im.size[1] + 4)
            self.imgsize = (int(self.viewport.cget('width')) - 1,int(self.viewport.cget('height')) - 1)
            self.is_img_loaded = im_tk
            sprite = self.viewport.create_image((4, 4), anchor=NW, image=im_tk, tag='image')
        except:
            print('File not found, or dialog cancelled!')
            #raise

    def PreviewAudio(self, event=None):
        if self.btn_preview.cget('state') != DISABLED:
            self.dsp.render_segments(self.seg, preview=True)

    def RenderToFile(self, event=None):
        if self.btn_render.cget('state') != DISABLED:
            self.dsp.render_segments(self.seg, preview=False)

    def About(self, event=None):
        aboutscreen = Toplevel()
        aboutscreen.title('About ImageSound')
        info = Label(aboutscreen, text='Programmed by Mario Krušelj\n\n\nMaster\'s Degree Thesis\n\nConverting Digital Image to Sound\nUsing Additive Synthesis\n\n\nFaculty of Electrical Engineering\nJosip Juraj Strossmayer University of Osijek\n\n\n© 2015-20xx', justify='left')
        info.grid(padx=10, pady=10, sticky=N)
        pic = ImageTk.PhotoImage(Image.open('mario.png'))
        logo = Label(aboutscreen, image=pic)
        logo.grid(row=0, column=1, padx=10, pady=10)
        closeabout = Button(aboutscreen, text='Close', padx=5, pady=5, command=aboutscreen.destroy)
        closeabout.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        closeabout.focus_force()
        aboutscreen.bind('<Escape>', lambda close: aboutscreen.destroy())
        aboutscreen.bind('<Return>', lambda close: aboutscreen.destroy())
        self.ModalPopup(aboutscreen)

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
        wnd.geometry("%dx%d+%d+%d" % (size + (x, y)))
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

    def ValidateIfNum(self, user_input, new_value, widget_name):
        # disallow anything but numbers in the input
        valid = new_value == '' or new_value.isdigit()
        # now that we've ensured the input is only integers, range checking!
        if valid:
            # get minimum and maximum values of the widget to be validated
            minval = int(self.root.nametowidget(widget_name).config('from')[4])
            maxval = int(self.root.nametowidget(widget_name).config('to')[4])
            # make sure that input doesn't have more digits than the maximum value
            # and that it's in min-max range
            if len(user_input) > len(str(maxval)) or int(user_input) not in range(minval, maxval):
                valid = False
        if not valid:
            self.root.bell()
        return valid

if __name__ == '__main__':
    mainwindow = ImageSoundGUI()
    mainloop()
