from PyQt5 import QtCore
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout,
                             QLineEdit, QFormLayout, QHBoxLayout, QFrame, QPushButton, 
                             QLabel, QComboBox, QProgressBar, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QMenu,
                             QDialog, QDateEdit, QToolButton, QWidgetAction, QCheckBox
                             )

from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtSvg import QSvgRenderer


from datetime import datetime
import time
import logging
import random

# Configuração do logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')


Total_font = QFont()
Total_font.setPointSize(14)  # Set the font size to 14 (adjust as needed)
Total_font.setBold(True)  # Make the text bold

from PyQt5.QtCore import QThread, pyqtSignal

def create_checkbox_menu_button(title, options, selected_options_set):
    """
    Cria um botão com menu suspenso contendo checkboxes.
    
    :param title: Título do botão principal.
    :param options: Lista de strings (opções).
    :param callback: Função chamada quando checkbox é clicado.
    :param selected_options_set: Set externo compartilhado para controle de seleção.
    :return: QPushButton
    """
    button = QPushButton(title)
    button.setStyleSheet("background-color: #333; font-size: 12px; color: white;")
    button.setCursor(Qt.PointingHandCursor)

    menu = QMenu()
    menu.setStyleSheet("""
        QMenu {
            color: white;
            border: 1px solid rgb(41, 41, 46);
            padding: 4px;
        }
        QMenu::item {
            padding: 4px 10px;
            color: white;          
        }
    """)

    for option in options:
        checkbox = QCheckBox(option)
        checkbox.setChecked(option in selected_options_set)

        def toggle_option(checked, opt=option):
            if checked:
                selected_options_set.add(opt)
            else:
                selected_options_set.discard(opt)

        checkbox.stateChanged.connect(toggle_option)

        action = QWidgetAction(menu)
        action.setDefaultWidget(checkbox)
        menu.addAction(action)

    button.setMenu(menu)
    return button

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

class SyncThread(QThread):
    progress_signal = pyqtSignal(int)  # Sinal para atualizar a barra de progresso
    finished_signal = pyqtSignal()  # Sinal para enviar os dados sincronizados

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
       
        for i in range(0, 101, 10):  # Simula progresso
            self.progress_signal.emit(i)
            self.msleep(100)
        
        # Executa o processo de sincronização
        self.controller.synchronize_data()
        self.finished_signal.emit()
        
