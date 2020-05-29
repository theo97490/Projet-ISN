from tkinter import *
from GameConstants import *
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


currWorld = None
resTiles = []
resDecors = []
resMaps = []
resEntities = []
resDialogs = []
worlds = []

dialogTimeStop = False
pauseTimeStop = False

currentMode = TILE

window = None
canvas = None

margin = 0
editorMode = False


class Ressource:
    def __init__(self, path: str, config: dict):
        self.name = config["name"]
        self.animSpeed = config["animSpeed"]
        self.collisions = config["physicalCollisions"]
        self.animConfig = config["animations"]
        self.animations = {}

        

        if type(self.animConfig) is dict:
            for key in self.animConfig:
                texture = []
                spritesNumber = self.animConfig[key][0]
                if spritesNumber > 1:
                    for i in range(spritesNumber):
                        if key == "Default":
                            texture.append(getImage(path + self.name + i.__str__() + ".png"))

                        else:
                            folder = self.name + "_" + key + "/"
                            texture.append(getImage(path + folder + self.name + "_" + key + i.__str__() + ".png"))
                    
                elif spritesNumber == 1:
                    if key == "Default":
                        texture.append(getImage(path + self.name + ".png"))
                    else:
                        texture.append(getImage(path + self.name + "_" + key + ".png"))
                
                self.animations[key] = texture
                
        elif type(self.animConfig) is list:
            texture = []
            spritesNumber = self.animConfig[0]
            if spritesNumber > 1:
                for i in range(spritesNumber):
                    texture.append(getImage(path + self.name + i.__str__() + ".png"))

            elif spritesNumber == 1:
                texture.append(getImage(path + self.name + ".png"))
                
            self.animConfig = {"Default": self.animConfig}
            self.animations["Default"] = texture

        elif self.animConfig == None:
            texture = []
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
        self.name = config['name']
        self.worldCoords = config['worldCoords']
        self.width, self.height = config['size']
        self.startPos = config['startPos']
        self.dir = directory
        
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
        self.reset()
        dialogTimeStop = False

    def reset(self):
        self.i = 0 
        if self.funcID != None:
            window.unbind("<KeyPress-f>", self.funcID)
            self.funcID = None

        if self.label != None:
            self.label.destroy()


    def next(self):
        if not self.end:
            self.i += 1
            if self.i < self.res.getLen(self.dialIndex):
                self.label.config(text=self.res.getDialog(self.dialIndex, self.i))
            else:
                self.end = True
                self.reset()

    def show(self, index):
        global dialogTimeStop

        self.end = False
        dialogTimeStop = True
        
        
        self.funcID = window.bind("<KeyPress-f>", lambda event: self.next())
        self.dialIndex = index
        self.label = Label(window, font=self.font, text=self.res.getDialog(index, self.i), image=self.img,borderwidth=0,compound=CENTER, relief=FLAT)
        self.label.place(x=caseX * size/2 + margin - 4.5*size, y=3*HEIGHT/4 - size)

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
        
        if not editorMode:
            self._pendingLoop = window.after(tick, self.outerLoop)

        if currWorld != None:
            currWorld.currRegion.entities.append(self)

    def cleanUp(self):
        super().cleanUp()
        if self._pendingLoop != None:
            window.after_cancel(self._pendingLoop)
            self._pendingLoop = None
        currWorld.currRegion.entities.remove(self)


    def move(self, dirx, diry):
        #dirx et diry sont des directions égales à 1 ou -1

        diry = -diry
        dx =  dirx * self.speed
        dy =  diry * self.speed
        
        while(self.checkCollisions(dx, 0)):
            dx -= dirx * 1/self.speed
        
        while(self.checkCollisions(0, dy)):
            dy -= diry * 1/self.speed

        if self.x + dx > size * caseX or self.x + dx < 0:
            dx = 0
            self.OnBorderTouch()

        if self.y + dy > size * caseY or self.y + dy < 0:
            dy = 0
            self.OnBorderTouch()
        
        self.x += dx
        self.y += dy

        canvas.move(self.obj, dx ,dy)
        self.tkinterFix.move(dx, dy)
    
    def moveTowards(self, x, y):
        norme = self.getDistance(x,y)
        x = x - self.x
        y = y - self.y
        y = -y
        self.move(x / norme, y / norme)
    
    def animate(self):
        if self.currAnim != self.lastAnim:
                self.lastAnim = self.currAnim
                self.animCounter = 0
                self.animTick = self.animSpeed

        super().animate()
        return True

    def checkCollisions(self, dx, dy):
        x1, y1, x2, y2 = canvas.bbox(self.obj)
        items = canvas.find_overlapping(x1 + dx, y1 + dy, x2 + dx, y2 + dy)
        for item in items:
            tags = canvas.gettags(item)
            if "collision" in tags:
                self.OnCollision()
                return True
        return False 
    
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
        self._pendingLoop = window.after(tick, self.outerLoop)
        if not dialogTimeStop:
            self.loop()
        else:
            self.timeStopLoop()
        
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

    def move(self, dirx, diry):
        if dirx > 0:
            self.currAnim = self.facingDirection = RIGHT
        elif dirx < 0:
            self.currAnim = self.facingDirection = LEFT
        elif diry > 0:
            self.currAnim = self.facingDirection = UP
        elif diry < 0:
            self.currAnim = self.facingDirection = DOWN
        else:
            self.currAnim = "Default"

        super().move(dirx, diry)

    def checkGround(self):
        items = canvas.find_overlapping(*canvas.bbox(self.obj))
        walkable = findObjectByTag(DECOR, items, "walk", first=True)
        if walkable != None:
            walkable.OnWalk(self)
            return True
        return False

    def checkCollisionDamage(self):
        if self.invicibility:
            self.invCounter += 1
            if self.invCounter == self.invTick:
                self.invCounter = 0
                self.invicibility = False
        else:
            items = canvas.find_overlapping(*canvas.bbox(self.obj))

            for entity in findObjectByTag(ENTITY, items, "entity"):
                if entity.side != self.side:
                    entity.OnHit()
                    print( "[COLLISION] " + self.res.name + " collided with " + entity.res.name)
                    self.health -= entity.contactDamage
                    print("[DAMAGE] current health : "+ self.health.__str__())
                    self.invicibility = True
    def RandomMove(self, value):
        Rand = random.randint(0,4)
        if (Rand == 0) :
             self.direction = (1, 0)
        elif (Rand == 1) :
            self.direction = (-1, 0)
        elif (Rand == 2) :
            self.direction = (0, 1)
        else :
            self.direction = (0, -1)

    def FacePlayer(self):
        distanceX = self.x-player.x
        distanceY = self.y-player.y
        if (abs(distanceY) > abs(distanceX)):
            if (distanceY > 0):
                self.facingDirection = UP
            else :
                self.facingDirection = DOWN
        else :
            if (distanceX > 0):
                self.facingDirection = LEFT
            else :
                self.facingDirection = RIGHT
                            
    def loop(self):
        self.checkGround()
        super().loop()
        self.checkCollisionDamage()    

