from PyQt5.QtWidgets import QApplication
from GUI import Main

def main():
    app = QApplication([])
    app.setStyle("Fusion")
    app.setStyle("background-color: #D3D3D3;")

    window = Main()
    window.show()

    app.exec_()

if __name__ == "__main__":
    main()