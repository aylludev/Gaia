#!/bin/bash
cd /home/amawta/Gaia && source env/bin/activate && python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Gaia.settings')
import django
django.setup()
from django.conf import settings
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
print('DEBUG:', settings.DEBUG)
print('CSRF_TRUSTED_ORIGINS:', settings.CSRF_TRUSTED_ORIGINS)
"
