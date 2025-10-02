import logging
import os
from typing import Optional
import dotenv

dotenv.load_dotenv()

LOG_DIR = "logs"
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
SUMMARY_LOG = "summaries.jsonl"

TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL: Optional[str] = os.getenv("OPENROUTER_BASE_URL")

def ensure_dirs() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    summary_dir = os.path.dirname(SUMMARY_LOG)
    if summary_dir:
        os.makedirs(summary_dir, exist_ok=True)
    if not os.path.exists(SUMMARY_LOG):
        with open(SUMMARY_LOG, "w", encoding="utf-8"):
            pass

def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging once for the app."""
    ensure_dirs()
    log_file = os.path.join(LOG_DIR, "bot.log")
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )

