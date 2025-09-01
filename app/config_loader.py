
import os
from dotenv import load_dotenv
from estatecore_backend.config import Config

def load_config(app):
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(env_path, override=True)
    app.config.from_object(Config)
