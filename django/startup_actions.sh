#!/bin/bash

cp -r /tmp/locale/ /src/
cp -r /tmp/translations/ /src/
python manage.py update_translations master.pot
django-admin makemessages -l en
django-admin makemessages -l es
django-admin makemessages -l fr
django-admin makemessages -l pt
python manage.py collectstatic --noinput
python manage.py compilemessages
python manage.py showmigrations
python manage.py migrate
if [ "$DJANGO_RUNSERVER" = "true" ]; then
    echo "Running Django development server"
    python manage.py runserver 0.0.0.0:8000
else
    echo "Running Gunicorn server"
    gunicorn tiip.wsgi:application -w 2 -b :8000 --reload --timeout 120
fi
