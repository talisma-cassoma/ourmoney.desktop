from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QScrollArea,
                             QLineEdit, QFormLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QComboBox, QProgressBar, QWidget)
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime
from syncdata import SyncManager  # Certifique-se de ter o arquivo syncData.py
from db import (get_all_transactions, create_table, insert_transaction, delete_transaction)

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sync_manager = SyncManager(self)  # Passando a referência
        self.initUI()

        # Cria um temporizador para atualizar o status de conexão
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

    def initUI(self):
        self.setWindowTitle("OUR-MONKEY")
        self.setGeometry(100, 100, 1000, 600)

        self.main_frame = QFrame()
        self.main_layout = QVBoxLayout(self.main_frame)

        # Coluna superior com status e sincronização
        self.status_frame = QFrame()
        self.status_layout = QHBoxLayout(self.status_frame)

        self.status_label = QLabel("Status: Checando...")
        self.status_layout.addWidget(self.status_label)

        self.sync_button = QPushButton("Sincronizar")
        self.sync_button.clicked.connect(self.sync_and_show_progress)
        self.status_layout.addWidget(self.sync_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.status_layout.addWidget(self.progress_bar)

        self.main_layout.addWidget(self.status_frame)

        # Inputs para adicionar transações
        self.transaction_inputs_frame = QFrame()
        self.transaction_inputs_layout = QFormLayout(self.transaction_inputs_frame)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText('Descrição')

        self.type_input = QComboBox()
        self.type_input.addItems(["saida", "entrada"])

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText('Categoria')

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText('Preço')

        self.add_button = QPushButton(text="Adicionar Transação")
        self.add_button.clicked.connect(self.add_transaction)

        # Adiciona os widgets de input ao layout
        self.transaction_inputs_layout.addRow('Descrição:', self.description_input)
        self.transaction_inputs_layout.addRow('Tipo:', self.type_input)
        self.transaction_inputs_layout.addRow('Categoria:', self.category_input)
        self.transaction_inputs_layout.addRow('Preço:', self.price_input)
        self.transaction_inputs_layout.addRow(self.add_button)

        self.main_layout.addWidget(self.transaction_inputs_frame)

        # Área inferior para exibir transações registradas
        self.transaction_list_frame = QFrame()
        self.transaction_list_layout = QVBoxLayout(self.transaction_list_frame)

        self.transactions_label = QLabel('Transações Registradas')
        self.transaction_list_layout.addWidget(self.transactions_label)

        self.transaction_scroll_area = QScrollArea()
        self.transaction_scroll_area.setWidgetResizable(True)
        self.transaction_list_widget = QWidget()
        self.transaction_list_layout_inside = QVBoxLayout(self.transaction_list_widget)
        self.transaction_list_widget.setLayout(self.transaction_list_layout_inside)

        self.transaction_scroll_area.setWidget(self.transaction_list_widget)
        self.transaction_list_layout.addWidget(self.transaction_scroll_area)

        self.main_layout.addWidget(self.transaction_list_frame)

        self.setCentralWidget(self.main_frame)

        # Carregar as transações já registradas
        self.load_collection()
    
    def update_status(self):
        online = self.sync_manager.is_online()
        if online:
            self.status_label.setText("Status: Online")
        else:
            self.status_label.setText("Status: Offline")

    def sync_and_show_progress(self):
        self.progress_bar.setValue(0)
        for i in range(1, 101):
            self.progress_bar.setValue(i)
            QApplication.processEvents()

        self.sync_manager.pull_data()  # Chama a função que puxa os dados
        self.progress_bar.setValue(100)

    def add_transaction(self):
        description = self.description_input.text()
        trans_type = self.type_input.currentText()
        category = self.category_input.text()
        price = self.price_input.text()

        if description and trans_type and category and price:
            insert_transaction(description, ("income" if trans_type == "entrada" else "outcome"), category, float(price))
            self.load_collection()  # Recarrega as transações
            self.clear_inputs()

    def load_collection(self):
        for i in reversed(range(self.transaction_list_layout_inside.count())):
            widget = self.transaction_list_layout_inside.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        transactions = get_all_transactions()
        for transaction in transactions:
            # Converter a tupla para lista para que possamos modificar os valores
            transaction = list(transaction)
            # Modificar o tipo da transação conforme necessário
            if transaction[2] == 'income':
                transaction[2] = 'entrada'
            elif transaction[2] == 'outcome':
                transaction[2] = 'saida'

            frame = TransactionCard(*transaction)
            self.transaction_list_layout_inside.addWidget(frame)

    def clear_inputs(self):
        self.description_input.clear()
        self.category_input.clear()
        self.price_input.clear()


class TransactionCard(QFrame):
    def __init__(self, trans_id, description, trans_type, category, price, owner, email, createdAt, synced):
        super().__init__()
        layout = QHBoxLayout(self)
        
        # Estilo da transação
        self.setStyleSheet("""
            border-radius: 10px;
            padding: 2px;
            background-color: rgb(41, 41, 46);
            height: 20px;
            margin-bottom: 4px;
        """)

        # Descrição
        desc_label = QLabel(f'{description}')
        layout.addWidget(desc_label)

        # Tipo
        type_label = QLabel(f'{trans_type}')
        layout.addWidget(type_label)
        
        # Categoria
        category_label = QLabel(f'{category}')
        layout.addWidget(category_label)
        
        # Preço
        price_label = QLabel(f'DH$ {price:.2f}')
        price_color = (79, 255, 203) if trans_type == "entrada" else (247, 91, 105)
        price_label.setStyleSheet(f'color: rgb{price_color};')
        layout.addWidget(price_label)

        # Data e Sincronizado
        parsed_datetime = datetime.strptime(createdAt, '%Y-%m-%d %H:%M:%S.%f')
        formatted_datetime = parsed_datetime.strftime("%Y-%m-%d")
        createdAt_label = QLabel(f'{formatted_datetime}')
        layout.addWidget(createdAt_label)
        
        synced_color = (79, 255, 203) if synced else (128, 128, 128)
        synced_label = QLabel(f'{("sincronizado" if synced else "desincronizado")}')
        synced_label.setStyleSheet(f'color: rgb{synced_color};')
        layout.addWidget(synced_label)

        # Botão Deletar
        delete_button = QPushButton('Deletar')
        delete_button.clicked.connect(lambda: self.delete_transaction(trans_id))
        layout.addWidget(delete_button)

    def delete_transaction(self, trans_id):
        delete_transaction(trans_id)
        self.setParent(None)  # Remove a transação da interface


def main():
    app = QApplication([])
    app.setStyle('Fusion')
    window = Main()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
