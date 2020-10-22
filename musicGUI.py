import tkinter as tk
from tkinter import ttk

class tut1:
    def __init__(self):
        root = tk.Tk()
        root.title("Feet to Meters")

        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.feet = tk.StringVar()
        feet_entry = ttk.Entry(mainframe, width=7, textvariable=self.feet)
        feet_entry.grid(column=2, row=1, sticky=(tk.W, tk.E))

        self.meters = tk.StringVar()
        ttk.Label(mainframe, textvariable=self.meters).grid(column=2, row=2, sticky=(tk.W, tk.E))

        ttk.Button(mainframe, text="Calculate", command=self.calculate).grid(column=3, row=3, sticky=tk.W)

        ttk.Label(mainframe, text="feet").grid(column=3, row=1, sticky=tk.W)
        ttk.Label(mainframe, text="is equivalent to").grid(column=1, row=2, sticky=tk.E)
        ttk.Label(mainframe, text="meters").grid(column=3, row=2, sticky=tk.W)

        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        feet_entry.focus()
        root.bind("<Return>", self.calculate)

        root.mainloop()
    def calculate(self,*args):
        try:
            value = float(self.feet.get())
            self.meters.set(int(0.3048 * value * 10000.0 + 0.5)/10000.0)
        except ValueError:
            pass

class musicgui:
    playlists = None
    selectedplaylist = None

    songqueue = None

    def __init__(self, playlistnames):
        root = tk.Tk()
        root.option_add('*tearOff', tk.FALSE)
        root.wm_title("sPoTiFy")
        root.wm_iconbitmap('shitify.ico')

        self.selectedplaylist = tk.StringVar()
        self.playlists = playlistnames
        self.songqueue = tk.StringVar(value=[f"{i}: Temp" for i in range(1,101)])

        primaryframe = ttk.Frame(root)
        primaryframe.grid()

        # QUEUE
        queuelabelframe = ttk.Labelframe(primaryframe, text="Song queue")
        queuelist = tk.Listbox(queuelabelframe, height=15, listvariable=self.songqueue, state="disabled")
        queuelabelframe.grid(column=0, row=0)
        queuelist.grid()

        # DEFINING THE PLAYING FRAME
        playingframe = ttk.Frame(primaryframe, relief='groove', padding=5)
        playingframe.grid(column=1, row=0, sticky='')

        songinfo = ttk.Label(playingframe, text="No song selected")
        songinfo.grid(column=0, row=0)

        songdesc = ttk.Label(playingframe, text="No song selected")
        songdesc.grid(column=0, row=1)

        playingframeseperator = ttk.Separator(playingframe, orient=tk.HORIZONTAL)
        playingframeseperator.grid(column=0, row=2, sticky='we')

        songprogress = ttk.Progressbar(playingframe, orient=tk.HORIZONTAL, mode='determinate')
        songprogress.grid(column=0, row=3, sticky='s')

        # SONG SELECTION
        songlistlabelframe = ttk.Labelframe(primaryframe, text="Song list")
        templistvalue = ['test', 'test2', 'test3']
        songlist = tk.StringVar(value=list(reversed(templistvalue)))
        queuelist = tk.Listbox(songlistlabelframe, height=15, listvariable=songlist)
        songlistlabelframe.grid(column=2, row=0)
        queuelist.grid()

        # BOTTOM LEFT LOGO
        shitifyiconimage = tk.PhotoImage(file="shitify64.png")
        shitifyiconlabel = ttk.Label(primaryframe, image=shitifyiconimage)
        shitifyiconlabel.grid(column=0, row=1, sticky='nesw')

        # BOTTOM MIDDLE BUTTONS
        bottommiddleframe = ttk.Frame(primaryframe, relief='groove', padding=5)
        bottommiddleframe.grid(column=1, row=1,  sticky='ns')

        pausebutton = ttk.Button(bottommiddleframe, text="PAUSE", command=self.pause)
        pausebutton.grid(row=0, column=0, columnspan=2, sticky='ew')

        skipbutton = ttk.Button(bottommiddleframe, text="SKIP", command=self.skip)
        skipbutton.grid(row=1)

        blacklistbutton = ttk.Button(bottommiddleframe, text="BLACKLIST", command=self.blacklist)
        blacklistbutton.grid(row=1, column=1)

        # BOTTOM RIGHT PLAYLIST SELECT
        playlistselectframe = ttk.Frame(primaryframe, relief='groove', padding=3)
        playlistselectframe.grid(row=1, column=2, sticky='ns')

        playlistselectcombobox = ttk.Combobox(playlistselectframe,
                                              values=self.playlists,
                                              textvariable=self.selectedplaylist)
        playlistselectcombobox.grid(sticky='ewn')

        playlistselectbutton = ttk.Button(playlistselectframe, text="SELECT", command=self.chooseplaylist)
        playlistselectbutton.grid(row=1)

        root.mainloop()

    def skip(self, *args):
        print("skip")
        pass

    def pause(self, *args):
        print("pause")
        pass

    def blacklist(self, *args):
        print("bl")
        pass

    def updateplaylists(self, playlists):
        self.playlists = playlists

    def chooseplaylist(self, *args):
        print(self.selectedplaylist.get())
        pass


playlists = ('music', 'bangers')
musicgui(playlists)
