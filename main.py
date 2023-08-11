from PySide6.QtWidgets import QApplication
import sys,os


from ui import ChessWindow


if __name__=="__main__":
    app=QApplication(sys.argv)
    window=ChessWindow()
    window.show()
    sys.exit(app.exec())