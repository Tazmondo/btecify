import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk


class musicgui:
    playlists = None
    selectedplaylist = None

    songqueue = None

    volume: tk.IntVar

    output = ""

    def __init__(self, playlistnames):
        root = ThemedTk(theme='black')
        print(root.get_themes())
        root.option_add('*tearOff', tk.FALSE)
        root.wm_title("sPoTiFy")
        root.wm_iconbitmap('shitify.ico')

        self.selectedplaylist = tk.StringVar()
        self.playlists = playlistnames
        self.songqueue = tk.StringVar(value=[f"{i}: Temp" for i in range(1,101)])
        self.volume = tk.IntVar(value=50)

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
        skipbutton.grid(row=1, sticky='w')

        blacklistbutton = ttk.Button(bottommiddleframe, text="BLACKLIST", command=self.blacklist)
        blacklistbutton.grid(row=1, column=1, sticky='e')

        volumeslider = ttk.LabeledScale(bottommiddleframe, from_=0, to=100, variable=self.volume, compound='bottom')
        volumeslider.scale.set(30)
        volumeslider.grid(row=2, columnspan=2, sticky='ew')

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
