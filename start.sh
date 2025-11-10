#!/bin/bash
# Run database migrations
python -m flask db upgrade

# Start the application with gunicorn
# Railway automatically sets PORT environment variable
gunicorn run:app --bind 0.0.0.0:${PORT:-8000}
