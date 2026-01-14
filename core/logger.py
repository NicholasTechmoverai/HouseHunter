import logging
import sys

def setup_logger(name: str = "app"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # or INFO in production

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
    )

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


"""
from utils.logger import setup_logger

# Initialize logger with a custom name
logger = setup_logger("socket")  # Can also be "recipes", "auth", etc.

# 🔍 DEBUG: Internal, low-level information for development
logger.debug("Detailed info: function started, variables set, etc.")

# ✅ INFO: High-level operations, like connections, successful events
logger.info("User connected to /recipes namespace")
logger.info(f"Recipe {recipe_id} metadata sent to user {user.name}")

# ⚠️ WARNING: Something unexpected, but not a crash
logger.warning("Missing recipe_id in received socket data")
logger.warning(f"User {user.email} tried to access restricted resource")

# ❌ ERROR: A serious problem occurred, but app continues
logger.error("Failed to fetch recipe from database")

# 💥 EXCEPTION: Like .error(), but logs full traceback (use inside except blocks)
try:
    ...
except Exception as e:
    logger.exception(f"Unhandled error in on_get_meta: {e}")
"""