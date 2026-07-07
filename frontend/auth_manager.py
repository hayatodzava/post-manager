import json
from pathlib import Path

class AuthManager:
    def __init__(self):
        self.token_file = Path.home() / ".post_app" / "token.json"
        self.token_file.parent.mkdir(exist_ok=True)
    
    def save_auth_data(self, token: str, user_data: dict):
        """Saves the token and user data"""
        with open(self.token_file, "w") as f:
            json.dump({
                "access_token": token,
                "user": user_data
            }, f)
    
    def load_auth_data(self) -> dict | None:
        """Loads saved data"""
        if self.token_file.exists():
            with open(self.token_file) as f:
                return json.load(f)
        return None
    
    def get_token(self) -> str | None:
        """Returns only the token"""
        data = self.load_auth_data()
        return data.get("access_token") if data else None
    
    def get_user(self) -> dict | None:
        """Returns user data"""
        data = self.load_auth_data()
        return data.get("user") if data else None
    
    def is_admin(self) -> bool:
        """Checks whether the user is an admin"""
        user = self.get_user()
        return user.get("is_admin", False) if user else False
    
    def clear_token(self):
        if self.token_file.exists():
            self.token_file.unlink()