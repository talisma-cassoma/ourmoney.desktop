import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QFont

class EllipsisMenuApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Central widget setup
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Ellipsis menu button
        menu_button = QPushButton("⋮")
        menu_button.setFont(QFont("Arial", 20))  # Set font size for ellipsis
        menu_button.setFixedSize(40, 40)  # Adjust size
        menu_button.setStyleSheet("border: none;")  # Optional: Remove border
        
        # Create a QMenu for the ellipsis button
        menu = QMenu()
        menu.addAction("Option 1")
        menu.addAction("Option 2")
        menu.addAction("Option 3")
        
        # Connect the menu to the button
        menu_button.setMenu(menu)

        layout.addWidget(menu_button)
        layout.addStretch()
        self.setCentralWidget(central_widget)

        # Window settings
        self.setWindowTitle("Ellipsis Menu Example")
        self.resize(200, 150)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EllipsisMenuApp()
    window.show()
    sys.exit(app.exec_())
