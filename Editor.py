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


Profiling = True
showFixBbox = False


if Profiling:
    cp = cProfile.Profile()
    cp.enable()


#Constantes
test = 27
WIDTH = 1920
HEIGHT = 1080
tick = 15 #Environs 1 update par frame
TILE = "TILE"
DECOR = "DECOR"
ENTITY = "ENTITY"
DIALOG = "DIALOG"
UP = "Up"
DOWN = "Down"
LEFT = "Left"
RIGHT = "Right"

dialogTimeStop = False
pauseTimeStop = False

#Chemins de dossier
tilesFolder = "./data/tiles/"
mapsFolder = "./data/maps/"
saveFolder = "./data/saves/"
decorsFolder = "./data/decorations/"
entitiesFolder = "./data/entities/"
dialogsFolder = "./data/dialogs/"

currWorld = None
resTiles = []
resDecors = []
resMaps = []
resEntities = []
resDialogs = []
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

class Ressource:
    def __init__(self, path: str, config: dict):
        self.name = config["name"]
        self.animSpeed = config["animSpeed"]
        self.collisions = config["physicalCollisions"]
        self.animConfig = config["animations"]
        self.animations = {}

        texture = []

        if type(self.animConfig) is dict:
            for key in self.animConfig:
                spritesNumber = self.animConfig[key][0]
                if spritesNumber > 1:
                    for i in range(spritesNumber):
                        if key == "Default":
                            texture.append(getImage(path + self.name + i.__str__() + ".png"))

                        else:
                            texture.append(getImage(path + self.name + "_" + key + i.__str__() + ".png"))
                    
                elif spritesNumber == 1:
                    if key == "Default":
                        texture.append(getImage(path + self.name + ".png"))
                    else:
                        texture.append(getImage(path + self.name + "_" + key + ".png"))
                
                self.animations[key] = texture

        elif type(self.animConfig) is list:
            spritesNumber = self.animConfig[0]
            if spritesNumber > 1:
                for i in range(spritesNumber):
                    texture.append(getImage(path + self.name + i.__str__() + ".png"))

            elif spritesNumber == 1:
                texture.append(getImage(path + self.name + ".png"))
                
            self.animConfig = {"Default": self.animConfig}
            self.animations["Default"] = texture

        elif self.animConfig == None:
            texture.append(getImage(path + self.name + ".png"))
            self.animations["Default"] = texture
            
    def getTexture(self, key="Default", index=0, rotation=0):
        return ImageTk.PhotoImage(self.animations[key][index].rotate(rotation, expand=True))

class Res_Tile(Ressource):
    pass

class Res_Decor(Ressource):
    def __init__(self, path: str,config: dict):
        super().__init__(path, config)
        self.className = config['class']

class Res_Entity(Ressource):
    def __init__(self, path: str, config: dict):
        super().__init__(path, config)
        self.className = config['class']
        self.speed = config['speed']
        self.size = config['size']
        self.side = config['side']
        self.health = config['health']
        self.contactDamage = config['contactDamage']
        self.dialogs = None

        if self.className == "NPC":
            pass

class Res_Map:
    def __init__(self, directory: str ,config: dict):
        self.id = config['mapID']
        self.name = config['mapName']
        self.size = config['size'].lower()
        self.directory = directory
        
class Res_Dialog:
    def __init__(self, name, texts, dialogs):
        self.name = name
        self.texts = texts
        self.dialogs = dialogs

    def getDialog(self, index, i):
        string = ""
        for a in range(len(self.dialogs[index][i])):
            string += self.texts[self.dialogs[index][i][a]]
        return string

    def getLen(self, index):
        return len(self.dialogs[index])

