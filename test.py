from tkinter import *
from PIL import Image, ImageTk
import os, json
from tkinter import filedialog
from tkinter import messagebox

from math import * 
import sys

import cProfile
from weakref 


WIDTH = 1920
HEIGHT = 1080

tick = 15

window = Tk()
window.configure(height=HEIGHT, width=WIDTH)
window.attributes('-fullscreen', True)
window.geometry(WIDTH.__str__()+"x"+HEIGHT.__str__()+"+"+"300+300")
canvas = Canvas(window)
canvas.pack(fill=BOTH, expand=1)




window.mainloop()