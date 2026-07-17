"""
WSGI entrypoint for production servers (Gunicorn, Waitress, uWSGI, etc.).

  gunicorn -c gunicorn.conf.py wsgi:app
  waitress-serve --listen=0.0.0.0:8000 wsgi:app
"""

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app()
