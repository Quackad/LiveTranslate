import json
import os
from platformdirs import user_config_dir

APP_NAME = "LiveTranslator"
CONFIG_PATH = os.path.join(user_config_dir(APP_NAME), "settings.json")

default_settings = {
    "translate_from": "English",
    "translate_to": "Spanish",
    "theme": "dark.qss",
    "font_family": "Courier New",
    "font_size": 11,
    "use_colored_text": True,
    "mic_index": 0,
    "use_desktop_audio": False
}

def load_settings():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    settings = default_settings.copy()

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                user_settings = json.load(f)
                settings.update(user_settings)
        except Exception as e:
            print(f"[Settings] Failed to load settings: {e}")

    # Save back any missing defaults
    save_settings(settings)
    return settings

def save_settings(settings):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print("[Settings] Failed to save settings:", e)
