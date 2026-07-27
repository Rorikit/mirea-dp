#!/bin/sh
set -eu
install -d -m 700 -o 101 -g 101 /opt/mirea-dp/tls
install -m 644 -o 101 -g 101 /etc/letsencrypt/live/168.222.202.190/fullchain.pem /opt/mirea-dp/tls/fullchain.pem
install -m 600 -o 101 -g 101 /etc/letsencrypt/live/168.222.202.190/privkey.pem /opt/mirea-dp/tls/privkey.pem
cd /opt/mirea-dp
if /usr/bin/docker compose -f docker-compose.server.yml ps --status running --services | grep -qx nginx; then
  /usr/bin/docker compose -f docker-compose.server.yml exec -T nginx nginx -s reload
fi
