#!/usr/bin/env python3
from openrazer.client import constants as razer_constants
from openrazer.client import DeviceManager
from pynput.keyboard import Key, Listener
from collections import defaultdict
from distutils import util as distutils
import colorsys
import random
import os
import time
import threading
import json
import glob
from itertools import cycle

settings = open("{}/waveSettings".format(os.path.dirname(os.path.realpath(__file__))), "r").read().split("\n")
settings = [i for i in settings if len(i) > 0]
settings = {i.split(" = ")[0]: i.split(" = ")[1] for i in settings}

quit = False
ledBases = {}
basehue = float(settings["basehue"])
maxHue = float(settings["maxhue"])
colorStep = float(settings["colorstep"])
backStep = float(settings["colorbackstep"])
isRev = bool(distutils.strtobool(settings["backwards"]))
doWorkspace = bool(distutils.strtobool(settings["showWorkspace"]))
doReset = bool(distutils.strtobool(settings["doResetOnScriptChange"]))
doVM = bool(distutils.strtobool(settings["checkVM"]))
speed = float(settings["speed"])
watchConfig = bool(distutils.strtobool(settings["watchConfig"]))
devices = [i for i in DeviceManager().devices if i is not i.type == "keyboard"]
mouse = [i for i in DeviceManager().devices if i is not i.type == "mouse"][0]
rows = {1: [0,1,2,3,4,5],2: [1,2,3,4,5],3: [0,1,2,3,4,5],4: [0,1,2,3,4,5],5: [0,1,2,3,4,5],6: [0,1,2,3,4,5],7: [0,1,2,3,4,5],8: [0,1,2,3,4,5],20: [0], 9: [0,1,2,3,4,5],10: [0,1,2,3,4,5],11: [0,1,2,3,4,5],12: [0,1,2,3,4,5],13: [0,1,2,3,4,5],14: [0,1,2,3,4,5],15: [0,1,2,5],16: [0,1,2,4,5],17: [0,1,2,5], "mouse": [0,1]}
ledColors = {}
ledMaxs = {}
ledSteps = {}
ledBackSteps = {}
scrlPressed = False
canScrlPress = True
vmOn = False
ignored = []
hueList = {}
threads = []
reversedList = {}

#change color on scrl lk press for barrier (synergy) mouse lock status
def on_press(key):
    global scrlPressed,ignored
    if key == Key.scroll_lock:
        if scrlPressed and canScrlPress == True:
            scrlPressed = False
            if(vmOn == False and doVM == True):
                devices[0].fx.advanced.matrix[0, 16] = (25,0,0)
                if([0, 16] not in ignored):
                    ignored.append([0, 16])
            else:
                devices[0].fx.advanced.matrix[0, 16] = tuple(map(lambda x: int(256 * x), colorsys.hsv_to_rgb(ledColors[(16, 0)], 1, 0.5)))
                if([0, 16] in ignored):
                    ignored = [i for i in ignored if i != [0, 16]]
        elif(scrlPressed == False and canScrlPress == True):
            scrlPressed = True
            devices[0].fx.advanced.matrix[0, 16] = (255,255,255)
            if([0, 16] not in ignored):
                ignored.append([0, 16])

#change hue for every key 
def rowCycler(device):
    global reversedList,ignored,basehue,colorStep,ledMaxs,ledColors
    for _ in cycle([0]):
        for row in rows:
            for i in rows[row]:
                #set colour of each key
                if(row == "mouse"):
                    ledHue = ledColors[(row, i)]
                    if [i, row] not in ignored:
                        mouse.fx.advanced.matrix[0, i] = tuple(map(lambda x: int(256 * x), colorsys.hsv_to_rgb(ledHue, 1, 0.5)))
                else:
                    ledHue = ledColors[(row, i)]
                    if [i, row] not in ignored:
                        device.fx.advanced.matrix[i, row] = tuple(map(lambda x: int(256 * x), colorsys.hsv_to_rgb(ledHue, 1, 0.5)))
                #change the next colour of the key hue
                if(reversedList[(row, i)] == False):
                    if(ledHue + ledSteps[(row, i)] > ledMaxs[(row, i)]):
                        ledColors[(row, i)] = ledMaxs[(row, i)]
                        ledColors[(row, i)] -= ledBackSteps[(row, i)]
                        reversedList[(row, i)] = True
                    else:
                        ledColors[(row, i)] += ledSteps[(row, i)]
                else:
                    if(ledHue - ledSteps[(row, i)] < ledBases[(row, i)]):
                        ledColors[(row, i)] = ledBases[(row, i)]
                        ledColors[(row, i)] += ledSteps[(row, i)]
                        reversedList[(row, i)] = False
                    else:
                        ledColors[(row, i)] -= ledBackSteps[(row, i)]

        time.sleep(speed)

