from tkinter import *
from PIL import Image, ImageTk
import os, json
from tkinter import filedialog

import sys


WIDTH = 1920
HEIGHT = 1080

tilesFolder = "./data/tiles/"
mapFolder = "./data/maps/"
saveFolder = "./data/saves/"
decorFolder = "./data/decorations/"

window = Tk()
window.configure(height=HEIGHT, width=WIDTH)
window.attributes('-fullscreen', True)
window.geometry(WIDTH.__str__()+"x"+HEIGHT.__str__()+"+"+"300+300")
canvas = Canvas(window)
canvas.pack(fill=BOTH, expand=1)

resTiles = []
resDecors = []
resMaps = []

caseX = 15
caseY = 10
size = int(1080 / caseY)
margin = WIDTH - caseX*size

switch = False

class Res_Tile:
    #Classe regroupe les propriétés d'une tile
    def __init__(self, config: dict):
        self.id = config['tileID']
        self.name = config['tileName']
        self.isWall = config['isWall']
        #self.canTP = config['canTeleport']
        self.texture = Image.open(tilesFolder + self.name + ".png").resize((size,size), Image.BOX)
    
    def getTexture(self, rotation: int = 0):
        return ImageTk.PhotoImage(self.texture.rotate(rotation))

class Res_Decor:
    def __init__(self, config: dict):
        self.id = config['decorID']
        self.name = config['decorName']
        self.usable = config['usable']
        self.canTp = config['canTp']
        self.collision = config['hasCollisions']
        self.images = config['images']
        self.animTime = config['animationTime']
        self.texture = []

        #if self.images > 1:
        #    for i in range (self.images):
        #        self.texture.append(Image.open(decorFolder + self.name + "-" + i.__str__() + ".png").resize((size,size), Image.BOX))
        #        #ajoute les images ayant le format nom-numero.png
        #elif self.images == 1:
        #    self.texture.append(Image.open(decorFolder + self.name + ".png").resize((size,size), Image.BOX))

        if self.images > 1:
            for i in range (self.images):
                img = Image.open(decorFolder + self.name + "-" + i.__str__() + ".png")
                width, height = img.size
                img = img.resize((int(width * size/32), int(height * size/32)), Image.BOX)
                self.texture.append(img)

        elif self.images == 1:
            img = Image.open(decorFolder + self.name + ".png")
            width, height = img.size
            img = img.resize((int(width * size/32), int(height * size/32)), Image.BOX)
            self.texture.append(img)

class Res_Map:
    def __init__(self, directory: str ,config: dict):
        self.id = config['mapID']
        self.name = config['mapName']
        self.size = config['size'].lower()
        self.directory = directory

