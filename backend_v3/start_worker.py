#!/usr/bin/env python3
"""
Start script for Music Assistant Backend V3 Celery worker.
"""

import os
import sys

if __name__ == "__main__":
    os.execvp("celery", [
        "celery",
        "-A", "app.celery_app",
        "worker",
        "--loglevel=info"
    ])