import os
import sys
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from datetime import datetime
import json
import uuid
import subprocess
import torch
import whisper # Oficial para estabilidade no Mac

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QApplication, 
    QTextEdit
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal,
    pyqtProperty, QPropertyAnimation, QRectF
)
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer

# --- CONFIGURAÇÃO DE DISPOSITIVO (MAC MPS) ---
if torch.backends.mps.is_available():
    DEVICE = "mps"
else:
    DEVICE = "cpu"

# Variáveis Globais para os Modelos (Carregados via Warmup)
WHISPER_MODEL = None
EXTRACTOR_INSTANCE = None

# --- SCHEMA E CONFIGURAÇÕES ORIGINAIS ---
from typing import Literal
import pandas as pd
#from laurium.decoder_models import llm, prompts, pydantic_models, extract
from langchain_core.output_parsers import PydanticOutputParser

schema = {
    "id": uuid.UUID,
    "description": str,
    "type": Literal["income", "outcome"],
    "category": str,
    "price": float,
    "owner": str,
    "email": str,
    "createdAt": datetime,
    "status": Literal["synced", "unsynced"]
}

descriptions = {
    "id": "Unique UUID for the transaction",
    "description": "Descrição do gasto/entrada",
    "type": "Se o registro é income ou outcome",
    "category": "Categoria do gasto/entrada",
    "price": "Valor numérico (float)",
    "owner": "Nome do dono do gasto/entrada por padrão é Bot",
    "email": "E-mail associado,por padrão é bot@ourmoney.com",
    "createdAt": "Data e hora em ISO8601",
    "status": "Status de sincronização synced ou unsynced, por padrão é unsynced"
}

# --- CLASSE DE EXTRAÇÃO (Lógica Original) ---
class ExpenseExtractor:
    def __init__(self):
        # Sugestão: Use qwen2.5:1.5b no Mac Air para ser instantâneo. 
        # Se preferir o 7b, apenas mude o nome abaixo.
        self.llm = llm.create_llm(
            llm_platform="ollama",
            model_name="qwen2.5:1.5b", 
            temperature=0.0
        )

        system_message = prompts.create_system_message(
            base_message=(
                "Você é um sistema de extração de transações financeiras.\n\n"
                "Sua tarefa é analisar um texto em português brasileiro e extrair "
                "APENAS transações financeiras reais.\n\n"

                "REGRAS OBRIGATÓRIAS:\n"
                "1. Retorne SOMENTE JSON válido, sem explicações, comentários ou texto extra.       \n"
                "2. O JSON deve seguir EXATAMENTE o schema fornecido.\n"
                "3. Se não houver nenhuma transação financeira clara, retorne uma lista         vazia [].\n"
                "4. Cada transação deve gerar UM objeto JSON separado.\n\n"

                "REGRAS DE INTERPRETAÇÃO:\n"
                "- 'gastei', 'paguei', 'comprei' → type = outcome\n"
                "- 'recebi', 'ganhei', 'salário', 'pix recebido' → type = income\n"
                "- Se o valor não for explícito, NÃO crie a transação.\n"
                "- Valores devem ser convertidos para float (ex: 'vinte reais' → 20.0).\n\n"

                "CATEGORIAS:\n"
                "- Alimentos (mercado, padaria, restaurante, lanche)\n"
                "- Transporte (uber, ônibus, gasolina)\n"
                "- Moradia (aluguel, luz, água, internet)\n"
                "- Lazer (cinema, jogos, streaming)\n"
                "- Saúde (farmácia, médico)\n"
                "- Outros (se não se encaixar claramente)\n\n"

                "PADRÕES:\n"
                "- owner: sempre 'Bot'\n"
                "- email: sempre 'bot@ourmoney.com'\n"
                "- status: sempre 'unsynced'\n"
            ),
            keywords=list(descriptions.values())
        )       


        self.prompt = prompts.create_prompt(
            system_message=system_message,
            examples=None,
            example_human_template=None,
            example_assistant_template=None,
            final_query=(
                "Texto para análise:\n\n{text}\n\n"
                "Extraia todas as transações financeiras conforme as regras "
                "e retorne apenas o JSON."),
            schema=schema,
            descriptions=descriptions
        )

        self.OutputModel = pydantic_models.make_dynamic_example_model(
            schema=schema,
            descriptions=descriptions,
            model_name="Expense"
        )

        self.parser = PydanticOutputParser(pydantic_object=self.OutputModel)

        self.extractor = extract.BatchExtractor(
            llm=self.llm,
            prompt=self.prompt,
            parser=self.parser
        )

    def extract(self, text: str) -> list:
        df = pd.DataFrame({"text": [text]})
        result = self.extractor.process_chunk(df, text_column="text")
        data = result.to_dict(orient="records")

        now = datetime.utcnow().isoformat() + "Z"
        for item in data:
            item["id"] = str(uuid.uuid4())
            item["createdAt"] = now
            item["status"] = "unsynced"
            item.setdefault("owner", "Bot")
            item.setdefault("email", "bot@ourmoney.com")


