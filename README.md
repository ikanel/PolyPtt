# Send/Receive PTT/Paging Messages to/from Polycom Phones

The majority of Polycom phones have a feature called push-to-talk (PTT) or paging capability. In simple terms, PTT broadcasts audio messages to all phones connected to a specific channel. This can be used for announcements, alarms, and similar purposes. Polycom uses UDP multicast messages for broadcasting, which are not available outside the local network segment. To broadcast from outside the local network, an agent within the local network is required to accept connections from the outside world.

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

Sample NGINX config to proxy ui part and websocket server
```bash
  server {
          listen 443 ssl; # managed by Certbot
          listen [::]:443 ssl ipv6only=on; # managed by Certbot
          ssl_certificate /etc/letsencrypt/live/raspberry5.ddns.net/fullchain.pem; 
          ssl_certificate_key /etc/letsencrypt/live/raspberry5.ddns.net/privkey.pem;
          include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
          ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

          auth_basic "Protected area";
          auth_basic_user_file /etc/apache2/.htpasswd;        

          root /var/www/polyptt-ui/;

          # Add index.php to the list if you are using PHP
          index index.html index.htm index.nginx-debian.html;

          server_name _;

          location / {
                  # First attempt to serve request as file, then
                  # as directory, then fall back to displaying a 404.
                  try_files $uri $uri/ =404;
          }

      
    location /ws {
          proxy_pass http://localhost:8765;

          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_set_header Host $host;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      }

          # deny access to .htaccess files, if Apache's document root
          # concurs with nginx's one
          #
          #location ~ /\.ht {
          #       deny all;
          #}
  }


  server {
      listen 80 default_server;
      server_name _;
      return 301 https://$host$request_uri;
  }
```

_Note: Modern browsers does not allow to use microphone for the non-https connections._
You may consider using https://letsencrypt.org/ to create free ssl certs.
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
Update pttMulticast/playerconf.py with a link to the generated so/dylib library.

## Payload structure
The structure of the PTT/Paging packets is described in pttMulticast/ea70568-audio-packet-format.pdf
  
