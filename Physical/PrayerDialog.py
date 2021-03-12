# !/usr/bin/python3
"""
Simple Dialog box for prayers and responses.
"""


from tkinter import Tk, Toplevel, Frame, Label, Entry, StringVar, Button
from tkinter import WORD, INSERT, END, E, W, N, S, ACTIVE
from tkinter.scrolledtext import ScrolledText


class PrayerDialog(Toplevel):

    def __init__(self, parent, title=None, 
                 middle="Prayer", mustHaveSubject=True):
        # extended from TopLevel, but transient so a dialog ...
        Toplevel.__init__(self, parent)
        self.transient(parent)
        # init details
        if title:
            self.title(title)
        else:
            self.title("Input required")
        self.headings = ["Subject", "* " + middle, "Author"]
        self.mustHaveSubject = mustHaveSubject
        if mustHaveSubject:
            self.headings[0] = "* " + self.headings[0]
        self.parent = parent
        self.result = None
        # provide a home for details and find if there is a focus on it ...
        body = Frame(self)
        body.grid(column=0, row=0, padx=5, pady=5, sticky=(N, E, W, S))
        body.grid_rowconfigure(1, weight=3)
        self.initial_focus = self.body(body)
        # provide standard buttons if required (override with pass to remove)
        self.buttonbox()
        self.grab_set()
        # in no focus use whole dialog
        if not self.initial_focus:
            self.initial_focus = self
        # ensure closing dialog does so neatly
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        # overlay parent
        self.geometry("+%d+%d" % (parent.winfo_rootx(),
                                  parent.winfo_rooty()))
        # set focus and wait
        self.initial_focus.focus_set()
        self.wait_window(self)

    #
    # construction hooks

    def enter(self, event):
        # override dialog wide enter event for the ScrolledText box
        event.widget.insert(INSERT, "\n")
        return "break"  # so we don't propergate to class or parent level!

    def tab(self, event):
        # if tab event for the ScrolledText box, move to next box
        if event.widget == self.widgets[1][1]:
            self.widgets[2][1].focus_set()
        return "break"  # so we don't propergate to class or parent level!

    def body(self, frame):
        # create dialog body.  return widget that should have
        # initial focus.  this method can be overridden
        self.error = StringVar()
        self.label = Label(frame, textvariable=self.error)
        self.label.grid(column=0, row=0, padx=5, pady=5, sticky=(N, E, W, S))
        row = 1
        self.widgets = []
        for heading in self.headings:
            label = Label(frame, text=heading)
            label.grid(column=0, row=row, padx=5, pady=5, sticky=(N, E, W, S))
            frame.grid_rowconfigure(row, weight=1)
            row += 1
            if len(self.widgets) == 1:  # doing middle input
                entry = ScrolledText(frame, height=10, width=40, wrap=WORD)
                entry.bind("<Return>", self.enter)
                entry.bind("<Tab>", self.tab)
                frame.grid_rowconfigure(row, weight=3)
            else:
                entry = Entry(frame)
                frame.grid_rowconfigure(row, weight=1)
            entry.grid(column=0, row=row, padx=5, pady=5, sticky=(N, E, W, S))
            row += 1
            self.widgets.append([label, entry])
        focus = self.widgets[1][1]  # focus on middle box
        if self.mustHaveSubject:
            focus = self.widgets[0][1]  # focus on subject box
        return focus

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        box = Frame(self)
        box.grid(column=0, row=1, padx=5, pady=5, sticky=(N, E, W, S))
        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.grid(column=0, row=0, padx=5, pady=5, sticky=(N, E, W, S))
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.grid(column=1, row=0, padx=5, pady=5, sticky=(N, E, W, S))
        self.defaultBindings()
        return

    def defaultBindings(self):
        # add bindings for default keys
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        return

    #
    # standard button semantics
    #
    def ok(self, event=None):
        # allow for some validation of input before closing ...
        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
        else:  # all ok so accept and close
            self.withdraw()
            self.update_idletasks()
            self.apply()
            self.cancel()
        return

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()
        return

    #
    # command hooks
    #
    def validate(self):
        # any validation, return True of ok or False if errors
        ok = True
        middle = self.widgets[1][1].get(1.0, END).strip()
        if len(middle) == 0:
            ok = False
            self.error.set("Must enter a " + self.headings[1])
        elif self.mustHaveSubject:
            subject = self.widgets[0][1].get().strip()
            if len(subject) == 0:
                ok = False
                self.error.set("Must enter a " + self.headings[0])
        return ok

    def apply(self):
        # override if need to do something more
        self.result = [self.widgets[0][1].get().strip(),
                       self.widgets[1][1].get(1.0, END).strip(),
                       self.widgets[2][1].get().strip(),
                       ]
        return


if __name__ == '__main__':
    root = Tk()
    '''
    d = PrayerDialog(root)
    root.mainloop()
    if d.result:
        print("Results:", *d.result, sep="\n")
    else:
        print("Dialog cancelled")
    '''
    d = PrayerDialog(root, middle="Response", mustHaveSubject=False)
    root.mainloop()
    if d.result:
        print("Results:", *d.result, sep="\n")
    else:
        print("Dialog cancelled")
