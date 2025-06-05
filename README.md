# Send and Receive PTT and Paging Messages to/from Polycom Phones

This project enables two main use cases for sending and receiving Push-To-Talk (PTT) audio and Paging messages with Polycom phones:

1. **Web-based UI**: Use a Vue frontend with a Python backend to send/receive PTT audio messages to Polycom phones—either via multicast groups or direct unicast.
2. **Command-line script**: Use the `loop.py` script to accomplish the same functionality without a web interface.

---

## 🖥️ Web Frontend Setup

To use the web interface:

1. Navigate to the `ui` folder.
2. Run `npm run build` to compile the Vue project.
3. Deploy the generated build to any web server (e.g., **NGINX**, **Apache**, **IIS**).
4. Configure phone IP addresses in the `Vue.app` if necessary.

---

## ⚙️ Configuration

- Set the `MCAST_GRP` (multicast group address) and `PORT` for both the backend and frontend.
- **Important for macOS users**: macOS does not support UDP multicast outside the local subnet. As a result, the default Polycom multicast IP may not work. Use addresses like `224.0.0.251` instead.

---

## 🎧 Audio Codec Notes

Polycom SoundPoint phones (e.g., models 450 and 550) ignore codec configuration and always transmit audio as **G.726 QI** — a variant of the G.726 codec using reversed bit order in the payload.

- No native Python libraries support this format.
- This project uses the `spandsp` C library with a custom C++ wrapper.
- To build the codec module:
  ```bash
  cd g726
  cmake .
  cmake --build .
- Update pttMulticast/playerconf.py with a link to the generated so/dylib library.

## Payload structure
The structure of the PTT/Paging packets is described in pttMulticast/ea70568-audio-packet-format.pdf
  