class MainWindow(QMainWindow):
    def __init__(self,):
        super().__init__()
        self.controller = None
        self.last_date = None
        #self.last_added_transaction = {'price': 0.0, 'type': '' }
        self.fetching = False
        self.total_of_income = 0
        self.total_of_outcome = 0

        # Create and start the thread for status updates
        self.status_thread = None

        self.sync_thread = None

        self.filters = {
            "keyword": "",
            "category": set(),
            "type": set(),
            "status": set(),
            "year": set(),
            "month": set(),
        }

    def set_controller(self, controller):
        """Define o controlador para a GUI."""
        self.controller = controller
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

        """ save file """
        self.safe_file_label = QLabel("guardar em:")
        self.status_layout.addWidget(self.safe_file_label)

        self.file_type_input = QComboBox()
        self.file_type_input.setStyleSheet("color: white;")
        self.file_type_input.addItems(["json", "csv", "excel", "report"])
        # Connect signals to the methods.
        self.file_type_input.activated.connect(self.save_file)
        # # Add block 1 to thes status layout
        self.status_layout.addWidget(self.file_type_input)
    
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
        self.income_label.setAlignment(QtCore.Qt.AlignCenter)
        self.income_label.setFont(Total_font)
        self.expense_label = QLabel(f'Saídas: {formatted_outcome} DH$')
        self.expense_label.setAlignment(QtCore.Qt.AlignCenter)
        self.expense_label.setFont(Total_font)
        self.income_label.setStyleSheet("color: rgb(79, 255, 203);")
        self.expense_label.setStyleSheet("color: rgb(247, 91, 105);")

        self.totals_layout.addWidget(self.income_label)
        self.totals_layout.addWidget(self.expense_label)

        # Add block 2 to the main layout
        self.blocks_layout.addWidget(self.totals_frame)

        self.main_layout.addWidget(self.blocks_frame)

  # --- search + filter area ---
        self.search_frame = QFrame()
        hl = QHBoxLayout(self.search_frame)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(5)


        # Campo de busca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setStyleSheet("background-color: black; padding: 6px;")
        hl.addWidget(self.search_input, 1)
        
        # Botão de busca com SVG
        self.search_btn = QToolButton()
        self.search_btn.setIcon(self.svg_icon(
            '''<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="white"><path d="M784-120 532-372q-30 24-69 38t-83 14q-109 0-184.5-75.5T120-580q0-109 75.5-184.5T380-840q109 0 184.5 75.5T640-580q0 44-14 83t-38 69l252 252-56 56ZM380-400q75 0 127.5-52.5T560-580q0-75-52.5-127.5T380-760q-75 0-127.5 52.5T200-580q0 75 52.5 127.5T380-400Z"/></svg>'''
        ))
        self.search_btn.setAutoRaise(True)
        self.search_btn.clicked.connect(self.update_keyword_filter)
        hl.addWidget(self.search_btn)

        # Botão de filtro
        self.filter_btn = QToolButton()
        self.filter_btn.setIcon(self.svg_icon(
            '''<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="white"><path d="M440-120v-240h80v80h320v80H520v80h-80Zm-320-80v-80h240v80H120Zm160-160v-80H120v-80h160v-80h80v240h-80Zm160-80v-80h400v80H440Zm160-160v-240h80v80h160v80H680v80h-80Zm-480-80v-80h400v80H120Z"/></svg>'''
        ))
        self.filter_btn.setAutoRaise(True)
        self.filter_btn.clicked.connect(self.toggle_filters)
        hl.addWidget(self.filter_btn)

        self.main_layout.addWidget(self.search_frame)

        # Frame de filtros
        self.filter_frame = QFrame()
        self.filter_frame.setVisible(False)
        fl = QHBoxLayout(self.filter_frame)
        fl.setContentsMargins(0,0,0,0)
        fl.setSpacing(10)

        # Filtros fixos por categoria
        category_btn = create_checkbox_menu_button(
              title="categoria",
              options=["alimentaçao", "internet", "saude", "bebida"], 
                selected_options_set= self.filters["category"])

        
        fl.addWidget(category_btn)

        # Filtro de status
        status_button = create_checkbox_menu_button(
            title="status", 
            options=["sincronizado", "dessincronizado"], 
            selected_options_set = self.filters["status"]
        )
        fl.addWidget(status_button)

        # Filtro de ano
        year_button = create_checkbox_menu_button(
            title = "ano", 
            options = ["2025", "2024"],
            selected_options_set = self.filters["year"]
            )
        fl.addWidget(year_button)


        # Filtro de mes
        month_button = create_checkbox_menu_button(
            title="mes", 
            options = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setempbro", "outubro", "novembro", "dezembro"],
            selected_options_set = self.filters["month"]
            )
        fl.addWidget(month_button)

        #Filtro de tipo
        type_filter_button = create_checkbox_menu_button(
            title="tipo", 
            options=["entrada","saida"], 
             selected_options_set = self.filters["type"]
            )
        
        fl.addWidget(type_filter_button)

        self.main_layout.addWidget(self.filter_frame)

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
        self.transaction_table.setHorizontalHeaderLabels(['Descrição', 'Ações', 'Tipo', 'Categoria', 'Preço', 'Data', 'Sincronizado'])
        self.transaction_table.setStyleSheet("color: white; ")

        self.transaction_table.verticalScrollBar().valueChanged.connect(self.on_scroll) # Connect scroll event

        # Set fixed height for rows
        #self.transaction_table.setFixedHeight(300)  # Set a fixed height for the table
        self.transaction_table.verticalHeader().setDefaultSectionSize(50)  # Set a default row height
        # Hide the vertical row numbers
        self.transaction_table.verticalHeader().setVisible(False)

        self.transaction_table.setColumnWidth(0, 150)  # Make last column stretch
        self.transaction_table.setColumnWidth(1, 60) # 
        self.transaction_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Resize columns to fit the table
        self.transaction_list_layout.addWidget(self.transaction_table)

        self.main_layout.addWidget(self.transaction_list_frame)

        self.setCentralWidget(self.main_frame)

        # Load registered transactions
        self.load_collection()

    def save_file(self, index):
        self.controller.export_file(index)

    def sync_and_show_progress(self):
        if self.sync_thread and self.sync_thread.isRunning():
            QMessageBox.warning(self, "Sincronização em andamento", "A sincronização já está em andamento!")
            return

        self.sync_thread = SyncThread(self.controller)
        self.sync_thread.progress_signal.connect(self.update_progress_bar)
        self.sync_thread.finished_signal.connect(self.sync_finished)

        self.progress_bar.setValue(0)
        self.sync_thread.start()

    def update_progress_bar(self, value):
        """Atualiza o valor da barra de progresso."""
        self.progress_bar.setValue(value)

    def sync_finished(self):
        """Executado quando a sincronização termina."""       
        self.controller.main_window.last_date = None
        self.controller.main_window.load_collection()
        self.progress_bar.setValue(100)

    def add_transaction(self):
        description = self.description_input.text().strip().lower()
        trans_type = self.type_input.currentText().lower()
        category = self.category_input.text().strip().lower()
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
        transactions = self.controller.fetch_transactions(self.last_date, self.filters)

        if not append:
            self.transaction_table.setRowCount(0)  # Clear the table if not appending

        for transaction in transactions:
            row_position = self.transaction_table.rowCount()
            self.transaction_table.insertRow(row_position)

            # Map and populate transaction fields
            self.transaction_table.setItem(row_position, 0, QTableWidgetItem(transaction.description))  # Description
            type_item = QTableWidgetItem('entrada' if transaction.type == 'income' else 'saida')  # Type
            self.transaction_table.setItem(row_position, 2, type_item)

            self.transaction_table.setItem(row_position, 3, QTableWidgetItem(transaction.category))  # Category
            price_color = "rgb(79, 255, 203)" if transaction.type == "income" else "rgb(247, 91, 105)"
            price = QLabel(f'{transaction.price}')
            price.setStyleSheet(f'color: {price_color};')
            self.transaction_table.setCellWidget(row_position, 4, price)
            
            try:
                # Check if transaction[7] is not None or empty
                if not transaction.created_at:
                    raise ValueError("Empty or None date string")
                date = transaction.created_at

                self.transaction_table.setItem(row_position, 5, QTableWidgetItem(date))
            except Exception as e:
                logging.error(f'Unexpected error with id: {transaction.id} with date: {date} , error: {e}')

            # Display synced status
            synced_color = "rgb(79, 255, 203)" if transaction.status =='synced' else "rgb(128, 128, 128)"
            synced_status = QLabel("sincronizado" if transaction.status=='synced' else "desincronizado")
            synced_status.setStyleSheet(f'color: {synced_color};')
            self.transaction_table.setCellWidget(row_position, 6, synced_status)

            # Delete button with confirmation dialog
            # delete_button = QPushButton('Deletar')
            # delete_button.setStyleSheet("color: white;")
            # delete_button.clicked.connect(lambda _, trans_id=transaction.id: self.confirm_delete_transaction(trans_id))
            # self.transaction_table.setCellWidget(row_position, 6, delete_button)
            
            # Create ellipsis menu for actions
            ellipsis_button = QPushButton("⋮")
            ellipsis_button.setStyleSheet("background: transparent; font-size: 18px; color: white; width: 5px;")
            ellipsis_button.setCursor(Qt.PointingHandCursor)
            
            # Add menu to button
            menu = QMenu()
            menu.setStyleSheet("""
                QMenu {
                    background-color: rgb(61, 61, 66);
                    color: white;
                    border: 1px solid rgb(41, 41, 46);
                    padding: 4px;
                    width: 60px; /* Reduce width */
                }
                QMenu::item {
                    padding: 4px 10px; /* Adjust padding for compactness */
                    font-size: 12px; /* Smaller font size */
                }
                QMenu::item:selected {
                    background-color: rgb(79, 255, 203); /* Highlight color */
                    color: rgb(128, 128, 128)
                }
             """)
            edit_action = menu.addAction("Edit")
            delete_action = menu.addAction("Delete")
        
            ellipsis_button.setMenu(menu)
        
            # Connect actions
            edit_action.triggered.connect(lambda _,id = transaction.id,
                description=transaction.description,
                type=transaction.type,
                category=transaction.category,
                price= transaction.price,
                status= transaction.status,
                date=date: self.open_edit_dialog(id,description,type,category, price, status, date))
            delete_action.triggered.connect(lambda _, trans_id=transaction.id: self.confirm_delete_transaction(trans_id))
        
            # Add ellipsis button to table
            self.transaction_table.setCellWidget(row_position, 1, ellipsis_button)
        

            # Save the last transaction's date
            self.last_date = transaction.created_at
        
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
    
    def open_edit_dialog(self, id,description,type,category,price, status, date):
        # Criar o diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Transação")
        dialog.setFixedWidth(400)

        # Layout do diálogo
        layout = QFormLayout(dialog)

        # Inputs
        description_input = QLineEdit(description)
        type_input = QComboBox()
        type_input.addItems(["saida", "entrada"])
        type_input.setCurrentText(type)
        category_input = QLineEdit(category)
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.fromString(date, "dd-MM-yyyy"))
        price_input = QLineEdit(price.replace(" DH$", ""))
        
        # Botões
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Salvar")
        cancel_button = QPushButton("Cancelar")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        # Adicionar ao layout
        layout.addRow("Descrição:", description_input)
        layout.addRow("Tipo:", type_input)
        layout.addRow("Categoria:", category_input)
        layout.addRow("Preço:", price_input)
        layout.addRow("Data:", date_input)
        layout.addRow(buttons_layout)

        # Conectar botões
        cancel_button.clicked.connect(dialog.reject)
        save_button.clicked.connect(lambda: self.save_edited_transaction(dialog, id, description_input, type_input, category_input, price_input.text().strip(), status, date_input))

        # Mostrar o diálogo
        dialog.exec_()

    def save_edited_transaction(self, dialog, id, description_input, type_input, category_input, price, status, date_input):
        # Obter valores dos inputs
        
        self.last_date = None
        id= str(id)
        description = str(description_input.text())
        type_input = str(type_input.currentText())
        category = str(category_input.text())
        date = f"{date_input.date().toString("yyyy-MM-dd")}T{f"12:34:{f'{random.randint(0, 59):02d}'}.789Z"}"
        price =  float(price)
        status = str(status)

        self.controller.edit_transaction(id, description, type_input, category, price, status, date)

        # Fechar o diálogo
        dialog.accept()
        # Refresh the table after deletion
        self.load_collection()

    def svg_icon(self, svg_str):
        """Converte string SVG em QIcon."""
        renderer = QSvgRenderer(bytearray(svg_str, encoding='utf-8'))
        pix = QPixmap(24, 24)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()
        return QIcon(pix)

    def toggle_filters(self):
        self.filter_frame.setVisible(not self.filter_frame.isVisible())

    def clear_inputs(self):
        self.description_input.clear()
        self.category_input.clear()
        self.price_input.clear()

    def update_keyword_filter(self): 
        self.last_date = None
        self.filters["keyword"] = self.search_input.text().strip().lower()
        # Recalculate totals
        self.total_of_income, self.total_of_outcome = self.controller.get_total_of_transactions()

        # Format totals with space as a thousands separator
        formatted_income = f"{self.total_of_income:,.2f}".replace(",", " ")
        formatted_outcome = f"{self.total_of_outcome:,.2f}".replace(",", " ")

        # Update labels with formatted values
        self.income_label.setText(f"Entradas: {formatted_income} DH$")
        self.expense_label.setText(f"Saídas: {formatted_outcome} DH$")

        self.load_collection()
        #clear keyword 
        #self.filters["keyword"] = ""

    
