from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QScrollArea,
                             QLineEdit, QFormLayout, QHBoxLayout, QFrame, QPushButton, 
                             QLabel, QComboBox, QProgressBar, QWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox,QListWidget )

from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QFont

from datetime import datetime
import time

from controller import Controller

Total_font = QFont()
Total_font.setPointSize(14)  # Set the font size to 14 (adjust as needed)
Total_font.setBold(True)  # Make the text bold


from PyQt5.QtCore import QThread, pyqtSignal

class StatusCheckerThread(QThread):
    status_signal = pyqtSignal(bool)  # Signal to emit the online status

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = True  # Flag to control thread execution

    def run(self):
        while self.running:
            # Check the status
            online = self.controller.is_online()
            self.status_signal.emit(online)
            self.msleep(5000)  # Wait for 5 seconds between checks

    def stop(self):
        self.running = False

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = Controller(self)
        self.last_date = None
        self.last_added_transaction = {'price': 0.0, 'type': '' }
        self.fetching = False
        self.total_of_income, self.total_of_outcome = self.controller.get_total_of_transactions()
        self.initUI()

        # Create and start the thread for status updates
        self.status_thread = StatusCheckerThread(self.controller)
        self.status_thread.status_signal.connect(self.update_status_label)
        self.status_thread.start()

    def update_status_label(self, online):
        if online:
            self.status_label.setText("Status: Online")
        else:
            self.status_label.setText("Status: Offline")

    def closeEvent(self, event):
        # Ensure the thread stops when the application closes
        self.status_thread.stop()
        self.status_thread.wait()
        super().closeEvent(event)

    def initUI(self):
        self.setWindowTitle("OUR-MONKEY")
        self.setGeometry(100, 100, 950, 750)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # self.setMinimumHeight(400)

        self.main_frame = QFrame()
        self.main_layout = QVBoxLayout(self.main_frame)
        self.main_frame.setStyleSheet("background-color: rgb(61, 61, 66); color: #D3D3D3;")
        # Status and sync area at the top
        self.status_frame = QFrame()
        self.status_layout = QHBoxLayout(self.status_frame)

        self.status_label = QLabel("Status: Checando...")
        self.status_layout.addWidget(self.status_label)

        self.sync_button = QPushButton("Sincronizar")
        self.sync_button.clicked.connect(self.sync_and_show_progress)
        self.status_layout.addWidget(self.sync_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("background-color: black")
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
        self.transaction_inputs_frame.setStyleSheet("background-color: rgb(61, 61, 66); border-radius: 16px; color: #D3D3D3;")
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

        formatted_income = f"{self.total_of_income:,.2f}".replace(",", " ")
        formatted_outcome = f"{self.total_of_outcome:,.2f}".replace(",", " ")

        self.income_label = QLabel(f'Entradas: {formatted_income} DH$')
        self.income_label.setAlignment(Qt.AlignCenter)
        self.income_label.setFont(Total_font)
        self.expense_label = QLabel(f'Saídas: {formatted_outcome} DH$')
        self.expense_label.setAlignment(Qt.AlignCenter)
        self.expense_label.setFont(Total_font)
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

        self.transaction_table.verticalScrollBar().valueChanged.connect(self.on_scroll) # Connect scroll event

        # Set fixed height for rows
        #self.transaction_table.setFixedHeight(300)  # Set a fixed height for the table
        self.transaction_table.verticalHeader().setDefaultSectionSize(50)  # Set a default row height
        # Hide the vertical row numbers
        self.transaction_table.verticalHeader().setVisible(False)

        self.transaction_table.setColumnWidth(1, 150)  # Make last column stretch
        self.transaction_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Resize columns to fit the table
        self.transaction_list_layout.addWidget(self.transaction_table)

        self.main_layout.addWidget(self.transaction_list_frame)

        self.setCentralWidget(self.main_frame)

        # Load registered transactions
        self.load_collection()

    def sync_and_show_progress(self):
        self.progress_bar.setValue(0)
        for i in range(1, 101):
            self.progress_bar.setValue(i)
            QApplication.processEvents()

        self.controller.pull_data()  # Chama a função que puxa os dados
        self.progress_bar.setValue(100)

    def add_transaction(self):
        description = self.description_input.text().strip()
        trans_type = self.type_input.currentText()
        category = self.category_input.text().strip()
        price_text = self.price_input.text().strip()
    
        # Validação dos campos
        if not description or not trans_type or not category or not price_text:
            QMessageBox.warning(self, "Erro", "Todos os campos são obrigatórios!")
            return
    
        try:
            price = float(price_text)  # Tenta converter o preço para número
        except ValueError:
            QMessageBox.warning(self, "Erro", "Preço deve ser um número válido!")
            return
    
        # Insere a transação se tudo estiver correto
        self.controller.insert_transaction(
            description, 
            "income" if trans_type == "entrada" else "outcome", 
            category, 
            price
        )
        self.last_date = None
    
        # Atualiza os totais
        if trans_type == "entrada":
            self.total_of_income += price
            self.income_label.setText(f"Entradas: {self.total_of_income:,.2f} DH$".replace(",", " "))
        else:
            self.total_of_outcome += price
            self.expense_label.setText(f"Saídas: {self.total_of_outcome:,.2f} DH$".replace(",", " "))
    
        # Recarrega as transações e limpa os campos
        self.load_collection()
        self.clear_inputs()
            
    def load_collection(self, append=False):
        """
        Load transactions into the table. If `append` is True, add to the existing table.
        """
        # Set fetching flag to avoid duplicate fetches
        if self.fetching:
            return

        self.fetching = True

        # Fetch transactions
        transactions = self.controller.fetch_transactions(self.last_date)

        if not append:
            self.transaction_table.setRowCount(0)  # Clear the table if not appending

        for transaction in transactions:
            row_position = self.transaction_table.rowCount()
            self.transaction_table.insertRow(row_position)

            # Map and populate transaction fields
            self.transaction_table.setItem(row_position, 0, QTableWidgetItem(transaction[1]))  # Description
            type_item = QTableWidgetItem('entrada' if transaction[2] == 'income' else 'saida')  # Type
            self.transaction_table.setItem(row_position, 1, type_item)

            self.transaction_table.setItem(row_position, 2, QTableWidgetItem(transaction[3]))  # Category
            price_color = "rgb(79, 255, 203)" if transaction[2] == "income" else "rgb(247, 91, 105)"
            price = QLabel(f'DH$ {transaction[4]:.2f}')
            price.setStyleSheet(f'color: {price_color};')
            self.transaction_table.setCellWidget(row_position, 3, price)

            # Format and display the date
            formatted_date = datetime.strptime(transaction[7], '%Y-%m-%d %H:%M:%S.%f').strftime("%Y-%m-%d")
            self.transaction_table.setItem(row_position, 4, QTableWidgetItem(formatted_date))

            # Display synced status
            synced_color = "rgb(79, 255, 203)" if transaction[8] else "rgb(128, 128, 128)"
            synced_status = QLabel("sincronizado" if transaction[8] else "desincronizado")
            synced_status.setStyleSheet(f'color: {synced_color};')
            self.transaction_table.setCellWidget(row_position, 5, synced_status)

            # Delete button with confirmation dialog
            delete_button = QPushButton('Deletar')
            delete_button.setStyleSheet("color: white;")
            delete_button.clicked.connect(lambda _, trans_id=transaction[0]: self.confirm_delete_transaction(trans_id))
            self.transaction_table.setCellWidget(row_position, 6, delete_button)

            # Save the last transaction's date
            self.last_date = transaction[7]
        
        self.fetching = False

    def on_scroll(self, value):
        """
        Detect when the user scrolls near the bottom and load more transactions.
        """
        scroll_bar = self.transaction_table.verticalScrollBar()
        if value == scroll_bar.maximum() and not self.fetching:
            self.load_collection(append=True)

    def confirm_delete_transaction(self, transaction_id):
        # Create a confirmation dialog
        reply = QMessageBox.question(self, 'Confirmação', "Você realmente quer deletar esta transação?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        # If user confirms, delete the transaction
        if reply == QMessageBox.Yes:
            self.delete_transaction(transaction_id)

    def delete_transaction(self, transaction_id):
        # Delete the transaction via the controller
        self.controller.delete_transaction(transaction_id)
        self.last_date = None

        # Recalculate totals
        self.total_of_income, self.total_of_outcome = self.controller.get_total_of_transactions()

        # Format totals with space as a thousands separator
        formatted_income = f"{self.total_of_income:,.2f}".replace(",", " ")
        formatted_outcome = f"{self.total_of_outcome:,.2f}".replace(",", " ")

        # Update labels with formatted values
        self.income_label.setText(f"Entradas: {formatted_income} DH$")
        self.expense_label.setText(f"Saídas: {formatted_outcome} DH$")

        # Refresh the table after deletion
        self.load_collection()

    
    def clear_inputs(self):
        self.description_input.clear()
        self.category_input.clear()
        self.price_input.clear()