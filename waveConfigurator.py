#!/usr/bin/env python3
import sys
import os
import threading
import time

args = sys.argv
directory = ""#directory to use

fileTxt = open("{}/waveSettings".format(directory), "r").read()
oldFile = fileTxt
fileTxt = fileTxt.split("\n")
fileTxt = [i for i in fileTxt if i != ""]
fileTxt = {i.split(" = ")[0]: eval(i.split(" = ")[1]) for i in fileTxt}
failed = False

args.pop(0)

#restarts wave effect
def resetWave():
    global failed
    os.system("kill -9 `ps aux | grep wave.py | grep -v grep | awk '{print $2}'` > /dev/null 2>&1")
    time.sleep(0.01)
    failed = True
    os.system("python3 {}/wave.py".format(directory))

#do options
if(len(args) > 0):
    if(args[0] == "--list" or args[0] == "-l"):
        print("The options are:\n{}".format("\n".join([k for k, v in fileTxt.items()])))
        failed = True
    elif(args[0] in ["-{}".format(i) for i in fileTxt] or args[0] in [i for i in fileTxt]):
        if(len(args) > 1):
            val = eval(str(fileTxt[args[0].replace("-", "")]))
            try:
                if(type(eval(args[1])) == type(val)):
                    print("Changed {}: {} to {}: {}".format(args[0].replace("-", ""), val, args[0].replace("-", ""), args[1]))
                    newFile = []
                    for k, v in fileTxt.items():
                        if(k == args[0].replace("-", "")):
                            newFile.append("{} = {}".format(k, args[1]))
                        else:
                            newFile.append("{} = {}".format(k, v))
                    newFile = "\n\n".join(newFile)
                    with open("{}/waveSettings".format(directory), 'w') as filetowrite:
                        filetowrite.write(newFile)
                    threading.Thread(target=resetWave).start()
                else:
                    print("You must use a", type(val).__name__)
                    failed = True
            except (SyntaxError, NameError, TypeError, ZeroDivisionError):
                print("You must use a", type(val).__name__)
                failed = True
        else:
            print("You must use the command like -hue 0.64 do waveconf --list to list options")
            failed = True
    else:
        print("You must use the command like -hue 0.64 do waveconf --list to list options")
        failed = True
else:
    print("You must use the command like -hue 0.64 do waveconf --list to list options")
    failed = True

while True:
    if(failed == True):
        os._exit(0)
    time.sleep(1 / 60)