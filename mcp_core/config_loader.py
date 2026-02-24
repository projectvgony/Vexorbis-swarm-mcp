
import os
import json
import logging
from typing import Dict


def load_global_model_config() -> Dict[str, str]:
    """
    Attempts to load model configuration from the global Antigravity config.
    Returns empty dict if not found, preserving Single Source of Truth.
    """
    try:
        home = os.path.expanduser("~")
        config_path = os.path.join(home, ".gemini", "antigravity", "mcp_config.json")

        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
            
            # Retrieve 'models' section if present
            return data.get("models", {})

    except Exception as e:
        logging.warning(f"Failed to load global config: {e}")

    return {}
