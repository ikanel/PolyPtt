import receiver
import threading
import time
from pynput import keyboard
from ptt_multicast import record_and_send_broadcast
import  receiver
MCAST_GRP = '224.0.0.251'
IFACE = 'en0'  # Change if you’re using a different interface
MCAST_PORT = 5002

current_task="Listen"

def on_press2(key):
    global current_task
    #while not stop_event.is_set():
    try:
        if key.char=='b':
            print("Switching to Broadcasting mode")
            current_task="Broadcast"
        elif key.char=='r':
            print("Switching to Listening mode")
            current_task="Listen"
        elif key.char=='q':
            print("Quiting")
            current_task="Quit"
    except AttributeError:
        print("Unsupported command: use only b for broadcast and r for listening")

listener = keyboard.Listener(on_press=on_press2)
listener.start()

print("Click B to start broadcast, Q for exit. All other time system is in listening mode")


while current_task!="Quit":
    if current_task=="Broadcast":
        receiver.release_sock()
        record_and_send_broadcast(MCAST_GRP, MCAST_PORT)
        current_task="Listen"
        print("Back to Listening mode")
    elif current_task=="Listen":
        receiver.wait_for_broadcast(MCAST_GRP, MCAST_PORT)





