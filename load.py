import sys

import tkinter as tk

from spansh import SpanshViewer

from config import config

from theme import theme

PLUGIN_NAME = "Spansh"

# Holds globals
this = sys.modules[__name__]
this.s = None
this.parent = None
this.system = None

def plugin_start3(plugin_dir):
    """
    Load Template plugin into EDMC
    """

    # TODO: setup logging

    print ("%s loaded!" % PLUGIN_NAME)

    return PLUGIN_NAME

def plugin_stop():
    """
    EDMC is closing
    """
    print ("Farewell cruel world!")
    if this.s:
        this.s.close()


def open_spansh():
    print ("Open spansh!")
    if this.s != None:
        if not this.s.closed():
            print ("Spansh already running")
            return
        else:
            this.s = None

    this.s = SpanshViewer(this.parent)
    this.s.start()

    if this.system != None:
        print ("Setting position to: %s" % this.system)
        this.s.update_position(this.system)

def enterB(event):
    this.spansh_button.configure(background=theme.current['foreground'],
                                 foreground=theme.current['background'])


def leaveB(event):
    this.spansh_button.configure(background=theme.current['background'],
                                 foreground=theme.current['foreground'])


def plugin_app(parent):
    this.parent = parent
    this.spansh = tk.Frame(parent)
    this.spansh.columnconfigure(2, weight=1)
    this.spansh_button = tk.Button(this.spansh, text="Spansh-gin",
                                   command=this.open_spansh,
                                   width=28, borderwidth=0)

    this.spansh_button.bind('<Enter>', enterB)
    this.spansh_button.bind('<Leave>', leaveB)

    this.spansh_button.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)

    return this.spansh


# Detect journal events
def dashboard_entry(cmdr, system, station, entry):
    if (entry['event'] == 'Location' or
        entry['event'] == 'FSDJump' or
        entry['event'] == 'StartUp'):


        if this.s == None:
            # Cache the position for when we'll launch the spansh plugin
            this.system = system
        else:
            this.s.update_position(system)
