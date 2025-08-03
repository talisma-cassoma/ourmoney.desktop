from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox,
    QPushButton, QSpinBox, QFrame, QApplication, QScrollArea, QInputDialog
)
from PyQt5.QtCore import Qt
import sys


class ItemWidget(QWidget):
    def __init__(self, name, price=0, quantity=1):
        super().__init__()

        # QFrame que serve como o "container visual"
        self.main_frame = QFrame()
        self.main_frame.setObjectName("itemFrame")  # Nome para estilização

        # Layout do frame
        frame_layout = QHBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(10)

        # Checkbox com o nome
        self.checkbox = QCheckBox(name)
        frame_layout.addWidget(self.checkbox, stretch=1)

        # SpinBox para quantidade
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setValue(quantity)
        self.quantity_spin.setFixedWidth(50)
        frame_layout.addWidget(self.quantity_spin)

        # SpinBox para preço
        self.price_input = QSpinBox()
        self.price_input.setMaximum(10000)
        self.price_input.setValue(price)
        self.price_input.setSuffix(" DH$")
        self.price_input.setFixedWidth(80)
        frame_layout.addWidget(self.price_input)

        frame_layout.addStretch()

        # Layout principal do ItemWidget (envolve o frame)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_frame)

        # Estilização via CSS usando o objectName
        self.setStyleSheet("""
            QFrame#itemFrame {
                background-color: rgb(61, 61, 66);
                border-radius: 8px;
                padding: 6px;
            }
            QCheckBox {
                font-size: 14px;
                color: white;
            }
            QSpinBox, QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)

    def increase_quantity(self):
        self.quantity_spin.setValue(self.quantity_spin.value() + 1)

    def decrease_quantity(self):
        if self.quantity_spin.value() > 1:
            self.quantity_spin.setValue(self.quantity_spin.value() - 1)
    def is_checked(self):
        return self.checkbox.isChecked()

    def get_formatted_text(self):
        name = self.checkbox.text()
        quantity = self.quantity_spin.value()
        price = self.price_input.value()

        if quantity > 1 and price > 0:
            return f"- [x] {name} {quantity}x({price})"
        elif quantity > 1:
            return f"- [x] {name} {quantity}x"
        elif price > 0:
            return f"- [x] {name} {price}"
        else:
            return f"- [x] {name}"

class CategorySection(QFrame):
    def __init__(self, title, items):
        super().__init__()

        self.layout = QVBoxLayout()  # ← corrigido
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        
        self.title = title

        header = QLabel(f"<b>{title}</b>")
        self.layout.addWidget(header)

        self.item_widgets = []  # ← adicionado

        for item in items:
            widget = ItemWidget(
                name=item["name"],
                quantity=item.get("quantity", 1),
                price=item.get("price", 0)
            )
            widget.setStyleSheet("""
                QWidget {
                    background-color: #444;
                    border-radius: 8px;
                    padding: 6px;
                }
                QCheckBox {
                    font-size: 14px;
                    color: white;
                }
                QSpinBox {
                    background-color: #333;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 4px;
                }
                QPushButton {
                    background-color: #555;
                    color: white;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #777;
                }
            """)
            self.layout.addWidget(widget)
            self.item_widgets.append(widget)

        self.add_button = QPushButton("+ Adicionar Item")
        self.add_button.setCursor(Qt.PointingHandCursor)
        self.add_button.clicked.connect(self.add_item_widget)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)

        self.setStyleSheet("""
            QFrame {
                background-color: #3a3a3f;
                border-radius: 12px;
                padding: 5px;
                margin: 10px;
            }
            QLabel {
                color: #ffffff;
                font-size: 16px;
            }
        """)

    def add_item_widget(self):
        name, ok = QInputDialog.getText(self, "Adicionar Item", "Nome do item:")
        if ok and name.strip():
            new_widget = ItemWidget(name=name.strip(), price=0, quantity=1)
            self.layout.insertWidget(self.layout.count() - 1, new_widget)
            self.item_widgets.append(new_widget)

    def get_checked_items_text(self):
        lines = []
        for item in self.item_widgets:
            if item.is_checked():
                lines.append(item.get_formatted_text())
        return lines

class HouseHoldList(QWidget):
    def __init__(self):
        super().__init__()

        self.sections = []  # Guardar referências às seções

        outer_layout = QVBoxLayout(self)

        title = QLabel("<h2>Lista Comida 2025</h2>")
        outer_layout.addWidget(title)
        
        copy_button = QPushButton("📋 Copy List")
        copy_button.setCursor(Qt.PointingHandCursor)
        copy_button.setStyleSheet("background-color: #5a5a5a; color: white; padding: 8px; border-radius: 6px;")
        copy_button.clicked.connect(self.copy_list_to_clipboard)

        outer_layout.addWidget(copy_button)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Widget interno com layout para as seções
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        self.add_section("Carnes + Proteínas", [
            {"name": "Poulet", "quantity": 2, "price": 50},
            {"name": "Steak", "price": 200},
            {"name": "Atún", "price": 35},
            {"name": "Peito de dinde", "price": 50},
            {"name": "Osso buco", "price": 100},
            {"name": "Ovo", "quantity": 3, "price": 45}
        ])
        
        self.add_section("Carboidratos + Legumes", [
            {"name": "Açúcar", "price": 10},
            {"name": "Ketchup", "price": 14},
            {"name": "Maionese", "price": 32},
            {"name": "Milho doce", "price": 13},
            {"name": "Massa tomate", "price": 15},
            {"name": "Feijão castanho", "price": 40},
            {"name": "Feijão branco", "price": 30},
            {"name": "Alho", "price": 10},
            {"name": "Azeite", "price": 50},
            {"name": "Arroz", "quantity": 4, "price": 18}
        ])

        self.add_section("Épices", [
            {"name": "Pimenta preta", "price": 5}
        ])

        self.add_section("Laticínios e Outros", [
            {"name": "Creme fraiche", "quantity": 3, "price": 13},
            {"name": "Queijo"}
        ])

        self.add_section("LEGUMES", [
            {"name": "Batata rena", "price": 10},
            {"name": "Batata Doce", "price": 10},
            {"name": "Tomate", "price": 10},
            {"name": "Cebola", "price": 8},
            {"name": "Cenoura", "price": 7},
            {"name": "Beringela", "price": 5},
            {"name": "Pepino", "price": 5}
        ])

        self.add_section("Limpeza e Higiene", [
            {"name": "Saco de lixo", "price": 15},
            {"name": "Gel douche", "price": 20},
            {"name": "Gel da pia", "price": 35},
            {"name": "Papel cozinha", "price": 20},
            {"name": "Papel HIGIENICO", "price": 30},
            {"name": "Amaciador", "price": 40},
            {"name": "Detergente da roupa", "price": 60},
            {"name": "Lixivia", "price": 5},
            {"name": "Spray de limpar cozinha", "price": 40},
            {"name": "Insecticida Zentjek (crianças)", "price": 36},
            {"name": "Spray Insecticida", "price": 13},
            {"name": "Modex", "price": 15}
        ])
        

        scroll_area.setWidget(self.content_widget)
        outer_layout.addWidget(scroll_area)

    def add_section(self, title, items):
        section = CategorySection(title, items)
        self.sections.append(section)
        self.content_layout.addWidget(section)

    def copy_list_to_clipboard(self):
        lines = ["Lista Comida 2025", ""]
        for section in self.sections:
            section_lines = section.get_checked_items_text()
            if section_lines:
                lines.append(section.title)
                lines.extend(["    " + line for line in section_lines])
                lines.append("")  # Espaço entre seções

        full_text = "\n".join(lines).strip()
        QApplication.clipboard().setText(full_text)
        print("Lista copiada:\n", full_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HouseHoldList()
    window.setStyleSheet("background-color: #2b2b2b; color: white;")
    window.resize(420, 600)
    window.show()
    sys.exit(app.exec_())
