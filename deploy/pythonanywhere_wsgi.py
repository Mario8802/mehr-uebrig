"""Copy into the WSGI file selected on PythonAnywhere's Web tab.

Use the configured virtualenv with the same Python version. The PostgreSQL
server must be version 14 or newer for Django 5.2. See docs/DEPLOYMENT.md.
"""
import os
import sys
from pathlib import Path

project = Path.home() / 'mehr-uebrig'
sys.path.insert(0, str(project))
from dotenv import load_dotenv
load_dotenv(project / '.env', override=False)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
