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
window, canvas = GameCore.initialize(True)

world = None
currentMode = TILE

def save():
    fileName = save_input.get()
    world.saveRegion(fileName)

loaded = False
def askWorldFolder():
    global world
    global loaded

    path = filedialog.askdirectory(initialdir = mapsFolder ,title = "Select Map Directory") + "/"
    if path != "/":
        try:
            with open(path + "config.json", "r") as file:
                js = json.load(file)
                if type(world) is GameCore.World:
                    world.currRegion.unload()
                world = GameCore.World(edit=(path, js))
                if not loaded:
                    loaded = True
                    window.quit()
        except:
            traceback.print_exc()
            result = messagebox.askyesno("Python",'There is no config.json in "' + path +'", \nWould you like to create one ?')
            if result:
                with open(path + "config.json", "w") as file:
                    file.write(
                            ('{\n'
                            '   "name" : "Name",\n'
                            '   "worldCoords" : [5,5],\n'
                            '   "size": [5,5],\n'
                            '   "startPos": [0,0]\n'
                            '}'))
                    
                    os.startfile(path + "config.json")

def ButtonWorldLoad(direction):
    x = 0
    y = 0
    if direction == LEFT:
        x -= 1
    elif direction == RIGHT:
        x += 1
    elif direction == TOP:
        y += 1
    elif direction == BOTTOM:
        y -= 1

    if not world.loadRegion(x,y):
        coordx, coordy = world.regionCoords
        save_input.delete(0,len(save_input.get()) + 1)
        save_input.insert(0,"Region "+ coordx.__str__() + " " + coordy.__str__())
            
    textCoord.delete("1.0",END)
    textCoord.insert("1.0", world.regionCoords.__str__())

def OnClick(event):

    if event.y < 0 or event.y > size*caseY or event.x < GameCore.margin or event.x > size*caseX + GameCore.margin:
        return False
        
    index = selector.curselection()
    name = selector.get(index)
    currRegion = world.currRegion

    if currentMode == TILE:
        y = event.y//size
        x = (event.x-GameCore.margin)//size
    
        if event.num == 1:
            currRegion.tiles[y][x].changeTile(name)
        elif event.num == 3:
            currRegion.tiles[y][x].rotate(90)

    elif currentMode == DECOR:
        if event.num == 1:
            res = GameCore.getRes(DECOR, name)
            try:
                tempClass = getattr(sys.modules[GameCore], res.className)
            except:
                tempClass = GameCore.Decor
            if hasattr(tempClass, "parameters"):
                kw = {}
                parameters = tempClass.parameters
                for key in parameters:
                    val = 0
                    if parameters[key] == "Int":
                        val = simpledialog.askinteger("Tkinter", "Ce décor a des paramètres supplémentaires à saisir \n Entrez " + key + " de type Integer" )
                    elif parameters[key] == "String":
                        val = simpledialog.askstring("Tkinter", "Ce décor a des paramètres supplémentaires à saisir \n Entrez " + key + " de type String" )
                    kw[key] = val

                decor = tempClass(name, event.x - GameCore.margin, event.y, **kw)
            else:
                decor = tempClass(name, event.x - GameCore.margin, event.y)
            

        elif event.num == 3:
            items = canvas.find_overlapping(event.x, event.y, event.x, event.y)
            decor = GameCore.findObjectByTag(DECOR, items, "decor", first=True)
            if decor != None:
                decor.cleanUp()
                


    elif currentMode == ENTITY:
        if event.num == 1:
            res = GameCore.getRes(ENTITY, name)
            try:
                tempClass = getattr(sys.modules[GameCore], res.className)
            except:
                tempClass = GameCore.Entity

            if res.name == "player":
                entity = tempClass(event.x - GameCore.margin, event.y)
            else:
                entity = tempClass(res.name, event.x - GameCore.margin, event.y)

        elif event.num == 3:
            found = False
            items = canvas.find_overlapping(event.x, event.y, event.x, event.y)
            entity = GameCore.findObjectByTag(ENTITY, items, "entity", first=True)
            if entity != None:
                entity.cleanUp()
                
def switchMode(mode: str):
    global currentMode

    res = None
    selector.delete(0,END)

    if mode == TILE:
        res = GameCore.resTiles

    elif mode == DECOR:
        res = GameCore.resDecors 
        
    elif mode == ENTITY:
        res = GameCore.resEntities

    else: 
        raise Exception("Bad switch mode")
        breakpoint()

    currentMode = mode

    for thing in res:
        selector.insert(END, thing.name)

    selector.select_set(0)

world_button = Button(window, text="Select world folder", command=askWorldFolder)
world_button.place(relx=0.5, rely=0.5, anchor=CENTER)
world_button.config(font=("TkDefaultFont", 30))
window.mainloop()

world_button.place(relx=0 ,x=50, rely=0, y=40, anchor=NW)
world_button.config(font=("TkDefaultFont", 10))

textCoord   = Text(window, width=8, height=2)
textCoord.insert("1.0", world.regionCoords.__str__())
world_up    = Button(window, text="Up", command=lambda: ButtonWorldLoad(TOP))
world_down  = Button(window, text="Down", command=lambda: ButtonWorldLoad(BOTTOM))
world_left  = Button(window, text="Left", command=lambda: ButtonWorldLoad(LEFT))
world_right = Button(window, text="Right", command=lambda: ButtonWorldLoad(RIGHT))

create = Button(window,text="Create", command=lambda: world.currRegion.new("grass3"))
create.place(x=50, y=350)

textCoord.place(x=145, y=550)
world_up.place(x=150, y=500)
world_down.place(x=150, y=600)
world_right.place(x=200, y=550)
world_left.place(x=100, y=550)

selector = Listbox(window)
for i in range(len(GameCore.resTiles)):
    for tile in reversed(GameCore.resTiles):
        selector.insert(i, tile.name)
    break 

selector.select_set(0)
selector.place(x=50,y=100)

tile_button     = Button(window, text="Tile", command=lambda: switchMode(TILE))
decor_button    = Button(window, text="Decor", command=lambda: switchMode(DECOR))
entity_button   = Button(window, text="Entity", command=lambda: switchMode(ENTITY))

tile_button.place(x=50, y=75)
window.update()
decor_button.place(x=50+tile_button.winfo_width(), y=75)
window.update()
entity_button.place(x=decor_button.winfo_x() + decor_button.winfo_width() ,y=75)

save_input = Entry(window)
save_input.place(x=50, y=HEIGHT-100)

save_button = Button(window, text="Save", command=save)
save_button.place(x=150, y=HEIGHT-100)

canvas.bind('<Button>', OnClick)

#Tests
Test = True
window.mainloop()


