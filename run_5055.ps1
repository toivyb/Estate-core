$env:DATABASE_URL = "postgresql+psycopg2://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/estatecore_dev"
$env:FLASK_APP    = "estatecore_backend.app"
$env:FLASK_ENV    = "production"
python -m flask run --port=5055
