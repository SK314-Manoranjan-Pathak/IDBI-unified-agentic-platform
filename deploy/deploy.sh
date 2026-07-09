#!/bin/bash
# deploy.sh — Quick redeploy on EC2 (run via SSM session or cron).
# Pulls latest code, rebuilds frontend, restarts all services.

set -e
cd /opt/idbi-platform

echo "=== Pulling latest code ==="
git pull origin main

echo "=== Updating Python dependencies ==="
source venv/bin/activate
pip install -r requirements.txt --quiet

echo "=== Rebuilding frontend ==="
cd frontend
npm install --production=false
npm run build
cd ..

echo "=== Restarting services ==="
pm2 restart all
sudo systemctl restart idbi-backend

echo "=== Verifying health ==="
sleep 5
curl -s http://localhost:8000/health
echo ""
curl -s -o /dev/null -w "Frontend: HTTP %{http_code}\n" http://localhost:3000

echo "=== Redeploy complete ==="
