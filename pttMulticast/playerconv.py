import math

import sounddevice as sd
import numpy as np
import ctypes
import os

def run_g726_decoder(inputBytes):
    # Load the library
    lib = ctypes.CDLL(os.path.abspath("../g726/cmake-build-debug/libg726.dylib"))  # Adjust for OS
    # Set function signature
    lib.decodeFromByteArray.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_int16),
        ctypes.c_uint16,
        ctypes.c_uint8,
        ctypes.c_uint8,
        ctypes.c_int
    ]
    lib.decodeFromByteArray.restype = ctypes.c_int16
    max_packet_size=9000

    output_size = max_packet_size * 4

    output_type = ctypes.c_int16 * output_size


    packets=math.ceil(len(inputBytes)/max_packet_size)

    result=[]

    for p in range(packets):
        input_data = bytes(inputBytes)[p*max_packet_size:(p+1)*max_packet_size]
        input_size = len(input_data)
        input_data_ptr_type = ctypes.c_uint8 * input_size
        input_data_ptr = input_data_ptr_type(*input_data)
        output = output_type()
        samples_encoded=lib.decodeFromByteArray(input_data_ptr,output,input_size,0,1,24000)
        result.append(output[:samples_encoded])

    return np.ctypeslib.as_array([item for sublist in result for item in sublist]).astype(np.int16)


def reverse_bits(byte):
    return int('{:08b}'.format(byte)[::-1], 2)


def decode_and_play(g726qi_data):
    standard_g726 = bytes(reverse_bits(b) for b in g726qi_data)
    decoded = run_g726_decoder(standard_g726)
    sd.play(decoded, 8000)
    sd.wait()

def convert_phone_file():
    # Load your G.726QI file
    with open("phone", "rb") as infile:
        qi_data = infile.read()

    # Reverse each byte
    standard_g726 = bytes(reverse_bits(b) for b in qi_data)

    decoded=run_g726_decoder(standard_g726)
    print(decoded)

    #data = np.frombuffer(decoded, dtype=np.int16)
    sd.play(decoded, 8000)
    sd.wait()

    # Save to new file
    with open("phone.g726", "wb") as outfile:
        outfile.write(standard_g726)

def play_sounds():
    for j in [24]:
        for i in range(4,5):
            fn=f"phone_{j}_{i}.pcm"
            print(fn)
            sd.default.channels=1
            with open(fn, "rb") as infile:
                qi_data = infile.read()
                data = np.frombuffer(qi_data, dtype=np.int16)
                sd.play(data, 8000)
                sd.wait()
#convert_phone_file()
#play_sounds()