class BasicElement:
    def __init__(self, id, resType: str, tileCoord: bool ,x: float, y: float, fix: bool, rotation = 0, tags = ""):
        self.res = getRes(resType, id)
        self._pendingAnimation = False
        self.x = x
        self.y = y
        self.rotation = rotation

        self.currAnim = "Default"
        self.animSpeed = self.res.animSpeed
        self.animCounter = 0
        self.animTick = 0

        if self.res.collisions:
            tags += " collision "

        self.image = self.res.getTexture(rotation=rotation)

        if tileCoord:
            self.obj = canvas.create_image(size*(x + 0.5) + margin, size*(y + 0.5), tags=tags, image=self.image)
        else:
            self.obj = canvas.create_image(x + margin, y, tags=tags, image=self.image)

        self.tkinterFix = None
        if fix:
            self.tkinterFix = TkinterFix(x, y, self)

        self._pendingAnimation = window.after(tick * self.animSpeed, self.animate)

    def cleanUp(self):
        if self._pendingAnimation:
            window.after_cancel(self._pendingAnimation)

        if self.tkinterFix != None:
            self.tkinterFix.cleanUp()

        canvas.delete(self.obj)

    def animate(self):
        if self.res.animSpeed != 0 and not self.res.animConfig == None:
            self._pendingAnimation = window.after(tick * self.res.animSpeed, self.animate)
            self.nextSprite()
                
    def nextSprite(self):
        images, loop = self.res.animConfig[self.currAnim]

        if self.animCounter == images:
            if loop:
                self.animCounter = 0
            else:
                window.after_cancel(self._pendingAnimation)
                self.OnAnimationEnd()
                return
            
        self.image = self.res.getTexture(self.currAnim, self.animCounter, self.rotation)
        canvas.itemconfig(self.obj, image=self.image)

        self.animCounter += 1

    def rotate(self, rotation, fixed=False):
        if fixed:
            self.rotation = rotation
        else:
            self.rotation += rotation

        self.rotation -= self.rotation // 360 * 360

        self.image = self.res.getTexture(self.currAnim, self.animCounter, self.rotation)
        canvas.itemconfig(self.obj, image=self.image)

    def OnAnimationEnd(self):
        pass

    def __eq__(self, other):
        if self.obj == other:
            return True
        else:
            return False

class Tile(BasicElement):
    def __init__(self, id, x: int, y: int, rotation: int = 0):
        super().__init__(id, TILE, True, x, y, False, rotation)

    def changeTile(self, id):
        self.__init__(id, self.x, self.y)

    def cleanUp(self):
        super().cleanUp()
        #currWorld.currRegion.tiles.remove(self)
    
class TkinterFix:
    #Tkinter a une manière spéciale de déterminer qu'est ce qui a changé sur l'écran qui permet de sauver des performances,
    #Cette classe permet de forcer l'affichage des entités qui bougent sans qu'il y ait des bugs d'affichage
    def __init__(self, x, y, entity, size=10):
        x0, y0, x1, y1 = canvas.bbox(entity.obj)

        if showFixBbox:
            self.obj = canvas.create_rectangle(x0 - size, y0 - size, x1 + size, y1 + size, fill="")
        else:
            self.obj = canvas.create_rectangle(x0 - size, y0 - size, x1 + size, y1 + size, fill="", outline="")

    def move(self, dx, dy):
        canvas.move(self.obj, dx, dy)

    def cleanUp(self):
        canvas.delete(self.obj)

class Dialog:
    def __init__(self, id):
        
        self.res = getRes(DIALOG, id)
        self.img = getImage(dialogsFolder + "dialog_frame.png", photoimage=True)

        #self.obj = None
        self.label = None
        self.font = Font(family="Times New Roman", size=24)
        self.i = 0
        self.dialIndex = 0
        
        self.funcID = None
        self.end = False

    def cleanUp(self):
        global dialogTimeStop

        self.end = False
        #self.reset()
        dialogTimeStop = False

