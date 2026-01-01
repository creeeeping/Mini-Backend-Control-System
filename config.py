from dotenv import load_dotenv
import os

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

TIME_WINDOW_SECONDS = int(os.getenv("TIME_WINDOW_SECONDS", 60))
MAX_REQUESTS = int(os.getenv("MAX_REQUESTS", 10))
