import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
from deep_translator import GoogleTranslator
from RealtimeSTT import AudioToTextRecorder
import colorama

# Optional: Extended logging
EXTENDED_LOGGING = False

class TranscriptionThread(QThread):
    update_text = pyqtSignal(str)
    update_translation = pyqtSignal(str)

    def __init__(self, recorder_config):
        super().__init__()
        self.recorder = AudioToTextRecorder(**recorder_config)
        self.prev_text = ""

    def preprocess_text(self, text):
        text = text.lstrip()
        if text.startswith("..."):
            text = text[3:].lstrip()
        if text:
            text = text[0].upper() + text[1:]
        return text

    def process_text(self, text):
        text = self.preprocess_text(text).rstrip()
        if text.endswith("..."):
            text = text[:-2]

        if not text:
            return

        try:
            translated = GoogleTranslator(source='auto', target='es').translate(text)
        except Exception:
            translated = "[Translation failed]"

        self.update_text.emit(text)
        self.update_translation.emit(translated)

    def run(self):
        try:
            while True:
                self.recorder.text(self.process_text)
        except KeyboardInterrupt:
            return

class TranslatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Speech Translator")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        self.label_transcript = QLabel("Live Transcription:")
        self.transcript_box = QTextEdit()
        self.transcript_box.setReadOnly(True)

        self.label_translation = QLabel("Translation:")
        self.translation_box = QTextEdit()
        self.translation_box.setReadOnly(True)

        layout.addWidget(self.label_transcript)
        layout.addWidget(self.transcript_box)
        layout.addWidget(self.label_translation)
        layout.addWidget(self.translation_box)

        self.setLayout(layout)

        recorder_config = {
            'spinner': False,
            'model': 'large-v2',
            'download_root': None,
            'realtime_model_type': 'tiny.en',
            'language': 'en',
            'silero_sensitivity': 0.05,
            'webrtc_sensitivity': 3,
            'post_speech_silence_duration': 0.7,
            'min_length_of_recording': 1.1,
            'min_gap_between_recordings': 0,
            'enable_realtime_transcription': True,
            'realtime_processing_pause': 0.02,
            'silero_deactivity_detection': True,
            'early_transcription_on_silence': 0,
            'beam_size': 5,
            'beam_size_realtime': 3,
            'no_log_file': True,
            'initial_prompt': (
                "End incomplete sentences with ellipses.\n"
                "Examples:\n"
                "Complete: The sky is blue.\n"
                "Incomplete: When the sky...\n"
                "Complete: She walked home.\n"
                "Incomplete: Because he...\n"
            )
        }

        self.thread = TranscriptionThread(recorder_config)
        self.thread.update_text.connect(self.display_transcript)
        self.thread.update_translation.connect(self.display_translation)
        self.thread.start()

    def display_transcript(self, text):
        self.transcript_box.append(text)

    def display_translation(self, translated):
        self.translation_box.append(translated)

if __name__ == '__main__':
    colorama.init()
    app = QApplication(sys.argv)
    window = TranslatorApp()
    window.show()
    sys.exit(app.exec())
