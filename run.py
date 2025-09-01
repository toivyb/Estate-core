from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if not in .env
    app.run(host="0.0.0.0", port=port)
