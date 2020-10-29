import vlc
import pafy
import pickle
import threading
import random
import time
from win10toast import ToastNotifier
from sys import exit

with open("programinfo.txt", "r") as file:
    lines = file.readlines()
APIKEY = lines[0]
PLAYLISTURL = lines[1]

DATAFILENAME = "data.txt"
SEEDURATIONKEYWORD = "NOTHING"
ICON = "btecify.ico"

pafy.set_api_key(APIKEY)


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
        song = pafy.new(url)
        return Song(song.videoid, song.title, url, song.duration, song.author)


class Playlist:
    url = ""
    name = ""
    seensongs: set[Song] = set()
    ytplaylist: set[Song] = set()
    addedsongs: set[Song] = set()
    removedsongs: set[Song] = set()

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
            self.refreshplaylistfromyoutube()
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
                            if video.videoid not in map(lambda a: a.vidid, G.songlist):
                                newsong = Song(video.videoid, video.title, video.watchv_url, video.duration, video.author,)
                                G.songlist.add(newsong)
                                self.ytplaylist.add(newsong)
                                print(f"Downloading and adding {video.title}")

                            else:
                                correlatesong = G.songlist[list(map(lambda a: a.vidid, G.songlist)).index(video.videoid)]
                                self.ytplaylist.add(correlatesong)
                                print(f"Finding and adding {video.title}")
                except pafy.util.GdataError as e:
                    print("Couldn't update songlist:", e)

        else:
            print("Local playlist - no update.")

    def removesong(self, song: Song):
        if song in self.addedsongs:
            self.addedsongs.remove(song)


class Player:
    song: Song = None
    paused: bool
    instance: vlc.Instance
    musicplayer: vlc.MediaPlayer
    songlist: list[Song]
    queue: list[Song]
    playlist: Playlist
    toaster: ToastNotifier

    def __init__(self):
        self.instance: vlc.Instance = vlc.Instance()
        self.musicplayer = self.instance.media_player_new()
        self.paused = False
        self.toaster = ToastNotifier()
        self.playlist = None
        self.songlist = None
        self.queue = []

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
            if self.song and self.song in self.playlist.getsongs() and self.song not in self.queue:
                self.playlist.seensongs.add(self.song)

            if len(self.queue) > 0:
                nextsong = self.queue.pop(0)
            else:
                print("yes")
                self.playlist.seensongs = set()
                self.queue = self.playlist.getqueue()
                playinglist = self.songlist
                random.shuffle(playinglist)
                print(self.queue)
                nextsong = self.queue.pop(0)
        else:
            nextsong = override
        errcount = 0
        print("Attempting to set song.")
        successful = False
        while not successful:
            while not self.setsong(nextsong):
                errcount += 1
                print("Retrying...")
                time.sleep(1)
                if errcount > 4:
                    return False
            self.toaster.show_toast(title="NOW PLAYING", msg=nextsong.name, icon_path=ICON, duration=5, threaded=True, sound=False)
            print("Attempting to play")
            if not self.play():
                print("Couldn't play? VLC State: ", self.musicplayer.get_state())
                continue
            successful = True
        print("\n---NEXT SONG---")
        print(songdetails(self.song))

        return True

    def manualsong(self, song: Song):
        self.nextsong(override=song)

    def skip(self):
        self.nextsong()

    def setvolume(self, value):
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        self.musicplayer.audio_set_volume(value)

    def getvolume(self):
        return self.musicplayer.audio_get_volume()

    def switchplaylist(self, playlist: Playlist):
        self.playlist = playlist
        self.songlist = playlist.getsongs()
        self.queue = playlist.getqueue()


import musicGUI


class GlobalVars:
    pass


G = GlobalVars()
G.input = ""
G.player = None
G.songlist: set[Song] = set()


def infunc():
    while True:
        while G.input:
            pass
        inp = input("")
        if not inp:
            G.input = SEEDURATIONKEYWORD

        else:
            G.input = inp


def songdetails(song):
    return (f"Title: {song.name}\n"
          f"Author: {song.author}\n"
          f"Duration: {song.duration}")


def savedata(stuff):
    with open(DATAFILENAME, "wb") as file:
        pickle.dump(stuff, file)


