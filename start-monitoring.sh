#!/bin/bash

# DeckFlow 모니터링 스택 시작 스크립트
echo "🚀 Starting DeckFlow Monitoring Stack..."

# Docker Compose로 Prometheus + Grafana 시작
docker-compose -f docker-compose.monitoring.yml up -d

echo "✅ Monitoring stack started!"
echo ""
echo "📊 Access points:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000"
echo "    - Username: admin"
echo "    - Password: admin"
echo ""
echo "🔍 Your FastAPI app should be running on port 8000 to collect metrics"
echo "📈 Metrics endpoint: http://localhost:8000/metrics"
echo ""
echo "💡 To stop the monitoring stack: docker-compose -f docker-compose.monitoring.yml down"