from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton,
    QLabel, QMessageBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QTextEdit,
    QDialog, QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Signal
from api_client import PostApiClient
from auth_manager import AuthManager
from async_utils import safe_run_async

# ========== DIALOG FOR CREATING/EDITING POSTS ==========
class PostDialog(QDialog):
    def __init__(self, parent=None, post_data=None):
        super().__init__(parent)
        self.post_data = post_data
        self.setWindowTitle("New post" if post_data is None else "Edit post")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.title_input = QLineEdit()
        if post_data:
            self.title_input.setText(post_data.get("title", ""))
        form.addRow("Title:", self.title_input)
        
        self.content_input = QTextEdit()
        self.content_input.setMaximumHeight(100)
        if post_data:
            self.content_input.setText(post_data.get("content", ""))
        form.addRow("Message:", self.content_input)
        
        self.public_check = QCheckBox("Public")
        if post_data:
            self.public_check.setChecked(post_data.get("is_public", False))
        form.addRow("Access:", self.public_check)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "content": self.content_input.toPlainText().strip(),
            "is_public": self.public_check.isChecked()
        }


class PostListWidget(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background: #f0f0f0;
            }
        """)

class UserEditDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("Edit user")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        if user_data:
            self.name_input.setText(user_data.get("name", ""))
        form.addRow("Name:", self.name_input)
        
        self.email_input = QLineEdit()
        if user_data:
            self.email_input.setText(user_data.get("email", ""))
        form.addRow("Email:", self.email_input)
        
        self.admin_check = QCheckBox("Admin")
        if user_data:
            self.admin_check.setChecked(user_data.get("is_admin", False))
        form.addRow("Access:", self.admin_check)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "is_admin": self.admin_check.isChecked()
        }
    
class UserCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create user")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name")
        form.addRow("Name:", self.name_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        form.addRow("Email:", self.email_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form.addRow("Password:", self.password_input)
        
        self.admin_check = QCheckBox("Admin")
        form.addRow("Access:", self.admin_check)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "password": self.password_input.text().strip(),
            "is_admin": self.admin_check.isChecked()
        }

class MainWindow(QMainWindow):
    logout_requested = Signal()
    
    def __init__(self, api_client: PostApiClient, auth_manager: AuthManager):
        super().__init__()
        self.api_client = api_client
        self.auth_manager = auth_manager
        self._show_only_my = False 
        
        self.setWindowTitle("Post Manager")
        self.setMinimumSize(800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(15)
        
        # ===== Top panel =====
        header = QHBoxLayout()
        title = QLabel("📋 Post Manager")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        
        self.user_label = QLabel("User")
        header.addWidget(self.user_label)
        
        self.logout_btn = QPushButton("🚪 Logout")
        self.logout_btn.clicked.connect(self.logout)
        header.addWidget(self.logout_btn)
        main_layout.addLayout(header)
        
        # ===== Tabs =====
        self.tab_widget = QTabWidget()
        
        self.posts_tab = QWidget()
        self.setup_posts_tab()
        self.tab_widget.addTab(self.posts_tab, "📋 Posts")
        
        self.users_tab = QWidget()
        self.setup_users_tab()
        self.tab_widget.addTab(self.users_tab, "👥 Users")
        
        if not self.auth_manager.is_admin():
            self.tab_widget.setTabVisible(1, False)
        
        main_layout.addWidget(self.tab_widget)
        
        user = self.auth_manager.get_user()
        if user:
            self.user_label.setText(f"👤 {user.get('name', 'User')}")
        
        self.load_posts()
        self.load_users()
    
    # ========== POSTS TAB ==========
    def setup_posts_tab(self):
        layout = QVBoxLayout(self.posts_tab)
        layout.setSpacing(10)
        
        # Filter panel
        filter_layout = QHBoxLayout()
        
        self.show_my_btn = QPushButton("📌 My only")
        self.show_my_btn.setCheckable(True)
        self.show_my_btn.clicked.connect(self.toggle_my_filter)
        filter_layout.addWidget(self.show_my_btn)
        
        self.refresh_posts_btn = QPushButton("🔄 Refresh")
        self.refresh_posts_btn.clicked.connect(self.load_posts)
        filter_layout.addWidget(self.refresh_posts_btn)
        
        filter_layout.addStretch()
        
        self.create_btn = QPushButton("➕ New post")
        self.create_btn.clicked.connect(self.create_post)
        filter_layout.addWidget(self.create_btn)
        
        layout.addLayout(filter_layout)
        
        # List of posts
        self.post_list = PostListWidget(self)
        layout.addWidget(self.post_list)
        
        self.post_status_label = QLabel("Loading posts...")
        self.post_status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.post_status_label)
    
    def toggle_my_filter(self):
        self._show_only_my = self.show_my_btn.isChecked()
        self.load_posts()
    
    def load_posts(self):
        self.post_status_label.setText("⏳ Loading...")
        self.post_list.clear()
        
        current_user = self.auth_manager.get_user()
        current_user_id = current_user.get("id") if current_user else None
        is_admin = self.auth_manager.is_admin()
        
        def on_success(posts):
            # Filter on the client side if the "Only mine" checkbox is selected
            if self._show_only_my:
                posts = [t for t in posts if t["user_id"] == current_user_id]
            
            for post in posts:
                self.add_post_item(post, current_user_id, is_admin)
            self.post_status_label.setText(f"✅ {len(posts)} post loaded")
        
        def on_error(error):
            self.post_status_label.setText("❌ load failure")
            QMessageBox.critical(self, "Error", str(error))
        
        safe_run_async(
            self.api_client.get_posts(),
            on_success=on_success,
            on_error=on_error
        )
    def add_post_item(self, post: dict, current_user_id: int, is_admin: bool):
        item = QListWidgetItem(self.post_list)
        
        # Creating a widget for a row
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # Title + visibility status
        title_text = f"<b>{post['title']}</b>"
        if post.get("is_public"):
            title_text += " <span style='color: #4CAF50; font-size: 10px;'>(🌐 public)</span>"
        else:
            title_text += " <span style='color: #888; font-size: 10px;'>(🔒 private)</span>"
        
        title_label = QLabel(title_text)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(title_label)
        
        # Message
        if post.get("content"):
            content_label = QLabel(post['content'])
            content_label.setWordWrap(True)
            content_label.setStyleSheet("color: #555; font-size: 12px;")
            layout.addWidget(content_label)
        
        # Author
        author_name = post.get("author_name", f"User #{post['user_id']}")
        author_label = QLabel(f"✍️ {author_name}")
        author_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(author_label)
        
        # Action buttons
        if is_admin or post["user_id"] == current_user_id:
            actions_layout = QHBoxLayout()
            actions_layout.addStretch()
            
            edit_btn = QPushButton("✏️ Edit")
            edit_btn.setFixedSize(120, 30)
            edit_btn.clicked.connect(lambda checked, tid=post["id"]: self.edit_post(tid))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("🗑️ Delete")
            delete_btn.setFixedSize(100, 30)
            delete_btn.setStyleSheet("color: red;")
            delete_btn.clicked.connect(lambda checked, tid=post["id"]: self.delete_post(tid))
            actions_layout.addWidget(delete_btn)
            
            layout.addLayout(actions_layout)
        
        widget.adjustSize()
        item.setSizeHint(widget.sizeHint())
        self.post_list.setItemWidget(item, widget)
    
    def create_post(self):
        dialog = PostDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["title"]:
                QMessageBox.warning(self, "Error", "A title is required")
                return
            
            def on_success(post):
                self.load_posts()
                self.post_status_label.setText("✅ Post created")
            
            def on_error(error):
                QMessageBox.critical(self, "Error", str(error))
            
            safe_run_async(
                self.api_client.create_post(data["title"], data["content"], data["is_public"]),
                on_success=on_success,
                on_error=on_error
            )
    
    def edit_post(self, post_id: int):
        def on_success(posts):
            post = next((t for t in posts if t["id"] == post_id), None)
            if not post:
                QMessageBox.warning(self, "Error", "Post not found")
                return
            
            dialog = PostDialog(self, post)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                
                def on_update_success(_):
                    self.load_posts()
                    self.post_status_label.setText("✅ Post updated")
                
                def on_update_error(error):
                    QMessageBox.critical(self, "Error", str(error))
                
                safe_run_async(
                    self.api_client.update_post(post_id, data["title"], data["content"], data["is_public"]),
                    on_success=on_update_success,
                    on_error=on_update_error
                )
        
        safe_run_async(
            self.api_client.get_posts(),
            on_success=on_success,
            on_error=lambda e: QMessageBox.critical(self, "Error", str(e))
        )
    
    def delete_post(self, post_id: int):
        reply = QMessageBox.question(
            self, "Confirmation",
            "Delete this post?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        def on_success(_):
            self.load_posts()
            self.post_status_label.setText("✅ Post deleted")
        
        def on_error(error):
            QMessageBox.critical(self, "Error", str(error))
        
        safe_run_async(
            self.api_client.delete_post(post_id),
            on_success=on_success,
            on_error=on_error
        )
    
    # ========== USER TAB ==========
    def setup_users_tab(self):
        layout = QVBoxLayout(self.users_tab)
        layout.setSpacing(10)
        
        # Action panel (admin only)
        if self.auth_manager.is_admin():
            actions_layout = QHBoxLayout()
            actions_layout.addStretch()
            
            self.create_user_btn = QPushButton("➕ Create user")
            self.create_user_btn.setFixedHeight(35)
            self.create_user_btn.clicked.connect(self.create_user)
            actions_layout.addWidget(self.create_user_btn)
            
            self.refresh_users_btn = QPushButton("🔄 Refresh")
            self.refresh_users_btn.setFixedHeight(35)
            self.refresh_users_btn.clicked.connect(self.load_users)
            actions_layout.addWidget(self.refresh_users_btn)
            
            layout.addLayout(actions_layout)
        
        # User table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Name", "Email", "Admin"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setSortingEnabled(True)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.itemDoubleClicked.connect(self.edit_user)
        layout.addWidget(self.users_table)
        
        self.users_status_label = QLabel("Loading users...")
        self.users_status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.users_status_label)
        
        # If not an admin — mask the status text
        if not self.auth_manager.is_admin():
            self.users_status_label.setText("⏳ Admins only")
            self.users_table.setRowCount(0)
            self.users_table.setEnabled(False)
    
    def load_users(self):
        if not hasattr(self, 'users_table'):
            return
        
        if not self.auth_manager.is_admin():
            self.users_status_label.setText("⏳ Admins only")
            self.users_table.setRowCount(0)
            return
        
        self.users_status_label.setText("⏳ Loading...")
        self.users_table.setRowCount(0)
        
        def on_success(users):
            self.users_table.setRowCount(len(users))
            for row, user in enumerate(users):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user["id"])))
                self.users_table.setItem(row, 1, QTableWidgetItem(user["name"]))
                self.users_table.setItem(row, 2, QTableWidgetItem(user["email"]))
                admin_text = "✔" if user.get("is_admin", False) else ""
                self.users_table.setItem(row, 3, QTableWidgetItem(admin_text))
            self.users_status_label.setText(f"✅ {len(users)} user loaded")
        
        def on_error(error):
            self.users_status_label.setText("❌ Load failure")
            QMessageBox.critical(self, "Error", str(error))
        
        safe_run_async(
            self.api_client.get_users(),
            on_success=on_success,
            on_error=on_error
        )

    def create_user(self):
        """Opens the new user creation dialog (admin only)"""
        if not self.auth_manager.is_admin():
            QMessageBox.warning(self, "Access denied", "Only administrators can create users")
            return
        
        dialog = UserCreateDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            
            if not data["name"] or not data["email"] or not data["password"]:
                QMessageBox.warning(self, "Error", "Fill in all fields")
                return
            
            def on_success(new_user):
                self.load_users()
                QMessageBox.information(self, "Success", f"User {new_user['name']} created")
            
            def on_error(error):
                QMessageBox.critical(self, "Error", str(error))
            
            safe_run_async(
                self.api_client.register(data["name"], data["email"], data["password"]),
                on_success=on_success,
                on_error=on_error
            )

    def edit_user(self, item):
        """Opens the user editing dialog on double-click."""
        if not self.auth_manager.is_admin():
            QMessageBox.warning(self, "Access denied", "Only administrators can edit users")
            return
        
        row = item.row()
        user_id = int(self.users_table.item(row, 0).text())
        current_name = self.users_table.item(row, 1).text()
        current_email = self.users_table.item(row, 2).text()
        is_admin = self.users_table.item(row, 3).text() == "✔"
        
        user_data = {
            "id": user_id,
            "name": current_name,
            "email": current_email,
            "is_admin": is_admin
        }
        
        dialog = UserEditDialog(self, user_data)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            
            # Sending a request to update the user
            def on_success(updated_user):
                self.load_users()
                QMessageBox.information(self, "Success", f"User {updated_user['name']} updated")
            
            def on_error(error):
                QMessageBox.critical(self, "Error", str(error))
            
            safe_run_async(
                self.api_client.update_user(user_id, data["name"], data["email"], data["is_admin"]),
                on_success=on_success,
                on_error=on_error
            )

    def logout(self):
        self.auth_manager.clear_token()
        self.logout_requested.emit()
        self.close()