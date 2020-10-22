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

    def __init__(self):
        root = tk.Tk()
        root.option_add('*tearOff', tk.FALSE)

        frame1 = ttk.Frame(root)
        frame1.grid(columnspan=3, rowspan=2)

        # QUEUE
        queuelabelframe = ttk.Labelframe(frame1, text="Song queue")
        templistvalue = list(range(1,101))
        listvalue = tk.StringVar(value=list(templistvalue))
        queuelist = tk.Listbox(queuelabelframe, height=15, listvariable=listvalue, state="disabled")
        queuelabelframe.grid(column=0, row=0)
        queuelist.grid()

        # DEFINING THE PLAYING FRAME
        playingframe = ttk.Frame(frame1, relief='groove', padding=5)
        playingframe.grid(column=1, row=0, columnspan=1, rowspan=4, sticky='nwe')

        songinfo = ttk.Label(playingframe, text="Temporary songname\nTemporary author\nTemporary duration")
        songinfo.grid(column=0, row=0)

        songdesc = ttk.Label(playingframe, text="TEMPORARY DESCRIPTION TEMPORARY DESCRIPTION\nTEMPORARY DESCRIPTION")
        songdesc.grid(column=0, row=1)

        playingframeseperator = ttk.Separator(playingframe, orient=tk.HORIZONTAL)
        playingframeseperator.grid(column=0, row=2, sticky='we')

        songprogress = ttk.Progressbar(playingframe, orient=tk.HORIZONTAL, mode='determinate')
        songprogress.grid(column=0, row=3, sticky='s')

        # SONG SELECTION
        songlistlabelframe = ttk.Labelframe(frame1, text="Song list")
        templistvalue = ['1: lol', '2: pog', '3: gay']
        songlist = tk.StringVar(value=list(reversed(templistvalue)))
        queuelist = tk.Listbox(songlistlabelframe, height=15, listvariable=songlist)
        songlistlabelframe.grid(column=2, row=0)
        queuelist.grid()

        # BOTTOM LEFT LOGO
        shitifyiconimage = tk.PhotoImage(file="shitify.png")
        shitifyiconlabel = ttk.Label(frame1, image=shitifyiconimage)
        shitifyiconlabel.grid(column=0, row=1, sticky='nesw')

        root.mainloop()

musicgui()