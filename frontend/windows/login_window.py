from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt
from api_client import PostApiClient
from auth_manager import AuthManager
from async_utils import safe_run_async

class LoginWindow(QMainWindow):
    def __init__(self, api_client: PostApiClient, auth_manager: AuthManager, on_login_success):
        super().__init__()
        self.api_client = api_client
        self.auth_manager = auth_manager
        self.on_login_success = on_login_success
        
        self.setWindowTitle("Sign in Post Manager")
        self.setFixedSize(400, 250)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        title = QLabel("📋 Post Manager")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setFixedHeight(35)
        layout.addWidget(self.email_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(35)
        layout.addWidget(self.password_input)
        
        self.login_btn = QPushButton("Sign in")
        self.login_btn.setFixedHeight(40)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        self.register_btn = QPushButton("Sign up")
        self.register_btn.setFixedHeight(30)
        self.register_btn.clicked.connect(self.handle_register)
        layout.addWidget(self.register_btn)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        self.check_saved_token()
    
    def check_saved_token(self):
        token = self.auth_manager.get_token()
        if token:
            self.api_client.set_token(token)
            self.close()
            if self.on_login_success:
                self.on_login_success()
    
    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Enter email and password")
            return
        
        self.status_label.setText("⏳ Signing in...")
        self.login_btn.setEnabled(False)
        
        def on_success(result):
            print(f"✅ Login successful!")
            self.auth_manager.save_auth_data(
                result["access_token"],
                result["user"]
            )
            self.status_label.setText("✅ Success!")
            self.login_btn.setEnabled(True)
            
            self.close()
            
            if self.on_login_success:
                self.on_login_success()
            else:
                print("❌ self.on_login_success = None!")
            
        def on_error(error):
            print(f"❌ Login failure: {error}")
            self.status_label.setText("❌ Login failure")
            self.login_btn.setEnabled(True)
            QMessageBox.critical(self, "Error", str(error))
        
        safe_run_async(
            self.api_client.login(email, password),
            on_success=on_success,
            on_error=on_error
        )
    
    def handle_register(self):
        from .register_window import RegisterWindow
        self.register_window = RegisterWindow(self.api_client)
        self.register_window.show()