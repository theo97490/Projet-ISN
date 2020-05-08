from tkinter import *
from PIL import Image, ImageTk
import os, json
from tkinter import filedialog
from tkinter import messagebox

import sys

#Constantes
WIDTH = 1920
HEIGHT = 1080
tick = int(1/60 * 1000) 
TILE = "TILE"
DECOR = "DECOR"
ENTITY = "ENTITY"
UP = "Up"
DOWN = "Down"
LEFT = "Left"
RIGHT = "Right"

#Chemins de dossier
tilesFolder = "./data/tiles/"
mapsFolder = "./data/maps/"
saveFolder = "./data/saves/"
decorsFolder = "./data/decorations/"
entitiesFolder = "./data/entities/"

currWorld = None
resTiles = []
resDecors = []
resMaps = []
resEntities = []
worlds = []

#Grille
caseX = 15
caseY = 10
size = int(1080 / caseY)
margin = WIDTH - caseX*size

currentMode = TILE

#Configuration de la fenêtre
window = Tk()
window.configure(height=HEIGHT, width=WIDTH)
window.attributes('-fullscreen', True)
window.geometry(WIDTH.__str__()+"x"+HEIGHT.__str__()+"+"+"300+300")
canvas = Canvas(window)
canvas.pack(fill=BOTH, expand=1)

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

        if self.images > 1:
            for i in range (self.images):
                img = Image.open(decorsFolder + self.name + "-" + i.__str__() + ".png")
                width, height = img.size
                img = img.resize((int(width * size/32), int(height * size/32)), Image.BOX)
                self.texture.append(img)

        elif self.images == 1:
            img = Image.open(decorsFolder + self.name + ".png")
            width, height = img.size
            img = img.resize((int(width * size/32), int(height * size/32)), Image.BOX)
            self.texture.append(img)

    def getTexture(self, index, rotation: int = 0):
        return ImageTk.PhotoImage(self.texture[index].rotate(rotation))

class Res_Map:
    def __init__(self, directory: str ,config: dict):
        self.id = config['mapID']
        self.name = config['mapName']
        self.size = config['size'].lower()
        self.directory = directory

class Res_Entity:
    def __init__(self, directory: str, config: dict):
        self.id = config['entityID']
        self.name = config['name']
        self.type = config['type']
        self.speed = config['speed']
        self.size = config['size']
        self.animations = {}
        
        self.animConfig = animConfig = config['Animations']

        for key in animConfig:
            texture = []
            spritesNumber = animConfig[key]
            if spritesNumber > 1:
                for i in range(spritesNumber):
                    img = Image.open(entitiesFolder + directory + key + self.name + "_" + i.__str__() + ".png")
                    width, height = img.size
                    img = img.resize((int(width * size/32), int(height * size/32)), Image.BOX)
                    texture.append(img)

            elif spritesNumber == 1:
                img = Image.open(entitiesFolder + directory + self.name + "_" + key + ".png")
                width, height = img.size
                img = img.resize((int(width * size/32), int(height * size/32)), Image.BOX)
                texture.append(img)

            self.animations[key] = texture
    
    def getTexture(self, key: str, index: int):
        return ImageTk.PhotoImage(self.animations[key][index])
  
class Entity:
    def __init__(self, id, x: float, y: float):
        if x < 0 or x > caseX * size or y < 0 or y > caseY * size:
            raise Exception(x + " " + y + " Isn't a valid position for an Entity")
            breakpoint()

        self.res = getRes(ENTITY, id)
        self.x = x
        self.y = y
        self.speed = self.res.speed
        self.currAnim = None
        self.lastAnim = None
        self.animCounter = -1
        self._pendingAnimation = None
        self._pendingLoop = None

        self.image = self.res.getTexture("Idle", 0)
        self.obj = canvas.create_image(x + margin, y, tags="entity", image=self.image)

        self._pendingLoop = window.after(tick, self.loop)

    def cleanUp(self):
        if self._pendingAnimation != None:
           window.after_cancel(self._pendingAnimation)
           self._pendingAnimation = None

        if self._pendingLoop != None:
            window.after_cancel(self._pendingLoop)
            self._pendingLoop = None

        canvas.delete(self.obj)

    def move(self, dirx, diry):
        #dirx et diry sont des directions égales à 1 ou -1
        if dirx == 1:
            self.currAnim = RIGHT
        elif dirx == -1:
            self.currAnim = LEFT
        elif diry == 1:
            self.currAnim = UP
        elif diry == -1:
            self.currAnim = DOWN
        else:
            self.currAnim = "Idle"
        dx =  dirx * self.speed
        dy = -diry * self.speed

        self.x = dx
        self.y = dy

        canvas.move(self.obj, dx ,dy)
    
    def animate(self):
        if self.currAnim != self.lastAnim:
            self.lastAnim = self.currAnim
            self.animCounter = -1

        self.animCounter += 1
        if self.animCounter == self.res.animConfig[self.currAnim]:
            self.animCounter = 0

        self.image = self.res.getTexture(self.currAnim, self.animCounter)
        canvas.itemconfig(self.obj, image=self.image)

    def loop(self):
        pass

    def __eq__(self, other):
        if self.obj == other:
            return True
        else:
            return False
       
