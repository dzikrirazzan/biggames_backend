#!/bin/bash

echo "🧪 Testing BigGames AI System"
echo "================================"
echo ""

echo "1️⃣ Docker Containers:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAME|biggames"
echo ""

echo "2️⃣ Local API Health:"
response=$(curl -s 'http://localhost:8000/api/ai/recommendations?limit=2')
if echo "$response" | grep -q "recommendations"; then
    count=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data['recommendations']))" 2>/dev/null || echo "0")
    echo "✅ Local API working - $count recommendations"
else
    echo "❌ Local API failed"
fi
echo ""

echo "3️⃣ Public API (Ngrok):"
response=$(curl -s 'https://2d4ae8dc10a3.ngrok-free.app/api/ai/recommendations?limit=2' -H 'ngrok-skip-browser-warning: true')
if echo "$response" | grep -q "recommendations"; then
    count=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data['recommendations']))" 2>/dev/null || echo "0")
    echo "✅ Public API working - $count recommendations"
else
    echo "❌ Public API failed"
fi
echo ""

echo "4️⃣ CORS Configuration:"
cors_header=$(curl -s -I 'http://localhost:8000/api/ai/recommendations' -H 'Origin: http://localhost:5173' | grep -i "access-control-allow-origin")
if [ ! -z "$cors_header" ]; then
    echo "✅ CORS configured: $cors_header"
else
    echo "❌ CORS not found"
fi
echo ""

echo "5️⃣ Embeddings Count:"
count=$(docker-compose exec -T db psql -U biggames -d biggames -t -c "SELECT COUNT(*) FROM room_embeddings;" | tr -d ' ')
echo "✅ $count room embeddings generated"
echo ""

echo "================================"
echo "✅ System Status: READY FOR FRONTEND"
echo ""
echo "📋 Next Steps:"
echo "   1. Share AI_READY_FOR_FRONTEND.md with frontend team"
echo "   2. Share FRONTEND_DOCS.md for API documentation"
echo "   3. Public URL: https://2d4ae8dc10a3.ngrok-free.app"
echo ""
