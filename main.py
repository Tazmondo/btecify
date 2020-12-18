import os.path
import pickle
import random
import sys
import threading
import time
import webbrowser
import pathlib

import appdirs
import pafy
import pypresence
import semantic_version as semver
import vlc
from pynput import keyboard as kb
from win10toast import ToastNotifier

import musicGUI

APIKEYLENGTH = 39

try:  # Make sure it doesn't crash if there is no console.
    sys.stdout.write("\n")
    sys.stdout.flush()
except AttributeError:
    class DummyStream:
        """ dummyStream behaves like a stream but does nothing. """
        def __init__(self): self.isatty = False
        def write(self, data): pass
        def read(self, data): pass
        def flush(self): pass
        def close(self): pass
    # and now redirect all default streams to this dummyStream:
    sys.stdout = DummyStream()
    sys.stderr = DummyStream()
    sys.stdin = DummyStream()
    sys.__stdout__ = DummyStream()
    sys.__stderr__ = DummyStream()
    sys.__stdin__ = DummyStream()

ICON = "assets\\btecify.ico"
APPNAME = "btecify"
TESTINGMODE = False
if os.path.isfile("testingmodedetectionfile"):
    TESTINGMODE = True
VERSION = "1.2.1"

if not TESTINGMODE:
    DATADIRECTORY = appdirs.user_data_dir(APPNAME, appauthor=False)
    LOGDIRECTORY = appdirs.user_log_dir(APPNAME, appauthor=False)
    DATAFILE = DATADIRECTORY + "\\" + "data.txt"
    APIKEYFILE = DATADIRECTORY + "\\" + "apikey.txt"
    LOGFILE = LOGDIRECTORY + "\\" + "BTECIFY LOG-{0.tm_year:0>4}.{0.tm_mon:0>2}.{0.tm_mday:0>2}.{0.tm_hour:0>2}.{0.tm_min:0>2}.{0.tm_sec:0>2}.log".format(time.localtime())
else:
    DATADIRECTORY = "./testingdata"
    LOGDIRECTORY = "./testingdata/Logs"
    DATAFILE = DATADIRECTORY + "/" + "data.txt"
    APIKEYFILE = DATADIRECTORY + "/" + "apikey.txt"
    LOGFILE = LOGDIRECTORY + "/" + "BTECIFY LOG-{0.tm_year:0>4}.{0.tm_mon:0>2}.{0.tm_mday:0>2}.{0.tm_hour:0>2}.{0.tm_min:0>2}.{0.tm_sec:0>2}.log".format(time.localtime())

# Creating all directories and files if they don't already exist.
try:
    os.makedirs(LOGDIRECTORY)  # Log directory is inside data direectory and also creates the logs folder so it is used here.
except FileExistsError:
    print(f"Directory {LOGDIRECTORY} already exists.")

for savefile in (DATAFILE, APIKEYFILE, LOGFILE):
    try:
        with open(savefile, "r"):
            pass
    except FileNotFoundError:
        with open(savefile, "w") as f:
            if savefile == DATAFILE:
                pickle.dump({}, f)
            pass

# Deleting log files beyond the last 10 to stop them from piling up
logpath = pathlib.Path(LOGDIRECTORY).absolute()
for i in list(logpath.iterdir())[:-10]:  # All log files except most recent 5
    i.unlink()

APIKEY = ""
try:
    with open(APIKEYFILE, "r") as file:
        APIKEY = file.read()
    if len(APIKEY) != APIKEYLENGTH:
        raise ValueError("Incorrect key length. Make sure to use the right key:", APIKEY, len(APIKEY))
except (FileNotFoundError, ValueError) as e:
    errmsg = ""
    if type(e) is FileNotFoundError:
        print("apikey file not found")
        errmsg = "No youtube api key found, please enter one."
    elif type(e) is ValueError:
        print(e)
        errmsg = "Incorrect api key, please enter a new one."
    while len(APIKEY) != APIKEYLENGTH:
        APIKEY = musicGUI.msgbox("Error", errmsg, str)
        errmsg = "Incorrect api key, please enter a new one."
    with open(APIKEYFILE, "w") as file:
        file.write(APIKEY)