class Entity(BasicElement):
    def __init__(self, id, x: float, y: float, rotation=0, tags=""):
        #if x < 0 or x > caseX * size or y < 0 or y > caseY * size:
        #    raise Exception(x + " " + y + " Isn't a valid position for an Entity")
        #    breakpoint()

        super().__init__(id, ENTITY, False, x, y, True, rotation, " entity " + tags)

        self.side = self.res.side
        self.health = self.res.health
        self.speed = self.res.speed
        self.contactDamage = self.res.contactDamage
        
        self.invicibility = False
        self.invTick = 60
        self.invCounter = 0
        
        self.lastAnim = None
        
        self._pendingLoop = None

        self._pendingLoop = window.after(tick, self.outerLoop)

        if currWorld != None:
            currWorld.currRegion.entities.append(self)

    def cleanUp(self):
        super().cleanUp()
        if self._pendingLoop != None:
            window.after_cancel(self._pendingLoop)
            self._pendingLoop = None
        currWorld.currRegion.entities.remove(self)
    
    def animate(self):
        if self.currAnim != self.lastAnim:
                self.lastAnim = self.currAnim
                self.animCounter = 0
                self.animTick = self.animSpeed

        super().animate()
        return True
    
    def getDistance(self, *args):
        #Recupère la distance entre self et une entité si un argument donné,
        #Sinon récupère la distance entre self et les coordonées donné
        if len(args) == 1 and isinstance(args[0], Entity):
            return sqrt((args[0].x - self.x)**2 + (args[0].y - self.y)**2 )
        elif len(args) == 2:
            return sqrt((args[0] - self.x)**2 + (args[1] - self.y)**2)
        else:
            raise Exception("Bad arguments in function getDistance")
            breakpoint()

    def OnCollision(self):
        pass

    def OnDeath(self):
        pass

    def OnBorderTouch(self):
        pass
    
    def OnHit(self):
        pass
    
    def outerLoop(self):
        pass
    #    self._pendingLoop = window.after(tick, self.outerLoop)
    #    if not dialogTimeStop:
    #        self.loop()
    #    else:
    #        self.timeStopLoop()
        
    def timeStopLoop(self):
        pass 

    def loop(self):
        pass

    def __eq__(self, other):
        if self.obj == other:
            return True
        else:
            return False

class Mob(Entity):
    def __init__(self, id, x, y, rotation=0, tags=""):
        super().__init__(id, x, y, rotation=rotation, tags=tags)
        self.facingDirection = None  

class MeleeEnemy(Mob):
    def __init__(self, id, x, y, rotation=0):
        super().__init__(id, x, y, rotation)
        self.timer = 0
        self.stopTimer = False
        self.timer2 = 0
        self.step = 0
        self.direction = (0, 0)
        
class RangedEnemy(Mob):
    def __init__(self, id, x, y, rotation=0):
        super().__init__(id, x, y, rotation)
        self.timer = 0
        self.stopTimer = False
        self.timer2 = 0
        self.step = 0
        self.direction = (0, 0)
        self._timerShootArrow = 0
        
class Skill(Entity):
    def __init__(self, id, x: float, y: float, rotation=0):
        super().__init__(id, x, y, rotation)
        self.animStatus = None

    def OnAnimationEnd(self):
        self.animStatus = END
        self.cleanUp()
      
class Player(Mob):
    #Classe singleton
    def __init__(self, x: float, y: float):
        super().__init__("player", x, y)
        self.sword = None
        self.action = None
        self._pendingMelee = None
        self.currency = 0
        self.timer = 0

        self._timerShootArrow = 0

        #window.bind("<KeyPress-a>", lambda event: self.setAction("Melee"))
        #window.bind("<KeyPress-e>", lambda event: self.setAction("Use"))
        #window.bind("<KeyPress-z>", lambda event: self.setAction("Shoot"))

class Projectile(Entity):
    def __init__(self, id, x, y, dirx, diry, rotation=0):
        super().__init__(id, x, y, rotation=rotation)
        self.initDir = (dirx, diry)

class Npc(Mob):
    def __init__(self, id, x, y, dialogID):
        super().__init__(id, x, y, tags="usable")
        self.dialogID = dialogID
        self.dialog = Dialog(self.dialogID)
        self.index = 0

class Jhony(Npc):
    def __init__(self, *args):
        super().__init__(*args)
        self.step = 0 #Avancement

        self.moveTick_1 = int(3*size/self.speed)
        self.moveTick_2 = int(2*size/self.speed)

