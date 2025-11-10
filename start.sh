#!/bin/bash
# Run database migrations
flask db upgrade

# Start the application with gunicorn
gunicorn run:app --bind 0.0.0.0:$PORT
