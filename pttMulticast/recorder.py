import time

import sounddevice as sd
from G722 import  G722
import numpy as np
import queue

sample_rate = 16000  # G.722 requires 16kHz
channels = 1
q = queue.Queue()

def play_g722(g722_bytes):
    pcm_data = g722_to_pcm(g722_bytes)
    pcm_array = np.frombuffer(pcm_data, dtype=np.int16)

    # Play with sounddevice
    sd.play(pcm_array, samplerate=sample_rate)
    sd.wait()

def play_PCM(pcm_data):
    # Play with sounddevice
    pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
    sd.play(pcm_array, samplerate=sample_rate)
    sd.wait()

def rec_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""

    if status:
        print(status)
    q.put(indata.copy())

stop_flag = False

def on_press(key):
    global stop_flag
    try:
        if key.name=='space':
            stop_flag = True
    except AttributeError:
        print("Press space to stop")
        pass
    return False  # stop the listener

def queue_to_bytes(q):
    return np.array([q.get() for _ in range(q.qsize())], dtype=np.int16)

def record_from_mic():
    from pynput import keyboard	
    global stop_flag
    stop_flag=False
    print('#' * 80)
    print('Press space to stop the recording')
    print('#' * 80)
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    try:
        with sd.InputStream(samplerate=sample_rate,
                            channels=channels, callback=rec_callback, dtype='int16'):
            while not stop_flag:
                time.sleep(1)
    except KeyboardInterrupt:
        print('\nRecording finished: ')
    except Exception as e:
        print("Error while recording:",e)
    listener.stop()

    print(f"Size of thr recording, bytes: {q.qsize()}")
    return queue_to_bytes(q)

def record_from_mic_with_duration(duration):
    # Step 1: Record raw PCM audio
    print("Recording...")
    recording = sd.rec(int(sample_rate*duration),samplerate=sample_rate, channels=channels, dtype='int16')
    input("Click Enter when finish")
    sd.stop()
    #sd.wait()
    print("Recording done.")
    pcm_bytes = recording.tobytes()
    return pcm_bytes


def pcm_to_g722(pcm_bytes):
    br=64000
    print(f"Encoding to G.722...{len(pcm_bytes)} bytes")
    try:
        codec = G722(sample_rate, br)
        pcm=np.frombuffer(pcm_bytes, dtype='<i2')
        g722_bytes = codec.encode(pcm)

    except Exception as e:
        print("Error encoding:",e)

    print("Encoding successful. G.722 byte array length:", len(g722_bytes))
    return g722_bytes

def g722_to_pcm(g722_bytes):
    br=64000
    print(f"Encoding from G.722...{len(g722_bytes)} bytes")
    try:
        codec = G722(sample_rate, br)
        pcm_bytes = codec.decode(g722_bytes)
    except Exception as e:
        print("Error encoding:",e)

    print("Encoding successful. PCM byte array length:", len(pcm_bytes))
    return pcm_bytes

#play_g722(pcm_to_g722(record_from_mic()))
