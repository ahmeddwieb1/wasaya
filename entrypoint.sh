#!/bin/bash
echo "=== Starting entrypoint script ==="
echo "=== Starting sleep ==="
sleep 15
echo "=== Running migrations ==="
alembic upgrade head

echo "=== Starting application ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000