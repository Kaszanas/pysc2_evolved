import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOGGING_FORMAT = "[%(asctime)s][%(process)d/%(thread)d][%(levelname)s][%(filename)s:%(lineno)s] - %(message)s"

# Controls the timeout for connecting to the game via websockets:
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", 60))
logging.warning(f"pysc2_evolved: TIMEOUT_SECONDS={TIMEOUT_SECONDS}")
