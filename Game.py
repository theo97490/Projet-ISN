import GameCore
from GameConstants import *
from tkinter import *
from PIL import Image, ImageTk
import os, json
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
from tkinter.font import Font

import traceback
import random

from math import * 
import fractions

import sys

import cProfile 


window = Tk()
window.configure(height=HEIGHT, width=WIDTH)
window.attributes('-fullscreen', True)
window.geometry(WIDTH.__str__()+"x"+HEIGHT.__str__()+"+"+"300+300")
canvas = Canvas(window)
canvas.pack(fill=BOTH, expand=1)

GameCore.initialize(window, canvas)

world = GameCore.World("stfu")
player = GameCore.Player(size, size)
gui = GameCore.GUI()

window.mainloop()