class MeleeEnemy(Mob):
    def __init__(self, id, x, y, rotation=0):
        super().__init__(id, x, y, rotation)
        self.timer = 0
        self.stopTimer = False
        self.timer2 = 0
        self.step = 0
        self.direction = (0, 0)


    def loop(self):
        #Deplacement        

        if (self.getDistance(player) < 250):
            self.moveTowards(player.x, player.y)
            
        else:
            if (self.timer >= 60) :
                self.timer = 0
                self.stopTimer = True

                if (random.randint(0,1) <= 0.2):
                    if (random.randint(0,1) <= 0.75):
                        self.step = 50
                    else:
                        self.step = 100    
                    self.RandomMove(self.step)
                    
                    self.timer2 = self.step/self.speed
            
            if self.timer2 != 0:
                self.move(*self.direction)
                self.timer2 -= 1
            else:
                self.direction = (0,0)
                self.stopTimer = False

            if not self.stopTimer:
                self.timer += 1
            
        super().loop()

        
    
    def RandomMove(self, value):
            Rand = random.randint(0,4)
            if (Rand == 0) :
                self.direction = (1, 0)
            elif (Rand == 1) :
                self.direction = (-1, 0)
            elif (Rand == 2) :
                self.direction = (0, 1)
            else :
                self.direction = (0, -1)

