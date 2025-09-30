#!/usr/bin/env python3
"""
FastAPI server startup script for Music Assistant V4
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8004,
        reload=True
    )