class Tile:
    def __init__(self, id, x: int, y: int, rotation: int = 0):
        if type(id) is int:
            self.restile = resTiles[id]
        elif type(id) is str:
            for tile in resTiles:
                if tile.name == id:
                    self.restile = tile
                    break        
        self.rotation = rotation
        self.image = self.restile.getTexture(rotation)
        self.x = x
        self.y = y
        self.obj = canvas.create_image(margin + size*(x + 0.5), size*(y + 0.5), tags="tile", image=self.image)
    
    def rotate(self, rotation: int, fixed: bool = False):
        if fixed:
            self.rotation = rotation 
        else:
            self.rotation += rotation 

        self.rotation = self.rotation - 360 * (self.rotation // 360)
        print(360 * (self.rotation // 360))

        self.image = self.restile.getTexture(self.rotation)
        canvas.itemconfig(self.obj, image=self.image)

    def changeTile(self, id):
        if type(id) is int:
            self.restile = resTiles[id]
        elif type(id) is str:
            for tile in resTiles:
                if tile.name == id:
                    self.restile = tile
                    break 
        self.image = self.restile.getTexture(self.rotation)
        canvas.itemconfig(self.obj, image=self.image)

class Decor:
    def __init__(self, id, x: float, y: float, rotation: int = 0):
        if type(id) is int:
            self.resDecor = resDecors[id]
        elif type(id) is str:
            for decor in resDecors:
                if decor.name == id:
                    self.resDecor = decor
                    break 

        self.x = x
        self.y = y
        self.rotation = rotation

        self.image = ImageTk.PhotoImage(self.resDecor.texture[0])
        self.obj = canvas.create_image(x, y, tags="decor", image=self.image)

        self.animCounter = -1
        self._pendingAnimation = False

        if self.resDecor.images > 1 and self.resDecor.animTime != 0:
            self._pendingAnimation = window.after(self.resDecor.animTime * 1000, self.animate)

    def cleanUp(self):
        #Fonction à utiliser avant de supprimer cet objet
        #Ne pas définir la fonction intégrée __del__(self) car elle pose problème 
        if self._pendingAnimation != False:
            window.after_cancel(self._pendingAnimation)

        canvas.delete(self.obj)

    def animate(self):
        self._pendingAnimation = window.after(self.resDecor.animTime * 1000, self.animate)
        self.nextSprite()

    def nextSprite(self):
        self.animCounter += 1
        if self.animCounter == self.resDecor.images:
            self.animCounter = 0

        self.image = ImageTk.PhotoImage(self.resDecor.texture[self.animCounter])
        canvas.itemconfig(self.obj, image=self.image)


    def changeDecor(self, id):
        if self._pendingAnimation != False:
            window.after_cancel(self._pendingAnimation)
            self._pendingAnimation = False

        if type(id) is int:
            self.resDecor = resDecors[id]
        elif type(id) is str:
            for decor in resDecors:
                if decor.name == id:
                    self.resDecor = decor
                    break

        self.image = ImageTk.PhotoImage(self.resDecor.images[0])
        canvas.itemconfig(self.obj, image=self.image)
                     
class Region:
    def __init__(self):
        self.tiles = [[0 for i in range(caseX)]for i in range(caseY)]
        for y in range(caseY):
            for x in range(caseX):
                self.tiles[y][x] = Tile(0,x,y)
        self.entities = []
        self.decor = []
        

    def load(self, path: str):
        with open(path) as file:
            data = json.load(file)
            tiles = data['tiles']
            for y in range(caseY):
                for x in range(caseX):
                    filetile = tiles[y][x]
                    self.tiles[y][x].changeTile(filetile[0])
                    self.tiles[y][x].rotate(filetile[1], True)
            for decor in self.decor:
                canvas.delete(decor.obj)
            self.decor = []
            for decor in data['decor']:
                self.decor.append(Decor(decor[0],decor[1][0],decor[1][1]))

    def save(self, path: str):
        data = [[0 for i in range(caseX)]for i in range(caseY)]
        for y in range(caseY):
            for x in range(caseX):
                tile: Tile = self.tiles[y][x]
                data[y][x] = [tile.restile.id, tile.rotation]

        decorPos = []
        for decor in self.decor:
            decorPos.append([decor.resDecor.id, (decor.x, decor.y)])
        
        with open(saveFolder + path + ".data", "x") as file:
            dic = {'tiles': data, 'decor': decorPos }
            json.dump(dic, file)
    

def initRessources():
    tile_configs = []
    decor_configs = []

    for (dirpath, dirnames, filenames) in os.walk(tilesFolder):
        for file in filenames:
            if ".json" in file:
                tile_configs.append(file)
        break

    for (dirpath, dirnames, filenames) in os.walk(decorFolder):
        for file in filenames:
            if ".json" in file:
                decor_configs.append(file)
        break

    for id in range(len(tile_configs)):
        for config in tile_configs:
            with open(tilesFolder + config) as file:
                js = json.load(file)
                if js['tileID'] == id:
                    resTiles.append(Res_Tile(js))
                    break
    
    for id in range(len(decor_configs)):
        for config in decor_configs:
            with open(decorFolder + config) as file:
                js = json.load(file)
                if js['decorID'] == id:
                    resDecors.append(Res_Decor(js))
                    break
        
def initMap():
    #wip
    folders = []
    for (dirpath, dirnames, filenames) in os.walk(mapFolder):
        for id in range(len(dirnames)):
            for folder in dirnames:
                with open(mapFolder + folder + "/config.json") as file:
                    js = json.load(file)
                    if js['mapID'] == id:
                        resMaps.append(Res_Map(folder,js))
        break

def importFile():
    path = filedialog.askopenfilename(initialdir = saveFolder ,title = "Select Region Map ",filetypes = (("data files","*.data"),("all files","*.*")))
    if path != "":
        currRegion.load(path)

def save():
    fileName = save_input.get()
    currRegion.save(fileName)

def switch_selector():
    global switch
    if switch:
        selector.delete(0,len(resDecors))
        for i in range(len(resTiles)):
            for tile in reversed(resTiles):
                selector.insert(i, tile.name)
            break
        selector.select_set(0)
        switch = False
    else:
        selector.delete(0,len(resTiles))
        for i in range(len(resDecors)):
            for decor in reversed(resDecors):
                selector.insert(i, decor.name)
            break
        selector.select_set(0)
        switch = True

initRessources()

currRegion = Region()

selector = Listbox(window)
for i in range(len(resTiles)):
    for tile in reversed(resTiles):
        selector.insert(i, tile.name)
    break

selector.select_set(0)
selector.place(x=50,y=100)

switch_button = Button(window, text="Changer tiles/decor", command=switch_selector)
switch_button.place(x=50,y=75)

save_input = Entry(window)
save_input.place(x=50, y=HEIGHT-100)

save_button = Button(window, text="Save", command=save)
save_button.place(x=150, y=HEIGHT-100)

import_button = Button(window, text="Import", command=importFile)
import_button.place(x=150, y=HEIGHT-50)


def OnTileClick(event):
    index = selector.curselection()
    name = selector.get(index)

    print("clicked")
    print(event.y//(size) , ";" , (event.x-margin)//size )

    y = event.y//size
    x = (event.x-margin)//size
    
    if y < 0 or y > caseY or x < 0 or x > caseX:
        return False

    print(event.num)

    if not switch:
        if event.num == 1:
            currRegion.tiles[y][x].changeTile(name)
        elif event.num == 3:
            currRegion.tiles[y][x].rotate(90)

def OnNothingClick(event):
    y = event.y//size
    x = (event.x-margin)//size

    if y < 0 or y > caseY or x < 0 or x > caseX:
        return False
        
    if switch:
        index = selector.curselection()
        name = selector.get(index)
        currRegion.decor.append(Decor(name,event.x,event.y))

def OnDecorClick(event):

    y = event.y//size
    x = (event.x-margin)//size

    if y < 0 or y > caseY or x < 0 or x > caseX:
        return False

    found = False
    if switch:
        items = canvas.find_overlapping(event.x, event.y, event.x + 1, event.y + 1)
        for item in items:
            if found:
                break
            for tag in canvas.gettags(item):
                if tag == "decor":
                    found = True
                    for i in range(len(currRegion.decor)):
                        if currRegion.decor[i].obj == item:
                            currRegion.decor[i].cleanUp()
                            currRegion.decor.pop(i) 
                            break
                    break

def Debug(event):
    breakpoint()
    
canvas.tag_bind("tile", '<Button-1>', OnTileClick)
canvas.tag_bind("tile", '<Button-3>', OnTileClick)
canvas.tag_bind("decor", '<Button-3>', OnDecorClick)
canvas.bind('<Button-1>', OnNothingClick)
window.bind('<Escape>', Debug)
window.mainloop()