class RangedEnemy(Mob):
    def __init__(self, id, x, y, rotation=0):
        super().__init__(id, x, y, rotation)
        self.timer = 0
        self.stopTimer = False
        self.timer2 = 0
        self.step = 0
        self.direction = (0, 0)
        self._timerShootArrow = 0
    def shootArrow(self):

            dirx = diry = dx = dy = 0
            if self.facingDirection == UP:
                diry = 1
                dy = -size
            elif self.facingDirection == DOWN:
                diry = -1
                dy = size
            elif self.facingDirection == RIGHT:
                dirx = 1
                dx = size
            elif self.facingDirection == LEFT:
                dx = -size
                dirx = -1

            Projectile("arrow", self.x + dx, self.y + dy, dirx, diry, getRotation(dirx, diry))
            self.action = None


    def loop(self):
        #Deplacement        

        distanceX = self.x-player.x
        distanceY = self.y-player.y

        if (self.getDistance(player) < 500):
            if (-10 < distanceX < 10 or -10 < distanceY < 10  ):
                if(self._timerShootArrow == 60):
                    self.FacePlayer()
                    self.shootArrow()
                    self._timerShootArrow = 0
                else : 
                    self._timerShootArrow += 1 
            else :
                self.direction = (0, -1)
                if (abs(distanceY) < abs(distanceX)):
                    self.moveTowards(self.x, player.y)
                else :
                    self.moveTowards(player.x, self.y)
        elif (self.getDistance(player) < 1000):
            self.moveTowards(player.x, player.y)

        else:
            if (self.timer >= 60) :
                self.timer = 0
                self.stopTimer = True

                if (random.randint(0,1) <= 0.2):
                    if (random.randint(0,1) <= 0.75):
                        self.step = 50
                    else:
                        self.step = 100    
                    self.RandomMove(self.step)

                    self.timer2 = self.step/self.speed

            if self.timer2 != 0:
                self.move(*self.direction)
                self.timer2 -= 1
            else:
                self.direction = (0,0)
                self.stopTimer = False

            if not self.stopTimer:
                self.timer += 1

        super().loop()

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
        global player
        player = self
        super().__init__("player", x, y)

        self.sword = None
        self.action = None
        self._pendingMelee = None
        self.currency = 0
        self.timer = 0

        self._timerShootArrow = 0

        window.bind("<KeyPress-a>", lambda event: self.setAction("Melee"))
        window.bind("<KeyPress-e>", lambda event: self.setAction("Use"))
        window.bind("<KeyPress-z>", lambda event: self.setAction("Shoot"))

    def cleanUp(self):
        global player
        super().cleanUp()
        player = None
    
    def meleeAttack(self):
        self._pendingMelee = window.after(tick, self.meleeAttack)
        self.action = "Pending"

        if self.sword == None:
            dx = dy = rotation = 0 
            
            if self.facingDirection == RIGHT:
                rotation = -90
                dx = size

            elif self.facingDirection == LEFT:
                rotation = 90
                dx = -size

            elif self.facingDirection == DOWN:
                rotation = 180
                dy = size

            elif self.facingDirection == UP:
                dy = -size

            self.sword = Skill("player_sword", self.x + dx, self.y + dy, rotation)
        
        elif self.sword.animStatus == END:
            self.sword = None
            window.after_cancel(self._pendingMelee)
            self._pendingMelee = None
            self.action = None
        

    def shootArrow(self):
        if self.timer > self._timerShootArrow + 20:
            self._timerShootArrow = self.timer

            dirx = diry = dx = dy = 0
            if self.facingDirection == UP:
                diry = 1
                dy = -size
            elif self.facingDirection == DOWN:
                diry = -1
                dy = size
            elif self.facingDirection == RIGHT:
                dirx = 1
                dx = size
            elif self.facingDirection == LEFT:
                dx = -size
                dirx = -1

            Projectile("arrow", self.x + dx, self.y + dy, dirx, diry, getRotation(dirx, diry))
            self.action = None

    def use(self):
        x0, y0, x1, y1 = canvas.bbox(self.obj)

        if self.facingDirection == UP:
            y1 = y0 - size/2
        elif self.facingDirection == DOWN:
            y0 = y1 + size/2
        elif self.facingDirection == LEFT:
            x1 = x0 - size/2
        elif self.facingDirection == RIGHT:
            x0 = x1 + size/2

        items = canvas.find_overlapping(x0, y0, x1, y1)
        usable = findObjectByTag(DECOR, items, "usable", first=True)
        if usable != None:
            usable.OnUse(self)
        else:
            usable = findObjectByTag(ENTITY, items, "usable", first=True)
            if usable != None:
                usable.OnUse(self)
        
        self.action = None


    def setAction(self, action: str):
        print(action)
        if self.action == None:
            self.action = action

    def loop(self):
        dirx = diry = 0
        
        if self.action == None:
            if arrowsStatus[UP]: diry += 1
            if arrowsStatus[DOWN]: diry -= 1
            if arrowsStatus[LEFT]: dirx -= 1
            if arrowsStatus[RIGHT]: dirx += 1
            self.move(dirx, diry)

        elif self.action != "Pending":
            if self.action == "Melee": self.meleeAttack()
            if self.action == "Use": self.use()
            if self.action == "Shoot": self.shootArrow()
            
        super().loop()
        self.timer += 1

    def timeStopLoop(self):
        self.action = None

