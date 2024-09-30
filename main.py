from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QScrollArea,
                             QLineEdit, QFormLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QComboBox, QProgressBar, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)

from PyQt5.QtCore import Qt, QTimer
from datetime import datetime
from syncdata import SyncManager
from db import (get_all_transactions, create_table, insert_transaction, delete_transaction)

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sync_manager = SyncManager(self)
        self.initUI()

        # Timer for updating the status of connection
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

    def initUI(self):
        self.setWindowTitle("OUR-MONKEY")
        self.setGeometry(100, 100, 1000, 600)

        self.main_frame = QFrame()
        self.main_layout = QVBoxLayout(self.main_frame)

        # Status and sync area at the top
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

        # Two blocks (side by side) for transaction input and totals
        self.blocks_frame = QFrame()
        self.blocks_layout = QHBoxLayout(self.blocks_frame)
        self.blocks_frame.setStyleSheet("background-color: rgb(41, 41, 46); border-radius: 16px;")

        # Block 1: Transaction inputs
        self.transaction_inputs_frame = QFrame()
        self.transaction_inputs_frame.setFixedWidth(400)
        self.transaction_inputs_frame.setStyleSheet("background-color: rgb(61, 61, 66); border-radius: 16px;")
        self.transaction_inputs_layout = QFormLayout(self.transaction_inputs_frame)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText('Descrição')

        self.type_input = QComboBox()
        self.type_input.setStyleSheet("color: white;")
        self.type_input.addItems(["saida", "entrada"])

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText('Categoria')

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText('Preço')

        self.add_button = QPushButton(text="Adicionar Transação")
        self.add_button.clicked.connect(self.add_transaction)

        # Add widgets to the layout
        self.transaction_inputs_layout.addRow('Descrição:', self.description_input)
        self.transaction_inputs_layout.addRow('Tipo:', self.type_input)
        self.transaction_inputs_layout.addRow('Categoria:', self.category_input)
        self.transaction_inputs_layout.addRow('Preço:', self.price_input)
        self.transaction_inputs_layout.addRow(self.add_button)

        # Add block 1 to the main layout
        self.blocks_layout.addWidget(self.transaction_inputs_frame)

        # Block 2: Total incomes and expenses
        self.totals_frame = QFrame()
        self.totals_frame.setStyleSheet("background-color: rgb(61, 61, 66); border-radius: 16px; padding: 10px;")
        self.totals_layout = QVBoxLayout(self.totals_frame)

        self.income_label = QLabel(f'Entradas: {self.sync_manager.get_total_of_income_transactons()}')
        self.expense_label = QLabel(f'Saídas:  {self.sync_manager.get_total_of_outcome_transactons()}')
        self.income_label.setStyleSheet("color: rgb(79, 255, 203);")
        self.expense_label.setStyleSheet("color: rgb(247, 91, 105);")

        self.totals_layout.addWidget(self.income_label)
        self.totals_layout.addWidget(self.expense_label)

        # Add block 2 to the main layout
        self.blocks_layout.addWidget(self.totals_frame)

        self.main_layout.addWidget(self.blocks_frame)

        # Block 3: List of registered transactions using QTableWidget
        self.transaction_list_frame = QFrame()
        self.transaction_list_frame.setStyleSheet("background-color: rgb(41, 41, 46); border-radius: 2px;")
        self.transaction_list_layout = QVBoxLayout(self.transaction_list_frame)

        self.transactions_label = QLabel('Transações Registradas')
        self.transactions_label.setStyleSheet("color: white;")
        self.transaction_list_layout.addWidget(self.transactions_label)

        # Create the table widget
        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(7)  # Adjust number of columns based on the data
        self.transaction_table.setHorizontalHeaderLabels(['Descrição', 'Tipo', 'Categoria', 'Preço', 'Data', 'Sincronizado', 'Ações'])
        self.transaction_table.setStyleSheet("color: white; ")

        # Set fixed height for rows
        #self.transaction_table.setFixedHeight(300)  # Set a fixed height for the table
        self.transaction_table.verticalHeader().setDefaultSectionSize(50)  # Set a default row height

        self.transaction_table.setColumnWidth(1, 150)  # Make last column stretch
        self.transaction_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Resize columns to fit the table
        self.transaction_list_layout.addWidget(self.transaction_table)

        self.main_layout.addWidget(self.transaction_list_frame)

        self.setCentralWidget(self.main_frame)

        # Load registered transactions
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
        # Clear previous transactions
        self.transaction_table.setRowCount(0)  # Clear the table

        # Load and display transactions
        transactions = get_all_transactions()
        for transaction in transactions:
            transaction = list(transaction)
            if transaction[2] == 'income':
                transaction[2] = 'entrada'
            elif transaction[2] == 'outcome':
                transaction[2] = 'saida'

            row_position = self.transaction_table.rowCount()
            self.transaction_table.insertRow(row_position)

            # Add transaction details to the table
            self.transaction_table.setItem(row_position, 0, QTableWidgetItem(transaction[1]))  # Description
            self.transaction_table.setItem(row_position, 1, QTableWidgetItem(transaction[2]))  # Type
            self.transaction_table.setItem(row_position, 2, QTableWidgetItem(transaction[3]))  # Category

            price_color = "rgb(79, 255, 203)" if transaction[2] == "entrada"  else "rgb(247, 91, 105)"
            price = QLabel(f'DH$ {transaction[4]:.2f}')
            price.setStyleSheet(f'color: {price_color};')
            self.transaction_table.setCellWidget(row_position, 3, price)  # Price

            # Format the date
            parsed_datetime = datetime.strptime(transaction[7], '%Y-%m-%d %H:%M:%S.%f')
            formatted_datetime = parsed_datetime.strftime("%Y-%m-%d")
            self.transaction_table.setItem(row_position, 4, QTableWidgetItem(formatted_datetime))  # Date

            # Synced status
            synced_color = "rgb(79, 255, 203)" if transaction[8] else "rgb(128, 128, 128)"
            synced_status = QLabel("sincronizado" if transaction[8] else "desincronizado")
            synced_status.setStyleSheet(f'color: {synced_color};')
            self.transaction_table.setCellWidget(row_position, 5, synced_status)

            # Delete button with confirmation dialog
            delete_button = QPushButton('Deletar')
            delete_button.setStyleSheet("color: white;")
            delete_button.clicked.connect(lambda _, trans_id=transaction[0]: self.confirm_delete_transaction(trans_id))
            self.transaction_table.setCellWidget(row_position, 6, delete_button)

    def confirm_delete_transaction(self, transaction_id):
        # Create a confirmation dialog
        reply = QMessageBox.question(self, 'Confirmação', "Você realmente quer deletar esta transação?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        # If user confirms, delete the transaction
        if reply == QMessageBox.Yes:
            self.delete_transaction(transaction_id)

    def delete_transaction(self, transaction_id):
        delete_transaction(transaction_id)
        self.load_collection()  # Refresh the table after deletion
    
    def clear_inputs(self):
        self.description_input.clear()
        self.category_input.clear()
        self.price_input.clear()

def main():
    app = QApplication([])
    app.setStyle("Fusion")

    window = Main()
    window.show()

    app.exec_()

if __name__ == "__main__":
    main()
