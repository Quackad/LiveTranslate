import threading
from PyQt6.QtCore import QThread, pyqtSignal
from RealtimeSTT import AudioToTextRecorder
from deep_translator import GoogleTranslator
from rich.text import Text
import sounddevice as sd
import platform
import time

class TranscriptionThread(QThread):
    update_rich_text = pyqtSignal(object)
    finished_loading = pyqtSignal()

    def __init__(self, input_lang='en', output_lang='es', mic_index=None, use_colors=True,
                 font=None, use_desktop_audio=False):
        super().__init__()
        self.input_lang = input_lang
        self.output_lang = output_lang
        self.mic_index = mic_index
        self.use_colors = use_colors
        self.selected_font = font
        self.use_desktop_audio = use_desktop_audio

        self.recorder = None
        self.prev_text = ""
        self.full_sentences = []
        self.running = False
        self.worker_thread = None  # the Python thread

        self.end_of_sentence_detection_pause = 0.45
        self.unknown_sentence_detection_pause = 0.7
        self.mid_sentence_detection_pause = 2.0

    def stop(self):
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=3)
        self.quit()
        self.wait()

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
            style = "yellow" if i % 2 == 0 else "cyan"
            if not self.use_colors:
                style = ""
            rich.append(sentence, style=style)
            rich.append(" ")
        if live_text:
            live_style = "bold yellow" if self.use_colors else ""
            rich.append(live_text, style=live_style)
        self.update_rich_text.emit(rich)

    def on_realtime_update(self, text):
        text = self.preprocess_text(text)
        self.prev_text = text
        self.emit_combined_rich_text(text)

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
        self.emit_combined_rich_text("")

    def run_recorder_loop(self):
        while self.running:
            try:
                self.recorder.text(self.process_text)
            except Exception as e:
                print("[STT] Exception:", e)
            time.sleep(0.1)

    def run(self):
        config = {
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

        # Input source selection
        if self.use_desktop_audio and platform.system() == "Windows":
            try:
                devices = sd.query_devices()
                wasapi_host = next((i for i, h in enumerate(sd.query_hostapis())
                                    if h['name'].lower() == 'windows wasapi'), None)
                if wasapi_host is not None:
                    loopbacks = [i for i, d in enumerate(devices)
                                 if d['hostapi'] == wasapi_host and d['max_input_channels'] > 0 and d['name'].endswith(" (loopback)")]
                    if loopbacks:
                        config['input_device_index'] = loopbacks[0]
                        print("[Audio] Using desktop loopback:", devices[loopbacks[0]]['name'])
            except Exception as e:
                print("[Audio] Failed to enable loopback:", e)
        elif self.mic_index is not None:
            config['input_device_index'] = self.mic_index

        self.recorder = AudioToTextRecorder(**config)
        self.finished_loading.emit()

        self.running = True
        self.worker_thread = threading.Thread(target=self.run_recorder_loop)
        self.worker_thread.start()

        # Wait until thread is asked to stop
        while self.running:
            time.sleep(0.1)
