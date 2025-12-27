import os
import sys
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from datetime import datetime

import torch
import whisper

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QApplication, 
    QTextEdit, QScrollArea
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal,
    pyqtProperty, QPropertyAnimation, QRectF
)
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtSvg import QSvgRenderer

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# Troque para: tiny / base / small / medium
WHISPER_MODEL = whisper.load_model("small").to(DEVICE)

class AudioRecorder(QThread):
    finished = pyqtSignal(str)

    def __init__(self, samplerate=44100):
        super().__init__()
        self.samplerate = samplerate
        self.recording = True
        self.audio_data = []

    def run(self):
        with sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            callback=self.callback
        ):
            while self.recording:
                sd.sleep(100)

        audio = np.concatenate(self.audio_data, axis=0)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        audio_dir = os.path.join(base_dir, "recordings")
        os.makedirs(audio_dir, exist_ok=True)

        filename = os.path.join(
            audio_dir,
            f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        )

        write(filename, self.samplerate, audio)
        self.finished.emit(filename)

    def callback(self, indata, frames, time, status):
        if self.recording:
            self.audio_data.append(indata.copy())

    def stop(self):
        self.recording = False

class TranscriberThread(QThread):
    finished = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, audio_path, language="pt"):
        super().__init__()
        self.audio_path = audio_path
        self.language = language

    def run(self):
        try:
            if not os.path.exists(self.audio_path):
                self.log.emit("Erro: Arquivo não encontrado.")
                return

            self.log.emit("Transcrevendo...")
            result = WHISPER_MODEL.transcribe(
                self.audio_path,
                language=self.language,
                verbose=False
            )
            text = result.get("text", "").strip()
            self.finished.emit(text)

        except Exception as e:
            self.finished.emit(f"Erro na transcrição: {str(e)}")

SVG_MIC = """<svg viewBox="-3 0 19 19" xmlns="http://www.w3.org/2000/svg"><path fill="white" d="M11.665 7.915v1.31a5.257 5.257 0 0 1-1.514 3.694a5.174 5.174 0 0 1-1.641 1.126 5.04 5.04 0 0 1-1.456.384v1.899h2.312a.554.554 0 0 1 0 1.108H3.634a.554.554 0 0 1 0-1.108h2.312v-1.899a5.045 5.045 0 0 1-1.456-.384 5.174 5.174 0 0 1-1.641-1.126a5.257 5.257 0 0 1-1.514-3.695v-1.31a.554.554 0 1 1 1.109 0v1.31a4.131 4.131 0 0 0 1.195 2.917 3.989 3.989 0 0 0 5.722 0a4.133 4.133 0 0 0 1.195-2.917v-1.31a.554.554 0 1 1 1.109 0zM3.77 10.37a2.875 2.875 0 0 1-.233-1.146V4.738A2.905 2.905 0 0 1 3.77 3.58a3 3 0 0 1 1.59-1.59a2.902 2.902 0 0 1 1.158-.233 2.865 2.865 0 0 1 1.152.233a2.977 2.977 0 0 1 1.793 2.748l-.012 4.487a2.958 2.958 0 0 1-.856 2.09a3.025 3.025 0 0 1-.937.634a2.865 2.865 0 0 1-1.152.233a2.905 2.905 0 0 1-1.158-.233A2.957 2.957 0 0 1 3.77 10.37z"/></svg>"""

class RecordButton(QWidget):
    clicked = pyqtSignal()
    def __init__(self, size=80):
        super().__init__()
        self.setFixedSize(size, size)
        self._bg_color = QColor("#555555")
        self.renderer = QSvgRenderer(bytearray(SVG_MIC, encoding="utf-8"))
        self.anim = QPropertyAnimation(self, b"bgColor", self)
        self.anim.setDuration(350)

    def mousePressEvent(self, event):
        self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self._bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())
        size = int(self.width() * 0.45)
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        self.renderer.render(painter, QRectF(x, y, size, size))

    def animate_to(self, color_hex):
        self.anim.stop()
        self.anim.setStartValue(self._bg_color)
        self.anim.setEndValue(QColor(color_hex))
        self.anim.start()

    def getBgColor(self): return self._bg_color
    def setBgColor(self, color): 
        self._bg_color = color
        self.update()
    bgColor = pyqtProperty(QColor, getBgColor, setBgColor)

class BotUI(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = None
        self.is_recording = False
        self.setWindowTitle("Whisper Transcriber Pro")

        # Layout Principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Status
        self.status = QLabel("Toque no botão para gravar")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-weight: bold; font-size: 16px; color: #bbb;")
        self.main_layout.addWidget(self.status)

        # Campo de Texto Transcrito (Substituindo Label por QTextEdit)
        self.transcription_display = QTextEdit()
        self.transcription_display.setReadOnly(True) # Apenas leitura
        self.transcription_display.setPlaceholderText("O texto transcrito aparecerá aqui...")
        self.transcription_display.setStyleSheet("""
            QTextEdit {
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 10px;
                padding: 15px;
                font-size: 15px;
                line-height: 150%;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 5px;
            }
        """)
        # Adiciona ao layout com stretch para ocupar o espaço disponível
        self.main_layout.addWidget(self.transcription_display, stretch=1)

        # Container para o botão (centralizado)
        self.button_layout = QVBoxLayout()
        self.button = RecordButton(100)
        self.button.clicked.connect(self.toggle_recording)
        self.button_layout.addWidget(self.button, alignment=Qt.AlignCenter)
        self.main_layout.addLayout(self.button_layout)

    def toggle_recording(self):
        if not self.is_recording:
            self.recorder = AudioRecorder()
            self.recorder.finished.connect(self.finished_audio)
            self.recorder.start()
            self.button.animate_to("#2ecc71") # Vermelho gravando
            self.status.setText("Gravando áudio...")
            self.is_recording = True
        else:
            self.recorder.stop()
            self.status.setText("Processando arquivo...")
            self.is_recording = False

    def finished_audio(self, filename):
        self.button.animate_to("#555555")
        self.status.setText("transcrevendo...")
        
        self.transcriber = TranscriberThread(filename)
        self.transcriber.finished.connect(self.show_transcription)
        self.transcriber.start()

    def show_transcription(self, text):
        self.status.setText("✅ Transcrição Concluída")
        if text:
            self.transcription_display.setPlainText(text)
        else:
            self.transcription_display.setPlainText("(Nenhum som detectado)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Estilo mais moderno
    
    window = BotUI()
    window.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
            color: white;
            font-family: 'Segoe UI', Arial;
        }
    """)
    # Tamanho inicial maior (800x600) e permite redimensionar
    window.resize(700, 600)
    window.show()
    sys.exit(app.exec_())