#!/usr/bin/env bash
# Render Build Script for Council Workspace System
# Render calls this automatically on every deployment.
set -o errexit  # Exit immediately if any command fails

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Collect all static files into /staticfiles/ (served by WhiteNoise)
python manage.py collectstatic --no-input

# 3. Apply all database migrations
python manage.py migrate

# 4. Seed canonical departments and council memo templates (idempotent — safe to re-run)
python manage.py seed_test_data
