from waitress import serve
from app import app
import logging

# Configure logging to show waitress output
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    print("Starting production server on http://0.0.0.0:8080")
    serve(app, host='0.0.0.0', port=8080)
