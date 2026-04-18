import logging
from pathlib import Path

def setup_logging(log_file: Path = None, debug: bool = False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    if log_file is None:
        logs_dir = Path(__file__).parent / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / 'runqc.log'

    # Create file handler
    fh = logging.FileHandler(log_file, mode='a')
    fh.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    # Create formatter and add it to handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add handlers to the logger if they haven't been added yet
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
