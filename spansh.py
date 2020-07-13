import json
import os
import pyperclip
import re
import requests
import threading
import time

import tkinter as tk
import tkinter.font as tkFont


# EDMC imports
from theme import theme
from config import config

HELP_MSG = """
Spansh-gin Howto

1) Plot your route on
   https://spansh.co.uk
2) Copy the route URL above ^
3) Plot!
4) When you jump to a system
   on the route, the plugin
   will copy it for you: just
   open the map and paste it

NOTES:

1) Routes get stale quickly:
   replot on Spansh if the
   plotting here fails.
2) If you feed a route and
   you are not in a system on
   that route, you may have
   to copy the next system
   manually as the plugin has
   to assume the first system
   in the route is the
   desired one. To avoid this
   replot the route on Spansh
   from your current system.
   This is ONLY needed if you
   plot a route in the plugin
   and you are NOT on the
   route.
3) To refresh settings
   changed from EDMC, you
   have to close and reopen
   Spansh-gin window.

"""

# TODO
# 7) switcha a logging

# DONE
# 2) mettere un messaggio se il plotting e' stale
# 3) mettere always on top (possibilmente accedendo alla config)
# 4) l'ultimo waypoint non si cancella quando viene raggiunto
# 5) quando aggiorna la textarea con qualcosa che e' in fondo la fa ripartire
#    dall'inizio
# 6) controlla URL
# 8) metti degli switch di debug per disabilitare automaticamente gli import e
#    le altre cagate di dbg


DEBUG = False

class SpanshViewer():

    def __init__(self, parent):
        self.parent = parent
        self.current = ""
        self.target = 0
        self.arrived = False
        self.systems = []
        self.update_needed = False
        self.timer = None
        self.stop = False
        self.lab = None
        self.url = None
        self.button = None
        self.sem = threading.Semaphore()

    def fetch_data(self, url):
        if not DEBUG:
            r = requests.get(url)
            data = r.json()
        else:
            import parse
            data = parse.data

        return data

    def button_callback(self):
        url = self.url.get()
        if url == "":
            return

        # we need to switch from a spansh user-link to an api one
        url = url.split("?")[0]
        url = url.replace("plotter", "api")
        print (url)

        if DEBUG:
            url = "https://spansh.co.uk/api/results/zuppa"

        # if not url.startswith("https://spansh.co.uk/api/results/"):
        if not re.match(r"^https://(www\.)?spansh.co.uk/api/results/", url):
            print ("Wrong URL, not spansh!")
            self.show_error("The URL you pasted is not a spansh.co.uk URL."
                            " Please copy a plot URL from https://spansh.co.uk"
                            " here before pressing the Plot! button")
            return

        data = self.fetch_data(url)

        if ("status" not in data or data['status'] != "ok" or
            "result" not in data or "system_jumps" not in data["result"]):
            print ("Did not get results!")
            self.show_error("Failed to get results from the URL you pasted.\n\n"
                            "It's most likely due to an old link, please replot"
                            " the route on https://spansh.co.uk and paste a"
                            " fresh link here.")
            return

        # reset systems
        self.systems = []
        for sys in data['result']['system_jumps']:
            self.systems.append(sys["system"])

        # In case the route is plotted while already traveling on it and we are
        # already on a waypoint, update the target
        with self.sem:
            if self.current != "":
                if self.current not in self.systems:
                    print ("Current system is not in ")
                    self.show_error(("Warning! The current system (%s) is *not*"
                                     "on the route. I copied the first system "
                                     " for you, but make sure you are not "
                                     "already some step ahead before jumping!")
                                    % self.current)
                else:
                    self.set_target_index(self.current)

            # An update is always needed when reloading a plot
            self.update_needed = True

    def show_error(self, text):
        # self.starz.configure(state=tk.NORMAL)
        # self.starz.delete(1.0, tk.END)
        # self.starz.insert("end", text)
        # self.starz.see("1.0")
        # self.starz.configure(state=tk.DISABLED)
        ErrorPopup(self.app, text)

    def update_starz(self):
        with self.sem:
            if self.update_needed:
                print ("Updating star list")
                self.starz.configure(state=tk.NORMAL)
                self.starz.delete(1.0, tk.END)
                for sys_idx in xrange(len(self.systems)):
                    self.starz.insert("end", "%s\n" % self.systems[sys_idx])
                    if sys_idx < self.target or self.arrived:
                        self.starz.tag_add("done", "%s.0" % (sys_idx+1),
                                           "%s.0" % (sys_idx+2))
                    elif sys_idx == self.target:
                        print ("target: %d" % sys_idx)
                        self.starz.tag_add("target", "%s.0" % (sys_idx+1),
                                           "%s.0" % (sys_idx+2))
                        # copy system name to the clipboard
                        pyperclip.copy(self.systems[self.target])
                        # scroll so that the target line is
                        self.starz.see("%s.0" % (sys_idx+1))

                if self.arrived: # scroll to the end
                    self.starz.see("%s.0" % (sys_idx+1))

                self.starz.configure(state=tk.DISABLED)

            self.update_needed = False
            if not self.stop:
                # recall self after x seconds
                self.timer = threading.Timer(1.0, self.update_starz)
                self.timer.start()

    def set_target_index(self, system):
        try:
            current_idx = self.systems.index(system)
        except ValueError:
            print ("System %s not found, doing nothing!" % system)
            return False

        if current_idx < len(self.systems) - 1:
            self.target = current_idx + 1
            self.arrived = False
        else: # we arrived at destination
            self.target = current_idx
            self.arrived = True

        print ("Set target to %d" % self.target)

        return True

    def update_position(self, system):
        with self.sem:
            print ("Updating position to %s" % system)
            self.current = system

            self.update_needed = self.set_target_index(system)

            # if an update is not needed, we possibly deviated or relogged in a
            # system that is not in the route. So it's highly likely the
            # clipboard has been invalidated, let's copy again the target
            # system
            if self.update_needed == False and len(self.systems) != 0:
                pyperclip.copy(self.systems[self.target])

    def close(self):
        self.stop = True
        if self.timer:
            print ("Waiting for timer thread to finish")
            self.timer.join()
        print ("Done. Destroying window")
        self.app.destroy()
        print ("Done.")

    def closed(self):
        return self.stop

    def start(self):
        self.app = tk.Toplevel(self.parent,
                               background=theme.current['background'])

        self.app.title("Spansh-gin - EDMC Spansh support")
        self.lab = tk.Label(self.app, text = "Route URL: ",
                            background=theme.current['background'],
                            foreground=theme.current['foreground'])
        self.lab.grid(row=0)

        self.url = tk.Entry(self.app)
        self.url.grid(row=0, column=1, sticky="W")
        self.button = tk.Button(self.app, text="Plot!",
                                background=theme.current['background'],
                                foreground=theme.current['foreground'],
                                command=self.button_callback)
        self.button.grid(row=0, column=2, sticky="W")

        # Text area for stars
        self.starz = tk.Text(self.app, height=30, width=30,
                             background=theme.current['background'],
                             foreground=theme.current['foreground'],
                             borderwidth=0)


        # Prepare fonts for tags
        target_font = tkFont.Font(self.starz, self.starz.cget("font"))
        target_font.configure(weight="bold", underline=True)
        done_font = tkFont.Font(self.starz, self.starz.cget("font"))
        done_font.configure(weight="normal", overstrike=True)

        # Prepare tags
        self.starz.tag_configure("target", foreground="green4",
                                 font=target_font)
        self.starz.tag_configure("done", foreground="slate gray",
                                 font=done_font)

        self.starz.insert("end", HELP_MSG)

        self.starz.configure(state=tk.DISABLED)
        self.starz.grid(row=1, columnspan=3)

        self.app.configure(background=theme.current['background'],
                           borderwidth=0)

        self.app.protocol("WM_DELETE_WINDOW", self.close)


        self.emptylabel = tk.Label(self.app,
                                   background=theme.current['background'],
                                   borderwidth=0,
                                   height=max(self.button.winfo_height(),
                                              self.url.winfo_height(),
                                              self.lab.winfo_height()))

        # Topmost
        self.app.attributes('-topmost',
                            1 if config.getint('always_ontop') else 0)

        # start the star list updater
        self.update_starz()


