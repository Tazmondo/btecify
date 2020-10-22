import vlc
import pafy
import pickle
from typing import List
import threading
import random
import time
from win10toast import ToastNotifier

with open("programinfo.txt", "r") as file:
    lines = file.readlines()
    APIKEY = lines[0]
    PLAYLISTURL = lines[1]


DATAFILENAME = "data.txt"
SEEDURATIONKEYWORD = "NOTHING"
ICON = "shitify.ico"

pafy.set_api_key(APIKEY)


class GlobalVars:
    pass
G = GlobalVars()
G.input = ""
G.player = None


class Song:
    vidid = ""
    name = ""
    url = ""
    duration = ""
    author = ""
    watched = False
    blacklist = False

    def __init__(self, vidid: str, name: str, url: str, duration: str, author: str,
                 watched: bool = False, blacklist: bool = False):
        self.vidid = vidid
        self.name = name
        self.url = url
        self.duration = duration
        self.author = author
        self.watched = watched
        self.blacklist = blacklist


class Playlist:
    url = ""
    songs: List[Song] = []
    name = ""

    def __init__(self, url: str, songs: List[Song], name: str):
        self.url = url
        self.songs = songs
        self.name = name


class Player:
    song: Song = None
    paused: bool
    instance: vlc.Instance
    musicplayer: vlc.MediaPlayer
    songlist: List[Song]
    playinglist: List[Song]
    toaster: ToastNotifier

    def __init__(self, songlist, playlist):
        self.instance: vlc.Instance = vlc.Instance()
        self.musicplayer = self.instance.media_player_new()
        self.songlist = songlist
        self.playinglist = playlist
        self.paused = False
        self.toaster = ToastNotifier()

        G.player = self

    def play(self):
        self.musicplayer.play()

    def pause(self):
        self.musicplayer.pause()
        self.paused = not self.paused

    def setsong(self, isong):
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
        pos = self.musicplayer.get_position()
        if pos > 0.99:
            return True
        return False

    def getpos(self):
        return self.musicplayer.get_position()

    def nextsong(self):
        if self.song:
            self.song.watched = True
        if len(self.playinglist) > 0:
            nextsong = self.playinglist.pop(0)
            errcount = 0
            while not self.setsong(nextsong):
                errcount += 1
                print("Retrying...")
                time.sleep(1)
                if errcount > 4:
                    return False
            self.toaster.show_toast(title="NOW PLAYING", msg=nextsong.name, icon_path=ICON, duration=5, threaded=True, sound=False)
            self.play()
            print("\n---NEXT SONG---")
            print(songdetails(self.song))

        else:
            for i in self.songlist:
                i.watched = False
            playinglist = self.songlist
            random.shuffle(playinglist)

        return True

    def manualsong(self, song):
        self.setsong(song)
        self.play()
        print("\n---NOW PLAYING---")
        print(songdetails(song))

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

    def switchplaylist(self, playlist):
        self.songlist = playlist.songs
        self.playinglist = generateplaylist(playlist)
        self.nextsong()


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


def generateplaylist(playlist: Playlist):
    playinglist = []
    for song in playlist.songs:
        if not song.watched and not song.blacklist:
            playinglist.append(song)

    if not playinglist:
        for song in playlist.songs:
            song.watched = False
            playinglist = list(filter(lambda a: not a.blacklist, playlist.songs))
    random.shuffle(playinglist)
    return playinglist


def searchsongname(targetlist: List[Song], targetvalue):
    targetlist = targetlist.copy()
    temp = []
    for i in range(0, len(targetvalue)):
        for song in targetlist:
            if song.name[i] == targetvalue[i]:
                temp.append(song)
        targetlist = temp.copy()
        temp = []
    return targetlist


def urlstuff(songlist, url, force=False):
    playlistobject = pafy.get_playlist2(url)
    playlistlength = len(playlistobject)

    if playlistlength - 1 != len(songlist) or force:
        print("Songlist is updating.")
        for video in playlistobject:
            if video.videoid not in map(lambda a: a.vidid, songlist):
                songlist.append(
                    Song(video.videoid, video.title, video.watchv_url, video.duration, video.author, watched=False)
                )
                print(f"Adding {video.title}")

        for song in songlist:
            if song.vidid not in map(lambda a: a.videoid, playlistobject):
                songlist.remove(song)
                print(f"Removing {song.name}")

    return songlist


