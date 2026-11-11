from PyQt5.QtWidgets import QApplication
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Starting OurMoney")

def main():
    from controller import Controller
    from GUI import MainWindow

    app = QApplication([])
    app.setStyle("Fusion")
    app.setStyle("background-color: #D3D3D3;")


    window = MainWindow()
    controller = Controller(main_window=window)
    window.set_controller(controller)
    
    window.show()

    app.exec_()

if __name__ == "__main__":
    main()