class Projectile(Entity):
    def __init__(self, id, x, y, dirx, diry, rotation=0):
        super().__init__(id, x, y, rotation=rotation)
        self.initDir = (dirx, diry)
    
    def OnHit(self):
        self.cleanUp()

    def OnBorderTouch(self):
        self.cleanUp()

    def OnCollision(self):
        self.cleanUp()

    def move(self, dirx, diry):
        self.rotation = getRotation(dirx, diry)
        super().move(dirx, diry)

    def loop(self):
        self.move(*self.initDir)
        #self.moveTowards(player.x, player.y)
        super().loop()
        canvas.update()

class Npc(Mob):
    def __init__(self, id, x, y, dialogID):
        super().__init__(id, x, y, tags="usable")
        self.dialogID = dialogID
        self.dialog = Dialog(self.dialogID)
        self.index = 0


    def cleanUp(self):
        super().cleanUp()
        self.dialog.cleanUp()

    def timeStopLoop(self):
        #Utilisez cette loop pour animer le npc lorsque
        #le temps est arrété
        pass

    def OnUse(self, entity):
        pass

class Jhony(Npc):
    def __init__(self, *args):
        super().__init__(*args)
        self.step = 0 #Avancement

        self.moveTick_1 = int(3*size/self.speed)
        self.moveTick_2 = int(2*size/self.speed)

    def OnUse(self, *args):
        if self.step == 0:
            self.dialog.show(0)
        if self.step >= 2:
            self.dialog.show(1)


    def timeStopLoop(self):
        if self.dialog.end:
            if self.step == 2:
                self.dialog.cleanUp()

            if self.step == 1:
                self.dialog.show(1)
                self.step += 1

            if self.step == 0:
                if self.moveTick_1 > 1:
                    self.moveTick_1 -= 1
                    self.move(0, 1)

                elif self.moveTick_2 > 1:
                    self.moveTick_2 -= 1
                    self.move(1, 0)
                else:
                    self.step += 1

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
        
    def OnUse(self, player: Player):
        self.nextSprite()
        player.currency += 20
        print("[CHEST] Player current currency : " + player.currency.__str__())

