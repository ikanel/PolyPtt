#Implementation pf the Paging/PTT protocol according to the https://h30434.www3.hp.com/psg/attachments/psg/Desk_IP_Conference_Phones/12304/2/ea70568-audio-packet-format.pdf
import struct
import time
import uuid,subprocess
import recorder
import socket
import netifaces

MULTICAST_IP="224.0.0.251" #new multicast

IFACE = 'wlan0'  # This value for the raspberry. Change if you’re using a different interface
#IFACE = 'en0'  # This value for the macos wifi. Change if you’re using a different interface

PORT = 5001
SAMPLE_RATE = 16000
PAYLOAD_TYPE = 9  # ITU-T G.722 audio 64 kbit/s
CHANNEL = 26 #1 for ptt 26 for paging
CALLER="IGOR G KANEL"

def get_ip_addr():
    return netifaces.ifaddresses(IFACE)[netifaces.AF_INET][0]['addr']

def create_ptt_command(opCode,channel,hostSN,callerIdlength,callerId):
    command = struct.pack('!BBIB13s', opCode, channel, hostSN,callerIdlength,callerId.encode(encoding="ascii"))
    return command

def get_host_serial_number():
    # Get MAC address as an integer
    mac = uuid.getnode()
    # Convert to hex and get last 4 characters (2 bytes)
    last4 = f'{mac:012x}'[-4:]
    return int(last4,16)

def create_rtp_header(channel,hostSN,callerIdlength,callerId,timestamp):
    opCode=0x10
    codec=0x09
    flags=0
    command = struct.pack('!BBIB13sBBI', opCode, channel, hostSN, callerIdlength, callerId.encode(encoding="ascii"),codec,flags,timestamp)
    return  command

def transmit_packet(sock,header,payload=None):
   packet=header
   if payload:
         packet += payload
   result=sock.sendto(packet, (MULTICAST_IP, PORT))
   return result

def init_ptt_session(sock,channel=CHANNEL):
    for i in range(32):
        cmd=create_ptt_command(0xF, channel, get_host_serial_number(), 13, CALLER)
        time.sleep(0.030)  # Wait 30ms between packets
        transmit_packet(sock,cmd)

def send_g722_audio_package(g722_bytes,sock,channel=CHANNEL):
    # Open WAV file (must be 16kHz, mono, 8-bit mu-law for PT=0)
    TIMESTAMP = 0
    chunk_size=240
    prev_data = None

    for i in range(0, len(g722_bytes), chunk_size):
        # Main loop: send 160 samples (20ms @ 8kHz) per RTP packet
        data =g722_bytes[i:i + chunk_size]
        if not data:
            cmd=create_ptt_command(0xFF, channel, get_host_serial_number(), 13, CALLER)
            transmit_packet(sock,cmd)
            break
        header = create_rtp_header(channel, get_host_serial_number(), 13, CALLER,TIMESTAMP)
        TIMESTAMP+=chunk_size
        if prev_data:
            packet = prev_data+data
        else:
            packet = data

        transmit_packet(sock,header,packet)# Send RTP packet

        time.sleep(0.02)  # Wait 20ms
        prev_data = data


def init_sock(MCAST_GRP,MCAST_PORT,MCAST_IFACE="en0"):
    global MULTICAST_IP,PORT,IFACE,sock
    MULTICAST_IP=MCAST_GRP
    PORT=MCAST_PORT
    IFACE=MCAST_IFACE

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ttl = struct.pack('b', 100)  # Time-to-live
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
    sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(get_ip_addr()))
    return sock


def record_and_send_broadcast(MCAST_GRP,MCAST_PORT,MCAST_IFACE="en0"):

    sock=init_sock(MCAST_GRP,MCAST_PORT,MCAST_IFACE)
    rec=recorder.pcm_to_g722(recorder.record_from_mic())

    init_ptt_session(sock)
    send_g722_audio_package(rec,sock)
    print("Broadcast sent")
    sock.close()

#record_and_send_broadcast(MULTICAST_IP,PORT)