pafy.set_api_key(APIKEY)
BROWSER = webbrowser.get("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s")

CLIENTID = '783393560506531882'
POLLRATE = 0.05
RPCRATE = 17 // POLLRATE


class Song:
    vidid = ""
    name = ""
    url = ""
    duration = ""
    author = ""
    blacklist = False

    def __init__(self, vidid: str, name: str, url: str, duration: str, author: str, blacklist: bool = False):
        self.vidid = vidid
        self.name = name
        self.url = url
        self.duration = duration
        self.author = author
        self.blacklist = blacklist

    @staticmethod
    def createsongfromurl(url: str):
        try:
            song = pafy.new(url)
            return Song(song.videoid, song.title, url, song.duration, song.author)
        except ValueError as e:
            print("INVALID SONG URL!!!", e)
            return False


class Playlist:
    url = ""
    name = ""
    seensongs: set[Song] = set()
    ytplaylist: set[Song] = set()
    removedsongs: set[Song] = set()
    addedsongs: set[Song] = set()

    def __init__(self,  name: str, url: str = "", songs: list[Song] = None, addedsongs: set[Song] = None,
                 removedsongs: set[Song] = None, autoupdate: bool = True):
        if songs is None:
            songs = []
        if addedsongs is None:
            addedsongs = set()
        if removedsongs is None:
            removedsongs = set()
        self.url = url
        self.ytplaylist = set(songs)
        self.addedsongs = addedsongs
        self.removedsongs = removedsongs
        self.name = name
        if autoupdate:
            try:
                self.refreshplaylistfromyoutube()
            except ValueError as e:
                print("INVALID PLAYLIST URL!!!", e)
                self.url = ""
        self.seensongs = set()

    def getqueue(self):
        queue = [i for i in self.getsongs() if i not in self.seensongs]
        random.shuffle(queue)
        return queue

    def getsongs(self):
        return (self.ytplaylist - self.removedsongs) | self.addedsongs

    def refreshplaylistfromyoutube(self, force=False):
        if self.url:
            playlistobject = pafy.get_playlist2(self.url)
            playlistlength = len(playlistobject)

            if playlistlength != len(self.ytplaylist) or force:
                print("Songlist is updating.")
                try:
                    for video in playlistobject:
                        if video.videoid not in map(lambda a: a.vidid, self.ytplaylist):
                            if video.videoid not in map(lambda a: a.vidid, G.songset):
                                newsong = Song(video.videoid, video.title, video.watchv_url, video.duration, video.author,)
                                G.songset.add(newsong)
                                self.ytplaylist.add(newsong)
                                print(f"Downloading and adding {video.title}")

                            else:
                                songlist = list(G.songset)
                                correlatesong = songlist[list(map(lambda a: a.vidid, songlist)).index(video.videoid)]
                                self.ytplaylist.add(correlatesong)
                                print(f"Finding and adding {video.title}")
                except pafy.util.GdataError as e:
                    print("Couldn't update songlist:", e)

        else:
            print("Local playlist - no update.")

    def removesong(self, song: Song):
        if song in self.addedsongs:
            self.addedsongs.remove(song)
        self.removedsongs.add(song)

    def addsong(self, song: Song):
        if song in self.removedsongs:
            self.removedsongs.remove(song)
        self.addedsongs.add(song)

    def clearcustomsongs(self):
        self.addedsongs = set()
        self.removedsongs = set()