class Player(Entity):
    #Classe singleton
    def __init__(self, x: float, y: float):
        super().__init__("player", x, y)

    def loop(self):
        self._pendingLoop = window.after(tick, self.loop)
        dirx = diry = 0
        if arrowsStatus[UP]: diry += 1
        if arrowsStatus[DOWN]: diry -= 1
        if arrowsStatus[LEFT]: dirx -= 1
        if arrowsStatus[RIGHT]: dirx += 1

        self.move(dirx, diry)

        if not(arrowsStatus[UP] or arrowsStatus[DOWN] or arrowsStatus[LEFT] or arrowsStatus[RIGHT]):
            self.currAnim = "Idle"

        self.animate()

class GeneralMobAI(Entity):
    def AI(self):
        #AI a ecrire ici
        pass

class Tile:
    def __init__(self, id, x: int, y: int, rotation: int = 0):
        self.res = getRes(TILE, id)       
        self.rotation = rotation
        self.image = self.res.getTexture(rotation)
        self.x = x
        self.y = y
        self.obj = canvas.create_image(margin + size*(x + 0.5), size*(y + 0.5), tags="tile", image=self.image)
    
    def cleanUp(self):
        canvas.delete(self.obj)

    def rotate(self, rotation: int, fixed: bool = False):
        if fixed:
            self.rotation = rotation 
        else:
            self.rotation += rotation 

        self.rotation = self.rotation - 360 * (self.rotation // 360)
        print(360 * (self.rotation // 360))

        self.image = self.res.getTexture(self.rotation)
        canvas.itemconfig(self.obj, image=self.image)

    def changeTile(self, id):
        self.res = getRes(TILE, id)
        self.image = self.res.getTexture(self.rotation)
        canvas.itemconfig(self.obj, image=self.image)

    def __eq__(self, other):
        if self.obj == other:
            return True
        else:
            return False

class Decor:
    def __init__(self, id, x: float, y: float, rotation: int = 0):

        if x < 0 or x > caseX * size or y < 0 or y > caseY * size:
            raise Exception(x + " " + y + " Isn't a valid position for a Decor")
            breakpoint()

        self.res = getRes(DECOR, id)
        self.x = x
        self.y = y
        self.rotation = rotation

        self.image = self.res.getTexture(0)
        self.obj = canvas.create_image(x + margin, y, tags="decor", image=self.image)

        self.animCounter = -1
        self._pendingAnimation = False

        if self.res.images > 1 and self.res.animTime != 0:
            self._pendingAnimation = window.after(self.res.animTime * 1000, self.animate)

    def cleanUp(self):
        #Fonction à utiliser avant de supprimer cet objet
        #Ne pas définir la fonction intégrée __del__(self) car elle pose problème 
        if self._pendingAnimation != False:
            window.after_cancel(self._pendingAnimation)

        canvas.delete(self.obj)

    def animate(self):
        self._pendingAnimation = window.after(self.res.animTime * 1000, self.animate)
        #self.nextSprite()
        self.animCounter += 1
        if self.animCounter == self.res.images:
            self.animCounter = 0

        self.image = self.res.getTexture(self.animCounter)
        canvas.itemconfig(self.obj, image=self.image)

    def nextSprite(self):
        self.animCounter += 1
        if self.animCounter == self.res.images:
            self.animCounter = 0

        self.image = self.res.getTexture(self.animCounter)
        canvas.itemconfig(self.obj, image=self.image)

    def changeDecor(self, id):
        if self._pendingAnimation != False:
            window.after_cancel(self._pendingAnimation)
            self._pendingAnimation = False

        self.res = getRes(DECOR, id)
        self.image = ImageTk.PhotoImage(self.res.images[0])
        canvas.itemconfig(self.obj, image=self.image)

    def __eq__(self, other):
        if self.obj == other:
            return True
        else:
            return False    
                     
class Region:
    def __init__(self):
        self.tiles = []
        self.entities = []
        self.decors = []
    
    def load(self, path: str):
        self.unload()
        try:
            with open(path) as file:
                data = json.load(file)
                tiles = data['tiles']

                self.tiles = [[0 for i in range(caseX)] for i in range(caseY)]

                for y in range(caseY):
                    for x in range(caseX):
                        filetile = tiles[y][x]
                        self.tiles[y][x] = Tile(filetile[0], x, y, filetile[1])

                for decor in data['decor']:
                    self.decors.append(Decor(decor[0],decor[1][0],decor[1][1]))
                
                for entity in data['entities']:
                    #A l'emplacement 1 on a le type de l'entité qui correspond à une classe définie dans notre programme
                    #En utilisant getattr, on peut instancier une classe à partir d'un string donc de entity[1]

                    temp = getattr(sys.modules[__name__], entity[1])(entity[0], entity[2][0], entity[2][1])
                    self.entities.append(temp)
                return True
        except:
            print("Cannot load map")
            return False

    def unload(self):
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                self.tiles[y][x].cleanUp()

        for decor in self.decors:
            decor.cleanUp()

        for entity in self.entities:
            entity.cleanUp()

        self.tiles = []
        self.decors = []
        self.entities = []
                
    def save(self, path: str):
        tilesData = [[0 for i in range(caseX)]for i in range(caseY)]
        for y in range(caseY):
            for x in range(caseX):
                tile: Tile = self.tiles[y][x]
                tilesData[y][x] = [tile.res.id, tile.rotation]

        decorsData = []
        for decor in self.decors:
            decorsData.append([decor.res.id, (decor.x, decor.y)])

        entitiesData = []
        for entity in self.entities:
            entitiesData.append([entity.id, entity.res.type, (entity.x, entity.y)])
        
        with open(path + ".data", "w") as file:
            dic = {'tiles': tilesData, 'decor': decorsData, 'entities': entitiesData}
            json.dump(dic, file)

    def new(self, id):
        self.unload()
        self.tiles = [[0 for i in range(caseX)]for i in range(caseY)]
        for y in range(caseY):
            for x in range(caseX):
                self.tiles[y][x] = Tile(id, x, y)

class World:
    def __init__(self, config: dict, worldDir: str):
        self.id = config['mapID']
        self.name = config['mapName']
        self.width = config['size'][0]
        self.height = config['size'][1]
        self.startPos = (config['startPos'][0], config['startPos'][1])
        self.dir = worldDir
        self.currRegion = Region()

        self.regionCoords = self.startPos
        self.loadRegion(*self.startPos, fixed=True)
    
    def loadRegion(self, x: int, y: int, fixed=False):
        #Spécificités de l'editeur de map à enlever pour le jeu
        #Si fixed n'est pas précisé, ajoute x et y à la position actuelle
        if fixed:
            coords = (x,y)
        else:
            a, b = self.regionCoords
            coords = (a+x, b+y)

        x, y = coords

        if x > self.width or x < 0 or y < 0 or y > self.height:
            return "Coords Error"
        
        self.regionCoords = coords
        if not self.currRegion.load(self.dir + "Region " +  x.__str__() + " " + y.__str__() + ".data"):
            return False

    def saveRegion(self, name: str):
        self.currRegion.save(self.dir + name)

def getRes(ressource, id):
    res = None
    if ressource == TILE:
        res = resTiles
    elif ressource == DECOR:
        res = resDecors
    elif ressource == ENTITY:
        res = resEntities
    else:
        raise Exception('Ressource type not properly defined')

    if type(id) is int:
            return res[id]
    elif type(id) is str:
        for thing in res:
            if thing.name == id:
                return thing

    raise Exception("Ressource of type " + ressource + " not found" )
                
def initRessources():
    tile_configs = []
    decor_configs = []
    wNames = []
    eNames = []

    #Tiles
    for (dirpath, dirnames, filenames) in os.walk(tilesFolder):
        for file in filenames:
            if ".json" in file:
                tile_configs.append(file)
        break
    
    #Decors
    for (dirpath, dirnames, filenames) in os.walk(decorsFolder):
        for file in filenames:
            if ".json" in file:
                decor_configs.append(file)
        break

    #Maps #Non utilisé 
    for (dirpath, dirnames, filenames) in os.walk(mapsFolder):
        for folder in dirnames:
            for (dirpath, dirnames, filenames) in os.walk(mapsFolder + folder):
                if "config.json" in file:
                    wNames.append(folder + "/")
                    break
        break

    #Entities
    for (dirpath, dirnames, filenames) in os.walk(entitiesFolder):
        for folder in dirnames:
            for (dirpath, dirnames, filenames) in os.walk(entitiesFolder + folder):
                for file in filenames:
                    if "config.json" in file:
                        eNames.append(folder + "/")
                        break
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
            with open(decorsFolder + config) as file:
                js = json.load(file)
                if js['decorID'] == id:
                    resDecors.append(Res_Decor(js))
                    break
    
    #Non utilisé
    #for id in range(len(worlds)):
    #    for world in wNames:
    #        with open(mapsFolder + world + "config.json") as file:
    #            js = json.load(file)
    #            if js['mapID'] == id:
    #                worlds.append(World(js, mapsFolder + world))
    #                break

    for id in range(len(eNames)):
        for entity in eNames:
            with open(entitiesFolder + entity + "config.json") as file:
                js = json.load(file)
                if js['entityID'] == id:
                    resEntities.append(Res_Entity(entity, js))
                    break
        
def importFile():
    #path = filedialog.askopenfilename(initialdir = saveFolder ,title = "Select Region Map ",filetypes = (("data files","*.data"),("all files","*.*")))
    #if path != "":
    #    currRegion.load(path)
    pass

def save():
    fileName = save_input.get()
    currWorld.saveRegion(fileName)

loaded = False
def askWorldFolder():
    global currWorld
    global loaded

    path = filedialog.askdirectory(initialdir = mapsFolder ,title = "Select Map Directory") + "/"
    if path != "/":
        try:
            with open(path + "config.json", "r") as file:
                js = json.load(file)
                if type(currWorld) is World:
                    currWorld.currRegion.unload()
                currWorld = World(js, path)
                if not loaded:
                    loaded = True
                    window.quit()
        except:
            result = messagebox.askyesno("Python",'There is no config.json in "' + path +'", \nWould you like to create one ?')
            if result:
                with open(path + "config.json", "w") as file:
                    file.write(
                        '{\n'
                            '   "mapID": 0,\n'
                            '   "mapName" : "Name",\n'
                            '   "size" : [5,5],\n'
                            '   "startPos": [0,0]\n'
                        '}')
                    os.startfile(path + "config.json")

def shutdown():
    window.destroy()
    os._exit(1)

def Debug(event):
    breakpoint()

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

    if not currWorld.loadRegion(x,y):
        coordx, coordy = currWorld.regionCoords
        save_input.delete(0,len(save_input.get()) + 1)
        save_input.insert(0,"Region "+ coordx.__str__() + " " + coordy.__str__())
            
    textCoord.delete("1.0",END)
    textCoord.insert("1.0", currWorld.regionCoords.__str__())

def arrowPressed(event):
    arrowsStatus[event.keysym] = True

def arrowReleased(event):
    arrowsStatus[event.keysym] = False
    
def OnClick(event):

    if event.y < 0 or event.y > size*caseY or event.x < margin or event.x > size*caseX + margin:
        return False

    index = selector.curselection()
    name = selector.get(index)
    currRegion = currWorld.currRegion

    if currentMode == TILE:
        y = event.y//size
        x = (event.x-margin)//size
    
        if event.num == 1:
            currRegion.tiles[y][x].changeTile(name)
        elif event.num == 3:
            currRegion.tiles[y][x].rotate(90)

    elif currentMode == DECOR:
        if event.num == 1:
            currRegion.decors.append(Decor(name,event.x - margin, event.y))

        elif event.num == 3:
            found = False
            items = canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for item in items:
                if found:
                    break
                for tag in canvas.gettags(item):
                    if tag == "decor":
                        found = True
                        for decor in currRegion.decors:
                            if decor == item:
                                decor.cleanUp()
                                currRegion.decors.remove(decor) 
                                break
                        break

    elif currentMode == ENTITY:
        if event.num == 1:
            res: Res_Entity = getRes(ENTITY, name)
            currRegion.entities.append(getattr(sys.modules[__name__], res.type)(event.x - margin, event.y))

        elif event.num == 3:
            found = False
            items = canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for item in items:
                if found:
                    break
                for tag in canvas.gettags(item):
                    if tag == "entity":
                        found = True
                        for entity in currRegion.entities:
                            if entity == item:
                                entity.cleanUp()
                                currRegion.entities.remove(entity) 
                                break
                        break

def switchMode(mode: str):
    global currentMode

    res = None
    selector.delete(0,END)

    if mode == TILE:
        res = resTiles

    elif mode == DECOR:
        res = resDecors 
        
    elif mode == ENTITY:
        res = resEntities

    else: 
        raise Exception("Bad switch mode")
        breakpoint()

    currentMode = mode

    for thing in res:
        selector.insert(END, thing.name)

    selector.select_set(0)

#Flèches directionnelles
arrowsStatus = {"Up": False, "Down": False, "Left": False, "Right": False}
for char in ["Up", "Down", "Left", "Right"]:
    window.bind("<KeyPress-%s>" % char, arrowPressed)
    window.bind("<KeyRelease-%s>" % char, arrowReleased)


initRessources()

world_button = Button(window, text="Select world folder", command=askWorldFolder)
world_button.place(relx=0.5, rely=0.5, anchor=CENTER)
world_button.config(font=("TkDefaultFont", 30))
window.protocol("WM_DELETE_WINDOW", shutdown)
window.mainloop()

world_button.place(relx=0 ,x=50, rely=0, y=40, anchor=NW)
world_button.config(font=("TkDefaultFont", 10))

textCoord   = Text(window, width=8, height=2)
textCoord.insert("1.0", currWorld.regionCoords.__str__())
world_up    = Button(window, text="Up", command=lambda: ButtonWorldLoad(TOP))
world_down  = Button(window, text="Down", command=lambda: ButtonWorldLoad(BOTTOM))
world_left  = Button(window, text="Left", command=lambda: ButtonWorldLoad(LEFT))
world_right = Button(window, text="Right", command=lambda: ButtonWorldLoad(RIGHT))

create = Button(window,text="Create", command=lambda: currWorld.currRegion.new("grass3"))
create.place(x=50, y=350)

textCoord.place(x=145, y=550)
world_up.place(x=150, y=500)
world_down.place(x=150, y=600)
world_right.place(x=200, y=550)
world_left.place(x=100, y=550)

selector = Listbox(window)
for i in range(len(resTiles)):
    for tile in reversed(resTiles):
        selector.insert(i, tile.name)
    break 

selector.select_set(0)
selector.place(x=50,y=100)

tile_button = Button(window, text="Tile", command=lambda: switchMode(TILE))
decor_button = Button(window, text="Decor", command=lambda: switchMode(DECOR))
entity_button = Button(window, text="Entity", command=lambda: switchMode(ENTITY))

tile_button.place(x=50, y=75)
window.update()
decor_button.place(x=50+tile_button.winfo_width(), y=75)
window.update()
entity_button.place(x=decor_button.winfo_x() + decor_button.winfo_width() ,y=75)

save_input = Entry(window)
save_input.place(x=50, y=HEIGHT-100)

save_button = Button(window, text="Save", command=save)
save_button.place(x=150, y=HEIGHT-100)

import_button = Button(window, text="Import", command=importFile)
import_button.place(x=50, y=HEIGHT-50)

canvas.bind('<Button>', OnClick)
window.bind('<Escape>', Debug)



###################################
#test zone

window.mainloop()