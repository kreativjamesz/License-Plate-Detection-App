"""
Development state management para sa hot reload
Saves at restores ang current application state during development
"""

import json
import os
from typing import Optional, Dict, Any
from pathlib import Path

DEV_STATE_FILE = ".dev_state.json"

class DevStateManager:
    @staticmethod
    def save_state(state: Dict[str, Any]) -> None:
        """Save current application state para sa hot reload"""
        try:
            with open(DEV_STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"💾 Dev state saved: {state}")
        except Exception as e:
            print(f"❌ Failed to save dev state: {e}")
    
    @staticmethod
    def load_state() -> Optional[Dict[str, Any]]:
        """Load saved application state"""
        try:
            if os.path.exists(DEV_STATE_FILE):
                with open(DEV_STATE_FILE, 'r') as f:
                    state = json.load(f)
                print(f"📂 Dev state loaded: {state}")
                return state
            return None
        except Exception as e:
            print(f"❌ Failed to load dev state: {e}")
            return None
    
    @staticmethod
    def clear_state() -> None:
        """Clear saved state file"""
        try:
            if os.path.exists(DEV_STATE_FILE):
                os.remove(DEV_STATE_FILE)
                print("🗑️ Dev state cleared")
        except Exception as e:
            print(f"❌ Failed to clear dev state: {e}")
    
    @staticmethod
    def is_dev_mode() -> bool:
        """Check if running in development mode"""
        return os.environ.get('DEV_MODE') == 'true'

def save_app_state(current_user: Optional[str] = None, current_route: str = "home", **kwargs):
    """Convenience function para sa pag-save ng app state"""
    state = {
        "current_user": current_user,
        "current_route": current_route,
        "timestamp": str(Path().cwd()),
        **kwargs
    }
    DevStateManager.save_state(state)

def load_app_state() -> Dict[str, Any]:
    """Convenience function para sa pag-load ng app state"""
    state = DevStateManager.load_state()
    if state is None:
        return {
            "current_user": None,
            "current_route": "home"
        }
    return state