class ErrorPopup:
    def __init__(self, parent, message):
        self.top = tk.Toplevel(parent)
        self.top.title("Error! Spansh-gin")
        self.top.configure(background=theme.current['background'],
                           borderwidth=0)
        self.myLabel = tk.Label(self.top, text=message,
                                background=theme.current['background'],
                                foreground=theme.current['foreground'],
                                borderwidth=0, justify=tk.LEFT,
                                wraplength=2*parent.winfo_width())
        self.myLabel.pack()

        self.button = tk.Button(self.top, text="Ok", command=self.close)
        self.button.pack()

        self.top.lift(aboveThis=parent)

    def close(self):
        self.top.destroy()



def send_fake_positions(s):
    time.sleep(10)
    print ("aggiorno")
    s.update_position("Stuelou ER-L d8-145")
    time.sleep(5)
    s.update_position("Stuelou MD-I d10-137")
    time.sleep(5)

    s.update_position("Eol Prou OM-V d2-155")
    time.sleep(5)
    s.update_position("Colonia")

if __name__ == "__main__":
    # launch with PYTHONPATH pointing to the EDMarketconnector dir
    DEBUG = True
    theme.current =  {
        "background"         : "grey4",	# OSX inactive dark titlebar color
        "foreground"         : "orange",
        "activebackground"   : "white",
        "activeforeground"   : "grey4",
        "disabledforeground" : "grey3",
        "highlight"          : "grey2",
        "font"               : "TkDefaultFont",
    }

    app = tk.Tk()
    s = SpanshViewer(app)
    s.start()
    s.update_position("Prua Phoe VD-A d1-1")
    t = threading.Thread(target=send_fake_positions, args=(s, ))
    t.start()
    app.mainloop()
    t.join()
