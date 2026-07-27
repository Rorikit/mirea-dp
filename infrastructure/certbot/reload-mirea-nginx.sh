#!/bin/sh
set -eu
cd /opt/mirea-dp
/usr/bin/docker compose -f docker-compose.server.yml exec -T nginx nginx -s reload
