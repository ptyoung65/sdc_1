#!/bin/bash

set -e

echo "Starting SDC Application..."

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"

# Wait for Milvus
echo "Waiting for Milvus..."
while ! nc -z milvus 19530; do
  sleep 1
done
echo "Milvus is ready!"

# Wait for Elasticsearch
echo "Waiting for Elasticsearch..."
while ! curl -s http://elasticsearch:9200/_cluster/health > /dev/null; do
  sleep 1
done
echo "Elasticsearch is ready!"

# Run database migrations
echo "Running database migrations..."
cd /app/backend
alembic upgrade head

# Initialize search indexes
echo "Initializing search indexes..."
python -c "
from app.core.database import get_db
from app.core.database.hybrid_search import HybridSearchService
import asyncio

async def init_indexes():
    service = HybridSearchService()
    await service.vector_client.create_collection('documents', dimension=768)
    await service.vector_client.create_collection('chunks', dimension=768)
    await service.search_client.create_index('documents')
    await service.search_client.create_index('chunks')
    print('Indexes initialized')

asyncio.run(init_indexes())
" || echo "Indexes already exist or initialization skipped"

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4