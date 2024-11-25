from PyQt5.QtWidgets import QApplication
from GUI import Main

def main():
    app = QApplication([])
    app.setStyle("Fusion")

    window = Main()
    window.show()

    app.exec_()

if __name__ == "__main__":
    main()