# def searchsongname(targetlist: List[Song], targetvalue: str):
#     targetlist = targetlist.copy()
#     temp = []
#     for i in range(0, len(targetvalue)):
#         for song in targetlist:
#             if song.name[i].lower() == targetvalue[i].lower():
#                 temp.append(song)
#         targetlist = temp.copy()
#         temp = []
#     return targetlist

def searchsongname(targetlist: list[Song], targetvalue: str):
    targetlist = targetlist.copy()
    matches = []
    for target in targetlist:
        if target.name.lower().find(targetvalue) != -1:
            matches.append(target)
    return matches


def main():
    saveinfo = {
        'songs': set(),
        'playlists': {
            'empty': Playlist("empty")
        },
        'options': {
            'volume': 50
        },
    }
    with open(DATAFILENAME, "rb") as file:
        try:
            loaddata: dict = pickle.load(file)
            saveinfo.update(loaddata)
        except EOFError:
            print("Could not retrieve data.")
    G.songlist = sorted(saveinfo['songs'], key=lambda a: a.name.lower())
    inp = ""
    saveinfo['playlists']['empty'] = Playlist("empty")
    playlist: Playlist = saveinfo['playlists']['empty']

    print("List is up to date!")

    # curplayerthread = threading.Thread(target=Player, daemon=False, args=[playlist.songs, generateplaylist(playlist)])
    # curplayerthread.start()
    # while G.player is None:
    #     pass
    # player = G.player
    player = Player()
    player.setvolume(saveinfo['options']['volume'])
    print("Created sound player.")

    guithread = threading.Thread(target=musicGUI.Musicgui, args=[list(saveinfo['playlists'].values()), saveinfo['options']])
    guithread.start()
    while musicGUI.G.musicgui is None:
        pass
    gui: musicGUI.Musicgui = musicGUI.G.musicgui
    print("Started GUI!")

    while playlist is None:
        inp = gui.output
        if not gui.output[0]:
            time.sleep(0.4)
            continue
        if inp[0] == "switchlist":
            playlist = saveinfo['playlists'][inp[1]]
            playlist.refreshplaylistfromyoutube()
            player.switchplaylist(playlist)
        elif inp[0] == "EXIT":
            print("Closed window...")
            exit("exiting")
        elif inp[0] != "":
            gui.clearoutput()
        else:
            pass

    savedata(saveinfo)
    print("Selected first playlist.")
    gui.clearoutput()

    def updategui():
        gui.updatesonglist(G.songlist.copy())
        gui.updatequeue(player.queue.copy())
        gui.updatesong(player.song)
        gui.updateprogressbar(int(player.getpos() * 100))
        gui.updateplaylists(saveinfo['playlists'].values())

    first = True
    updategui()
    print(player.finished())
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
                    saveinfo['options']['volume'] = value
                    print(f"Setting volume to {value}%")
                else:
                    print(f"Volume: {player.getvolume()}")

            elif (command.lower() == "addlist" or command == 'al') and len(inp) > 1:
                name = inp[1]
                if name not in saveinfo['playlists']:
                    if len(inp) == 3:
                        url = inp[2]
                        newplaylist = Playlist(name, url)
                        saveinfo['playlists'][newplaylist.name] = newplaylist
                        print(f"Added playlist {newplaylist.name} with url {newplaylist.url}")
                    elif len(inp) == 2:
                        newplaylist = Playlist(name)
                        saveinfo['playlists'][newplaylist.name] = newplaylist
                        print(f"Added playlist {newplaylist.name} with no url.")
                else:
                    print("Playlist already exists: "+name)

            elif (command == 'switchlist' or command == 'sl') and len(inp) > 1:
                target = inp[1]
                if target not in saveinfo['playlists']:
                    print("Invalid playlist.")
                else:
                    targetpl = saveinfo['playlists'][target]
                    targetpl.refreshplaylistfromyoutube()
                    playlist = targetpl
                    player.switchplaylist(targetpl)

            elif (command == 'removelist' or command == 'rl') and len(inp) > 1:
                target = inp[1]
                print(target)
                if target.name in saveinfo['playlists']:
                    print("Deleting", target)
                    del saveinfo['playlists'][target.name]

            elif command == "getcurrentsong" or command == 'gcs':
                print("\n"+songdetails(player.song))

            elif command == "oldblacklist" or command == 'bl':  # Not in use anymore...
                if len(inp) > 1:
                    value = " ".join(inp[1:])
                    matches = searchsongname(playlist.getsongs().copy(), value)

                    if len(matches) > 1:
                        print("Be more specific. Found: ")
                        print(list(k.name for k in matches))
                    elif not matches:
                        print("Not found.")
                    else:
                        matches[0].blacklist = not matches[0].blacklist
                        print(f"{matches[0].name} has blacklist now set to: {matches[0].blacklist}")
                else:
                    player.song.blacklist = not player.song.blacklist
                    print(f"{player.song.name} has blacklist now set to: {player.song.blacklist}")

            elif command == "blacklist" and len(inp) == 2:
                selectedsongs = inp[1]

                if len(selectedsongs) != 0:
                    for song in selectedsongs:
                        playlist.removesong(song)
                pass

            elif command == "requeue":
                player.queue = playlist.getqueue()

            elif command == "unwatch" and len(inp) > 1:
                targetplaylistname = inp[1]
                if targetplaylistname in saveinfo['playlists']:
                    targetplaylist = saveinfo['playlists'][targetplaylistname]
                    targetplaylist.seensongs = set()
                    player.queue = playlist.getqueue()
                else:
                    print("Received unwatch but no valid playlist: "+targetplaylistname)

            elif command == "song" and len(inp) > 1:
                song = inp[1]
                print(song, type(song))
                if type(song) is str:
                    matches = searchsongname(playlist.getsongs().copy(), song)
                    if not matches:
                        print("Song not found.")
                    if len(matches) > 1:
                        print("Be more specific. Found: ")
                        print(list(k.name for k in matches))
                    else:
                        player.manualsong(matches[0])
                elif type(song) is Song:
                    player.manualsong(song)
                else:
                    print("Couldn't get manual song type?")

            elif command == "forceupdate" and len(inp) == 2:
                value = inp[1]
                if value in saveinfo['playlists']:
                    targetpl = saveinfo['playlists'][value]
                    targetpl.refreshplaylistfromyoutube(force=True)

            elif command == "addsong" and len(inp) >=2:
                playlist = inp[1]
                songs = inp[2:] or [player.song]
                for song in songs:
                    playlist.getsongs().append(song)

            elif command == "createsong" and len(inp) == 2:
                url = inp[1]
                G.songlist.append(Song.createsongfromurl(url))
                G.songlist = sorted(G.songlist, key=lambda a: a.name.lower())

            elif command == "EXIT":
                print("Exiting...")
                exit("Exited.")

            gui.clearoutput()
        updategui()
        savedata(saveinfo)
        time.sleep(0.1)


