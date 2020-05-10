from tkinter import *
from PIL import Image, ImageTk
import os, json
from tkinter import filedialog
from tkinter import messagebox

from math import * 
import sys

import cProfile


WIDTH = 1920
HEIGHT = 1080

tick = 15

window = Tk()
window.configure(height=HEIGHT, width=WIDTH)
window.attributes('-fullscreen', True)
window.geometry(WIDTH.__str__()+"x"+HEIGHT.__str__()+"+"+"300+300")
canvas = Canvas(window)
canvas.pack(fill=BOTH, expand=1)


img = Image.open("./data/entities/arrow/arrow_anim.png")
img = img.rotate(-90, expand=True)
width, height = img.size
width = int(width * 100/32)
height = int(height* 100/32)
img = img.resize((width, height), Image.BOX)
img = ImageTk.PhotoImage(img)
obj = canvas.create_image(100, 100, image=img)

fixer = canvas.create_rectangle(100 - width/2 - 50, 100 - height/2 - 50, 100 + width/2 + 50, 100 + height/2 + 50)

def move():
    window.after(tick, move)
    canvas.move(obj, 15, 0)
    #canvas.move(fixer, 15, 0)

canvas.after(tick, move)

window.mainloop()