#initialize
def wave_effect(device):
    device.fx.advanced.matrix.reset()
    mouse.fx.advanced.matrix.reset()

    global speed,basehue,rows,isRev,colorStep,ledMaxs,scrlPressed,vmOn,canScrlPress,ignored

    hue = basehue

    rowL = rows.items()

    if(isRev == True):
        rowL = reversed(rows.items()) 

    #change the initial colours for each key
    for row, v in rowL:
        for i in v:
            if(row == "mouse"):
                if((row, i) in ledColors and (row, i) in ledSteps and (row, i) in ledBackSteps and (row, i) in ledMaxs):
                    if [i, row] not in ignored:
                        mouse.fx.advanced.matrix[0, i] = tuple(map(lambda x: int(256 * x), colorsys.hsv_to_rgb(ledColors[(1, i)], 1, 0.4)))
                    hueList[(row, i)] = ledColors[(row, i)]
                    reversedList[(row, i)] = False
                    ledBases[(row, i)] = ledColors[(row, i)]
                else:
                    if [i, row] not in ignored:
                        mouse.fx.advanced.matrix[0, i] = tuple(map(lambda x: int(256 * x), colorsys.hsv_to_rgb(hue, 1, 0.4)))
                    hueList[(row, i)] = hue
                    reversedList[(row, i)] = False
                    ledColors[(row, i)] = hue
                    ledMaxs[(row, i)] = maxHue
                    ledSteps[(row, i)] = colorStep
                    ledBackSteps[(row, i)] = backStep
                    ledBases[(row, i)] = basehue
            elif((row, i) in ledColors and (row, i) in ledSteps and (row, i) in ledBackSteps and (row, i) in ledMaxs):
                if [i, row] not in ignored:
                    device.fx.advanced.matrix[i, row] = tuple(map(lambda x: int(256 * x), colorsys.hsv_to_rgb(ledColors[(row, i)], 1, 0.4)))
                hueList[(row, i)] = ledColors[(row, i)]
                reversedList[(row, i)] = False
                ledBases[(row, i)] = ledColors[(row, i)]
            else:
                if [i, row] not in ignored:
                    device.fx.advanced.matrix[i, row] = tuple(map(lambda x: int(256 * x), colorsys.hsv_to_rgb(hue, 1, 0.4)))
                hueList[(row, i)] = hue
                reversedList[(row, i)] = False
                ledColors[(row, i)] = hue
                ledMaxs[(row, i)] = maxHue
                ledSteps[(row, i)] = colorStep
                ledBackSteps[(row, i)] = backStep
                ledBases[(row, i)] = basehue
            
        hue += colorStep

    t = threading.Thread(target=rowCycler, args=(device, ))
    t.start()
    threads.append(t)

    if(doWorkspace == False and doVM == False):
        with Listener (on_press=on_press) as listener: 
            threads.append(listener)
            listener.join()
    else:
        t3 = threading.Thread(target=keyboardListen)
        t3.start()
        threads.append(t3)

        prevVMState = ""
        prevWorkspace = ""

        for _ in cycle([0]):
            if (quit == True or doWorkspace == False and doVM == False):
                break

            if(doWorkspace == True):
                workspaceS = int(os.popen("xdotool get_desktop").readline(1)) + 2
                if(prevWorkspace != workspaceS):
                    if [1, workspaceS] not in ignored:
                        if(len(ignored) <= 0):
                            ignored.append([1, workspaceS])
                        else:
                            ignored = [[1, workspaceS] for i in ignored if i == [1, prevWorkspace]]
                        device.fx.advanced.matrix[1, workspaceS] = (255,255,255)
                    prevWorkspace = workspaceS

            #get vm status for scrl lk colour
            if(doVM == True):
                #this is unsafe but ignore
                vmS = os.popen("echo {} | sudo -S virsh list --all | grep \" win10 \" | awk '{{ print $3}}'".format(open("{}/password".format(os.path.dirname(os.path.realpath(__file__)))).read())).readline(1)
                if(prevVMState != vmS):
                    if(vmS == "s"):
                        if([0, 16] not in ignored):
                            ignored.append([0, 16])
                        canScrlPress = False
                        vmOn = False
                        device.fx.advanced.matrix[0, 16] = (25, 0, 0)
                    else:
                        vmOn = True
                        canScrlPress = True
                        if([0, 16] in ignored):
                            ignored = [i for i in ignored if i != [0, 16]]
                prevVMState = vmS
                
            time.sleep(1)

#watch for scroll lock press if enabled
def keyboardListen(): 
    Listener(on_press=on_press).start()

restartF = False

#watch for file changes on config or script change if enabled
def fileWatcher():
    global restartF
    waveFileModified = os.stat("{}/wave.py".format(os.path.dirname(os.path.realpath(__file__)))).st_mtime
    settingsFileModified = os.stat("{}/waveSettings".format(os.path.dirname(os.path.realpath(__file__)))).st_mtime
    
    for _ in cycle([0]):
        if(os.stat("{}/waveSettings".format(os.path.dirname(os.path.realpath(__file__)))).st_mtime != settingsFileModified):
            restartF = True
            os.system('python3 {}/wave.py'.format(os.path.dirname(os.path.realpath(__file__))))
        if(doReset == True and os.stat("{}/wave.py".format(os.path.dirname(os.path.realpath(__file__)))).st_mtime != waveFileModified):
            restartF = True
            os.system('python3 {}/wave.py'.format(os.path.dirname(os.path.realpath(__file__))))
        time.sleep(10)

#start draw loop 
try:
    t = threading.Thread(target=wave_effect, args=(devices[0], ), daemon=True)
    t.start()
    threads.append(t)

    if(watchConfig == True or doReset == True):
        t2 = threading.Thread(target=fileWatcher)
        t2.start()
        threads.append(t2)

    for _ in cycle([0]):
        if(restartF == True):
            os._exit(0)
        devices[0].fx.advanced.draw()
        mouse.fx.advanced.draw()
        time.sleep(1 / 60)
except (KeyboardInterrupt, Exception) as e:
    quit = True
    devices[0].fx.wave(2)