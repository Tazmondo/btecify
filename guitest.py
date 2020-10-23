import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from typing import List
import threading
from time import sleep
import main


class globalvars:
    pass
G = globalvars()


class musicgui:
    playlists: List[str]
    selectedplaylist: tk.StringVar

    songqueue: tk.StringVar

    songlist = []
    songlistvar: tk.StringVar

    volume: tk.IntVar
    lastvol = -1

    output = [""]

    def __init__(self, playlists: List[main.Playlist]):
        root = ThemedTk(theme='black')
        root.option_add('*tearOff', tk.FALSE)
        root.wm_title("sPoTiFy")
        root.wm_iconbitmap('shitify.ico')

        self.selectedplaylist = tk.StringVar()
        self.playlists = playlists
        self.songqueue = tk.StringVar(value=[])
        self.volume = tk.IntVar(value=50)
        self.songlistvar = tk.StringVar(value=self.songlist)

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

        songinfo = ttk.Label(playingframe, text="No song playing")
        songinfo.grid(column=0, row=0)

        songdesc = ttk.Label(playingframe, text="")
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
        bottommiddleframe.grid(column=1, row=1, sticky='ns')

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

        playlistselectcombobox = ttk.Combobox(playlistselectframe, values=self.playlists,
                                              textvariable=self.selectedplaylist,
                                              state='readonly')
        playlistselectcombobox.set("No playlist selected.")
        playlistselectcombobox.grid(sticky='ewn')

        playlistselectbutton = ttk.Button(playlistselectframe, text="SELECT", command=self._chooseplaylist)
        playlistselectbutton.grid(row=1)

        def _updatebasedonvalues():
            if playlistselectcombobox.get() == "No playlist selected.":
                playlistselectbutton.configure(state=tk.DISABLED)
            else:
                playlistselectbutton.configure(state=tk.NORMAL)

            if songinfo['text'] == "No song playing":
                pausebutton.configure(state=tk.DISABLED)
                blacklistbutton.configure(state=tk.DISABLED)
                skipbutton.configure(state=tk.DISABLED)
            else:
                pausebutton.configure(state=tk.NORMAL)
                blacklistbutton.configure(state=tk.NORMAL)
                skipbutton.configure(state=tk.NORMAL)

            root.after(100, _updatebasedonvalues)

        _updatebasedonvalues()

        G.musicgui = self
        root.mainloop()

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
        if self.output[0] in ('volume', ''):
            volume = self.volume.get()
            if volume != self.lastvol:
                self.output = ['volume', volume]

    def updateplaylists(self, playlists):
        self.playlists.append(playlists)

    def addsong(self, song):
        self.songlist.append(song)


G.musicgui: musicgui = None

if __name__ == '__main__':
    ipl = ['music', 'bangers']
    x = threading.Thread(target=musicgui, args=[ipl])
    x.start()
    while G.musicgui is None:
        pass
    gui = G.musicgui
    gui.updateplaylists('calm')
