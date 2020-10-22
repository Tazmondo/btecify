import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from typing import List


class musicgui:
    playlists: List[str]
    selectedplaylist: tk.StringVar

    songqueue: tk.StringVar

    songlist = []
    songlistvar: tk.StringVar

    volume: tk.IntVar
    lastvol = -1

    output = [""]

    def __init__(self, playlistnames):
        self.root = ThemedTk(theme='black')
        self.root.option_add('*tearOff', tk.FALSE)
        self.root.wm_title("sPoTiFy")
        self.root.wm_iconbitmap('shitify.ico')

        self.selectedplaylist = tk.StringVar()
        self.playlists = playlistnames
        self.songqueue = tk.StringVar(value=[])
        self.volume = tk.IntVar(value=50)
        self.songlistvar = tk.StringVar(value=self.songlist)

        primaryframe = ttk.Frame(self.root)
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
        queuelist = tk.Listbox(songlistlabelframe, height=15, listvariable=self.songqueue)
        songlistlabelframe.grid(column=2, row=0)
        queuelist.grid()

        # BOTTOM LEFT LOGO
        shitifyiconimage = tk.PhotoImage(file="shitify64.png")
        shitifyiconlabel = ttk.Label(primaryframe, image=shitifyiconimage)
        shitifyiconlabel.grid(column=0, row=1, sticky='nesw')

        # BOTTOM MIDDLE BUTTONS
        bottommiddleframe = ttk.Frame(primaryframe, relief='groove', padding=5)
        bottommiddleframe.grid(column=1, row=1,  sticky='ns')

        pausebutton = ttk.Button(bottommiddleframe, text="PAUSE", command=self._pause)
        pausebutton.grid(row=0, column=0, columnspan=2, sticky='ew')

        skipbutton = ttk.Button(bottommiddleframe, text="SKIP", command=self._skip)
        skipbutton.grid(row=1, sticky='w')

        blacklistbutton = ttk.Button(bottommiddleframe, text="BLACKLIST", command=self._blacklist)
        blacklistbutton.grid(row=1, column=1, sticky='e')

        volumeslider = ttk.LabeledScale(bottommiddleframe, from_=0, to=100, variable=self.volume, compound='bottom')
        volumeslider.scale.set(30)
        volumeslider.scale.configure(command=self._volchange)
        volumeslider.grid(row=2, columnspan=2, sticky='ew')

        # BOTTOM RIGHT PLAYLIST SELECT
        playlistselectframe = ttk.Frame(primaryframe, relief='groove', padding=3)
        playlistselectframe.grid(row=1, column=2, sticky='ns')

        self.playlistselectcombobox = ttk.Combobox(playlistselectframe, values=self.playlists, textvariable=self.selectedplaylist,
                                     state='readonly')
        self.playlistselectcombobox.set("No playlist selected.")
        self.playlistselectcombobox.grid(sticky='ewn')

        self.playlistselectbutton = ttk.Button(playlistselectframe, text="SELECT", command=self._chooseplaylist)
        self.playlistselectbutton.grid(row=1)

        self._updatebasedonvalues()
        self.root.mainloop()

    def _updatebasedonvalues(self):
        if self.playlistselectcombobox.get() == "No playlist selected.":
            self.playlistselectbutton.configure(state=tk.DISABLED)
        else:
            self.playlistselectbutton.configure(state=tk.NORMAL)

        self.root.after(50, self._updatebasedonvalues)

    def _skip(self, *args):
        if not self.output[0]:
            self.output = ["skip"]

    def _pause(self, *args):
        if not self.output[0]:
            self.output = ["pause"]

    def _blacklist(self, *args):
        if not self.output[0]:
            self.output = ["blacklist"]

    def _chooseplaylist(self, *args):
        print(self.selectedplaylist.get())

    def _volchange(self, *args):
        volume = self.volume.get()
        if volume != self.lastvol:
            self.output = ['volume', volume]

    def updateplaylists(self, playlists):
        self.playlists = playlists

    def addsong(self, song):
        self.songlist.append(song)



ipl = ('music', 'bangers')
x = musicgui(ipl)
x.updateplaylists('calm')
