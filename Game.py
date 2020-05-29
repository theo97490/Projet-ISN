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


window = canvas = None
window, canvas = GameCore.initialize()

world = GameCore.World("stfu")
player = GameCore.Player(size, size)
gui = GameCore.GUI()

window.mainloop()