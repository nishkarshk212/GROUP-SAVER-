# Bot Configuration
API_ID = 33830507  # Get from my.telegram.org
API_HASH ="54e1e0d86c6c2768b65dc945bb2096c7"  # Get from my.telegram.org
BOT_TOKEN = "8587720230:AAEHakInRNby8me1WtxsoQ_JUbhTJAVJL6s"  # From @BotFather

# NSFW Detection Settings
NSFW_THRESHOLD = 0.7
AGE_RESTRICTION_YEARS = 18

# Processing Settings
MAX_FILE_SIZE_MB = 50
FRAME_SAMPLE_RATE = 5  # Process every Nth frame
GIF_FRAME_SAMPLE = 4

# Redis Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Paths
TEMP_DIR = "temp"
LOGS_DIR = "logs"

# Ensure directories exist
import os
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