class Teleporter(Decor):
    parameters = {"dx": "Int", "dy": "Int"}

    def __init__(self, *args, **kw):
        super().__init__(*args, tags="walk")
        self.dir = (kw["dx"], kw["dy"])
        self.arguments = kw

    def OnWalk(self, entity):
        if type(entity) is Player:
            currWorld.loadRegion(*self.dir)

class Region:
    def __init__(self):
        self.tiles = []
        self.entities = []
        self.decors = []
        self.path = ""

    def setPath(self, path: str):
        self.path = path

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

    def loadTerrain(self):
        self.unload()
        with open(self.path) as file:
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

    def loadEntities_FromData(self):
        with open(self.path) as file:
            data = json.load(file)
            self.loadEntities_FromMemory(data['entities'])
        return data['entities'] 
    
    def loadEntities_FromMemory(self, memory: list):
        for entity in memory:
            obj = getattr(sys.modules[__name__], getRes(ENTITY, entity[0]).className)(entity[0], *entity[1])
            if currWorld == None:
                self.entities.append(obj)
                
    def getEntitiesData(self):
        entitiesData = []
        for entity in self.entities:
            entitiesData.append([entity.res.name, (entity.x, entity.y)])

        return entitiesData


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

class World:
    def __init__(self, id=None, edit=None):
        """edit: tuple contennant path et js du monde à éditer (utilisé pour créer un res_map"""
        global currWorld
        currWorld = self

        if edit != None:
            self.res = Res_Map(*edit)
        elif id != None:
            self.res = getRes(MAP, id)
        else:
            raise Exception("Bad use of World Class")

        self.regionCoords = self.res.startPos
        self.currRegion = Region()

        self.worldMap = [[0 for i in range (10)] for i in range (10)]
        for map in resMaps:
            x, y = map.worldCoords
            self.worldMap[x][y] = map.name

        self.entitiesMemory = {}
        self.loadRegion(*self.res.startPos, fixed=True)
    
    def saveState(self):
        self.entitiesMemory[self.regionCoords.__str__()] = self.currRegion.getEntitiesData()
    
    def saveRegion(self, name: str):
        self.currRegion.save(self.res.dir + name)

    def loadRegion(self, x: int, y: int, fixed=False):
        if fixed:
            coords = (x,y)
        else:
            a, b = self.regionCoords
            coords = (a+x, b+y)

        x, y = coords

        if x > self.res.width or x < 0 or y < 0 or y > self.res.height:
            return "Coords Error"
        
        self.saveState()
        self.regionCoords = coords
        self.currRegion.setPath(self.res.dir + "Region " +  x.__str__() + " " + y.__str__() + ".data")
        self.currRegion.loadTerrain()

        if self.regionCoords.__str__() in self.entitiesMemory and not editorMode:
            self.currRegion.loadEntities_FromMemory(self.entitiesMemory)
        else:
            self.entitiesMemory[self.regionCoords.__str__()] = self.currRegion.loadEntities_FromData() 

    def changeWorld(self, world):
        pass

