import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path(__file__).parent.parent / "settings.json"

DEFAULTS = {
    "tilt": 0.0,
    "led": "green",
    "mirror": False,
}


def load() -> dict:
    try:
        data = json.loads(SETTINGS_PATH.read_text())
        return {**DEFAULTS, **data}
    except FileNotFoundError:
        return dict(DEFAULTS)
    except Exception as e:
        logger.warning(f"Could not load settings, using defaults: {e}")
        return dict(DEFAULTS)


def save(settings: dict):
    try:
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2))
    except Exception as e:
        logger.warning(f"Could not save settings: {e}")
