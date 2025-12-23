import sys
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from datetime import datetime

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal,
    pyqtProperty, QPropertyAnimation, QRectF
)
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer

# ===================== FASTER-WHISPER =====================
#from faster_whisper import WhisperModel

# ===================== AUDIO =====================

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
        filename = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        write(filename, self.samplerate, audio)
        self.finished.emit(filename)

    def callback(self, indata, frames, time, status):
        if self.recording:
            self.audio_data.append(indata.copy())

    def stop(self):
        self.recording = False

# ===================== TRANSCRIBER =====================

class TranscriberThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path

    def run(self):
        # Carregar modelo uma vez
        # model = WhisperModel("base")  # tiny, base, small, medium, large
        # segments, _ = model.transcribe(self.audio_path, language="pt")
        # text = " ".join([segment.text for segment in segments]).strip()
        self.finished.emit('Transcrição simulada do áudio.')

# ===================== BOTÃO SVG =====================

SVG_MIC = """
<svg viewBox="-3 0 19 19" xmlns="http://www.w3.org/2000/svg">
<path fill="white" d="M11.665 7.915v1.31a5.257 5.257 0 0 1-1.514 3.694
a5.174 5.174 0 0 1-1.641 1.126 5.04 5.04 0 0 1-1.456.384v1.899h2.312
a.554.554 0 0 1 0 1.108H3.634a.554.554 0 0 1 0-1.108h2.312v-1.899
a5.045 5.045 0 0 1-1.456-.384 5.174 5.174 0 0 1-1.641-1.126
a5.257 5.257 0 0 1-1.514-3.695v-1.31a.554.554 0 1 1 1.109 0v1.31
a4.131 4.131 0 0 0 1.195 2.917 3.989 3.989 0 0 0 5.722 0
a4.133 4.133 0 0 0 1.195-2.917v-1.31a.554.554 0 1 1 1.109 0z
M3.77 10.37a2.875 2.875 0 0 1-.233-1.146V4.738
A2.905 2.905 0 0 1 3.77 3.58a3 3 0 0 1 1.59-1.59
a2.902 2.902 0 0 1 1.158-.233 2.865 2.865 0 0 1 1.152.233
a2.977 2.977 0 0 1 1.793 2.748l-.012 4.487
a2.958 2.958 0 0 1-.856 2.09
a3.025 3.025 0 0 1-.937.634
a2.865 2.865 0 0 1-1.152.233
a2.905 2.905 0 0 1-1.158-.233
A2.957 2.957 0 0 1 3.77 10.37z"/>
</svg>
"""

class RecordButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, size=100):
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
    
        # Fundo circular
        painter.setBrush(self._bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())
    
        # SVG centralizado
        size = int(self.width() * 0.45)
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        rect = QRectF(x, y, size, size)
        self.renderer.render(painter, rect)

    def animate_to(self, color_hex):
        self.anim.stop()
        self.anim.setStartValue(self._bg_color)
        self.anim.setEndValue(QColor(color_hex))
        self.anim.start()

    def getBgColor(self):
        return self._bg_color

    def setBgColor(self, color):
        self._bg_color = color
        self.update()

    bgColor = pyqtProperty(QColor, getBgColor, setBgColor)

# ===================== UI =====================

class BotUI(QWidget):
    def __init__(self):
        super().__init__()

        self.recorder = None
        self.is_recording = False

        self.setWindowTitle("Gravador")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.status = QLabel("Clique para gravar")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        self.transcription_label = QLabel("")
        self.transcription_label.setWordWrap(True)
        self.transcription_label.setAlignment(Qt.AlignTop)
        self.transcription_label.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                padding: 10px;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.transcription_label)

        self.button = RecordButton(110)
        self.button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.button)

    def toggle_recording(self):
        if not self.is_recording:
            self.recorder = AudioRecorder()
            self.recorder.finished.connect(self.finished)
            self.recorder.start()

            self.button.animate_to("#2ecc71")  # verde
            self.status.setText("🔴 Gravando...")
            self.is_recording = True
        else:
            self.recorder.stop()
            self.status.setText("Salvando...")
            self.is_recording = False

    def finished(self, filename):
        self.button.animate_to("#555555")
        self.status.setText("🧠 Transcrevendo...")
        self.transcription_label.setText("")

        self.transcriber = TranscriberThread(filename)
        self.transcriber.finished.connect(self.show_transcription)
        self.transcriber.start()

    def show_transcription(self, text):
        self.status.setText("✅ Transcrição pronta")
        self.transcription_label.setText(text if text else "(Nenhum texto detectado)")

# ===================== MAIN =====================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = BotUI()
    window.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
            color: white;
            font-size: 14px;
        }
    """)
    window.resize(420, 400)
    window.show()

    sys.exit(app.exec_())
