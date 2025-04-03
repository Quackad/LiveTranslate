from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QComboBox,
    QLabel, QPushButton, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal
import sys
import soundcard as sc
import speech_recognition as sr 
from googletrans import Translator 
from gtts import gTTS 
import os 
import numpy as np
import time

#Using pydub and simpleaudio instead of playsound because playsound fucking hates windows for some reason
from pydub import AudioSegment
from pydub.playback import play

recognizer = sr.Recognizer()
translator = Translator()

class TranslatorThreat(QThread):
    update_text = pyqtSignal(str, str)

    def __init__(self, device_name, target_lang):
        super().__init__()
        self.device_name = device_name
        self.target_lang = target_lang
        self.running = True 

    def run(self):
        mic = sc.get_microphone(self.device_name,include_loopback=True)
        with mic.recorder(samplerate=16000) as recorder:
            while self.running:
                data = recorder.record(numframes=16000)
                audio = sr.AudioDate(data.tobytes(), 16000, 2)
                try: 
                    text = recognizer.recognize_google(audio, language='en')
                    translated = translator.translate(text, dest=self.target_lang).text
                    self.update_text.emit(text, translated)

                    tts = gTTS(translated, lang=self.target_lang)
                    tts.save(translated.mp3)
                    audio = AudioSegment.from_fuile("translated.mp3", format="mp3")
                    play(audio)
                    os.remove("translated.mp3")

                except sr.UnkownValueError:
                    continue
    
    def stop(self):
        self.running = False
        self.quit()

class AudioTranslatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Translator :)")
        self.setGeometry(100,100, 600, 400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        #Mic input select
        self.device_dropdown = QComboBox()
        self.device_dropdown.addItems(
            [str(m) for m in sc.all_microphones(include_loopback=True)]
        )
        self.layout.addWidget(QLabel("Select Audio Input:"))
        self.layout.addWidget(self.device_dropdown)

        self.lang_dropdown = QComboBox()
        self.lang_dropdown.addItems({
            "Spanish": "es", "French": "fr", "German": "de", "Japanese": "Ja", "Chinese": "zh-cn", "Arabic": "ar", "Russian": "ru"
        }.keys())
        self.layout.addWidget(QLabel("Translate to:"))
        self.layout.addWidget(self.lang_dropdown)

        self.btn_start = QPushButton("Start Translating")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_start.clicked.connect(self.start_translation)
        self.btn_stop.clicked.connect(self.stop_translation)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        self.layout.addLayout(btn_layout)

        self.text_original = QTextEdit()
        self.text_original.setReadOnly(True)
        self.text_translated = QTextEdit()
        self.text_translated.setReadOnly(True)
        self.layout.addWidget(QLabel("Heard:"))
        self.layout.addWidget(self.text_original)
        self.layout.addWidget(QLabel("Translated:"))
        self.layout.addWidget(self.text_translated)

        self.thread = None

    def start_translation(self):
        device = self.device_dropdown.currentText()
        lang = {
            "Spanish": "es", "French": "fr", "German": "de", "Japanese": "Ja", "Chinese": "zh-cn", "Arabic": "ar", "Russian": "ru"
        }[self.lang_dropdown.currentText()]
        self.thread = TranslatorThreat(device,lang)
        self.thread.update_text.connect(self.display_text)
        self.thread.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def stop_translation(self):
        if self.thread:
            self.thread.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def display_text(self, original, translated):
        self.text_original.append(original)
        self.text_translated.append(translated)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioTranslatorApp()
    window.show()
    sys.exit(app.exec())

        
