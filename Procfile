# web: python manage.py runserver 0.0.0.0:$PORT
# web: daphne tcx.asgi:application --port $PORT --bind 0.0.0.0 -v2
web: gunicorn tcx.wsgi
