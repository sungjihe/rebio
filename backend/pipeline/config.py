import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

RAW_DATA = os.path.join(BASE_DIR, "data", "raw")

NEO4J_URI        = os.getenv("NEO4J_URI")
NEO4J_USER       = os.getenv("NEO4J_USER")
NEO4J_PASSWORD   = os.getenv("NEO4J_PASSWORD")
