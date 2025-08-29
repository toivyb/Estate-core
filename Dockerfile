WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Put the code inside a proper package directory
COPY . /app/estatecore_backend

# Ensure this is the command (in Dockerfile CMD or fly.toml [processes])
# CMD ["gunicorn", "-b", "0.0.0.0:8080", "estatecore_backend:create_app()"]
