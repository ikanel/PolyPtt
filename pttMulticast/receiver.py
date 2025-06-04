import socket
import struct
import netifaces
import playerconv
MCAST_GRP = '224.0.0.251'

IFACE = 'en0'  # Change if you’re using a different interface
#IFACE = 'wlan0'  # Value for the Raspberry pi

MCAST_PORT = 5001

sock=None
playing=False
class BroadcastingCompletedException(Exception):
    pass

audio_packet_size={0:240,0x9:240,0xFD:90}
recv_packets={}

def unpack_packet(packed_data):

    unpacked=struct.unpack('!BBIB13s',packed_data[0:20])
    opCode, channel, hostSN, callerIdlength, callerId = unpacked

    if opCode==0xF:
        print("Init transmission")
    elif opCode==0xFF:
        print("End transmission")
        raise BroadcastingCompletedException("End of transmission")
    elif opCode==0x10:
        print("Send audio")

    print("Channel:",channel)
    print("host:",hostSN)
    print(f"callerId: {callerId} [{callerIdlength}] bytes")

    if len(packed_data)<=20:
        return None
    packed_data=packed_data[20:]

    unpacked=struct.unpack('!BBI', packed_data[0:6])
    codec, flags, timestamp = unpacked
    if codec==0x09:
        print("Codec G722")
    elif codec==0:
        print("G.711µ")
    elif codec==0xFD:
        print("Codec G.726QI")
    else:
        print(f"Unknown codec: {codec} cannot continue")
        return None
    print(f"sequence number:{timestamp}")
    packed_data=packed_data[6:]
    if len(packed_data)==0:
        return None

    if len(packed_data)>audio_packet_size[codec]:
        print("skipping first redundant packet: "+''.join('0x{:02X} '.format(x) for x in packed_data[:audio_packet_size[codec]]))

        packed_data=packed_data[audio_packet_size[codec]:]
    if len(packed_data)>0:
        print('Payload as bytes array: '+''.join('0x{:02X} '.format(x) for x in packed_data))
        return  timestamp,packed_data

def get_socket(MCAST_GRP,MCAST_PORT,IFACE="en0"):
    global sock
    if sock is not None:
        return
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))

    iface_ip = netifaces.ifaddresses(IFACE)[netifaces.AF_INET][0]['addr']
    mreq = struct.pack('4s4s', socket.inet_aton(MCAST_GRP), socket.inet_aton(iface_ip))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.settimeout(1.0)
    print(f"Listening on {MCAST_GRP}:{MCAST_PORT} via {IFACE} ({iface_ip})")

    return  sock

def release_sock():
    global sock
    if sock is None:
        return

    # Close the socket, unbinding it from the address and port
    sock.close()
    sock=None

def wait_for_broadcast(MCAST_GRP,MCAST_PORT,IFACE="en0"):
    global playing
    if playing:
        return
    # Create UDP socket
    get_socket(MCAST_GRP,MCAST_PORT,IFACE)
    try:
        data, addr = sock.recvfrom(1024*500)
        if addr[1] == MCAST_PORT:
            p=unpack_packet(data)
            if p is not None:
                seq,packet=p
                recv_packets[seq]=packet
    except KeyboardInterrupt:
        print("Stopping waiting for the broadcast because of the keyboard interrupt.")

    except BroadcastingCompletedException as e:
        if len(recv_packets)>0 and not playing:
            playing=True
            print("transfer completed. Decoding and playing")
            g726qi_bytes=[]
            for b in sorted(recv_packets.items()):
                g726qi_bytes+=b[1]
            recv_packets.clear()
            playerconv.decode_and_play(g726qi_bytes)
            playing=False
            return True
    except TimeoutError as e:
        pass
        #print ("Restart waitingi")

#while True:
#    wait_for_broadcast(MCAST_GRP, MCAST_PORT)
