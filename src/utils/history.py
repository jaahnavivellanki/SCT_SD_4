import os
import json
import logging
import dataclasses
from datetime import datetime
from typing import List, Dict, Any

from src.scraper.base import Product

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_FILE = "scraping_history.json"

def get_history_filepath() -> str:
    """Return the absolute path of the history file inside the workspace."""
    # We save in the root of the workspace directory
    return os.path.abspath(DEFAULT_HISTORY_FILE)

def save_session(url: str, products: List[Product], filepath: str = None) -> str:
    """
    Save a list of products from a scraping session into the local history file.

    :param url: The scraped target URL.
    :param products: List of Product dataclasses.
    :param filepath: Path to the JSON history file.
    :return: Generated session ID string.
    """
    if filepath is None:
        filepath = get_history_filepath()

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    session_data = {
        "session_id": session_id,
        "timestamp": timestamp,
        "url": url,
        "products_count": len(products),
        "products": [dataclasses.asdict(p) for p in products]
    }

    sessions = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                sessions = json.load(f)
                if not isinstance(sessions, list):
                    sessions = []
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read history file, resetting. Error: {e}")
            sessions = []

    # Prepend new session (latest first)
    sessions.insert(0, session_data)

    # Cap history at 30 sessions to keep data size reasonable
    sessions = sessions[:30]

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved scraping session {session_id} to history.")
    except IOError as e:
        logger.error(f"Failed to write history session: {e}")
        raise RuntimeError(f"Failed to write session history to file: {e}")

    return session_id

def get_all_sessions(filepath: str = None) -> List[Dict[str, Any]]:
    """
    Load and return all saved sessions from the history file.
    """
    if filepath is None:
        filepath = get_history_filepath()

    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            sessions = json.load(f)
            if isinstance(sessions, list):
                return sessions
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load sessions from history file: {e}")

    return []

def delete_session(session_id: str, filepath: str = None) -> None:
    """
    Delete a specific session by its session_id.
    """
    if filepath is None:
        filepath = get_history_filepath()

    sessions = get_all_sessions(filepath)
    updated_sessions = [s for s in sessions if s.get("session_id") != session_id]

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(updated_sessions, f, indent=2, ensure_ascii=False)
        logger.info(f"Deleted scraping session {session_id} from history.")
    except IOError as e:
        logger.error(f"Failed to update history file after deletion: {e}")
        raise RuntimeError(f"Failed to delete session: {e}")

def clear_all_history(filepath: str = None) -> None:
    """
    Wipe all saved sessions from the local history file.
    """
    if filepath is None:
        filepath = get_history_filepath()

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.info("Cleared all scraping history file.")
        except IOError as e:
            logger.error(f"Failed to delete history file: {e}")
            raise RuntimeError(f"Failed to clear history: {e}")
