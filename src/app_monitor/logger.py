# logger.py
import logging

# Create a shared logger
logger = logging.getLogger("app_monitor")
# logger.setLevel(logging.DEBUG)

# # Add a handler (e.g., console)
# if not logger.handlers:
#     console_handler = logging.StreamHandler()
#     formatter = logging.Formatter(
#         "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     )
#     console_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)