class Player:
    song: Song = None
    paused: bool
    instance: vlc.Instance
    musicplayer: vlc.MediaPlayer
    songlist: list[Song]
    queue: list[Song]
    playlist: Playlist
    toaster: ToastNotifier

    def __init__(self, playlist: Playlist):
        self.instance: vlc.Instance = vlc.Instance()
        self.musicplayer = self.instance.media_player_new()
        self.paused = False
        self.toaster = ToastNotifier()
        self.playlist = playlist
        self.songlist = None
        self.queue = []
        self.manual = False
        self.refreshplaylist()

        G.player = self

    def play(self):
        count = 0
        self.musicplayer.play()
        while not self.musicplayer.is_playing():
            print("Playing...")
            self.musicplayer.play()
            time.sleep(0.5)
            count += 1
            if count > 10:
                return False
        self.paused = False
        return True

    def pause(self):
        self.musicplayer.pause()
        self.paused = not self.paused

    def setsong(self, isong: Song):
        try:
            self.song = isong
            pafyobj = pafy.new(self.song.url)
            audio = pafyobj.getbest()  # Getbest instead of getbestaudio as getbestaudio caused VLC to error occasionally.
            url = audio.url
        except Exception as e:
            print(f"Error occurred while extracting {self.song.name}")
            print(e)
            return False

        media: vlc.Media = self.instance.media_new(url, ":no-video")  # Stops VLC from displaying any video.
        self.musicplayer.set_media(media)
        return True

    def finished(self):
        state = self.musicplayer.get_state()
        if state in [vlc.State.NothingSpecial, vlc.State.Stopped, vlc.State.Ended, vlc.State.Error]:
            return True
        return False

    def getpos(self):
        return self.musicplayer.get_position()

    def nextsong(self, override=None):
        print("nextsong called")

        if override is None:
            self.manual = False
            if self.song and self.song in self.playlist.getsongs() and self.song not in self.queue:
                self.playlist.seensongs.add(self.song)

            if len(self.queue) > 0:
                nextsong = self.queue.pop(0)
            else:
                print("yes")
                self.playlist.seensongs = set()
                self.queue = self.playlist.getqueue()
                nextsong = self.queue.pop(0)
        else:
            self.manual = True
            nextsong = override
        errcount = 0
        print("Attempting to set song.")
        successful = False
        while not successful:
            while not self.setsong(nextsong):
                errcount += 1
                print("Retrying...")
                time.sleep(1)
                if errcount > 8:
                    self.song = None
                    return False
            print("Attempting to play")
            if not self.play():
                print("Couldn't play? VLC State: ", self.musicplayer.get_state())
                continue
            successful = True
        self.toaster.show_toast(title="NOW PLAYING", msg=nextsong.name, icon_path=ICON, duration=5, threaded=True,
                                sound=False)
        print("\n---NEXT SONG---")
        print(songdetails(self.song))

        return True

    def manualsong(self, song: Song):
        self.nextsong(override=song)

    def skip(self):
        if len(self.playlist.getsongs()) > 0:
            self.nextsong()

    def setvolume(self, value):
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        self.musicplayer.audio_set_volume(value)

    def getvolume(self):
        return self.musicplayer.audio_get_volume()

    def refreshplaylist(self, playlist: Playlist = None):
        if playlist is None:
            playlist = self.playlist
        else:
            self.playlist = playlist
        self.songlist = playlist.getsongs()
        self.queue = playlist.getqueue()

    def seek(self, seekpercent):
        if self.musicplayer.is_seekable():
            self.musicplayer.set_time(int(self.musicplayer.get_length() * seekpercent))
            return True
        return False

    def getstart(self):
        return time.time() - (self.musicplayer.get_time() // 1000)

    def getend(self):
        return self.getstart() + (self.musicplayer.get_length() // 1000)


class GlobalVars:
    pass


G = GlobalVars()
G.input = ""
G.player = None
G.songset: set[Song] = set()
G.cursave = None
G.logs = []

oldprint = print


def print(*args, **kwargs):
    oldprint(*args, **kwargs)
    G.logs.append((time.localtime(), args))


def songdetails(song):
    return (f"Title: {song.name}\n"
          f"Author: {song.author}\n"
          f"Duration: {song.duration}")


def savedata(stuff, cursave=None):
    data = pickle.dumps(stuff)
    if cursave != data:
        with open(DATAFILE, "wb") as file:
            file.write(data)
            cursave = data
    return cursave


def savelog(logs, savedlog):
    if logs != savedlog:
        with open(LOGFILE, "w", encoding='utf-8') as f:
            for log in logs:
                logstr = ""
                timevalues = log[0]
                logstr += f"{timevalues.tm_hour:0>2}:{timevalues.tm_min:0>2}:{timevalues.tm_sec:0>2}: "
                for obj in log[1]:
                    objstring = str(obj).replace("\n", "\n\t  ")
                    logstr += objstring + " "
                f.write(logstr + "\n\n")
        savedlog = logs.copy()
    return savedlog


def searchsongname(targetlist: list[Song], targetvalue: str):
    targetlist = targetlist.copy()
    matches = []
    for target in targetlist:
        if target.name.lower().find(targetvalue) != -1:
            matches.append(target)
    return matches


def main():
    defaults = {
        'songs': set(),
        'playlists': {
            'empty': Playlist("empty")
        },
        'options': {
            'volume': 50,
            'keybinds': {
                'pause': '<alt>+p',
                'skip': '<alt>+s',
            },
            'discord': True
        },
        'playlistids': []
    }
    with open(DATAFILE, "rb") as file:
        try:
            loaddata: dict = pickle.load(file)
            if not loaddata['options']['keybinds']:
                loaddata['options']['keybinds'] = defaults['options']['keybinds']
            saveinfo = loaddata
        except EOFError:
            print("Could not retrieve data.")
            saveinfo = defaults
    G.songset: set[Song] = saveinfo['songs']
    inp = ""
    playlists = saveinfo['playlists']
    playlists['empty'] = Playlist("empty")
    playlist: Playlist = playlists['empty']
    options = saveinfo['options']

    keybinddict: dict[str: str] = options['keybinds']
    print("List is up to date!")

    # curplayerthread = threading.Thread(target=Player, daemon=False, args=[playlist.songs, generateplaylist(playlist)])
    # curplayerthread.start()
    # while G.player is None:
    #     pass
    # player = G.player
    player = Player(playlist)
    player.setvolume(options['volume'])
    print("Created sound player.")

    guithread = threading.Thread(target=musicGUI.Musicgui, args=[list(playlists.values()), options])
    guithread.start()
    while musicGUI.G.musicgui is None:
        pass
    gui: musicGUI.Musicgui = musicGUI.G.musicgui
    print("Started GUI!")

    def hotkeyfunction(hotkeyname):
        def newfunction():
            gui.output = hotkeyname
        return newfunction

    hotkeylistener = kb.GlobalHotKeys(
        hotkeys={v: hotkeyfunction(k) for k, v in keybinddict.items()}
    )
    hotkeylistener.start()

    def updatelistener(listener):
        listener.stop()
        newlistener = kb.GlobalHotKeys(
            hotkeys={v: hotkeyfunction(k) for k, v in keybinddict.items()}
        )
        newlistener.start()
        return newlistener

    cursave = savedata(saveinfo)
    savedlog = []

    rpc = None
    rpccount = 0

    def updatepresence(irpc):
        try:
            if options['discord']:
                if not irpc:
                    irpc = pypresence.Presence(CLIENTID)
                    irpc.connect()
                args = {
                    'large_image': 'btecify1024',
                    'large_text': APPNAME
                }
                if player.song:
                    args['details'] = f"{player.song.name} | {player.song.author}"
                    if player.paused:
                        args['state'] = "Paused"
                    else:
                        args['state'] = "Playing"
                        args['start'] = int(player.getstart())
                        args['end'] = int(player.getend())

                else:
                    args['state'] = "Stopped"

                irpc.update(**args)
                return irpc

            elif not options['discord']:
                if irpc:
                    irpc.close()
                return None

        except (pypresence.InvalidID, pypresence.InvalidPipe, RuntimeError, Exception) as e:
            print(e)
            print("Discord not found or presence failed.")
            return None

    def updategui():  # ORDER IS IMPORTANT!!!
        gui.updatecurrentplaylist(playlist)
        gui.updatesonglist(G.songset.copy())
        gui.updatesong(player.song, player.manual)
        gui.updatequeue(player.queue.copy())
        gui.updateprogressbar(int(player.getpos() * 100))
        gui.updateplaylists(playlists.values())
        gui.updatelogs(G.logs)
        gui.updatekeybinds(list(keybinddict.items()))

    def retrievelogs():
        logs = musicGUI.G.logs.copy()
        for log in logs:  # Trying to be more thread-safe and stuff idk
            musicGUI.G.logs.remove(log)
        return logs

    updategui()
    while True:
        if player.finished() and playlist and len(playlist.getsongs()) > 0:
            while not player.nextsong():
                print("SONG FAILED TO PLAY. MOVING ON.")

        if gui.output[0]:
            inp = gui.output
            command = inp[0]
            if command.lower() == "help":
                print("---HELP---")
                print("skip\npause\ngetsongs\ngetqueue\nvolume - value\naddlist - name - url\n"
                      "switchlist - name\nremovelist - name\ngetcurrentsong\nblacklist - (optional)songname\n"
                      "requeue\nunwatch")

            elif command.lower() == "skip" or command == 's':
                print("Skipping song.")
                player.skip()

            elif command.lower() == "pause" or command == 'p':
                if not player.paused:
                    print("Pausing...")
                    player.pause()
                    gui.pause()

                else:
                    print("Unpausing...")
                    player.pause()
                    gui.unpause()

            elif command.lower() == "volume" or command == 'v':
                if len(inp) > 1:
                    value = inp[1]
                    player.setvolume(value)
                    options['volume'] = value
                    print(f"Setting volume to {value}%")
                else:
                    print(f"Volume: {player.getvolume()}")

            elif (command.lower() == "addlist" or command == 'al') and len(inp) > 1:
                name = inp[1]
                if name not in playlists:
                    if len(inp) == 3:
                        url = inp[2]
                        newplaylist = Playlist(name, url)
                        playlists[newplaylist.name] = newplaylist
                        print(f"Added playlist {newplaylist.name} with url {newplaylist.url}")
                    elif len(inp) == 2:
                        newplaylist = Playlist(name)
                        playlists[newplaylist.name] = newplaylist
                        print(f"Added playlist {newplaylist.name} with no url.")
                else:
                    print("Playlist already exists: "+name)

            elif (command == 'switchlist' or command == 'sl') and len(inp) > 1:
                target = inp[1]
                if target not in playlists:
                    print("Invalid playlist.")
                else:
                    targetpl = playlists[target]
                    targetpl.refreshplaylistfromyoutube()
                    playlist = targetpl
                    player.refreshplaylist(targetpl)

            elif (command == 'removelist' or command == 'rl') and len(inp) > 1:
                target = inp[1]
                print(target)
                if target.name in playlists:
                    print("Deleting", target)
                    del playlists[target.name]

            elif command == "getcurrentsong" or command == 'gcs':
                print("\n"+songdetails(player.song))

            elif command == "blacklist" and len(inp) == 2:
                selectedsong = inp[1]

                if selectedsong is not None:
                    playlist.removesong(selectedsong)

            elif command == "removesongsfromplaylist" and len(inp) == 3:
                targetpl = inp[1]
                targetsongs = inp[2]
                if targetpl and targetsongs:
                    for song in targetsongs:
                        targetpl.removesong(song)

            elif command == "requeue":
                player.queue = playlist.getqueue()

            elif command == "unwatch" and len(inp) > 1:
                targetplaylistname = inp[1]
                if targetplaylistname in playlists:
                    targetplaylist = playlists[targetplaylistname]
                    targetplaylist.seensongs = set()
                    player.queue = playlist.getqueue()
                else:
                    print("Received unwatch but no valid playlist: "+targetplaylistname)

            elif command == "song" and len(inp) > 1:
                song = inp[1]
                if type(song) is str:
                    matches = searchsongname(playlist.getsongs().copy(), song)
                    if not matches:
                        print("Song not found.")
                    if len(matches) > 1:
                        print("Be more specific. Found: ")
                        print(list(k.name for k in matches))
                    else:
                        player.manualsong(matches[0])
                        manual = True
                elif type(song) is Song:
                    player.manualsong(song)
                    manual = True
                else:
                    print("Couldn't get manual song type?")

            elif command == "forceupdate" and len(inp) == 2:
                value = inp[1]
                if value in playlists:
                    targetpl = playlists[value]
                    targetpl.refreshplaylistfromyoutube(force=True)

            elif command == "addsong" and len(inp) >= 2:
                targetpl = inp[1]
                songs = inp[2:] or [player.song]
                for song in songs:
                    targetpl.addsong(song)

            elif command == "createsong" and len(inp) == 2:
                url = inp[1]
                newsong = Song.createsongfromurl(url)
                if newsong:
                    G.songset.add(newsong)

            elif command == "EXIT":
                break

            elif command == "resetfromyoutube" and len(inp) == 2:
                targetpl = inp[1]
                if targetpl in playlists:
                    targetpl = playlists[targetpl]
                    targetpl.clearcustomsongs()
                    player.refreshplaylist(targetpl)

            elif command == "removesongfromplaylists" and len(inp) == 3:
                targetsong = inp[1]
                targetplaylists = inp[2]
                for pl in targetplaylists:
                    pl.removesong(targetsong)

            elif command == "openinyoutube" and len(inp) > 1:
                songs = inp[1]
                for song in songs:
                    if song is not None:
                        print("Opening", song.url)
                        BROWSER.open_new_tab(song.url)

            elif command == "renameplaylist" and len(inp) == 3:
                targetpl: Playlist = inp[1]
                newname: str = inp[2]
                if targetpl and newname:
                    if targetpl.name != "empty" and newname not in playlists:
                        del playlists[targetpl.name]
                        targetpl.name = newname
                        playlists[targetpl.name] = targetpl

            elif command == "newapikey" and len(inp) == 1:
                key = ""
                while len(key) != APIKEYLENGTH:
                    key = musicGUI.msgbox("API Key", "Enter a new api key", str)
                    if not key:
                        key = ""
                        break
                if key:
                    pafy.set_api_key(key)
                    with open(APIKEYFILE, "w") as f:
                        f.write(key)

            elif command == "randomsong" and len(inp) == 1:
                song = random.choice(list(G.songset))
                player.manualsong(song)

            elif command == "copyplaylist" and len(inp) == 3:
                targetpl: Playlist = inp[1]
                newname: str = inp[2]
                if targetpl and newname:
                    playlists[newname] = Playlist(newname, targetpl.url, targetpl.ytplaylist,
                                                  targetpl.addedsongs, targetpl.removedsongs, False)

            elif command == "seek" and len(inp) == 2:
                seekpercent = inp[1]
                player.seek(seekpercent)

            elif command == "deletesongs" and len(inp) > 1:
                songs = inp[1:]

                for song in songs:
                    if song in G.songset:
                        G.songset.remove(song)

            elif command == "opendatadirectory" and len(inp) == 1:
                os.startfile(DATADIRECTORY.replace("/", "\\"))

            elif command == "defaultkeybinds" and len(inp) == 1:
                keybinddict.update(defaults['options']['keybinds'])
                updatelistener(hotkeylistener)

            elif command == "updatekeybinds" and len(inp) >= 2:
                old = keybinddict.copy()
                kbupdate = inp[1:]
                for j in kbupdate:
                    keybinddict[j[0]] = j[1]
                try:
                    updatelistener(hotkeylistener)
                except ValueError:
                    keybinddict = old
                    musicGUI.msgbox("Keybind", "Bad keybind format. Default format: '<A>+B'\nA is alt, ctrl, or shift\nB is any letter or number.", "Error")
                pass

            elif command == "discordpresence" and len(inp) == 2:
                options['discord'] = inp[1]

            gui.clearoutput()

        G.logs.extend(retrievelogs())
        updategui()
        rpccount += 1
        if rpccount == RPCRATE:
            rpc = updatepresence(rpc)
            rpccount = 0
        cursave = savedata(saveinfo, cursave)
        savedlog = savelog(G.logs, savedlog)
        time.sleep(0.05)
    print("Exiting program...")


if __name__ == '__main__':
    try:
        with open(DATAFILE, "rb") as f:
            obj: dict = pickle.load(f)

        if not obj['options'].get("version"):
            obj['options']['version'] = semver.Version('0.0.0')

        cver = obj['options']['version']
        if cver < semver.Version('1.1.0'):
            if not obj['options'].get('keybinds'):
                obj['options']['keybinds'] = {}

        if cver < semver.Version('1.2.0'):
            obj['options']['discord'] = True

        obj['options']['version'] = semver.Version(VERSION)

        with open(DATAFILE, "wb") as f:
            pickle.dump(obj, f)
    except Exception:
        pass
    main()
