import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "saerix:latest")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
NUM_CTX = int(os.getenv("NUM_CTX", "16384"))
WORKSPACE = os.getenv("WORKSPACE", ".")