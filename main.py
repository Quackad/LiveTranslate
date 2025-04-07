import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QComboBox,
    QLabel, QPushButton, QTextEdit
)
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QColor, QFont
from transcriber_thread import TranscriptionThread

LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Arabic": "ar",
}

class TranslatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Translation")
        self.setMinimumSize(800, 500)

        self.layout = QVBoxLayout(self)

        self.from_dropdown = QComboBox()
        self.from_dropdown.addItems(LANGUAGES.keys())

        self.to_dropdown = QComboBox()
        self.to_dropdown.addItems(LANGUAGES.keys())

        self.layout.addWidget(QLabel("Translate From:"))
        self.layout.addWidget(self.from_dropdown)
        self.layout.addWidget(QLabel("Translate To:"))
        self.layout.addWidget(self.to_dropdown)

        self.start_button = QPushButton("Start Translating")
        self.start_button.clicked.connect(self.start_transcription)
        self.layout.addWidget(self.start_button)

        self.loading_label = QLabel("Loading models, please wait...")
        self.loading_label.setStyleSheet("color: orange; font-weight: bold;")
        self.loading_label.setVisible(False)
        self.layout.addWidget(self.loading_label)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setFont(QFont("Courier New", 11))
        self.layout.addWidget(self.text_output)

        self.transcription_thread = None

    def start_transcription(self):
        self.start_button.setText("Listening...")
        self.start_button.setEnabled(False)
        self.loading_label.setVisible(True)

        input_lang = LANGUAGES[self.from_dropdown.currentText()]
        output_lang = LANGUAGES[self.to_dropdown.currentText()]
        self.transcription_thread = TranscriptionThread(input_lang, output_lang)
        self.transcription_thread.update_rich_text.connect(self.render_rich_text)
        self.transcription_thread.finished_loading.connect(self.on_model_ready)
        self.transcription_thread.start()

    def on_model_ready(self):
        self.loading_label.setVisible(False)

    def render_rich_text(self, rich_text):
        self.text_output.clear()
        cursor = self.text_output.textCursor()

        for span in rich_text.spans:
            fmt = QTextCharFormat()
            if "bold" in span.style:
                fmt.setFontWeight(QFont.Weight.Bold)
            if "cyan" in span.style:
                fmt.setForeground(QColor("cyan"))
            elif "yellow" in span.style:
                fmt.setForeground(QColor("gold"))
            else:
                fmt.setForeground(QColor("white"))

            segment = rich_text.plain[span.start:span.end]
            cursor.insertText(segment, fmt)

        self.text_output.setTextCursor(cursor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslatorApp()
    window.show()
    sys.exit(app.exec())
