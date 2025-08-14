"""
Entry point for running the payment‑based access control Flask application.

To start the development server, run this file with Python.  The application
will listen on port 5000 by default and will use the database configured in
`app/config.py`.
"""

from estatecore_backend import create_app

app = create_app()

if __name__ == "__main__":
    # Enable debug mode for development; remove or adjust for production.
    app.run(debug=True, host="0.0.0.0")