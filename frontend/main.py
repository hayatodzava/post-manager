import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from api_client import PostApiClient
from auth_manager import AuthManager
from async_utils import init_async_loop
from windows.login_window import LoginWindow
from windows.main_window import MainWindow

class PostApp:
    def __init__(self):
        self.api_client = PostApiClient()
        self.auth_manager = AuthManager()
        self.main_window = None
        self.login_window = None
        self._switching = False
    
    def run(self):
        init_async_loop()
        
        self.app = QApplication(sys.argv)
        self.app.aboutToQuit.connect(self.cleanup)
        
        auth_data = self.auth_manager.load_auth_data()
        if auth_data and auth_data.get("access_token"):
            self.api_client.set_token(auth_data["access_token"])
            QTimer.singleShot(0, self.show_main_window)
        else:
            QTimer.singleShot(0, self.show_login_window)
        
        sys.exit(self.app.exec())
    
    def cleanup(self):
        import asyncio
        from async_utils import run_async
        run_async(self.api_client.close())
    
    def show_login_window(self):
        if self._switching:
            return
        self._switching = True
        
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        
        if self.login_window is None:
            self.login_window = LoginWindow(
                self.api_client,
                self.auth_manager,
                self.on_login_success
            )
            self.login_window.show()
            self.login_window.raise_()
        
        self._switching = False
    
    def show_main_window(self):
        if self._switching:
            return
        self._switching = True
        
        if self.login_window:
            self.login_window.close()
            self.login_window = None
        
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self._switching = False
            return
        
        self.main_window = MainWindow(self.api_client, self.auth_manager)
        self.main_window.logout_requested.connect(self.on_logout_requested)
        self.main_window.show()
        self.main_window.raise_()
        
        self._switching = False
    
    def on_login_success(self):
        self.show_main_window()
    
    def on_logout_requested(self):
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        self.show_login_window()

if __name__ == "__main__":
    app = PostApp()
    app.run()