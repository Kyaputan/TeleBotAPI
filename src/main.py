import logging
from bot.bot import run_bot, bot
import config
import signal
import sys

config.setup_logging()
logger = logging.getLogger(__name__)

def shutdown_handler(signum, frame):
    try:
        bot.stop_polling()
        logger.info("--------------------Bot stopped successfully--------------------")
    except Exception as e:
        logger.error(f"Error stopping polling: {e}")
    sys.exit(0)
    

if __name__ == "__main__":
    logger.info("--------------------Starting bot--------------------")
    signal.signal(signal.SIGINT, shutdown_handler)
    run_bot()