class Decor(BasicElement):
    def __init__(self, id, x: float, y: float, rotation: int = 0, tags: str = "", **kwargs):

        if x < 0 or x > caseX * size or y < 0 or y > caseY * size:
            raise Exception(x + " " + y + " Isn't a valid position for a Decor")
            breakpoint()

        super().__init__(id, DECOR, False, x, y, False, rotation, "decor "+ tags)

        self.arguments = None
        if currWorld != None:
            currWorld.currRegion.decors.append(self)
    
    def cleanUp(self):
        super().cleanUp()
        currWorld.currRegion.decors.remove(self)

    def OnUse(self):
        pass

    def OnWalk(self):
        pass

class Chest(Decor):
    def __init__(self, *args):
        super().__init__(*args, tags="usable")
        
class Teleporter(Decor):
    parameters = {"dx": "Int", "dy": "Int"}

    def __init__(self, *args, **kw):
        super().__init__(*args, tags="walk")
        self.dir = (kw["dx"], kw["dy"])
        self.arguments = kw

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
                    if len(decor) == 3:
                        if decor[2] != None:
                            obj = getattr(sys.modules[__name__], getRes(DECOR, decor[0]).className)(decor[0], *decor[1], **decor[2])
                        else:
                            obj = getattr(sys.modules[__name__], getRes(DECOR, decor[0]).className)(decor[0], *decor[1])

                    if currWorld == None:
                        self.decors.append(obj)

                for entity in data['entities']:
                    #TODO Maybe faire comme au desus
                    obj = getattr(sys.modules[__name__], getRes(ENTITY, entity[0]).className)(entity[0], *entity[1])
                    if currWorld == None:
                        self.entities.append(obj)

                return True
        except:
            print("Cannot load map")
            return False

    def unload(self):
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                self.tiles[y][x].cleanUp()

        for decor in self.decors[:]:
            decor.cleanUp()

        for entity in self.entities[:]:
            entity.cleanUp()

        self.tiles = []
        self.decors = []
        self.entities = []
                
    def save(self, path: str):
        tilesData = [[0 for i in range(caseX)]for i in range(caseY)]
        for y in range(caseY):
            for x in range(caseX):
                tile: Tile = self.tiles[y][x]
                tilesData[y][x] = [tile.res.name, tile.rotation]

        decorsData = []
        for decor in self.decors:
            decorsData.append([decor.res.name, (decor.x, decor.y), decor.arguments])

        entitiesData = []
        for entity in self.entities:
            entitiesData.append([entity.res.name, (entity.x, entity.y)])
        
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
        self.name = config['name']
        self.width, self.height = config['size']
        self.startPos = config['startPos']
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

def getImage(path, imgSize=None, rotation=0, photoimage=False):
    img = Image.open(path)
    if type(imgSize) is tuple:
        img = img.resize(imgSize, Image.BOX)
    elif isinstance(imgSize, (int, float)):
        img = img.resize((imgSize,imgSize), Image.BOX)
    elif imgSize == None:
        width, height = img.size
        img = img.resize((int(width * size/32), int(height * size/32)), Image.BOX)
    else:
        raise Exception("getImage size parameter is wrong")
    
    if rotation != 0:
        img = img.rotate(rotation)
    
    if photoimage:
        return ImageTk.PhotoImage(img)
    else:
        return img

def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)

def getRotation(dirx, diry):
        rotation = 0
        if diry == 0:
            if dirx > 0:
                rotation = -90
            elif dirx < 0:
                rotation = 90 
            else:
                # ???
                return False

        elif diry > 0:
            rotation = degrees(atan(dirx/-diry))
        elif diry < 0:
            rotation = degrees(atan(dirx/-diry)) + 180
        
        return rotation

def findObjectByTag(resType, canvasItems, tag, first=False):
    objList = None
    returnList = []

    if resType == TILE:
        objList = currWorld.currRegion.tiles
    elif resType == DECOR:
        objList = currWorld.currRegion.decors
    elif resType == ENTITY:
        objList = currWorld.currRegion.entities
    else:
        raise Exception('Ressource type not properly defined')
        breakpoint()
    
    for item in canvasItems:
        if tag in canvas.gettags(item):
            for obj in objList:
                if item == obj:
                    if first:
                        return obj
                    else:
                        returnList.append(obj)

    if first:
        return None
    else:
        return returnList
    
def getRes(ressource, id):
    res = None
    if ressource == TILE:
        res = resTiles
    elif ressource == DECOR:
        res = resDecors
    elif ressource == ENTITY:
        res = resEntities
    elif ressource == DIALOG:
        res = resDialogs
    else:
        raise Exception('Ressource type not properly defined')
        breakpoint()
    

    if type(id) is int:
            return res[id]
    elif type(id) is str:
        for thing in res:
            if thing.name.lower() == id.lower():
                return thing

    raise Exception("Ressource of type " + ressource + " not found" )
    breakpoint()
                
def initRessources():
    tile_configs = []
    decor_configs = []
    wNames = []
    eNames = []
    dialNames = []
    

    #name
    #path
    #iterations folder
    #

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
    
    #Dialogs
    for (dirpath, dirnames, filenames) in os.walk(dialogsFolder):
        for filename in filenames:
            if ".json" in filename:
                for (_dirpath, _dirnames, _filenames) in os.walk(dialogsFolder):
                    for _filename in _filenames:
                        if filename.replace(".json", ".txt") in _filename:
                            dialNames.append(filename.replace(".json", ""))
                            break
                    break           
        break

    for config in tile_configs:
        with open(tilesFolder + config) as file:
            js = json.load(file)
            if "name" in js:
                resTiles.append(Res_Tile(tilesFolder,js))
                
    
    for config in decor_configs:
        with open(decorsFolder + config) as file:
            js = json.load(file)
            if "name" in js:
                resDecors.append(Res_Decor(decorsFolder,js))
                
    
    for entity in eNames:
        with open(entitiesFolder + entity + "config.json") as file:
            js = json.load(file)
            if "name" in js:
                resEntities.append(Res_Entity(entitiesFolder + entity, js))
                

    for dial in dialNames:
        with open(dialogsFolder + dial + ".json") as jsonFile:
            js = json.load(jsonFile)
            if "dialogs" in js:
                with open(dialogsFolder + dial + ".txt") as dialogFile:
                    text = dialogFile.readlines()
                    resDialogs.append(Res_Dialog(dial, text, js["dialogs"]))
            else:
                raise Exception("Json file doesn't either contain 'id' or 'dialogs' keys or an error occured while reading dialog texts")
   
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
                            ('{\n'
                            '   "name" : "Name",\n'
                            '   "worldCoords" : [5,5],\n'
                            '   "size": [5,5],\n'
                            '   "startPos": [0,0]\n'
                            '}'))
                    
                    os.startfile(path + "config.json")

def shutdown():
    window.destroy()
    if Profiling:
        cp.disable()
        cp.print_stats(sort="cumtime")
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
            res: Res_Decor = getRes(DECOR, name)
            tempClass = getattr(sys.modules[__name__], res.className)
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

                decor = tempClass(name, event.x - margin, event.y, **kw)
            else:
                decor = tempClass(name, event.x - margin, event.y)
            

        elif event.num == 3:
            items = canvas.find_overlapping(event.x, event.y, event.x, event.y)
            decor = findObjectByTag(DECOR, items, "decor", first=True)
            if decor != None:
                decor.cleanUp()
                


    elif currentMode == ENTITY:
        if event.num == 1:
            res: Res_Entity = getRes(ENTITY, name)
            if res.name == "player":
                entity = getattr(sys.modules[__name__], res.className)(event.x - margin, event.y)
            else:
                entity = getattr(sys.modules[__name__], res.className)(res.name, event.x - margin, event.y)

        elif event.num == 3:
            found = False
            items = canvas.find_overlapping(event.x, event.y, event.x, event.y)
            entity = findObjectByTag(ENTITY, items, "entity", first=True)
            if entity != None:
                entity.cleanUp()
                
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

import_button = Button(window, text="Import", command=importFile)
import_button.place(x=50, y=HEIGHT-50)

canvas.bind('<Button>', OnClick)
window.bind('<Escape>', Debug)

#Tests
Test = True
window.mainloop()


