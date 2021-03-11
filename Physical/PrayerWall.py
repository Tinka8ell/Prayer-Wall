#!/usr/bin/python3
# Prayer Wall main app
from tkinter import Tk, Button, Frame, Text, Toplevel, Canvas, PhotoImage, Label, IntVar, StringVar, LabelFrame, messagebox, Scrollbar
from tkinter.scrolledtext import ScrolledText
from tkinter import N, E, W, S, CENTER, NW, END, WORD, NORMAL, DISABLED
from tkinter.font import Font, families, names, nametofont, ITALIC, BOLD
from PIL import Image, ImageTk

import sys, socket, re, webbrowser
from time import time, sleep
from Prayers import Prayers, prayPost
from PrayerDialog import PrayerDialog

# orignal prayer wall:
WIDTH = 1280
HEIGHT = 1024

# current (reduced prayer wall:
WIDTH = 1024
HEIGHT = 768

defaultFont = None
italicFont = None
boldFont =  None
fontSize = None

counter = 0

icon = None

blue = '#0000FF' # bright blue!

heatColour = ['#00FF00', # green - unprayed rest us the #RRGGBB format
              '#FFFF00', # yellow
              '#FFDF00', 
              '#FFBF00', 
              '#FF9F00', 
              '#FF7F00', 
              '#FF5F00', 
              '#FF3F00', 
              '#FF1F00', 
              '#FF0000', # red
              ]

def newRequest(parent):
   # open form for new prayer request
   dialog = PrayerDialog(parent, title="New Prayer Request", mustHaveSubject=True)
   if dialog.result:
      subject, prayer, author = dialog.result
      if len(author) == 0:
         author = "Anon"
      ok = prayPost("add", postData=(subject, prayer, author))
      if ok:
         messagebox.showinfo("Pray4Chichester", "Thank you for your prayer", parent=parent)
      else:
         messagebox.showerror("Pray4Chichester", "Oops!  Newtwork error, please try that again.", parent=parent)
   return

def getGeometry(widget):
   # get the current geometry of the widget as integer tuple
   geometry = widget.geometry()
   m = re.match("(\d+)x(\d+)\+*([-+]*\d+)\+*([-+]*\d+)", geometry)
   if not m:
      raise ValueError("failed to parse geometry string")
   (w, h, x, y) = map(int, m.groups())
   intW = int(w)
   intH = int(h)
   intX = int(x)
   intY = int(y)
   return (intX, intY, intW, intH)


class BlueButton(Button):
   # simplified button with blue background and white foreground

   # Initialisation code
   def __init__(self, parent, column, row, *argv, text=None, command=None, padx=5, pady=5, sticky=(E, W), **args):
      super().__init__(parent, *argv, text=text, bg=blue, fg='white', command=command, **args)
      self.grid(column=column, row=row, padx=padx, pady=pady, sticky=sticky)
      return

