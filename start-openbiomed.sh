#!/bin/bash
# OpenBioMed 启动脚本
# 1. 启动 compose 服务
# 2. 连接容器到默认 bridge 网络（解决外网路由问题）

COMPOSE_FILE="docker-compose.openbiomed.yaml"

echo "Starting OpenBioMed services..."
docker compose -f "$COMPOSE_FILE" up -d

echo "Connecting containers to default bridge network for external access..."
docker network connect bridge openbiomed-web 2>/dev/null || echo "openbiomed-web already on bridge"
docker network connect bridge searxng 2>/dev/null || echo "searxng already on bridge"

# Restart SearXNG so it picks up the new network route
echo "Restarting SearXNG to apply network changes..."
docker restart searxng

# Re-connect after restart (container may have lost secondary network)
sleep 3
docker network connect bridge searxng 2>/dev/null || true

echo "OpenBioMed services started and connected to external network"
echo "  OpenBioMed UI: http://localhost:3001"
echo "  SearXNG:       http://localhost:9090"