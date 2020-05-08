from tkinter import *
from PIL import Image, ImageTk
import os, json
from tkinter import filedialog

WIDTH = 1920
HEIGHT = 1080

tilesFolder = "./data/tiles/"
mapFolder = "./data/maps/"
saveFolder = "./data/saves/"

window = Tk()
window.configure(height=HEIGHT, width=WIDTH)
window.attributes('-fullscreen', True)
window.geometry(WIDTH.__str__()+"x"+HEIGHT.__str__()+"+"+"300+300")
canvas = Canvas(window)
canvas.pack(fill=BOTH, expand=1)

resTiles = []
resMaps = []
currentRegion = []

caseX = 15
caseY = 10
size = int(1080 / caseY)
margin = WIDTH - caseX*size

grid = [[0 for i in range(caseX)]for i in range(caseY)]
decoration = []

class Res_Tile:
    #Classe regroupe les propriétés d'une tile
    def __init__(self, config: dict):
        self.id = config['tileID']
        self.name = config['tileName']
        self.isWall = config['isWall']
        #self.canTP = config['canTeleport']
        self.texture = Image.open(tilesFolder + config['tileName'] + ".png").resize((size,size))
    
    def getTexture(self, rotation: int = 0):
        return ImageTk.PhotoImage(self.texture.rotate(rotation))

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
        self.obj = canvas.create_image(margin + size*(x + 0.5), size*(y + 0.5), tags="clickable", image=self.image)
        

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
        #canvas.itemconfig(self.obj, image=self.image)

def initTiles():
    global resTiles
    f_configs = []

    for (dirpath, dirnames, filenames) in os.walk(tilesFolder):
        for file in filenames:
            if ".json" in file:
                f_configs.append(file)
        break

    for id in range(len(f_configs)):
        for config in f_configs:
            with open(tilesFolder + config) as file:
                js = json.load(file)
                if js['tileID'] == id:
                    resTiles.append(Res_Tile(js))
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

def save():
    fileName = save_input.get()
    data = [[0 for i in range(caseX)]for i in range(caseY)]
    for y in range(caseY):
        for x in range(caseX):
            tile: Tile = grid[y][x]
            data[y][x] = [tile.restile.id, tile.rotation]
            
    with open(saveFolder + fileName + ".data", "x") as file:
        json.dump(data, file)

def importFile():
    filename = filedialog.askopenfilename(initialdir = saveFolder ,title = "Select Region Map ",filetypes = (("data files","*.data"),("all files","*.*")))
    if filename != "":
        with open(filename, "r") as file:
            data = json.load(file)
            for y in range(caseY):
                for x in range(caseX):
                    filetile = data[y][x]
                    grid[y][x].changeTile(filetile[0])
                    grid[y][x].rotate(filetile[1], True)
        
#========================================================================================================================================================

initTiles()

for y in range(caseY):
    for x in range(caseX):
        grid[y][x] = Tile(0,x,y)


selector = Listbox(window)
for i in range(len(resTiles)):
    for tile in reversed(resTiles):
        selector.insert(i, tile.name)
    break

selector.select_set(0)
selector.place(x=50,y=100)

save_input = Entry(window)
save_input.place(x=50, y=HEIGHT-100)

save_button = Button(window, text="Save", command=save)
save_button.place(x=150, y=HEIGHT-100)

import_button = Button(window, text="Import", command=importFile)
import_button.place(x=150, y=HEIGHT-50)


def OnClick(event):
    index = selector.curselection()
    name = selector.get(index)

    print("clicked")
    print(event.y//(size) , ";" , (event.x-margin)//size )

    y = event.y//size
    x = (event.x-margin)//size
    
    if y < 0 or y > caseY or x < 0 or x > caseX:
        return False

    print(event.num)

    if event.num == 1:
        grid[y][x].changeTile(name)
    elif event.num == 3:
        grid[y][x].rotate(90)
    
    
canvas.tag_bind("clickable", '<Button-1>', OnClick)
canvas.tag_bind("clickable", '<Button-3>', OnClick)
window.mainloop()