class Card(Toplevel):

   # Initialisation code
   def __init__(self, prayerwall, prayer=(0, "A Prayer", 0), x=0, y=0, wrap=3, offset=False):
      super().__init__(prayerwall)
      self.prayerwall = prayerwall
      # give each card a unique number
      global counter
      self.counter = counter
      counter += 1

      # use 1 icon for all cards
      global icon
      if not icon:
         # create the icon
         load = Image.open("hands.png")
         w, h = load.size # get actual size
         proportion = (w / h)
         h = int(HEIGHT / 20 ) # reduce height to 5%
         w = int((HEIGHT / 20 ) * proportion) # in proportion
         icon = load.resize((w, h))
      
      self.timestamp = 0
      self.prefix = "Prayer #"
      self.number = 0

      edge = 0
      self.width = WIDTH - 2 * edge 
      self.height = HEIGHT - 2 * edge
      self.x = edge
      self.y = edge

      self.normal = defaultFont.copy()
      self.italic = italicFont.copy()
      self.bold = boldFont.copy()

      # consistent background
      self.coloured = []
      self.coloured.append(self)

      # row 1 - basically a frame for everything else and make it stretchy
      frame = Frame(self, bg='pink')
      frame.grid(row=1, column=0, sticky=(E, W, N, S))
      self.grid_columnconfigure(0, weight=1)
      self.grid_rowconfigure(1, weight=1)
      # make middle column (1) and balanced rows (1 & 3) stretchy
      frame.grid_columnconfigure(1, weight=1)
      frame.grid_rowconfigure(1, weight=3)
      frame.grid_rowconfigure(3, weight=3)
      self.frame = frame # so we can modify it's stretchiness
      self.coloured.append(frame) # so we can modify bg ...

      # row 0 heading - fixed height ...
      self.hands = ImageTk.PhotoImage(icon)
      myIcon = Label(frame, image=self.hands)
      myIcon.grid(row=0, column=0, sticky=(E, W, N, S))
      self.coloured.append(myIcon) # so we can modify bg ...
      heading = Frame(frame)
      heading.grid(row=0, column=1, columnspan=2, sticky=(E, W))
      heading.grid_columnconfigure(1, weight=1)
      heading.grid_columnconfigure(2, weight=1)
      self.coloured.append(heading) # so we can modify bg ...
      self.subject = StringVar()
      self.subject.set("Subject")
      label = Label(heading, textvariable=self.subject, font=self.bold, wraplength=int(self.width/2))
      # label = Label(frame, textvariable=self.subject, font=self.bold)
      label.grid(row=0, column=1, sticky=(E, W)) # , columnspan=2)
      self.coloured.append(label) # so we can modify bg ...
      self.zoom = BlueButton(heading, text="Zoom out", command=self.doZoom, row=0, column=2)
      
      # row 1 prayer text
      self.prayer = ScrolledText(frame, font=self.normal, height=5, wrap=WORD)
      self.prayer.grid(row=1, column=0, columnspan=3, sticky=(E, W, N, S))
      self.setParas("A Prayer")
      self.author = StringVar()
      self.author.set("Anon")

      # row 2 count and author
      self.countFrame = LabelFrame(frame, text="Prayed 0 times", font=self.normal)
      self.countFrame.grid(row=2, column=0, columnspan=2, sticky=(E, W, N, S))
      self.coloured.append(self.countFrame) # so we can modify bg ...
      ### add prayed and response and maybe new request buttons
      button1 = BlueButton(self.countFrame, text="I've prayed", command=self.doPrayed, row=1, column=1)
      button2 = BlueButton(self.countFrame, text="I want to respond", command=self.newResponse, row=1, column=2)
      self.buttons = (button1, button2) # so they don't get recycled!

      ### add author
      byFrame = LabelFrame(frame, text="by", font=self.normal)
      byFrame.grid(row=2, column=2, sticky=(E, W, N, S))
      self.coloured.append(byFrame) # so we can modify bg ...
      label = Label(byFrame, textvariable=self.author, font=self.italic)
      label.grid(row=0, column=0, padx=5, pady=5, sticky=(E, W))

      # row 3 optional responces
      self.responsesFrame = LabelFrame(frame, text="Responses", font=self.normal)
      self.responsesFrame.grid(row=3, column=1, columnspan=3, sticky=(E, W, N, S))
      self.responsesFrame.grid_rowconfigure(0, weight=1)
      self.responsesFrame.grid_columnconfigure(0, weight=1)
      self.coloured.append(self.responsesFrame) # so we can modify bg ...
      self.responseItems = ScrolledText(self.responsesFrame, font=self.normal, height=5, wrap=WORD)
      self.responseItems.grid(row=0, column=0, sticky=(E, W, N, S))
      self.responsesFrame.grid_forget() # make disappear
      self.responses = []

      # finish off
      self.protocol("WM_DELETE_WINDOW", self.userClose)
      self.bind("<Configure>", self.aChange)

      # make minimal
      self.overrideredirect(1) # no decorations
      # Give the box a border we can see and react to being selected ...
      # Windows has "SystemHighlight" - for now use LightGreen
      # and "SystemActiveBorder" - and Green
      self.config(highlightthickness=2, \
                  highlightcolor="LightGreen", \
                  highlightbackground="Green")

      # put in the right place
      self.timestamp = 0
      self.update(prayer, x, y, wrap, offset) # process any set-up as an update
      return

   def update(self, prayer, x, y, wrap=3, offset=False):
      # print(f'update({prayer}, {x}, {y}, {wrap}, {offset})')
      self.setup(x, y, wrap, offset)
      if len(prayer) > 1:
         self.setPrayer(prayer)
      return

   def setPrayer(self, prayer):
      number, subject, paras, author, count, responses = prayer
      self.setNumber(number)
      self.setSubject(subject)
      self.setParas(paras)
      self.setAuthor(author)
      self.setCount(count)
      self.setResponses(responses)
      return

   def prayers(self):
      return self.prayerwall.prayers()

   def refresh(self):
      self.setPrayer(self.prayerwall.getPrayer(self.number))
      return

   def setup(self, x, y, wrap=3, offset=False):
      # (x, y) coords in panel (0 to wrap-1)
      # wrap is number of cards per row and rows per panel
      # offset is true if on sencond (right) screen
      self.restore = {'x': x, 'y': y, 'wrap': wrap, 'offset': offset}
      edge = 1
      w = (WIDTH // wrap)
      h = (HEIGHT // wrap)
      self.width = w - 2 * edge
      self.height = h - 2 * edge
      # print(f"[{self.counter}] Setup: width = {self.width}, height = {self.height}")
      self.x = w * x + edge
      if offset:
         self.x += WIDTH
      self.y = h * y + edge
      diff = time() - self.timestamp # time since last move - so we don't disturb a card being read
      # print("diff:", diff)
      if diff > 60 * 5: # five minutes
         # only change shape or move if been over 5 minutes
         self.zoom.config(text="Zoom in")
         # print("deiconfying from:", self.state())
         self.state('normal')
         geometry = f'{self.width}x{self.height}+{self.x}+{self.y}'
         # print(f"Setting g to: {(self.x, self.y, self.width, self.height)}")
         self.geometry(geometry)
         self.timestamp = time()
      return

   def aChange(self, event):
      # change made to the window - some one is looking!
      # not all changes are relevant, so restrict ...
      (intX, intY, intW, intH) = getGeometry(self) # our geometry
      if (event.width == intW) and (event.height == intH): # a size match - might not match position
         # if got bigger and not already reacted - zoom font
         if intW > (self.width * 2.5) and intH > (self.height * 2.5) and self.normal.cget("size") == fontSize:
            self.normal.config(size=fontSize*2)
            self.bold.config(size=fontSize*2)
            self.italic.config(size=fontSize*2)
         # if got smaller and not already reacted - normalise font
         if intW < (self.width * 1.5) and intH < (self.height * 1.5) and self.normal.cget("size") != fontSize:
            self.normal.config(size=fontSize)
            self.bold.config(size=fontSize)
            self.italic.config(size=fontSize)
      # remember when we changed so we do not update too quickly
      self.timestamp = time() 
      return

   def userClose(self): # we don't want to be closed!
      return # do nothing

   def newRequest(self):
      newRequest(self)
      return

   def newResponse(self):
      # open form for prayer response
      dialog = PrayerDialog(self, title="Your Response", mustHaveSubject=False)
      if dialog.result:
         subject, response, author = dialog.result
         ok = prayPost("add", number=self.number, postData=(subject, response, author))
         if ok:
            self.refresh()
            messagebox.showinfo("Pray4Chichester", "Thank you for responding", parent=self)
         else:
            messagebox.showerror("Pray4Chichester", "Oops!  Newtwork error, please try that again.", parent=self)
      return

   def doPrayed(self):
      # print("doPrayed()")
      ok, response =self.prayers().prayed(int(self.number))
      if ok:
         self.refresh()
         messagebox.showinfo("Pray4Chichester", "Thank you for praying", parent=self)
      else:
         print("doPrayed(): error:", response.read())
         messagebox.showerror("Pray4Chichester", "Oops!  Newtwork error, please try that again.", parent=self)
      return

   def doZoom(self):
      zoom = self.zoom.cget("text")
      # print("doZoom(), zoom =", zoom)
      zoomOut = "Zoom out"
      if zoom == zoomOut:
         self.timestamp = 0 # so we will zoom
         # print("Zooming out:", self.restore)
         self.setup(**self.restore)
      else:
         self.zoom.config(text=zoomOut)
         # fill screen with prayer
         # print("Zooming in: offset =", self.restore["offset"])
         edge = 1
         self.width = WIDTH - 2 * edge
         self.height = HEIGHT - 2 * edge
         self.x = edge
         if self.restore["offset"]:
            self.x += WIDTH
         self.y = edge
         self.state('normal')
         geometry = f'{self.width}x{self.height}+{self.x}+{self.y}'
         # print(f"Setting g to: {(self.x, self.y, self.width, self.height)}")
         self.geometry(geometry)
         self.timestamp = time()
      return
      
   def setNumber(self, number):
      #old = self.title.get()[-1]
      #old = self.title()[-1]
      # print(f"setNumber[{self.counter}]({number}) from {old}")
      #self.title.set(self.prefix + str(number))
      self.number = number
      self.title(self.prefix + str(number))
      return

   def setSubject(self, subject):
      self.subject.set(subject)
      return

   def setCount(self, count):
      if count == 0:
         self.countFrame.config(text="Has never been prayed for")
      elif count == 1:
         self.countFrame.config(text="Has been prayed for once")
      else:
         self.countFrame.config(text="Has been prayed for " + str(count) + " times")
      # print(f"Count = '{count}', {int(count)}")
      count = int(count)
      if count >= len(heatColour):
         count = len(heatColour) - 1 # max out at red!
      # print(f"Count used = '{count}', compared to {len(heatColour)}")
      bg = heatColour[count]
      for widget in self.coloured:
         widget.config(bg=bg)
      return

   def setParas(self, paras):
      # just replace the text
      #self.prayer.config(state=NORMAL)
      self.prayer.delete(1.0, END)
      self.prayer.insert(END, paras)
      #self.prayer.config(state=DISABLED)
      return

   def setAuthor(self, author):
      self.author.set(author)
      return

   def setResponses(self, responses):
      # print(f"setResponses({len(responses)})")
      self.responseItems.config(state=NORMAL)
      self.responseItems.tag_config("separator", background="pink", foreground="pink")
      self.responseItems.delete(1.0, END)
      for i in range(len(responses)):
         # print(f"i: {i}, of {len(responses)}: {responses[i]}")
         if i > 0: # not first sesponse, so add separator
            self.responseItems.insert(END, "\n")
            self.responseItems.insert(END, "\n", "separator")
         response = responses[i] # just extract paras
         # print(f"i: {response}, of {len(self.responses)}")
         self.responseItems.insert(END, response)
      if len(responses) > 0:
         # self.responsesFrame.grid() # make appear
         self.responsesFrame.grid(row=3, column=1, columnspan=3, sticky=(E, W, N, S))
         #self.frame.grid_rowconfigure(3, weight=1) #len(self.responses))
      else:
         self.responsesFrame.grid_forget() # make disappear
      self.responseItems.config(state=DISABLED)
      return


class PrayerWall(Tk):

   # Initialisation code
   def __init__(self, name, col=0, row=0, **args):
      # print(f"PrayerWall({name}, {col}, {row}, {args})")
      super().__init__(**args)

      # set up globals
      global defaultFont
      global italicFont
      global boldFont
      global fontSize
      if not defaultFont:
         defaultFont = nametofont('TkDefaultFont')
         italicFont = defaultFont.copy()
         italicFont.config(slant=ITALIC)
         boldFont = defaultFont.copy()
         boldFont.config(weight=BOLD)
         fontSize = defaultFont.cget('size')

      self.Hostname = socket.gethostname()

      # set up window and make stretchy
      self.grid_columnconfigure(0, weight=1)
      self.grid_rowconfigure(0, weight=1)
      self.frame = Frame(self)
      self.frame.grid(row=0, column=0, sticky=(E, W, N, S))
      # add button
      self.frame.grid_columnconfigure(0, weight=1)
      self.frame.grid_rowconfigure(0, weight=1)
      button = Button(self.frame, text="New Prayer Request", bg=blue, command=self.newRequest)
      button.grid(row=0, column=0, padx=5, pady=5, sticky=(E, W, N, S))

      # get init data from PrayerWall database
      self.name = name
      self._prayers = None
      emptyRow = (None, None, None)
      empty = (emptyRow, emptyRow, emptyRow)
      self.left = []
      self.leftPanel = (col * 2, row)
      self.right = []
      self.rightPanel = (col * 2 + 1, row)
      

      # center the button
      self.update_idletasks()
      (intX, intY, intW, intH) = getGeometry(self)
      geometry = f'{intW}x{intH}+{intX}+{intY}'
      x = (WIDTH - intW) // 2
      y = (HEIGHT - intH) // 2
      geometry = f'{intW}x{intH}+{x}+{y}'
      self.geometry(geometry)

      # start the auto update
      self.tick()
      return

   def tick(self):
      # update panels every half minute
      self.refresh()
      self.after(30000, self.tick) # do it again after 30,000 ms (30 sec)
      return

   def prayers(self):
      if not self._prayers:
         self._prayers = Prayers()
      return self._prayers

   def refresh(self, force=False):
      if force:
         self._prayers = Prayers()
      self.left = self.buildPanel(self.leftPanel, self.left)
      self.right = self.buildPanel(self.rightPanel, self.right)
      return

   def getPrayer(self, number):
      return self.prayers().prayer(number, force=True)

   def buildPanel(self, coords, oldList):
      # print(f"buildPanel({coords}, {oldList})")
      offset = (coords[0] % 2) == 1
      panel = None
      wrap = 3
      try:
         basicPanel = self.prayers().panel(*coords)
         # print(f"basicPanel: {basicPanel}")
         wrap = self.prayers().wrap
         panel = []
         for row in basicPanel:
            # print(f"row: {row}")
            newRow = []
            for item in row:
               # print(f"item: {item}")
               number = int(item[0])
               newItem = [number]
               # print(f"newItem: {newItem}, number: {number}")
               if number > 0:
                  # number, subject, paras, author, count, responses
                  newItem = self.prayers().prayer(number)
               # print(f"newItem: {newItem}")
               newRow.append(newItem)
            panel.append(newRow)
      except Exception as e:
         # print("buildPanel(): exception:", e)
         self._prayers = None
         panel = None
      if panel:
         oldList = self.showPanel(panel, wrap, oldList, offset)
      return oldList

   def showPanel(self, panel, wrap, oldList, offset=True):
      # print(f"showPanel({panel}, {wrap}, {oldList}, {offset})")
      newList = []
      count = 0
      for y in range(wrap):
         row = None
         if y < len(panel):
            row = panel[y]
            for x in range(wrap):
               prayer = None
               old = None
               if x < len(row):
                  prayer = row[x]
                  if len(prayer) > 1:
                     if count < len(oldList):
                        old = oldList[count]
                        count += 1
                     if not old:
                        old = Card(self, prayer, x, y, wrap, offset)
                     else:
                        old.update(prayer, x, y, wrap, offset)
               if old:
                  newList.append(old)
      return newList

   def newRequest(self):
      newRequest(self)
      self.refresh(force=True)
      return


if __name__ == '__main__':
   pwname = "PrayerWall"
   name = socket.gethostname()
   col = 0
   row = 0
   if name.startswith(pwname):
      print("Real start up - PrayerWallCR -", name)
      col = int(name[len(pwname)])
      row = int(name[len(pwname)+1])
   else:
      print("Windows Testing")
      name = pwname + "00" # for testing
      # for testing on window laptop change the screen size
      WIDTH = 1366 // 2
      HEIGHT = 768
   print("Starting:", name)
   pw = PrayerWall(name, col, row)
   pw.mainloop()
