import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QComboBox,
    QLabel, QPushButton, QTextEdit, QHBoxLayout
)
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QPoint
from transcriber_thread import TranscriptionThread
from settings_dialog import SettingsDialog
from settings_manager import load_settings, save_settings

LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Arabic": "ar",
    "Portuguese": "pt",
    "Swedish": "sv",
}

THEMES_PATH = os.path.join(os.getcwd(), "themes")

# Lowkey this could just not be a function
def apply_theme(app, theme_name):
    theme_path = os.path.join(THEMES_PATH, theme_name)
    if os.path.exists(theme_path):
        with open(theme_path, "r") as f:
            app.setStyleSheet(f.read())

class TranslatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Translation")
        self.setMinimumSize(800, 500)

        settings = load_settings()
        self.theme_file = settings.get("theme", "dark.qss")
        self.use_colors = settings.get("use_colored_text", True)
        self.selected_font = QFont(settings.get("font_family", "Courier New"), settings.get("font_size", 11))
        self.input_device_index = settings.get("mic_index", None)
        self.capture_desktop_audio = settings.get("desktop_audio", False)
        self.from_lang = settings.get("translate_from", "English")
        self.to_lang = settings.get("translate_to", "Spanish")

        self.normal_mode = True
        self.transcription_running = False
        self._drag_pos = None

        self.layout = QVBoxLayout(self)

        self.from_dropdown = QComboBox()
        self.from_dropdown.addItems(LANGUAGES.keys())
        self.from_dropdown.setCurrentText(self.from_lang)

        self.to_dropdown = QComboBox()
        self.to_dropdown.addItems(LANGUAGES.keys())
        self.to_dropdown.setCurrentText(self.to_lang)

        self.layout.addWidget(QLabel("Translate From:"))
        self.layout.addWidget(self.from_dropdown)
        self.layout.addWidget(QLabel("Translate To:"))
        self.layout.addWidget(self.to_dropdown)

        btn_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Translating")
        self.start_button.clicked.connect(self.start_transcription)

        self.toggle_overlay_button = QPushButton("Overlay Mode")
        self.toggle_overlay_button.clicked.connect(self.toggle_overlay_mode)

        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedWidth(30)
        self.settings_button.clicked.connect(self.open_settings)

        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.toggle_overlay_button)
        btn_layout.addWidget(self.settings_button)
        self.layout.addLayout(btn_layout)

        self.loading_label = QLabel("Loading models, please wait...")
        self.loading_label.setStyleSheet("color: orange; font-weight: bold;")
        self.loading_label.setVisible(False)
        self.layout.addWidget(self.loading_label)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setFont(self.selected_font)
        self.layout.addWidget(self.text_output)

        self.transcription_thread = None
        self.apply_theme()

    def apply_theme(self):
        try:
            with open(f"./themes/{self.theme_file}", "r") as f:
                self.setStyleSheet(f.read())
        except Exception:
            pass

    def open_settings(self):
        dialog = SettingsDialog(
            self,
            current_theme=self.theme_file,
            font=self.selected_font,
            use_colors=self.use_colors,
            mic_index=self.input_device_index,
            from_lang=self.from_dropdown.currentText(),
            to_lang=self.to_dropdown.currentText(),
            desktop_audio=self.capture_desktop_audio
        )

        if dialog.exec():
            self.theme_file = dialog.selected_theme()
            self.input_device_index = dialog.selected_mic_index()
            self.selected_font = dialog.selected_font()
            self.use_colors = dialog.use_colored_text()
            self.capture_desktop_audio = dialog.desktop_audio_enabled()

            self.from_dropdown.setCurrentText(dialog.from_lang)
            self.to_dropdown.setCurrentText(dialog.to_lang)
            self.text_output.setFont(self.selected_font)
            self.apply_theme()

            save_settings({
                "theme": self.theme_file,
                "font_family": self.selected_font.family(),
                "font_size": self.selected_font.pointSize(),
                "use_colored_text": self.use_colors,
                "mic_index": self.input_device_index,
                "desktop_audio": self.capture_desktop_audio,
                "translate_from": self.from_dropdown.currentText(),
                "translate_to": self.to_dropdown.currentText(),
            })

    def start_transcription(self):
        if not self.transcription_running:
            self.start_button.setText("Stop")
            self.start_button.setEnabled(True)
            self.loading_label.setVisible(True)
            self.transcription_running = True

            input_lang = LANGUAGES[self.from_dropdown.currentText()]
            output_lang = LANGUAGES[self.to_dropdown.currentText()]
            self.transcription_thread = TranscriptionThread(
                input_lang, output_lang,
                mic_index=self.input_device_index,
                use_colors=self.use_colors,
                font=self.selected_font,
                use_desktop_audio=self.capture_desktop_audio
            )
            self.transcription_thread.update_rich_text.connect(self.render_rich_text)
            self.transcription_thread.finished_loading.connect(self.on_model_ready)
            self.transcription_thread.finished.connect(self.on_transcription_stopped)
            self.transcription_thread.start()
        else:
            self.start_button.setText("Stopping...")
            self.start_button.setEnabled(False)
            self.transcription_thread.stop()

    def on_model_ready(self):
        self.loading_label.setVisible(False)

    def on_transcription_stopped(self):
        self.transcription_running = False
        self.start_button.setText("Start Translating")
        self.start_button.setEnabled(True)

    def render_rich_text(self, rich_text):
        self.text_output.clear()
        cursor = self.text_output.textCursor()
        for span in rich_text.spans:
            fmt = QTextCharFormat()
            if self.use_colors:
                if "bold" in span.style:
                    fmt.setFontWeight(QFont.Weight.Bold)
                if "cyan" in span.style:
                    fmt.setForeground(QColor("cyan"))
                elif "yellow" in span.style:
                    fmt.setForeground(QColor("gold"))
            segment = rich_text.plain[span.start:span.end]
            cursor.insertText(segment, fmt)
        self.text_output.setTextCursor(cursor)

    def toggle_overlay_mode(self):
        self.normal_mode = not self.normal_mode
        if self.normal_mode:
            self.setWindowOpacity(1.0)
            self.setWindowFlags(Qt.WindowType.Window)
            self.showNormal()
        else:
            self.setWindowOpacity(0.85)
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.childAt(event.pos()) is None:
                self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslatorApp()
    window.show()
    sys.exit(app.exec())

