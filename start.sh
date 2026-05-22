#!/bin/bash
unset all_proxy HTTP_PROXY HTTPS_PROXY
cd "$(dirname "$0")"
source venv/bin/activate
exec uvicorn app.main:app --host 0.0.0.0 --port 9271
