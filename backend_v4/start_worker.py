#!/usr/bin/env python3
"""
Celery worker startup script for Music Assistant V4
"""

import sys
from app.celery_app import celery_app

if __name__ == "__main__":
    sys.exit(celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--pool=solo"
    ]))