from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QScrollArea,
                             QLineEdit, QFormLayout, QHBoxLayout, QFrame, QDateEdit,
                             QPushButton, QLabel, QComboBox)
from PyQt5.QtCore import Qt

from datetime import datetime

from db import (get_all_transactions, create_table, insert_transaction, delete_transaction)


class CreateTransaction(QFrame):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Passa a referência para a janela principal

        # Inputs para os detalhes da transação
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText('Descrição')

        self.type_input = QComboBox()
        self.type_input.addItems(["Saída","Entrada"])

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText('Categoria')

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText('Preço')

        self.add_button = QPushButton(text="Adicionar Transação")
        # Conectar o botão à função add_transaction
        self.add_button.clicked.connect(self.add_transaction)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Descrição:'))
        layout.addWidget(self.description_input)
        layout.addWidget(QLabel('Tipo:'))
        layout.addWidget(self.type_input)
        layout.addWidget(QLabel('Categoria:'))
        layout.addWidget(self.category_input)
        layout.addWidget(QLabel('Preço:'))
        layout.addWidget(self.price_input)
        layout.addWidget(self.add_button)

    def add_transaction(self):
        description = self.description_input.text()
        trans_type = self.type_input.currentText()
        category = self.category_input.text()
        price = self.price_input.text()

        # Campos padrão para owner e email
        #owner = 'talisma'
        #email = 'talisma@email.com'

        if description and trans_type and category and price:
            insert_transaction(description, trans_type, category, float(price))
            # Recarregar as transações após adicionar
            self.main_window.load_collection()
            # Limpar os campos de entrada
            self.description_input.clear()
            self.category_input.clear()
            self.price_input.clear()


class TransactionCard(QFrame):
    def __init__(self, trans_id, description, trans_type, category, price, owner, email, created_at):
        super().__init__()
        self.setStyleSheet(
            'background:white; border-radius:4px; color:black;'
        )
        self.setFixedHeight(150)
        self.trans_id = trans_id
        layout = QVBoxLayout()

        label = QLabel(f'<strong>{description}</strong>')
        date_label = QLabel(f"Tipo: {trans_type}, Categoria: {category}, Preço: {price}")

        # Ajuste o formato de data para incluir horas, minutos e segundos
        parsed_datetime = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f")
        formatted_datetime = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_created = QLabel(f"Data de Criação: {formatted_datetime}")

        delete_button = QPushButton(text='Deletar', clicked=self.delete_transaction_click)
        delete_button.setStyleSheet('background:red; padding:4px;')

        layout.addWidget(label)
        layout.addWidget(date_label)
        layout.addWidget(date_created)
        layout.addWidget(delete_button)
        layout.addStretch()
        self.setLayout(layout)

    def delete_transaction_click(self):
        delete_transaction(self.trans_id)
        self.close()


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_collection()

    def initUI(self):
        self.main_frame = QFrame()
        self.main_layout = QVBoxLayout(self.main_frame)

        # Adicionar o widget de registro de transações
        self.register_widget = CreateTransaction(self)
        self.main_layout.addWidget(self.register_widget)

        transactions_label = QLabel('Transações Registradas')
        transactions_label.setStyleSheet('font-size:18px;')
        self.main_layout.addWidget(transactions_label)
        self.transaction_collection_area()

        self.setCentralWidget(self.main_frame)

    def transaction_collection_area(self):
        scroll_frame = QFrame()
        self.transaction_collection_layout = QVBoxLayout(scroll_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_frame)
        scroll.setStyleSheet('QScrollArea{border:0px}')

        self.transaction_collection_layout.addStretch()
        self.main_layout.addWidget(scroll)

    def load_collection(self):
        # Limpar as transações anteriores antes de recarregar
        for i in reversed(range(self.transaction_collection_layout.count())):
            widget = self.transaction_collection_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        transactions = get_all_transactions()
        for transaction in transactions:
            frame = TransactionCard(*transaction)
            self.transaction_collection_layout.insertWidget(0, frame)


def main():
    app = QApplication([])
    app.setStyle('fusion')
    win = Main()
    win.show()
    app.exec_()


if __name__ == '__main__':
    main()
