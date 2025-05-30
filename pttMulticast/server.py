import asyncio
import websockets
import receiver
import base64
import recorder,playerconv
from ptt_multicast import CHANNEL
from receiver import BroadcastingCompletedException
from websockets.exceptions import InvalidHandshake
from urllib.parse import urlparse, parse_qs

OUTPUT_FILE = "output.raw"
import ptt_multicast
import socket,netifaces,struct
MCAST_GRP = '224.0.0.251'
IFACE = 'en0'  # Change if you’re using a different interface
MCAST_PORT = 5002
CHANNEL=1
ws=None
isPlaying=False
recv_packets={}
VALID_USERNAME = "igor"
VALID_PASSWORD = "polycom"



def get_socket(MCAST_GRP,MCAST_PORT,IFACE="en0"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))

    iface_ip = netifaces.ifaddresses(IFACE)[netifaces.AF_INET][0]['addr']
    mreq = struct.pack('4s4s', socket.inet_aton(MCAST_GRP), socket.inet_aton(iface_ip))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    print(f"Listening on {MCAST_GRP}:{MCAST_PORT} via {IFACE} ({iface_ip})")

    return  sock
class PolycomServerProtocol:
    def connection_made(self, transport):
        self.transport = transport
        print("UDP server ready")

    def datagram_received(self, data, addr):
        print(f"Received  from {addr}")
        global isPlaying
        if isPlaying:
            return
        try:
            p = receiver.unpack_packet(data)
            if p is not None and len(p) > 0:
                seq, packet = p
                recv_packets[seq] = packet

                if len(recv_packets)*240>16384:
                    g726qi_bytes = []
                    for b in sorted(recv_packets.items()):
                        g726qi_bytes += b[1]
                    recv_packets.clear()
                    pcm_bytes=playerconv.decode_g726qi(g726qi_bytes)

                    if ws != None:
                       asyncio.run(ws.send(bytes(pcm_bytes)))
        except BroadcastingCompletedException:
            pass
        except Exception as e:
            print("Exception on UDP recv:"+e)



async def receive_and_play(websocket):
    global ws,isPlaying
    ws=websocket
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                ptt_multicast.send_g722_audio_package(recorder.pcm_to_g722(message),sock,CHANNEL)
                print(f"Saved {len(message)} bytes")
            else:
                if(message=="start_broadcast"):

                    sock = ptt_multicast.init_sock(MCAST_GRP, MCAST_PORT, IFACE)
                    ptt_multicast.init_ptt_session(sock,CHANNEL)
                    isPlaying=True
                if(message=="stop_broadcast"):
                    if sock!=None:
                        sock.close()
                    await asyncio.sleep(1.0)
                    isPlaying=False

                print(f"Ignored unknown non-binary message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("Receive task: connection closed.")


async def send_to_client(websocket,sock):
    #while True:
    loop = asyncio.get_running_loop()
    try:
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: PolycomServerProtocol(),sock=sock
        )
    except Exception as e:
        print("Exception while connecting to UDP")



async def handle_connection(websocket):
    print("WSClient connected")
    try:
        query = parse_qs(urlparse(websocket.request.path).query)
        auth = query.get("auth", [None])[0]

        if not auth:
            await websocket.close()
            return

        try:
            decoded = base64.b64decode(auth).decode()
            username, password = decoded.split(":")
            if username != VALID_USERNAME or password != VALID_PASSWORD:
                await websocket.close()
                return
        except Exception:
            await websocket.close()
            return

        sock=None
        try:
            sock=get_socket(MCAST_GRP,MCAST_PORT,IFACE)
        except Exception as e:
            print(e)
        receive_task = asyncio.create_task(receive_and_play(websocket))
        send_task = asyncio.create_task(send_to_client(websocket,sock))

        # Wait for either task to finish (likely receive finishes when client disconnects)
        done, pending = await asyncio.wait(
            [receive_task,send_task],
            return_when=asyncio.ALL_COMPLETED
        )
        for task in pending:
            task.cancel()
    except Exception as e:
        print(e)

    print("WSClient disconnected")

async def main():


    async with websockets.serve(handle_connection, "localhost", 8765):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()  # Run forever

asyncio.run(main())