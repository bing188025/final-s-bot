# =============================================================
#  Discord Welcome Bot — Configuration
# =============================================================
#  Secrets are loaded from the .env file.
#  Copy .env.example to .env and fill in your values.
# =============================================================

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
WELCOME_CHANNEL_ID = int(os.environ["WELCOME_CHANNEL_ID"])
