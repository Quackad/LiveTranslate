from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox,
    QPushButton, QCheckBox, QFontComboBox, QHBoxLayout
)
import sounddevice as sd
import os

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_theme="light.qss", font="Courier New", use_colors=True,
                 mic_index=None, from_lang="English", to_lang="Spanish", desktop_audio=False):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        layout = QVBoxLayout()

        # Theme selection
        layout.addWidget(QLabel("Select Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.get_available_themes())
        self.theme_combo.setCurrentText(current_theme)
        layout.addWidget(self.theme_combo)

        # Microphone selection
        layout.addWidget(QLabel("Select Microphone Input:"))
        self.mic_combo = QComboBox()
        self.mics = self.get_microphones()
        self.mic_combo.addItems(self.mics)
        if mic_index is not None and mic_index < len(self.mics):
            self.mic_combo.setCurrentIndex(mic_index)
        layout.addWidget(self.mic_combo)

        # Font selection
        layout.addWidget(QLabel("Select Font:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(font)
        layout.addWidget(self.font_combo)

        # Colored text toggle
        self.color_checkbox = QCheckBox("Enable colored text")
        self.color_checkbox.setChecked(use_colors)
        layout.addWidget(self.color_checkbox)

        # Desktop audio toggle
        self.desktop_checkbox = QCheckBox("Use desktop audio instead of microphone")
        self.desktop_checkbox.setChecked(desktop_audio)
        layout.addWidget(self.desktop_checkbox)

        # Apply/Cancel buttons
        btn_layout = QHBoxLayout()
        self.save_button = QPushButton("Apply")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        # Language memory
        self.from_lang = from_lang
        self.to_lang = to_lang

        self.setLayout(layout)

    def get_available_themes(self):
        theme_dir = "./themes"
        if not os.path.exists(theme_dir):
            return []
        return [f for f in os.listdir(theme_dir) if f.endswith(".qss")]

    def get_microphones(self):
        return [dev['name'] for dev in sd.query_devices() if dev['max_input_channels'] > 0]

    def selected_theme(self):
        return self.theme_combo.currentText()

    def selected_font(self):
        return self.font_combo.currentFont()

    def use_colored_text(self):
        return self.color_checkbox.isChecked()

    def selected_mic_index(self):
        return self.mic_combo.currentIndex()

    def desktop_audio_enabled(self):
        return self.desktop_checkbox.isChecked()
