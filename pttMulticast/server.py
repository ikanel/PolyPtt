import asyncio
import websockets
import receiver
import recorder,playerconv
from receiver import BroadcastingCompletedException
import ptt_multicast
import socket,netifaces,struct
import re
from connectionSettings import MCAST_GRP,IFACE,MCAST_PORT,CHANNEL
wsClients = set()

isPlaying=False
recv_packets={}

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
                print(f"received {len(recv_packets)} packets")

                if len(recv_packets)*240>10000:
                    g726qi_bytes = []
                    for b in sorted(recv_packets.items()):
                        g726qi_bytes += b[1]
                    recv_packets.clear()
                    pcm_bytes=playerconv.decode_g726qi(g726qi_bytes)


                    for ws in wsClients:
                        try:
                            asyncio.create_task(ws.send(bytes(pcm_bytes)))
                        except Exception as e:
                            print(f"got an exception {e} trying to send message to ws. Removing the client from the connection pools")
                            wsClients.remove(ws)

        except BroadcastingCompletedException:
            print("Broadcasting completed")
        except Exception as e:
            print("Exception on UDP recv:"+e)



async def receive_and_play(websocket):
    global isPlaying,CHANNEL
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                if 'sock' in locals():
                    ptt_multicast.send_g722_audio_package(recorder.pcm_to_g722(message),sock,CHANNEL)
                    print(f"Saved {len(message)} bytes")
                else:
                    print("Payload not sent sock is not initialized")
            else:
                if "start_broadcast" in message:
                    match = re.search(r"channel:(\d{1,2})", message)
                    if match:
                        CHANNEL = int(match.group(1))
                    match = re.search(r"target:(\d{1,3}(?:\.\d{1,3}){3}):(\d+)", message)
                    if match:
                        trg_grp = match.group(1)
                        trg_port = int(match.group(2))
                        print(f"Broadcasting target: IP: {trg_grp}, Port: {trg_port}")
                    else:
                        trg_grp=MCAST_GRP
                        trg_port=MCAST_PORT

                    print(f"Broadcasting target: IP: {trg_grp}, Port: {trg_port} Channel: {CHANNEL}")


                    sock = ptt_multicast.init_sock(trg_grp, trg_port, IFACE)
                    ptt_multicast.init_ptt_session(sock,CHANNEL)
                    isPlaying=True
                if(message=="stop_broadcast"):
                    if 'sock' in locals() and sock!=None:
                        sock.close()
                        sock=None
                    await asyncio.sleep(1.0)
                    isPlaying=False

                print(f"Ignored unknown non-binary message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("Receive task: connection closed.")


async def send_to_client():
    loop = asyncio.get_running_loop()
    sock = None
    try:
        sock = get_socket(MCAST_GRP, MCAST_PORT, IFACE)
    except Exception as e:
        print(f"Cannot create a socket"+e)

    try:
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: PolycomServerProtocol(),sock=sock
        )
    except Exception as e:
        print(f"Exception while connecting to UDP:{e}")



async def handle_connection(websocket):
    print("WSClient connected")
    try:

        wsClients.add(websocket)
        receive_task = asyncio.create_task(receive_and_play(websocket))
        # Wait for either task to finish (likely receive finishes when client disconnects)
        await receive_task
        wsClients.remove(websocket)

    except Exception as e:
        print(e)

    print("WSClient disconnected")

async def main():
    async with  websockets.serve(handle_connection, "0.0.0.0", 8765):
        print("WebSocket server started at ws://localhost:8765")
        asyncio.create_task(send_to_client())
        await asyncio.Future()  # Run forever





asyncio.run(main())