def temp():
    with open(DATAFILENAME,"rb") as file:
        stuff = pickle.load(file)
    print(stuff)


if __name__ == '__main__':
    # import pickle
    #
    # with open("data.txt", "rb") as f:
    #     stuff = pickle.load(f)
    #
    # print(stuff)
    # newstuff = {}
    # songlistt = []
    # toaddlist = stuff['music'].songs
    # toaddlist.extend(stuff['bangers'].songs)
    # toaddlist.extend(stuff['calm'].songs)
    # for x in toaddlist:
    #     if x.name not in [i.name for i in songlistt]:
    #         songlistt.append(Song(x.vidid, x.name, x.url, x.duration, x.author))
    # #print([i.name for i in songlist])
    # #print(len(songlist))
    #
    # playlists = {}
    # playlists['music'] = Playlist(stuff['music'].name, stuff['music'].url, autoupdate=False)
    # playlists['bangers'] = Playlist(stuff['bangers'].name, stuff['bangers'].url, autoupdate=False)
    # playlists['calm'] = Playlist(stuff['calm'].name, stuff['calm'].url, autoupdate=False)
    #
    # newstuff['songs'] = songlistt
    # newstuff['playlists'] = playlists
    # newstuff['options'] = {}
    # savedata(newstuff)

    main()
