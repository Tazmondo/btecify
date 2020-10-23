import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from typing import List
import threading
from time import sleep
import main
from sys import exit


class globalvars:
    pass
G = globalvars()


class Musicgui:
    playlists: List[main.Playlist]
    playlistnames: List[str]
    selectedplaylist: tk.StringVar

    songqueuevar: tk.StringVar

    songlistvar: tk.StringVar

    progressbarvar: tk.IntVar

    volume: tk.IntVar
    lastvol = -1

    output = [""]
    playingsong: main.Song = None
    songqueue: List[main.Song] = []
    songlist: List[main.Song] = []
    progressbar: int = 0
    paused: bool = False

    changes = {
        'paused': False,
        'songlist': False,
        'songqueue': False,
        'songinfo': False,
        'playlistoptions': False,
        'progressbar': False,
        'playlistnotselected': True

    }

    def __init__(self, playlists: List[main.Playlist], defaults: dict):
        root = ThemedTk(theme='black')
        root.option_add('*tearOff', tk.FALSE)
        root.wm_title("sPoTiFy")
        root.wm_iconbitmap('shitify.ico')
        root.resizable(width=False, height=False)

        def _onclose():
            self.output = ["EXIT"]
            exit("Closing GUI thread.")
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", _onclose)

        self.selectedplaylist = tk.StringVar()
        self.playlists = playlists
        self._generateplaylistnames()
        self.songqueuevar = tk.StringVar(value=[])
        self.volume = tk.IntVar(value=50)
        self.songlistvar = tk.StringVar(value=[])
        self.progressbarvar = tk.IntVar(value=0)

        # MENU
        menubar = tk.Menu(root)
        root.configure(menu=menubar)

        menuplaylist = tk.Menu(menubar)
        menuqueue = tk.Menu(menubar)

        menubar.add_cascade(menu=menuplaylist, label="Playlist")
        menubar.add_cascade(menu=menuqueue, label="Queue")

        menuplaylist.add_command(label="New", command=self._newplaylist)
        menuplaylist.add_command(label="Unwatch", command=self._unwatchplaylist)

        menuqueue.add_command(label="Requeue", command=self._requeue)

        # PRIMARY FRAME

        primaryframe = ttk.Frame(root)
        primaryframe.grid()

        # QUEUE
        queuelabelframe = ttk.Labelframe(primaryframe, text="Song queue", relief='groove', borderwidth=5, padding=5)
        queuelabelframe.grid(column=0, row=0, columnspan=2, sticky='nswe')

        queuelist = tk.Listbox(queuelabelframe, height=15, listvariable=self.songqueuevar, state="disabled")
        queuelistscrollbar = ttk.Scrollbar(queuelabelframe, orient=tk.VERTICAL, command=queuelist.yview)

        queuelist.grid(column=0, row=0, sticky='nswe')
        queuelistscrollbar.grid(column=1, row=0, sticky='ns')

        queuelist['yscrollcommand'] = queuelistscrollbar.set

        # DEFINING THE PLAYING FRAME
        playingframe = ttk.Frame(primaryframe, relief='groove', padding=5)
        playingframe.grid(column=2, row=0, sticky='ew')

        songinfo = ttk.Label(playingframe, text="No song playing", justify=tk.CENTER, anchor=tk.CENTER)
        songinfo.grid(column=0, row=0, sticky='ew')

        songdesc = ttk.Label(playingframe, text="", justify=tk.CENTER, anchor=tk.CENTER)
        songdesc.grid(column=0, row=1)

        playingframeseperator = ttk.Separator(playingframe, orient=tk.HORIZONTAL)
        playingframeseperator.grid(column=0, row=2, sticky='wens')

        songprogress = ttk.Progressbar(playingframe, orient=tk.HORIZONTAL, mode='determinate', variable=self.progressbarvar)
        songprogress.grid(column=0, row=3, sticky='wes')

        playingframe.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # SONG SELECTION
        songlistlabelframe = ttk.Labelframe(primaryframe, text="Song list", relief='groove', borderwidth=5, padding=5)
        songlistlabelframe.grid(column=3, row=0, columnspan=2)

        songlist = tk.Listbox(songlistlabelframe, height=15, listvariable=self.songlistvar)
        songlistscrollbar = ttk.Scrollbar(songlistlabelframe, orient=tk.VERTICAL, command=songlist.yview)

        songsearchentry = tk.Entry(songlistlabelframe)

        songlist.grid(row=0, column=0, columnspan=2)
        songlistscrollbar.grid(row=0, column=2, sticky='ns')

        songlist['yscrollcommand'] = songlistscrollbar.set

        # BOTTOM LEFT LOGO
        shitifyiconimage = tk.PhotoImage(file="shitify64.png")
        shitifyiconlabel = ttk.Label(primaryframe, image=shitifyiconimage)
        shitifyiconlabel.grid(column=0, row=1, sticky='ewns')

        # BOTTOM LEFT PLAYLIST SELECT
        playlistselectframe = ttk.LabelFrame(primaryframe, text="Playlist select", relief='groove', padding=3)
        playlistselectframe.grid(row=1, column=1, sticky='ns')

        playlistselectcombobox = ttk.Combobox(playlistselectframe, values=self.playlistnames,
                                              textvariable=self.selectedplaylist,
                                              state='readonly')
        playlistselectcombobox.set("No playlist selected.")
        playlistselectcombobox.grid(sticky='ewn')

        playlistselectbutton = ttk.Button(playlistselectframe, text="SWITCH TO PLAYLIST", command=self._chooseplaylist,
                                          state=tk.DISABLED)
        playlistselectbutton.grid(row=1, sticky='s')

        # BOTTOM MIDDLE BUTTONS
        bottommiddleframe = ttk.LabelFrame(primaryframe, text="Player controls", relief='groove', padding=5)
        bottommiddleframe.grid(column=2, row=1, sticky='wnse')

        pausebutton = ttk.Button(bottommiddleframe, text="PAUSE", command=self._pause, state=tk.DISABLED)
        pausebutton.grid(row=0, column=0, columnspan=2, sticky='ew')

        skipbutton = ttk.Button(bottommiddleframe, text="SKIP", command=self._skip, state=tk.DISABLED)
        skipbutton.grid(row=1, sticky='w')

        removesongbutton = ttk.Button(bottommiddleframe, text="REMOVE SONG", command=self._blacklist, state=tk.DISABLED)
        removesongbutton.grid(row=1, column=1, sticky='e')

        volumeslider = ttk.LabeledScale(bottommiddleframe, from_=0, to=100, variable=self.volume, compound='bottom')
        volumeslider.scale.set(defaults['volume'])
        volumeslider.scale.configure(command=self._volchange)
        volumeslider.label.update()
        volumeslider.grid(row=2, columnspan=2, sticky='ew')

        bottommiddleframe.grid_rowconfigure((0, 1, 2), weight=1)
        bottommiddleframe.grid_columnconfigure((0, 1), weight=1)

        # BOTTOM RIGHT SONG CONTROLS
        songcontrolsframe = ttk.LabelFrame(primaryframe, text="Song selection controls", relief='groove', padding=3)
        songcontrolsframe.grid(row=1, column=3, sticky='ns')



        def _updatebasedonvalues():
            if self.changes['paused']:
                if self.playingsong is not None:
                    self.progressbarvar.set(value=self.progressbar)
                    songinfo['text'] = f"{self.playingsong.name}\n{self.playingsong.author}\n{self.playingsong.duration}"
                    if self.paused:
                        songdesc['text'] = "PAUSED"
                    else:
                        songdesc['text'] = "PLAYING"
                self._addchange('paused', False)

            if self.changes['songlist']:
                self.songlistvar.set(value=[i.name for i in self.songlist])
                if self.songlist:
                    songlist.configure(width=max([len(i.name) for i in self.songlist])+5)
                self._addchange('songlist', False)

            if self.changes['songqueue']:
                self.songqueuevar.set(value=[f"{i+1:>3}: {v.name}" for i, v in enumerate(self.songqueue)])
                if self.songqueue:
                    queuelist.configure(width=max([len(i.name) for i in self.songqueue])+5)
                self._addchange('songqueue', False)

            if self.changes['songinfo']:
                if self.playingsong is None:
                    pausebutton.configure(state=tk.DISABLED)
                    removesongbutton.configure(state=tk.DISABLED)
                    skipbutton.configure(state=tk.DISABLED)
                    songinfo['text'] = "No song playing"

                else:
                    pausebutton.configure(state=tk.NORMAL)
                    removesongbutton.configure(state=tk.NORMAL)
                    skipbutton.configure(state=tk.NORMAL)
                    songinfo['text'] = f"{self.playingsong.name}\n{self.playingsong.author}\n{self.playingsong.duration}"
                self._addchange('songinfo', False)

            if self.changes['playlistoptions']:
                self._generateplaylistnames()
                playlistselectcombobox['values'] = self.playlistnames

                self._addchange('playlistoptions', False)

            if self.changes['playlistnotselected']:
                if playlistselectcombobox.get() == "No playlist selected.":
                    playlistselectbutton.configure(state=tk.DISABLED)

                elif playlistselectbutton.instate((tk.DISABLED, )):
                    playlistselectbutton.configure(state=tk.NORMAL)
                    songdesc.configure(text="PLAYING")
                    self._addchange('playlistnotselected', False)

            if self.changes['progressbar']:
                self.progressbarvar.set(value=self.progressbar)
                self._addchange('progressbar', False)

            root.after(100, _updatebasedonvalues)

        _updatebasedonvalues()

        G.musicgui = self
        root.mainloop()

    def _setoutput(self, command, params=()):
        output = [command]
        output.extend(params)
        self.output = output

    def _skip(self, *args):
        if not self.output[0]:
            self._setoutput("skip")

    def _pause(self, *args):
        if not self.output[0]:
            self._setoutput("pause")

    def _blacklist(self, *args):
        if not self.output[0]:
            self._setoutput("blacklist")

    def _chooseplaylist(self, *args):
        if not self.output[0]:
            self._setoutput("switchlist", [self.selectedplaylist.get()])

    def _volchange(self, *args):
        if self.output[0] in ('volume', ''):
            volume = self.volume.get()
            if volume != self.lastvol:
                self._setoutput("volume", [volume])

    def _addchange(self, key, value=True):
        self.changes[key] = value

    def _generateplaylistnames(self):
        self.playlistnames = list([i.name for i in self.playlists])

    def _newplaylist(self):
        pass

    def _requeue(self):
        self._setoutput("requeue")

    def _unwatchplaylist(self):
        self._setoutput("unwatch", [self.selectedplaylist])

    def addplaylist(self, playlist):
        self.playlists.append(playlist)
        self._generateplaylistnames()
        self._addchange('playlistoptions')

    def addsong(self, song):
        self.songlist.append(song)
        self._addchange('songlist')

    def clearoutput(self):
        self._setoutput("")

    def pause(self):
        if not self.paused:
            self.paused = True
            self._addchange('paused')

    def unpause(self):
        if self.paused:
            self.paused = False
            self._addchange('paused')

    def updatesonglist(self, songlist: List[main.Song]):
        if self.songlist != songlist:
            self.songlist = songlist
            self._addchange('songlist')

    def updatequeue(self, songqueue: List[main.Song]):
        if self.songqueue != songqueue:
            self.songqueue = songqueue
            self._addchange('songqueue')

    def updatesong(self, song: main.Song):
        if self.playingsong != song:
            self.playingsong = song
            self._addchange('songinfo')

    def updateprogressbar(self, distance):
        if distance != self.progressbar:
            self.progressbar = distance
            self._addchange('progressbar')



G.musicgui: Musicgui = None

if __name__ == '__main__':
    import main
    settings = {
        'volume': 50
    }
    Musicgui([], settings)