class GUI:
    heartFile       = "./data/gui/heart.png"
    halfHeartFile   = "./data/gui/half_heart.png"
    nothingFile     = "./data/gui/blank.png"
    coinsFile       = "./data/gui/coin.png"
    guiSize = 75

    #Constants
    F_HEART = "F_HEART"
    H_HEART = "H_HEART"
    NOTHING = "NOTHING"

    def __init__(self):
        self.img_heart      = getImage(GUI.heartFile, 100, photoimage=True)
        self.img_halfHeart  = getImage(GUI.halfHeartFile, 100, photoimage=True)
        self.img_nothing    = getImage(GUI.nothingFile, 100, photoimage=True)
        self.img_coins      = getImage(GUI.coinsFile, 100, photoimage=True)

        self.font = Font(family="Calibri", size="20")
        
        self.coins = canvas.create_image(margin, size*((caseY-1) - 0.5), image = self.img_coins)
        self.coinsLabel = Label(window, text="0", font=self.font)
        self.coinsLabel.place(x=margin + 50, y= size*((caseY-1) - 0.5))

        self.hearts = []
        self.lastHealth = 0
        for i in range(3):
            self.hearts.append(canvas.create_image(margin + i * 100, size*(caseY-0.5)))
            self.changeHeart(i, GUI.F_HEART)
        self._pendingLoop = canvas.after(tick, self.loop)
    
    def cleanUp(self):
        for id in range(self.hearts):
            canvas.delete(id)
        canvas.after_cancel(self._pendingLoop)
    
    def changeHeart(self, heartID, heartType):
        img = None
        if heartType == GUI.F_HEART:
            img = self.img_heart
        elif heartType == GUI.H_HEART:
            img = self.img_halfHeart
        elif heartType == GUI.NOTHING:
            img = self.img_nothing
        
        canvas.itemconfig(self.hearts[heartID], image=img)
    def fillHeartsTo(self, value):
        #value nombre entre 0 et 9 (3 états par coeurs)
        paire = False
        if value == 0:
            self.changeHeart(0, GUI.NOTHING)
        for i in range(6):
            currHeart = floor(i/2)
            a = value - i 
            if paire and a > 1: 
                self.changeHeart(currHeart, GUI.F_HEART)
            if not paire and a == 1:
                self.changeHeart(currHeart, GUI.H_HEART)
                if currHeart + 1 <= 2:
                    self.changeHeart(currHeart + 1, GUI.NOTHING)
                    break
            if paire:
                paire = False
            else:
                paire = True                    
    def loop(self):
        self._pendingLoop = canvas.after(tick, self.loop)
        try:
            player 
        except:
            print("[GUI] [HealthBar] Couldn't retrieve player stats ")
            return

        self.coinsLabel.config(text=player.currency.__str__())

        if self.lastHealth != player.health:
            self.lastHealth = player.health
            #La division n'est pas assez précise, on utilise le module fraction 
            const = fractions.Fraction(100, 6)
            val = player.health // const 
            val = clamp(val, 0, 6)
            self.fillHeartsTo(val)

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
    elif ressource == MAP:
        res = resMaps
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
                
def initialize(mode=False):
    global window, canvas, editorMode, margin
    editorMode = mode
    window = Tk()
    window.configure(height=HEIGHT, width=WIDTH)
    window.attributes('-fullscreen', True)
    window.geometry(WIDTH.__str__()+"x"+HEIGHT.__str__()+"+"+"300+300")
    canvas = Canvas(window)
    canvas.pack(fill=BOTH, expand=1)
    for char in ["Up", "Down", "Left", "Right"]:
        window.bind("<KeyPress-%s>" % char, arrowPressed)
        window.bind("<KeyRelease-%s>" % char, arrowReleased)

    window.protocol("WM_DELETE_WINDOW", shutdown)

    if editorMode == True:
        margin = (WIDTH - caseX*size) 
    else:
        margin = (WIDTH - caseX*size)/2
    
    initRessources()
    return (window, canvas)

def initRessources():
    tile_configs = []
    decor_configs = []
    wNames = []
    eNames = []
    dialNames = []
    

    #def retrieveFiles(path: str, files: list):
    #    for (dirpath, dirnames, filenames) in os.walk(tilesFolder):
    #        for file in filenames:
    #            if ".json" in file:
    #                tile_configs.append(file)
    #        break

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
            for (_dirpath, _dirnames, _filenames) in os.walk(mapsFolder + folder):
                for file in _filenames:
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

    for world in wNames:
        with open(mapsFolder + world + "config.json") as file:
            js = json.load(file)
            if "name" in js:
                resMaps.append(Res_Map(mapsFolder + world, js)) 
    
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

def shutdown():
    window.destroy()
    if Profiling:
        cp.disable()
        cp.print_stats(sort="cumtime")
    os._exit(1)

def Debug(event):
    breakpoint()

def arrowPressed(event):
    arrowsStatus[event.keysym] = True

def arrowReleased(event):
    arrowsStatus[event.keysym] = False

#Flèches directionnelles
arrowsStatus = {"Up": False, "Down": False, "Left": False, "Right": False}


