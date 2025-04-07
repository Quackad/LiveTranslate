from PyQt6.QtCore import QThread, pyqtSignal
from RealtimeSTT import AudioToTextRecorder
from deep_translator import GoogleTranslator
from rich.text import Text

class TranscriptionThread(QThread):
    update_rich_text = pyqtSignal(object)
    finished_loading = pyqtSignal()

    def __init__(self, input_lang='en', output_lang='es'):
        super().__init__()
        self.input_lang = input_lang
        self.output_lang = output_lang
        self.recorder = None
        self.prev_text = ""
        self.full_sentences = []

        self.end_of_sentence_detection_pause = 0.45
        self.unknown_sentence_detection_pause = 0.7
        self.mid_sentence_detection_pause = 2.0

    def preprocess_text(self, text):
        text = text.lstrip()
        if text.startswith("..."):
            text = text[3:].lstrip()
        if text:
            text = text[0].upper() + text[1:]
        return text

    def emit_combined_rich_text(self, live_text=""):
        rich = Text()
        for i, sentence in enumerate(self.full_sentences):
            rich.append(sentence, style="yellow" if i % 2 == 0 else "cyan")
            rich.append(" ")
        if live_text:
            rich.append(live_text, style="bold yellow")
        self.update_rich_text.emit(rich)

    def on_realtime_update(self, text):
        text = self.preprocess_text(text)
        self.prev_text = text

        try:
            translated = GoogleTranslator(source='auto', target=self.output_lang).translate(text)
        except Exception:
            translated = "[...]"

        self.emit_combined_rich_text(translated)


    def process_text(self, text):
        text = self.preprocess_text(text).rstrip()
        if text.endswith("..."):
            text = text[:-2]
        if not text:
            return

        try:
            translated = GoogleTranslator(source='auto', target=self.output_lang).translate(text)
        except Exception:
            translated = "[Translation failed]"

        self.full_sentences.append(translated)
        self.prev_text = ""
        self.emit_combined_rich_text()

    def run(self):
        recorder_config = {
            'spinner': False,
            'model': 'large-v2',
            'download_root': None,
            'realtime_model_type': 'tiny',
            'language': self.input_lang,
            'silero_sensitivity': 0.05,
            'webrtc_sensitivity': 3,
            'post_speech_silence_duration': self.unknown_sentence_detection_pause,
            'min_length_of_recording': 1.1,
            'min_gap_between_recordings': 0,
            'enable_realtime_transcription': True,
            'realtime_processing_pause': 0.02,
            'on_realtime_transcription_update': self.on_realtime_update,
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

        self.recorder = AudioToTextRecorder(**recorder_config)
        self.finished_loading.emit()  # 🔥 Notify the GUI that we're ready

        try:
            while True:
                self.recorder.text(self.process_text)
        except KeyboardInterrupt:
            return
