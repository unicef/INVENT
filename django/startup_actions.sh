#!/bin/bash

python manage.py update_translations master.pot
django-admin makemessages -l en
django-admin makemessages -l es
django-admin makemessages -l fr
django-admin makemessages -l pt
python manage.py compilemessages
gunicorn tiip.wsgi:application -w 2 -b :8000 --reload --timeout 120