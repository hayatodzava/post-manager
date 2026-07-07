from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt
from api_client import PostApiClient
from async_utils import safe_run_async

class RegisterWindow(QMainWindow):
    def __init__(self, api_client: PostApiClient):
        super().__init__()
        self.api_client = api_client
        
        self.setWindowTitle("Sign up")
        self.setFixedSize(350, 250)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        title = QLabel("📝 Sign up")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name")
        self.name_input.setFixedHeight(35)
        layout.addWidget(self.name_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setFixedHeight(35)
        layout.addWidget(self.email_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(35)
        layout.addWidget(self.password_input)
        
        self.register_btn = QPushButton("Sign up")
        self.register_btn.setFixedHeight(40)
        self.register_btn.clicked.connect(self.handle_register)
        layout.addWidget(self.register_btn)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
    
    def handle_register(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        
        if not name or not email or not password:
            QMessageBox.warning(self, "Error", "Fill in all fields")
            return
        
        self.register_btn.setEnabled(False)
        self.status_label.setText("⏳ Sending...")
        
        def on_success(result):
            self.status_label.setText("✅ Account created!")
            self.register_btn.setEnabled(True)
            QMessageBox.information(self, "Success", "Now yoc can sign in!")
            self.close()
        
        def on_error(error):
            self.status_label.setText("❌ Error")
            self.register_btn.setEnabled(True)
            QMessageBox.critical(self, "Error", str(error))
        
        safe_run_async(
            self.api_client.register(name, email, password),
            on_success=on_success,
            on_error=on_error
        )