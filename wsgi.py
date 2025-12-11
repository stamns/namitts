"""
WSGI wrapper for Vercel deployment
This ensures the Flask app is properly configured for serverless environments
"""
import os
import sys

# Ensure PYTHONUNBUFFERED is set for proper logging
os.environ.setdefault('PYTHONUNBUFFERED', '1')

try:
    from app import app
except ImportError as e:
    print(f"ERROR: Failed to import app: {e}", file=sys.stderr)
    raise

# Vercel expects the WSGI application to be called 'app'
__all__ = ['app']
