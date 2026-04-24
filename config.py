import os
from dotenv import load_dotenv

# Load credentials from bg_key.env in the parent directory
load_dotenv("/Users/leoinv/Documents/CODE/bg_key.env")

BASE_URL = "https://api.bitget.com"

API_KEY = os.getenv("API_KEY", "")
API_SECRET = os.getenv("API_SECRET", "")
PASSPHRASE = os.getenv("PASSPHRASE", "")

DEFAULT_LIMIT = 200
PAGE_SIZE = 20
