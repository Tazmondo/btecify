from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Song, Playlist
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog as sd
from tkinter import font as tkfont
from tkinter import messagebox as mb
from ttkthemes import ThemedTk
import time

PLAYINGINFOPLACEHOLDER = "-" * 75


class globalvars:
    pass


G = globalvars()
G.logs = []

oldprint = print


def print(*args, **kwargs):
    oldprint(*args, **kwargs)
    G.logs.append((time.localtime(), args))


def searchsongname(targetlist: list[Song], targetvalue: str):
    targetlist = targetlist.copy()
    matches = []
    for target in targetlist:
        if target.name.lower().find(targetvalue) != -1:
            matches.append(target)
    return matches


def mylistbox(*args, **kwargs):
    kwargs.update({
        'bg': '#282828',
        'disabledforeground': 'gray80',
        'fg': 'white',
        'activestyle': 'dotbox',
        'selectbackground': '#282828',
        'selectforeground': 'red2'
    })

    return tk.Listbox(*args, **kwargs)


class Musicgui:
    selectedplaylist: tk.StringVar

    songqueuevar: tk.StringVar

    songlistvar: tk.StringVar
    playlistsongsvar: tk.StringVar

    extrainfoplaylistsvar: tk.StringVar

    progressbarvar: tk.IntVar

    songsearchqueryvar: tk.StringVar

    volume: tk.IntVar
    lastvol = -1
    seek: tk.DoubleVar

    output = [""]

    playlists: list[Playlist]
    playlistnames: list[str]
    playingsong: Song = None
    songqueue: list[Song] = []
    songqueuenew: list[Song] = []
    songlist: list[Song] = []
    currentplaylist: Playlist = None
    playlistwhichqueueisfrom: Playlist = None
    playlistwhichsongisfrom: Playlist = None
    playlistofplayingsong: Playlist = None
    displaysonglist: list[Song] = []
    displaysonglistnew: list[Song] = []
    displayplaylistsongs: list[Song] = []
    displayplaylistsongsnew: list[Song] = []
    progressbar: int = 0
    paused: bool = False
    playlistswithtargetsong: list[Playlist] = None
    extraplaylistselection: list[Playlist] = []
    logs = []
    newlogs = []
    changes = {
        'songlist': False,
        'songqueue': False,
        'songinfo': False,
        'playlistoptions': False,
        'progressbar': False,
        'resetselectedsongs': False,
        'playlistcomboboxupdate': False,
        'extrasonginfo': False,
        'playlistsongslist': False,
        'updatelogs': False,
        'seeking': False,
        'keybinds': False

    }

    def __init__(self, playlists: list[Playlist], defaults: dict):

        root = ThemedTk(theme='black')
        root.option_add('*tearOff', tk.FALSE)
        root.wm_title("btecify")
        root.wm_iconbitmap('assets\\btecify.ico')
        root.resizable(width=False, height=False)
        root.wm_iconify()
        root.wm_deiconify()

        for namefont in tkfont.names(root):
            rootfont = tkfont.nametofont(namefont)
            rootfont.config(family="Lucida Console")

        def _onclose():
            self.output = ["EXIT"]
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", _onclose)

        self.selectedplaylist = tk.StringVar()
        self.playlists = playlists
        self._generateplaylistnames()
        self.songqueuevar = tk.StringVar(value=[])
        self.volume = tk.IntVar(value=50)
        self.seek = tk.DoubleVar(value=0)
        self.songlistvar = tk.StringVar(value=[])
        self.playlistsongsvar = tk.StringVar(value=[])
        self.progressbarvar = tk.IntVar(value=0)
        self.songsearchqueryvar = tk.StringVar(value="")
        self.extrainfoplaylistsvar = tk.StringVar(value=[])
        self.searchfunc = searchsongname
        self.discordpresencevar = tk.BooleanVar(value=defaults['discord'])
        
        self.keybinds: list[tuple[str, str]] = []

        # CONSOLE
        consolewindow = tk.Toplevel(root)
        consolewindow.wm_title("Console Logs")
        consolewindow.wm_protocol("WM_DELETE_WINDOW", lambda: consolewindow.wm_withdraw())
        consolewindow.wm_withdraw()
        consolewindow.wm_resizable(False, False)

        consolewindowframe = ttk.Frame(consolewindow, padding=5, relief="groove")
        consolewindowframe.grid()

        consolewindowtext = tk.Text(consolewindowframe, foreground='white', background='black', state='disabled',
                                    width=100, height=40)
        consolewindowtext.grid(row=0, column=0)

        consolewindowtextscrollbar = ttk.Scrollbar(consolewindowframe, orient=tk.VERTICAL, command=consolewindowtext.yview)
        consolewindowtext['yscrollcommand'] = consolewindowtextscrollbar.set
        consolewindowtextscrollbar.grid(row=0, column=1, sticky='ns')

        def resetconsolewindow(*args):
            consolewindowtext.yview_moveto(1.0)
        consolewindowtext.bind('<Visibility>', resetconsolewindow)
        consolewindowtext.bind('<FocusIn>', resetconsolewindow)

        # KEYBINDS
        keybindwindow = tk.Toplevel(root)
        keybindwindow.wm_title("Keybindings")
        keybindwindow.wm_protocol("WM_DELETE_WINDOW", lambda: keybindwindow.wm_withdraw())
        keybindwindow.wm_resizable(False, False)
        keybindwindow.wm_withdraw()

        keybindwindowframe = ttk.Frame(keybindwindow, padding=5, relief='groove')
        keybindwindowframe.grid()

        keybindlistframe = ttk.Frame(keybindwindowframe, padding=3, relief='groove')
        keybindlistframe.grid(row=0, column=0)

        keybindings = [i for i in defaults['keybinds']]
        keybindlist = []
        for x in range(len(keybindings)):
            kbname = keybindings[x]
            newframe = ttk.Frame(keybindlistframe)
            newframe.grid(column=0, row=x)

            newlabel = ttk.Label(newframe, text=kbname+": ", width=max(map(lambda a: len(a), keybindings))+2)
            newlabel.grid(row=0, column=0)

            keybindtextvariable = tk.StringVar("")
            newentry = ttk.Entry(newframe, textvariable=keybindtextvariable)
            newentry.grid(row=0, column=1)
            newentry.bind('<FocusIn>', lambda *args: self._addchange('keybinds'))

            keybindlist.append((kbname, keybindtextvariable))

        keybindbuttonsframe = ttk.Frame(keybindwindowframe, padding=3, relief='groove')
        keybindbuttonsframe.grid(row=1, column=0)

        keybindbuttondefault = ttk.Button(keybindbuttonsframe, text="RESET TO DEFAULTS", command=lambda: self._setoutput("defaultkeybinds"))
        keybindbuttondefault.grid(row=0, column=0)

        keybindbuttonconfirm = ttk.Button(keybindbuttonsframe, text="CONFIRM KEYBINDINGS",
                                          command=lambda: self._setoutput("updatekeybinds", (
                                              [(i[0], i[1].get()) for i in keybindlist])))
        keybindbuttonconfirm.grid(row=0, column=1)

        # MENU
        menubar = tk.Menu(root)
        root.configure(menu=menubar)

        menuplaylist = tk.Menu(menubar)
        menusong = tk.Menu(menubar)
        menufile = tk.Menu(menubar)

        menubar.add_cascade(menu=menuplaylist, label="Playlist")
        menubar.add_cascade(menu=menusong, label="Song")
        menubar.add_cascade(menu=menufile, label="File")

        menubar.add_separator()

        menubar.add_command(label="Playlist: None", state="disabled")
        menubarplaylistlabelindex = len(menubar.winfo_children()) + 1

        menuplaylist.add_command(label="New...", command=self._newplaylist)
        menuplaylist.add_command(label="Delete", command=self._deleteplaylist)
        menuplaylist.add_command(label="Rename...", command=self._renameplaylist)
        menuplaylist.add_command(label="Copy...", command=self._copyplaylist)
        menuplaylist.add_separator()
        menuplaylist.add_command(label="Reset watched", command=self._unwatchplaylist)
        menuplaylist.add_command(label="Requeue", command=self._requeue)
        menuplaylist.add_separator()
        menuplaylist.add_command(label="Reset from Youtube", command=self._resetfromyoutube)

        menusong.add_command(label="New...", command=self._newsong)
        menusong.add_command(label="Delete", command=lambda: self._setoutput("deletesongs", self._getselectedsongs()))
        menusong.add_separator()
        menusong.add_command(label="Add selected songs to selected playlist", command=self._addsongtoplaylist)
        menusong.add_command(label="Remove selected songs from selected playlist",
                             command=lambda: self._setoutput("removesongsfromplaylist",
                                                             [self._getselectedplaylist(), self._getselectedsongs()]))
        menusong.add_separator()
        menusong.add_command(label="Play selected song", command=self._playselectedsong)
        menusong.add_command(label="Play random song", command=lambda: self._setoutput("randomsong"))

        menufile.add_command(label="Change API key", command=lambda: self._setoutput("newapikey"))
        menufile.add_command(label="View console logs", command=lambda: consolewindow.wm_deiconify())
        menufile.add_command(label="Open data directory", command=lambda: self._setoutput("opendatadirectory"))
        menufile.add_command(label="Change keybinds", command=lambda: keybindwindow.wm_deiconify())

        menufile.add_checkbutton(label="Discord Presence",
                                 command=lambda: self._setoutput('discordpresence', [self.discordpresencevar.get()]),
                                 variable=self.discordpresencevar)

        # PRIMARY FRAME

        primaryframe = ttk.Frame(root)
        primaryframe.grid()

        # QUEUE
        queuelabelframe = ttk.Labelframe(primaryframe, text="Song queue", relief='groove', borderwidth=5)
        queuelabelframe.grid(column=0, row=0, columnspan=2, rowspan=2, sticky='nswe')

        queuelist = mylistbox(queuelabelframe, height=15, listvariable=self.songqueuevar, width=50, exportselection=False, selectmode=tk.MULTIPLE)
        queuelistscrollbar = ttk.Scrollbar(queuelabelframe, orient=tk.VERTICAL, command=queuelist.yview)

        queuelist.grid(column=0, row=0, sticky='nswe')
        queuelistscrollbar.grid(column=1, row=0, sticky='ns')

        queuelist['yscrollcommand'] = queuelistscrollbar.set

        # PLAYER INFORMATION
        playingframe = ttk.Labelframe(primaryframe, text="Playing Song", relief='groove', padding=5)
        playingframe.grid(column=2, row=0, sticky='new')

        songinfo = ttk.Label(playingframe, text=f"No playlist\nNo song playing\nNo song author\nNo duration\n{PLAYINGINFOPLACEHOLDER}", justify=tk.CENTER, anchor=tk.CENTER)
        songinfo.grid(column=0, row=0, sticky='ew')

        songdesc = ttk.Label(playingframe, text="", justify=tk.CENTER, anchor=tk.CENTER)
        songdesc.grid(column=0, row=1)

        songprogress = ttk.Progressbar(playingframe, orient=tk.HORIZONTAL, mode='determinate', variable=self.progressbarvar)
        songprogress.grid(column=0, row=3, sticky='wes')

        songseeker = ttk.Scale(playingframe, from_=0, to=1, variable=self.seek)
        songseeker.grid(column=0, row=4, sticky='wes')
        songseeker.bind("<ButtonPress-1>", lambda *args: self.changes.update({'seeking': True}))
        songseeker.bind("<ButtonRelease-1>", lambda *args: self.changes.update({'seeking': False}))

        playingframe.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # SONG SELECTION AND SONG VIEWING
        songselectionandviewingframe = ttk.Frame(primaryframe)
        songselectionandviewingframe.grid(column=3, row=0, columnspan=2, rowspan=2)

        songlistnotebook = ttk.Notebook(songselectionandviewingframe)
        songlistnotebook.grid(column=0, row=0)

        songlistframe = ttk.Frame(songlistnotebook, padding=1)

        songlist = mylistbox(songlistframe, height=15, listvariable=self.songlistvar, selectmode=tk.MULTIPLE,
                             bg="#282828", disabledforeground="gray80", fg="white",
                             activestyle='dotbox', selectbackground="#282828", selectforeground="red2",
                             width=50, exportselection=False)
        songlistscrollbar = ttk.Scrollbar(songlistframe, orient=tk.VERTICAL, command=songlist.yview)
        ################################################################################################################

        playlistsongsframe = ttk.Frame(songlistnotebook, padding=1)

        playlistsongslist = mylistbox(playlistsongsframe, height=15, listvariable=self.playlistsongsvar, selectmode=tk.MULTIPLE,
                             bg="#282828", disabledforeground="gray80", fg="white",
                             activestyle='dotbox', selectbackground="#282828", selectforeground="red2",
                             width=50, exportselection=False)
        playlistsongslistscrollbar = ttk.Scrollbar(playlistsongsframe, orient=tk.VERTICAL, command=playlistsongslist.yview)
        ################################################################################################################

        _songlistsearchchangedcommand = root._register(self._songlistsearchchanged)
        songsearchentry = ttk.Entry(songselectionandviewingframe, validate="all", validatecommand=(_songlistsearchchangedcommand, '%V'),
                                   textvariable=self.songsearchqueryvar,)

        self.completeselectedsongs: list[Song] = []

        resetsonglistselectionbutton = ttk.Button(songselectionandviewingframe, text="RESET SELECTION|SELECTED: 0",
                                                  command=lambda: self._addchange("resetselectedsongs"))

        songlist.grid(row=0, column=0, columnspan=2)
        songlistscrollbar.grid(row=0, column=2, sticky='wns')

        playlistsongslist.grid(row=0, column=0, columnspan=2)
        playlistsongslistscrollbar.grid(row=0, column=2, sticky='wns')

        songsearchentry.grid(row=1, column=0, sticky='ews')
        resetsonglistselectionbutton.grid(row=2, column=0, sticky='nw')

        songlist['yscrollcommand'] = songlistscrollbar.set
        playlistsongslist['yscrollcommand'] = playlistsongslistscrollbar.set

        songlistnotebook.add(songlistframe, text="Song list")
        songlistnotebook.add(playlistsongsframe, text="empty")

        # BOTTOM LEFT LOGO
        btecifyiconimage = tk.PhotoImage(file="assets/btecify64.png")
        btecifyiconlabel = ttk.Label(primaryframe, image=btecifyiconimage)
        btecifyiconlabel.grid(column=0, row=2, sticky='ws')

        # PLAYLIST SELECT
        playlistselectframe = ttk.LabelFrame(primaryframe, text="Playlist select", relief='groove', padding=3)
        playlistselectframe.grid(row=2, column=3, sticky='wn')

        playlistselectcombobox = ttk.Combobox(playlistselectframe, values=self.playlistnames,
                                              textvariable=self.selectedplaylist, width=26,
                                              state='readonly')
        self.selectedplaylist.trace_add(mode="write", callback=self._playlistcomboboxvalueupdated)
        playlistselectcombobox.set(playlists[0].name)
        playlistselectcombobox.grid(sticky='ewn')

        playlistselectbutton = ttk.Button(playlistselectframe, text="SWITCH TO PLAYLIST", command=self._chooseplaylist)
        playlistselectbutton.grid(row=1, sticky='s')

        # PLAYER BUTTONS
        bottommiddleframe = ttk.LabelFrame(primaryframe, text="Player controls", relief='groove', padding=5)
        bottommiddleframe.grid(column=2, row=1, sticky='wnse')

        pausebutton = ttk.Button(bottommiddleframe, text="PAUSE", command=self._pause)
        pausebutton.grid(row=0, column=0, columnspan=2, sticky='ew')

        skipbutton = ttk.Button(bottommiddleframe, text="SKIP", command=self._skip)
        skipbutton.grid(row=1, sticky='w')

        removesongbutton = ttk.Button(bottommiddleframe, text="REMOVE SONG", command=self._playerremovesongbutton)
        removesongbutton.grid(row=1, column=1, sticky='e')

        volumeslider = ttk.LabeledScale(bottommiddleframe, from_=0, to=100, variable=self.volume, compound='bottom')
        volumeslider.scale.set(defaults['volume'])
        volumeslider.scale.configure(command=self._volchange)
        volumeslider.label.update()
        volumeslider.grid(row=2, columnspan=2, sticky='ew')

        bottommiddleframe.grid_rowconfigure((0, 1, 2), weight=1)
        bottommiddleframe.grid_columnconfigure((0, 1), weight=1)

        # EXTRA SONG INFORMATION
        extrasonginfoframe = ttk.Labelframe(primaryframe, text="Song Info", relief="sunken", padding=3)
        extrasonginfoframe.grid(row=2, column=1, columnspan=2, sticky="nesw")

        extrasonginfoname = ttk.Label(extrasonginfoframe, text="NO SONG", justify=tk.LEFT, anchor="w")
        extrasonginfoname.grid(row=0, column=0, sticky="nesw")

        extrasonginfoplaylistlabelframe = ttk.Labelframe(extrasonginfoframe, text="In Playlists", relief="groove", padding=5)
        extrasonginfoplaylistlabelframe.grid(row=1, column=0, sticky="w")

        extrasonginfoplaylists = mylistbox(extrasonginfoplaylistlabelframe, height=5, selectmode="browse", listvariable=self.extrainfoplaylistsvar,
                                           exportselection=False)
        extrasonginfoplaylists.grid(row=0, column=0, sticky="")

        extrasonginfoplaylistsresetbutton = ttk.Button(extrasonginfoplaylistlabelframe, text="RESET",
        command=lambda: extrasonginfoplaylists.selection_clear(0, 100000) or self.extraplaylistselection.clear())  # Executes two statements in one lambda.

        extrasonginfoplaylistsresetbutton.grid(row=1, column=0, sticky='nesw')

        extrasonginfobuttonsframe = ttk.Frame(extrasonginfoplaylistlabelframe, padding=2)
        extrasonginfobuttonsframe.grid(row=0, column=1, sticky='nesw')

        extrasonginforemovebutton = ttk.Button(extrasonginfobuttonsframe, text="REMOVE SONG FROM PLAYLISTS", command=self._extrasonginforemovebuttonfunc)
        extrasonginforemovebutton.grid(row=0, column=0, sticky='')

        extrasonginfoopensong = ttk.Button(extrasonginfobuttonsframe, text="OPEN IN YOUTUBE", command=lambda: self._setoutput("openinyoutube", [[*self.completeselectedsongs] or [self._getselectedsong()]]))
        extrasonginfoopensong.grid(row=1, column=0, sticky='')

        def _updatebasedonvalues():
            extrasongselectedplaylistvalues = self._getextrasongselectedplaylists(extrasonginfoplaylists)
            if self.changes['songinfo'] or extrasongselectedplaylistvalues != self.extraplaylistselection:
                if self.playingsong is not None:
                    self.progressbarvar.set(value=self.progressbar)
                    playlistofthissong = self.playlistwhichsongisfrom
                    if playlistofthissong is None:
                        playlistofthissong = "Played manually"
                        removesongbutton.configure(state='disabled')
                    else:
                        playlistofthissong = playlistofthissong.name
                        removesongbutton.configure(state='active')
                    songinfo['text'] = (f"{playlistofthissong}\n{self.playingsong.name[:len(PLAYINGINFOPLACEHOLDER)]}\n{self.playingsong.author}\n{self.playingsong.duration}\n" + PLAYINGINFOPLACEHOLDER)
                    if self.paused:
                        songdesc['text'] = "PAUSED"
                        pausebutton['text'] = "PLAY"
                    else:
                        songdesc['text'] = "PLAYING"
                        pausebutton['text'] = "PAUSE"

                targetsong = self._getselectedsong()
                if targetsong is not None:
                    extrasonginfoname['text'] = targetsong.name[:(queuelist.cget("width")//3)+len(PLAYINGINFOPLACEHOLDER)]
                    self.playlistswithtargetsong = list(filter(lambda a: targetsong in a.getsongs(), self.playlists))
                    self.extrainfoplaylistsvar.set([i.name for i in self.playlistswithtargetsong])
                    extrasonginfoplaylists.selection_clear(0, 1000000)
                    self.extraplaylistselection.extend([i for i in extrasongselectedplaylistvalues if i not in self.extraplaylistselection])

                    for i, v in enumerate(self.extraplaylistselection):
                        if v in self.playlistswithtargetsong:
                            extrasonginfoplaylists.selection_set(self.playlistswithtargetsong.index(v))
                        else:
                            self.extraplaylistselection.remove(v)
                else:
                    extrasonginfoname['text'] = "NO SONG"
                    self.extrainfoplaylistsvar.set([])
                    extrasonginfoplaylists.selection_clear(0, 10000)

                self._addchange('songinfo', False)

            if self.changes['resetselectedsongs']:
                songlist.selection_clear(0, 100000000)
                queuelist.selection_clear(0, 100000)
                playlistsongslist.selection_clear(0, 100000)

                self.completeselectedsongs = []
                resetsonglistselectionbutton.configure(
                    text=f"RESET SELECTION   |   SELECTED: 0")
                self._addchange('songinfo')
                self._addchange('resetselectedsongs', False)

            currentlyselectedsonglistvalues = self._getselectedvalues(songlist, self.displaysonglist)
            currentlyselectedqueuevalues = self._getselectedvalues(queuelist, self.songqueue)
            currentlyselectedplaylistsongsvalues = self._getselectedvalues(playlistsongslist, self.displayplaylistsongs)
            displayablesongsinsonglist = set([i for i in self.displaysonglistnew if i in self.completeselectedsongs])
            displayablesongsinqueuelist = set([i for i in self.songqueuenew if i in self.completeselectedsongs])
            displayablesongsinplaylistsongslist = set([i for i in self.displayplaylistsongsnew if i in self.completeselectedsongs])

            if self.changes['songlist'] or (currentlyselectedsonglistvalues != displayablesongsinsonglist) or (displayablesongsinqueuelist != currentlyselectedqueuevalues) or (displayablesongsinplaylistsongslist != currentlyselectedplaylistsongsvalues):
                if self.changes['songlist']:
                    self._songlistsearchchanged()
                    self.songlistvar.set(value=[i.name for i in self.displaysonglistnew])
                    self.playlistsongsvar.set(value=[i.name for i in self.displayplaylistsongsnew])
                    self.displaysonglist = self.displaysonglistnew
                    self.displayplaylistsongs = self.displayplaylistsongsnew

                    songlist.selection_clear(0, 1000000)
                    queuelist.selection_clear(0, 1000000)
                    playlistsongslist.selection_clear(0, 10000)

                    self._addchange('songinfo')
                    self._addchange('songlist', False)
                else:
                    self.completeselectedsongs.extend([i for i in currentlyselectedsonglistvalues if i not in self.completeselectedsongs])
                    self.completeselectedsongs.extend([i for i in currentlyselectedqueuevalues if i not in self.completeselectedsongs])
                    self.completeselectedsongs.extend([i for i in currentlyselectedplaylistsongsvalues if i not in self.completeselectedsongs])
                    for song in self.completeselectedsongs:
                        if song:
                            if song in self.displaysonglistnew:
                                songlist.selection_set(self.displaysonglistnew.index(song))
                            if song in self.songqueuenew:
                                queuelist.selection_set(self.songqueuenew.index(song))
                            if song in self.displayplaylistsongsnew:
                                playlistsongslist.selection_set(self.displayplaylistsongsnew.index(song))
                    self._addchange('songinfo')
                    resetsonglistselectionbutton.configure(text=f"RESET SELECTION   |   SELECTED: {len(self.completeselectedsongs)}")

            if self.changes['songqueue']:
                queuelist.selection_clear(0, 100000)
                self.songqueue = self.songqueuenew
                self.songqueuevar.set(value=[f"{i+1:>3}: {v.name}" for i, v in enumerate(self.songqueue)])
                self._addchange('songqueue', False)

            if self.changes['playlistoptions']:
                self._generateplaylistnames()
                playlistselectcombobox['values'] = self.playlistnames
                self._addchange('songinfo')
                self._addchange('playlistoptions', False)

            if self.changes['progressbar']:
                self.progressbarvar.set(value=self.progressbar)
                self._addchange('progressbar', False)

            if self.changes['playlistcomboboxupdate']:
                playlist = self._getselectedplaylist()
                label = "Playlist: "
                if playlist:
                    label += playlist.name
                else:
                    label += "None"
                menubar.entryconfigure(menubarplaylistlabelindex, label=label)

                songlistnotebook.tab(1, text=self._getselectedplaylist().name)
                self._addchange("songlist")
                self._addchange('playlistcomboboxupdate', False)

            if self.changes['updatelogs']:
                logstoadd = self.newlogs[len(self.logs):]
                consolewindowtext['state'] = 'normal'
                for log in logstoadd:
                    logstr = ""
                    timevalues = log[0]
                    logstr += f"{timevalues.tm_hour:0>2}:{timevalues.tm_min:0>2}:{timevalues.tm_sec:0>2}: "
                    for obj in log[1]:
                        objstring = str(obj).replace("\n", "\n\t  ")
                        logstr += objstring + " "
                    consolewindowtext.insert('end', logstr+"\n\n")
                consolewindowtext['state'] = 'disabled'

                self.logs = self.newlogs
                self._addchange('updatelogs', False)

            if self.changes['seeking']:
                val = self.seek.get()
                if 0 < val < 1:
                    self._setoutput('seek', [self.seek.get()])
            
            if self.changes['keybinds']:
                for kbset in keybindlist:
                    for j in self.keybinds:
                        if j[0] == kbset[0]:
                            kbset[1].set(j[1])
                self._addchange("keybinds", False)

            root.after(10, _updatebasedonvalues)

        _updatebasedonvalues()

        G.musicgui = self
        root.mainloop()

    def _setoutput(self, command, params=(), wait=False):
        if command != 'volume' and command != "seek":
            print(command, params)
        if params is None:
            params = ()
        output = [command]
        output.extend(params)
        self.output = output
        if wait:
            while self.output != ['']:
                time.sleep(0.01)

    def _skip(self, *args):
        if not self.output[0]:
            self._setoutput("skip")

    def _getextrasongselectedplaylists(self, playlistreeview: tk.Listbox) -> list[Playlist]:
        x = [self.playlistswithtargetsong[i] for i in playlistreeview.curselection()]
        return x

    def _extrasonginforemovebuttonfunc(self, *args):
        if not self.output[0]:
            self._setoutput("removesongfromplaylists", [self._getselectedsong(), self.extraplaylistselection], True)
            self._addchange("songinfo")

    def _pause(self, *args):
        if not self.output[0]:
            self._setoutput("pause")

    def _playerremovesongbutton(self, *args):
        if not self.output[0]:
            self._setoutput("blacklist", [self.playingsong], True)
            self._addchange('songinfo')

    def _chooseplaylist(self, *args):
        if not self.output[0]:
            self._setoutput("switchlist", [self.selectedplaylist.get()])

    def _playlistcomboboxvalueupdated(self, *args):
        self._addchange('playlistcomboboxupdate')
        pass

    def _newplaylist(self):
        name = sd.askstring("PLAYLIST CREATION", "Enter a playlist name")
        url = sd.askstring("PLAYLIST CREATION", "Enter a url (optional)")

        if name and type(name) is str:
            if url:
                self._setoutput("addlist", [name, url])
            else:
                self._setoutput("addlist", [name])

    def _deleteplaylist(self):
        self._setoutput("removelist", [self._getselectedplaylist()])

    def _renameplaylist(self):
        name = sd.askstring("PLAYLIST RENAME", "Enter a playlist name")
        self._setoutput("renameplaylist", [self._getselectedplaylist(), name])

    def _copyplaylist(self):
        self._setoutput("copyplaylist", [
            self._getselectedplaylist(),
            sd.askstring("PLAYLIST COPY", "Enter a playlist name")
        ])

    def _volchange(self, *args):
        if self.output[0] in ('volume', ''):
            volume = self.volume.get()
            if volume != self.lastvol:
                self._setoutput("volume", [volume])

    def _addchange(self, key, value=True):
        self.changes[key] = value

    def _generateplaylistnames(self):
        self.playlistnames = list([i.name for i in self.playlists])

    def _getselectedsong(self) -> Song:
        if len(self.completeselectedsongs) > 0:
            return self.completeselectedsongs[-1]
        return self.playingsong

    def _getselectedsongs(self) -> list[Song]:
        out = []
        if len(self.completeselectedsongs) > 0:
            out.extend(list(self.completeselectedsongs))
        elif self.playingsong is not None:
            out.append(self.playingsong)
        return out

    def _requeue(self):
        self._setoutput("requeue")

    def _unwatchplaylist(self):
        self._setoutput("unwatch", [self.selectedplaylist.get()])

    def _songlistsearchchanged(self, why=None):
        if why == 'focusin':
            self.songsearchqueryvar.set("")
            return self._songlistsearchchanged()
        query = self.songsearchqueryvar.get()
        if not query:
            self.displaysonglistnew = self.songlist
            self.displayplaylistsongsnew = sorted(list(self._getselectedplaylist().getsongs()), key=lambda a: a.name.lower())
        else:
            matches = self.searchfunc(self.songlist, query)
            self.displaysonglistnew = matches
            matches = self.searchfunc(list(self._getselectedplaylist().getsongs()), query)
            self.displayplaylistsongsnew = sorted(matches, key=lambda a: a.name.lower())
        self._addchange('songlist')
        return True

    @staticmethod
    def _getselectedvalues(songlistobject: tk.Listbox, listedlist: list):
        selectedindices = songlistobject.curselection()
        songobjs = set()
        for i in selectedindices:
            if i < len(listedlist):
                songobjs.add(listedlist[i])
        return songobjs

    def _addsongtoplaylist(self, *args):
        targetpl = self._getselectedplaylist()
        if targetpl:
            params = [targetpl]
            self._setoutput("addsong", params + self._getselectedsongs(), True)
            self._addchange("songinfo")

    def _getsongfromname(self, name):
        for song in self.songlist:
            if song.name == name:
                return song
        return None

    def _getplaylistfromname(self, name):
        for playlist in self.playlists:
            if playlist.name == name:
                return playlist
        return None

    def _getselectedplaylist(self):
        return self._getplaylistfromname(self.selectedplaylist.get())

    def _playselectedsong(self):
        if len(self.completeselectedsongs) >= 1:
            song = self.completeselectedsongs[-1]
            self._setoutput("song", [song])

    def _resetfromyoutube(self):
        self._setoutput("resetfromyoutube", [self.selectedplaylist.get()])

    def _newsong(self):
        url = sd.askstring("ADD A SONG", "Enter the song url")
        if url:
            self._setoutput("createsong", [url])

    def clearoutput(self):
        self._setoutput("")

    def pause(self):
        if not self.paused:
            self.paused = True
            self._addchange('songinfo')

    def unpause(self):
        if self.paused:
            self.paused = False
            self._addchange('songinfo')

    def updatesonglist(self, songlist: set[Song]):
        songlist = sorted(list(songlist), key=lambda a: a.name.lower())
        if self.songlist != songlist:
            print("updating songlist")
            self.songlist = songlist
            self._songlistsearchchanged()
            self._addchange('songlist')

    def updatequeue(self, songqueue: list[Song]):
        if self.songqueue != songqueue:
            print("updating queue")
            self.songqueuenew = songqueue
            self.playlistwhichqueueisfrom = self.currentplaylist
            self._addchange('songqueue')

    def updatesong(self, song: Song, ismanual=False):
        if self.playingsong != song:
            print("updating song")
            self.playingsong = song
            if not ismanual:
                self.playlistwhichsongisfrom = self.playlistwhichqueueisfrom
            else:
                self.playlistwhichsongisfrom = None
            self._addchange('songinfo')

    def updateprogressbar(self, distance):
        if distance != self.progressbar:
            self.progressbar = distance
            if not self.changes['seeking']:
                self.seek.set(distance/100)
            self._addchange('progressbar')

    def updateplaylists(self, playlists: list[Playlist]):
        if list(playlists) != self.playlists:
            print("updating playlists")
            self.playlists = list(playlists)
            self._addchange('playlistoptions')

    def updatecurrentplaylist(self, playlist: Playlist):
        self.currentplaylist = playlist

    def updatelogs(self, logs: list[tuple[time.struct_time, tuple]]):
        if logs != self.logs:
            self.newlogs = logs.copy()
            self._addchange('updatelogs')

    def updatekeybinds(self, keybinds: list[tuple[str, str]]):
        if keybinds != self.keybinds:
            self.keybinds = keybinds
            self._addchange("keybinds")

def msgbox(title="", warning="Something happened!", inputtype=None):
    """
    Creates a new messagebox based off of inputtype

    inputtype can be any from:
    {"Error", str, int, float}

    String inputs will result in a messagebox, while datatype inputs result in a dialogbox.
    """
    root = tk.Tk()
    root.wm_withdraw()
    returnval = None
    if inputtype == "Error":
        returnval =  mb.showerror(title=title, message=warning)
    elif inputtype == None:
        mb.showinfo(title=title or "Info", message=warning)
    elif inputtype == str:
        returnval = sd.askstring(title, warning, parent=root)
    elif inputtype == int:
        returnval = sd.askinteger(title, warning, parent=root)
    elif inputtype == float:
        returnval = sd.askfloat(title, warning, parent=root)
    root.destroy()
    return returnval

G.musicgui: Musicgui = None

if __name__ == '__main__':
    import main
    Musicgui([main.Playlist("empty")], {"volume": 0})
