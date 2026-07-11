#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
celery -A app.core.celery_app flower \
  --port=5555 \
  --url_prefix=flower
