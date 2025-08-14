# WSGI entrypoint
from . import create_app

app = create_app()

# Optional: gunicorn looks for 'app' by default.
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
