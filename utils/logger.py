import logging
from pathlib import Path

from utils.helppers import user_data_path

LOG_FILE = Path(user_data_path("app.log"))
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def get_logger(name):
    logging.basicConfig(
        filename=str(LOG_FILE),
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    return logging.getLogger(name)