# --- THREADS DE PROCESSAMENTO ---

class WarmupThread(QThread):
    """Thread para carregar os modelos sem travar a UI"""
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def run(self):
        global WHISPER_MODEL, EXTRACTOR_INSTANCE
        self.status.emit("Iniciando Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.status.emit("Carregando Whisper (Base)...")
        # 'base' é muito mais rápido que 'small' no Mac Air e evita SegFault
        WHISPER_MODEL = whisper.load_model("base").to(DEVICE)
        
        # self.status.emit("Configurando Extrator...")
        # EXTRACTOR_INSTANCE = ExpenseExtractor()
        
        self.status.emit("Sistema Pronto")
        self.finished.emit()

class AudioRecorder(QThread):
    finished = pyqtSignal(str)
    def __init__(self, samplerate=16000):
        super().__init__()
        self.samplerate, self.recording, self.audio_data = samplerate, True, []

    def run(self):
        with sd.InputStream(samplerate=self.samplerate, channels=1, callback=self.callback):
            while self.recording: sd.sleep(100)
        audio = np.concatenate(self.audio_data, axis=0)
        filename = f"temp_audio.wav"
        write(filename, self.samplerate, audio)
        self.finished.emit(filename)

    def callback(self, indata, frames, time, status):
        if self.recording: self.audio_data.append(indata.copy())
    def stop(self): self.recording = False

class ProcessingPipeline(QThread):
    """Executa Transcrição e depois Extração"""
    transcription_ready = pyqtSignal(str)
    extraction_ready = pyqtSignal(list)

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path

    def run(self):
        # 1. Transcrição
        result = WHISPER_MODEL.transcribe(self.audio_path, language="pt", fp16=False)
        text = result.get("text", "").strip()
        self.transcription_ready.emit(text)

        # # 2. Extração (se houver texto)
        # if text:
        #     expenses = EXTRACTOR_INSTANCE.extract(text)
        #     self.extraction_ready.emit(expenses)

# --- UI COMPONENTS ---

SVG_MIC = """<svg viewBox="-3 0 19 19" xmlns="http://www.w3.org/2000/svg"><path fill="white" d="M11.665 7.915v1.31a5.257 5.257 0 0 1-1.514 3.694a5.174 5.174 0 0 1-1.641 1.126 5.04 5.04 0 0 1-1.456.384v1.899h2.312a.554.554 0 0 1 0 1.108H3.634a.554.554 0 0 1 0-1.108h2.312v-1.899a5.045 5.045 0 0 1-1.456-.384 5.174 5.174 0 0 1-1.641-1.126a5.257 5.257 0 0 1-1.514-3.695v-1.31a.554.554 0 1 1 1.109 0v1.31a4.131 4.131 0 0 0 1.195 2.917 3.989 3.989 0 0 0 5.722 0a4.133 4.133 0 0 0 1.195-2.917v-1.31a.554.554 0 1 1 1.109 0zM3.77 10.37a2.875 2.875 0 0 1-.233-1.146V4.738A2.905 2.905 0 0 1 3.77 3.58a3 3 0 0 1 1.59-1.59a2.902 2.902 0 0 1 1.158-.233 2.865 2.865 0 0 1 1.152.233a2.977 2.977 0 0 1 1.793 2.748l-.012 4.487a2.958 2.958 0 0 1-.856 2.09a3.025 3.025 0 0 1-.937.634a2.865 2.865 0 0 1-1.152.233a2.905 2.905 0 0 1-1.158-.233A2.957 2.957 0 0 1 3.77 10.37z"/></svg>"""

class RecordButton(QWidget):
    clicked = pyqtSignal()
    def __init__(self, size=80):
        super().__init__()
        self.setFixedSize(size, size)
        self._bg_color = QColor("#555555")
        self.renderer = QSvgRenderer(bytearray(SVG_MIC, encoding="utf-8"))
        self.anim = QPropertyAnimation(self, b"bgColor", self)
    def mousePressEvent(self, event): self.clicked.emit()
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(self._bg_color); p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, self.width(), self.height())
        s = int(self.width() * 0.45)
        self.renderer.render(p, QRectF((self.width()-s)//2, (self.height()-s)//2, s, s))
    def animate_to(self, color_hex):
        self.anim.stop()
        self.anim.setDuration(350)
        self.anim.setEndValue(QColor(color_hex))
        self.anim.start()
    def getBgColor(self): return self._bg_color
    def setBgColor(self, c): self._bg_color = c; self.update()
    bgColor = pyqtProperty(QColor, getBgColor, setBgColor)

# --- CLASSE BotUI (Mantendo seu design original) ---

class BotUI(QWidget):
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.setWindowTitle("OurMoney Transcriber")
        
        # Layout Principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Status
        self.status = QLabel("Iniciando IA...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-weight: bold; font-size: 16px; color: #bbb;")
        self.main_layout.addWidget(self.status)

        # Display de Transcrição
        self.transcription_display = QTextEdit()
        self.transcription_display.setReadOnly(True)
        self.transcription_display.setPlaceholderText("O texto aparecerá aqui...")
        self.transcription_display.setStyleSheet("""
            QTextEdit { background-color: #252525; color: #e0e0e0; border-radius: 10px; padding: 15px; font-size: 15px; }
        """)
        self.main_layout.addWidget(self.transcription_display, stretch=1)

        # Botão
        self.button = RecordButton(100)
        self.button.clicked.connect(self.toggle_recording)
        self.button.setEnabled(False) # Só ativa quando o warmup acabar
        self.main_layout.addWidget(self.button, alignment=Qt.AlignCenter)

        # Inicia Warmup
        self.warmup = WarmupThread()
        self.warmup.status.connect(self.status.setText)
        self.warmup.finished.connect(self.on_warmup_finished)
        self.warmup.start()

    def on_warmup_finished(self):
        self.button.setEnabled(True)
        self.status.setText("Toque para gravar")
        self.button.animate_to("#3498db")

    def toggle_recording(self):
        if not self.is_recording:
            self.recorder = AudioRecorder()
            self.recorder.finished.connect(self.start_processing)
            self.recorder.start()
            self.button.animate_to("#e74c3c")
            self.status.setText("Gravando...")
            self.is_recording = True
        else:
            self.recorder.stop()
            self.button.animate_to("#3498db")
            self.status.setText("Processando...")
            self.is_recording = False

    def start_processing(self, filename):
        self.pipeline = ProcessingPipeline(filename)
        self.pipeline.transcription_ready.connect(self.show_transcription)
        self.pipeline.extraction_ready.connect(self.show_json)
        self.pipeline.start()

    def show_transcription(self, text):
        self.transcription_display.setPlainText(f"🗣️ Transcrição:\n{text}")
        self.status.setText("Extraindo dados...")

    def show_json(self, expenses):
        self.status.setText("✅ Concluído")
        self.transcription_display.append("\n\n📊 JSON Gerado:")
        self.transcription_display.append(json.dumps(expenses, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = BotUI()
    window.setStyleSheet("QWidget { background-color: #1a1a1a; color: white; font-family: 'Segoe UI'; }")
    window.resize(600, 700)
    window.show()
    sys.exit(app.exec_())