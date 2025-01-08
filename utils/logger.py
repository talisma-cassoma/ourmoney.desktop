import logging
import os

def get_logger(name):
    logging.basicConfig(
        filename=os.path.abspath("app.log"),
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    return logging.getLogger(name)
