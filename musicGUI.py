import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog as sd
from ttkthemes import ThemedTk
from time import sleep
import main
from sys import exit

PLAYINGINFOPLACEHOLDER = "-" * 75

searchfunc = main.searchsongname

class globalvars:
    pass
G = globalvars()


def MyListbox(*args, **kwargs):
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

    extrainfoplaylistsvar: tk.StringVar

    progressbarvar: tk.IntVar

    songsearchqueryvar: tk.StringVar

    volume: tk.IntVar
    lastvol = -1

    output = [""]

    playlists: list[main.Playlist]
    playlistnames: list[str]
    playingsong: main.Song = None
    songqueue: list[main.Song] = []
    songlist: list[main.Song] = []
    currentplaylist: main.Playlist = None
    displaysonglist: list[main.Song] = []
    displaysonglistnew: list[main.Song] = []
    progressbar: int = 0
    paused: bool = False
    playlistswithtargetsong: list[main.Playlist] = None
    extraplaylistselection: list[main.Playlist] = []
    changes = {
        'songlist': False,
        'songqueue': False,
        'songinfo': False,
        'playlistoptions': False,
        'progressbar': False,
        'playlistnotselected': True,
        'resetselectedsongs': False,
        'playlistcomboboxupdate': False,
        'extrasonginfo': False

    }

    def __init__(self, playlists: list[main.Playlist], defaults: dict):
        root = ThemedTk(theme='black')
        root.option_add('*tearOff', tk.FALSE)
        root.wm_title("sPoTiFy")
        root.wm_iconbitmap('btecify.ico')
        root.resizable(width=False, height=False)

        root.wm_iconify()
        root.wm_deiconify()

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
        self.songsearchqueryvar = tk.StringVar(value="")
        self.extrainfoplaylistsvar = tk.StringVar(value=[])

        # MENU
        menubar = tk.Menu(root)
        root.configure(menu=menubar)

        menuplaylist = tk.Menu(menubar)
        menusong = tk.Menu(menubar)

        menubar.add_cascade(menu=menuplaylist, label="Playlist")
        menubar.add_cascade(menu=menusong, label="Song")

        menubar.add_separator()

        menubar.add_command(label="Playlist: None")
        menubarplaylistlabelindex = 3

        menuplaylist.add_command(label="New...", command=self._newplaylist)
        menuplaylist.add_command(label="Delete", command=self._deleteplaylist)
        menuplaylist.add_separator()
        menuplaylist.add_command(label="Reset watched", command=self._unwatchplaylist)
        menuplaylist.add_command(label="Requeue", command=self._requeue)
        menuplaylist.add_separator()
        menuplaylist.add_command(label="Reset from Youtube", command=self._resetfromyoutube)

        menusong.add_command(label="New...", command=self._newsong)
        menusong.add_separator()
        menusong.add_command(label="Add selected songs to selected playlist", command=self._addsongtoplaylist)
        menusong.add_command(label="Remove selected songs from selected playlist")
        menusong.add_separator()
        menusong.add_command(label="Play selected song", command=self._playselectedsong)

        # PRIMARY FRAME

        primaryframe = ttk.Frame(root)
        primaryframe.grid()

        # QUEUE
        queuelabelframe = ttk.Labelframe(primaryframe, text="Song queue", relief='groove', borderwidth=5)
        queuelabelframe.grid(column=0, row=0, columnspan=2, rowspan=2, sticky='nswe')

        queuelist = MyListbox(queuelabelframe, height=15, listvariable=self.songqueuevar, state="disabled", width=50, exportselection=False)
        queuelistscrollbar = ttk.Scrollbar(queuelabelframe, orient=tk.VERTICAL, command=queuelist.yview)

        queuelist.grid(column=0, row=0, sticky='nswe')
        queuelistscrollbar.grid(column=1, row=0, sticky='ns')

        queuelist['yscrollcommand'] = queuelistscrollbar.set

        # PLAYER INFORMATION
        playingframe = ttk.Labelframe(primaryframe, text="Playing Song", relief='groove', padding=5)
        playingframe.grid(column=2, row=0, sticky='new')

        songinfo = ttk.Label(playingframe, text=f"No song playing\n{PLAYINGINFOPLACEHOLDER}", justify=tk.CENTER, anchor=tk.CENTER)
        songinfo.grid(column=0, row=0, sticky='ew')

        songdesc = ttk.Label(playingframe, text="", justify=tk.CENTER, anchor=tk.CENTER)
        songdesc.grid(column=0, row=1)

        songprogress = ttk.Progressbar(playingframe, orient=tk.HORIZONTAL, mode='determinate', variable=self.progressbarvar)
        songprogress.grid(column=0, row=3, sticky='wes')

        playingframe.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # SONG SELECTION
        songlistlabelframe = ttk.Labelframe(primaryframe, text="Song list", relief='groove', borderwidth=5)
        songlistlabelframe.grid(column=3, row=0, columnspan=2, rowspan=2)

        songlist = MyListbox(songlistlabelframe, height=15, listvariable=self.songlistvar, selectmode=tk.MULTIPLE,
                            bg="#282828", disabledforeground="gray80", fg="white",
                            activestyle='dotbox', selectbackground="#282828", selectforeground="red2",
                            width=50, exportselection=False)
        songlistscrollbar = ttk.Scrollbar(songlistlabelframe, orient=tk.VERTICAL, command=songlist.yview)

        _songlistsearchchangedcommand = root._register(self._songlistsearchchanged)
        songsearchentry = ttk.Entry(songlistlabelframe, validate="all", validatecommand=(_songlistsearchchangedcommand, '%V'),
                                   textvariable=self.songsearchqueryvar,)

        self.completeselectedsongs: list[main.Song] = []

        resetsonglistselectionbutton = ttk.Button(songlistlabelframe, text="RESET SELECTION",
                                                  command=lambda: self._addchange("resetselectedsongs"))

        songlist.grid(row=0, column=0, columnspan=2)
        songlistscrollbar.grid(row=0, column=2, sticky='wns')
        songsearchentry.grid(row=1, column=0, columnspan=2, sticky='ews')
        resetsonglistselectionbutton.grid(row=2, column=0, sticky='nw')

        songlist['yscrollcommand'] = songlistscrollbar.set

        # BOTTOM LEFT LOGO
        btecifyiconimage = tk.PhotoImage(file="btecify64.png")
        btecifyiconlabel = ttk.Label(primaryframe, image=btecifyiconimage)
        btecifyiconlabel.grid(column=0, row=2, sticky='ws')

        # PLAYLIST SELECT
        playlistselectframe = ttk.LabelFrame(primaryframe, text="Playlist select", relief='groove', padding=3)
        playlistselectframe.grid(row=2, column=3, sticky='wn')

        playlistselectcombobox = ttk.Combobox(playlistselectframe, values=self.playlistnames,
                                              textvariable=self.selectedplaylist,
                                              state='readonly')
        self.selectedplaylist.trace_add(mode="write", callback=self._playlistcomboboxvalueupdated)
        playlistselectcombobox.set("No playlist selected.")
        playlistselectcombobox.grid(sticky='ewn')

        playlistselectbutton = ttk.Button(playlistselectframe, text="SWITCH TO PLAYLIST", command=self._chooseplaylist)
        playlistselectbutton.grid(row=1, sticky='s')

        # BOTTOM MIDDLE BUTTONS
        bottommiddleframe = ttk.LabelFrame(primaryframe, text="Player controls", relief='groove', padding=5)
        bottommiddleframe.grid(column=2, row=1, sticky='wnse')

        pausebutton = ttk.Button(bottommiddleframe, text="PAUSE", command=self._pause)
        pausebutton.grid(row=0, column=0, columnspan=2, sticky='ew')

        skipbutton = ttk.Button(bottommiddleframe, text="SKIP", command=self._skip)
        skipbutton.grid(row=1, sticky='w')

        removesongbutton = ttk.Button(bottommiddleframe, text="REMOVE SONG", command=self._blacklist)
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

        extrasonginfoplaylists = MyListbox(extrasonginfoplaylistlabelframe, height=5, selectmode="browse", listvariable=self.extrainfoplaylistsvar,
                                           exportselection=False)
        extrasonginfoplaylists.grid(row=0, column=0, sticky="")

        extrasonginfoplaylistsresetbutton = ttk.Button(extrasonginfoplaylistlabelframe, text="RESET",
        command=lambda: extrasonginfoplaylists.selection_clear(0, 100000) or self.extraplaylistselection.clear())  # Executes two statements in one lambda.

        extrasonginfoplaylistsresetbutton.grid(row=1, column=0, sticky='nesw')

        extrasonginforemovebutton = ttk.Button(extrasonginfoplaylistlabelframe, text="REMOVE SONG FROM PLAYLISTS", command=self._extrasonginforemovebuttonfunc)
        extrasonginforemovebutton.grid(row=0, column=1, sticky='')

        def _updatebasedonvalues():
            extrasongselectedplaylistvalues = self._getextrasongselectedplaylists(extrasonginfoplaylists)
            if self.changes['songinfo'] or extrasongselectedplaylistvalues != self.extraplaylistselection:
                if self.playingsong is not None:
                    self.progressbarvar.set(value=self.progressbar)
                    songinfo['text'] = (f"{self.currentplaylist.name}\n{self.playingsong.name[:50]}\n{self.playingsong.author}\n{self.playingsong.duration}\n" + PLAYINGINFOPLACEHOLDER)
                    if self.paused:
                        songdesc['text'] = "PAUSED"
                    else:
                        songdesc['text'] = "PLAYING"

                    targetsong: main.Song = None
                    if len(self.completeselectedsongs) < 1:
                        targetsong = self.playingsong
                    else:
                        targetsong = self.completeselectedsongs[-1]

                    extrasonginfoname['text'] = targetsong.name[:75]
                    if (x := list(filter(lambda a: targetsong in a.getsongs(),
                                   self.playlists))) != self.playlistswithtargetsong:
                        self.playlistswithtargetsong = x
                        self.extrainfoplaylistsvar.set([i.name for i in self.playlistswithtargetsong])
                        extrasonginfoplaylists.selection_clear(0, 1000000)
                        self.extraplaylistselection = []

                    elif set(extrasongselectedplaylistvalues) != set(self.extraplaylistselection):
                        print([i.name for i in extrasongselectedplaylistvalues], [i.name for i in self.extraplaylistselection])
                        self.extraplaylistselection.extend([i for i in extrasongselectedplaylistvalues if i not in self.extraplaylistselection])
                        extrasonginfoplaylists.selection_clear(0, 10000)
                        for i, v in enumerate(self.extraplaylistselection):
                            extrasonginfoplaylists.selection_set(self.playlistswithtargetsong.index(v))

                self._addchange('songinfo', False)

            if self.changes['resetselectedsongs']:
                songlist.selection_clear(0, 100000000)

                self.completeselectedsongs = []
                self._addchange('resetselectedsongs', False)

            currentlyselectedvalues = self._getselectedvalues(songlist)
            # displayableselectedsongs = self.completeselectedsongs.intersection(set(self.displaysonglistnew))
            displayableselectedsongs = [i for i in self.displaysonglistnew if i in self.completeselectedsongs]
            if self.changes['songlist'] or (currentlyselectedvalues != displayableselectedsongs):
                if self.changes['songlist']:
                    self._songlistsearchchanged()
                    self.songlistvar.set(value=[i.name for i in self.displaysonglistnew])
                    self.displaysonglist = self.displaysonglistnew

                    # self.completeselectedsongs.update(currentlyselectedvalues)
                    self.completeselectedsongs.extend([i for i in currentlyselectedvalues if i not in self.completeselectedsongs])
                    songlist.selection_clear(0, last=len(self.displaysonglistnew) - 1)

                    self._addchange('songinfo')
                    self._addchange('songlist', False)
                else:
                    # self.completeselectedsongs.update(currentlyselectedvalues)
                    self.completeselectedsongs.extend([i for i in currentlyselectedvalues if i not in self.completeselectedsongs])
                    for song in self.completeselectedsongs:
                        if song:
                            if song in self.displaysonglistnew:
                                songlist.selection_set(self.displaysonglistnew.index(song))

            if self.changes['songqueue']:
                self.songqueuevar.set(value=[f"{i+1:>3}: {v.name}" for i, v in enumerate(self.songqueue)])
                self._addchange('songqueue', False)

            if self.changes['playlistoptions']:
                self._generateplaylistnames()
                playlistselectcombobox['values'] = self.playlistnames
                self._addchange('songinfo')
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

            if self.changes['playlistcomboboxupdate']:
                playlist = self._getselectedplaylist()
                label = "Playlist: "
                if playlist:
                    label += playlist.name
                else:
                    label += "None"
                menubar.entryconfigure(menubarplaylistlabelindex, label=label)
                self._addchange('playlistcomboboxupdate', False)

            root.after(250, _updatebasedonvalues)

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

    def _getextrasongselectedplaylists(self, playlistreeview: tk.Listbox) -> list[main.Playlist]:
        x = [self.playlistswithtargetsong[i] for i in playlistreeview.curselection()]
        return x

    def _extrasonginforemovebuttonfunc(self, *args):
        if not self.output[0]:
            self._setoutput("removesongfromplaylists", [])

    def _pause(self, *args):
        if not self.output[0]:
            self._setoutput("pause")

    def _blacklist(self, *args):
        if not self.output[0]:
            if len(self.completeselectedsongs) == 0:
                self._setoutput("blacklist", [[self.playingsong]])
            else:
                self._setoutput("blacklist", [list(self.completeselectedsongs)])

    def _chooseplaylist(self, *args):
        if not self.output[0]:
            self._setoutput("switchlist", [self.selectedplaylist.get()])

    def _playlistcomboboxvalueupdated(self, *args):
        self._addchange('playlistcomboboxupdate')
        pass

    def _deleteplaylist(self):
        self._setoutput("removelist", [self._getselectedplaylist()])

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
        name = sd.askstring("PLAYLIST CREATION", "Enter a playlist name")
        url = sd.askstring("PLAYLIST CREATION", "Enter a url (optional)")

        if url:
            self._setoutput("addlist", [name, url])
        else:
            self._setoutput("addlist", [name])

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
        else:
            matches = searchfunc(self.songlist, query)
            self.displaysonglistnew = matches
        self._addchange('songlist')
        return True

    def _getselectedvalues(self, songlistobject: tk.Listbox):
        selectedindices = songlistobject.curselection()
        songobjs = set()
        for i in selectedindices:
            if i < len(self.displaysonglist):
                songobjs.add(self.displaysonglist[i])
        return songobjs

    def _addsongtoplaylist(self, *args):
        targetpl = self._getselectedplaylist()
        if targetpl:
            params = [targetpl]
            if len(self.completeselectedsongs) > 0:
                params.extend(list(self.completeselectedsongs))
                self._setoutput("addsong", params)
            else:
                self._setoutput("addsong", params)

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
        url = sd.askstring("ADD A SONG","Enter the song url")
        self._setoutput("createsong",[url])

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

    def updatesonglist(self, songlist: set[main.Song]):
        songlist = sorted(list(songlist), key=lambda a: a.name.lower())
        if self.songlist != songlist:
            self.songlist = songlist
            self._songlistsearchchanged()
            self._addchange('songlist')

    def updatequeue(self, songqueue: list[main.Song]):
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

    def updateplaylists(self, playlists: list[main.Playlist]):
        if playlists != self.playlists:
            self.playlists = playlists
            self._addchange('playlistoptions')

    def updatecurrentplaylist(self, playlist: main.Playlist):
        self.currentplaylist = playlist


G.musicgui: Musicgui = None

if __name__ == '__main__':
    import main
    settings = {
        'volume': 50
    }
    Musicgui([], settings)
