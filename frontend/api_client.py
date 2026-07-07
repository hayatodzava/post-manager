import httpx
from typing import List, Dict, Optional

class PostApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Closes the HTTP client (call upon exit)"""
        await self.client.aclose()
    
    def set_token(self, token: str):
        """Saves the JWT token after login"""
        self.access_token = token
    
    def get_headers(self) -> Dict[str, str]:
        """Returns headers for authorized requests"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    async def register(self, name: str, email: str, password: str) -> Dict:
        """New user registration"""
        response = await self.client.post(
            f"{self.base_url}/register",
            json={"name": name, "email": email, "password": password}
        )
        response.raise_for_status()
        return response.json()
    
    async def login(self, email: str, password: str) -> Dict:
        """Login and retrieval of JWT token + user data"""
        response = await self.client.post(
            f"{self.base_url}/login",
            data={"username": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.set_token(data["access_token"])
        
        me_response = await self.client.get(
            f"{self.base_url}/me",
            headers=self.get_headers()
        )
        me_response.raise_for_status()
        user_data = me_response.json()
        data["user"] = user_data
        return data
    
    async def get_posts(self) -> List[Dict]:
        response = await self.client.get(
            f"{self.base_url}/posts",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

    async def create_post(self, title: str, content: str = "", is_public: bool = False) -> Dict:
        response = await self.client.post(
            f"{self.base_url}/posts",
            json={"title": title, "content": content, "is_public": is_public},
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

    async def update_post(self, post_id: int, title: Optional[str] = None, content: Optional[str] = None, is_public: Optional[bool] = None) -> Dict:
        data = {}
        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        if is_public is not None:
            data["is_public"] = is_public
        
        response = await self.client.patch(
            f"{self.base_url}/posts/{post_id}",
            json=data,
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def delete_post(self, post_id: int) -> None:
        """Delete post"""
        response = await self.client.delete(
            f"{self.base_url}/posts/{post_id}",
            headers=self.get_headers()
        )
        response.raise_for_status()

    async def get_users(self) -> List[Dict]:
        """Get a list of all users (authorized users only)"""
        response = await self.client.get(
            f"{self.base_url}/users",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def update_user(self, user_id: int, name: str, email: str, is_admin: bool) -> Dict:
        """Update user data (admin only)"""
        response = await self.client.patch(
            f"{self.base_url}/users/{user_id}",
            json={"name": name, "email": email, "is_admin": is_admin},
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()