def main():
    saveinfo = {}
    with open(DATAFILENAME, "rb") as file:
        try:
            saveinfo = pickle.load(file)
        except EOFError:
            print("Could not retrieve data.")
    saveinfo['reset'] = True
    inp = ""
    while inp not in saveinfo:
        print(list(i for i in saveinfo.keys()))
        inp = input("Enter playlist name\n")

    if inp != 'reset':
        playlist = saveinfo[inp]
        playlist.songs = urlstuff(playlist.songs, playlist.url)
        savedata(saveinfo)
        print(f"List updated. New length: {len(playlist.songs)}")

    else:
        playlist = Playlist(PLAYLISTURL, [], "music")
        playlist.songs = urlstuff(playlist.songs, playlist.url)
        saveinfo[playlist.name] = playlist
        savedata(saveinfo)
        print("List updated with default.")

    print("List is up to date!")

    curplayerthread = threading.Thread(target=Player, daemon=False, args=[playlist.songs, generateplaylist(playlist)])
    curplayerthread.start()
    while G.player is None:
        pass
    player = G.player
    print("Created sound player.")

    inputthread = threading.Thread(target=infunc, daemon=False)
    inputthread.start()
    print("Started input thread.")

    first = True
    while True:
        while (not G.input and not player.finished()) and not first:
            # Commented out because the input thread stops print from working in cmd prompt.
            numberofthings = int(player.getpos()*10)
            print("\b" * 12, end="")
            print("["+"■"*numberofthings + "-"*(10-numberofthings)+"]",end="")
            time.sleep(0.4)

            pass
        if player.finished() or first:
            if not player.nextsong():
                continue
            else:
                first = False


        if G.input:
            inp = G.input
            inp = inp.split(" ")
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

                else:
                    print("Unpausing...")
                    player.pause()

            elif command.lower() == "getsongs" or command == 'gs':
                for i in playlist.songs:
                    print(f'{i.name:>100} {i.watched:>5} {i.blacklist}')
                print(songdetails(player.song))

            elif command.lower() == "getqueue" or command == 'gq':
                output = ""
                length = len(player.playinglist)
                for i, v in enumerate(reversed(player.playinglist)):
                    output += f'{length - i:>3}: {v.name}\n'
                print(output, end="\n\n")
                print(songdetails(player.song))

            elif command.lower() == "volume" or command == 'v':
                if len(inp) > 1:
                    value = inp[1]
                    if value.isdigit():
                        value = int(value)
                        player.setvolume(value)
                        print(f"Setting volume to {value}%")
                    else:
                        print("Invalid volume. Must be between 0 and 100.")
                else:
                    print(f"Volume: {player.getvolume()}")

            elif (command.lower() == "addlist" or command == 'al') and len(inp) ==3:
                name = inp[1]
                url = inp[2]
                newplaylist = Playlist(url, [], name)
                saveinfo[newplaylist.name] = newplaylist
                print(f"Added playlist {newplaylist.name} with url {newplaylist.url}")

            elif (command == 'switchlist' or command == 'sl') and len(inp) > 1:
                target = inp[1]
                if target not in saveinfo:
                    print("Invalid playlist.")
                else:
                    targetpl = saveinfo[target]
                    targetpl.songs = urlstuff(targetpl.songs, targetpl.url)
                    playlist = targetpl
                    player.switchplaylist(targetpl)

            elif (command == 'removelist' or command == 'rl') and len(inp) > 1:
                target = inp[1]
                if target in saveinfo:
                    del saveinfo[target]

            elif command == "getcurrentsong" or command == 'gcs':
                print("\n"+songdetails(player.song))

            elif command == "blacklist" or command == 'bl':
                if len(inp) > 1:
                    value = " ".join(inp[1:])
                    matches = searchsongname(playlist.songs.copy(), value)

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

            elif command == "requeue":
                newqueue = generateplaylist(playlist)
                player.playinglist = newqueue
                playinglist = newqueue

            elif command == "unwatch":
                for song in playlist.songs:
                    song.watched = False
                newqueue = generateplaylist(playlist)
                player.playinglist = newqueue
                playinglist = newqueue

            elif command == "song" and len(inp) > 1:
                song = " ".join(inp[1:])
                matches = searchsongname(playlist.songs.copy(), song)
                if not matches:
                    print("Song not found.")
                if len(matches) > 1:
                    print("Be more specific. Found: ")
                    print(list(k.name for k in matches))
                else:
                    player.manualsong(matches[0])

            elif command == "forceupdate" and len(inp) == 2:
                value = inp[1]
                if value in saveinfo:
                    targetpl = saveinfo[value]
                    targetpl.songs = urlstuff(targetpl.songs, targetpl.url, force=True)

            G.input = ""
        savedata(saveinfo)


def temp():
    with open(DATAFILENAME,"rb") as file:
        stuff = pickle.load(file)
    print(stuff)

main()
