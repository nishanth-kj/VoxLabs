from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QTextEdit, QListWidget,
    QPushButton, QVBoxLayout, QWidget
)
from PyQt6.QtCore import Qt
from services.voice_service import get_voice_engine
from utils.logger import logger

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VoxLabs Enterprise Studio")
        self.resize(1200, 800)

        # Central Widget (Main workspace)
        self.central_widget = QWidget()
        layout = QVBoxLayout()
        self.workspace = QTextEdit()
        self.workspace.setPlaceholderText("Main Audio Workspace...")
        
        self.connect_btn = QPushButton("Load Local Voices")
        self.connect_btn.clicked.connect(self.load_voices)

        layout.addWidget(self.connect_btn)
        layout.addWidget(self.workspace)
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        # Left Panel (Project Explorer / Voices List)
        self.left_dock = QDockWidget("Project Explorer", self)
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.file_list = QListWidget()
        self.file_list.addItem("Project 1")
        self.file_list.addItem("Project 2")
        self.left_dock.setWidget(self.file_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        # Bottom Panel (Output / Terminal)
        self.bottom_dock = QDockWidget("Output / Terminal", self)
        self.bottom_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.append("VoxLabs Studio Initialized...")
        self.bottom_dock.setWidget(self.output_console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)

    def load_voices(self):
        logger.info("Loading local voices...")
        self.output_console.append("Initializing Voice Engine...")
        
        try:
            engine = get_voice_engine()
            voices = engine.list_voices()
            
            msg = f"Successfully loaded {len(voices)} local voices."
            logger.info(msg)
            self.output_console.append(msg)
            
            self.file_list.clear()
            for v in voices:
                self.file_list.addItem(f"{v['name']} ({v['voice_id'][:8]})")
                
            self.output_console.append(str(voices))
        except Exception as e:
            logger.error(f"Failed to load voices: {e}")
            self.output_console.append(f"Error loading voices: {e}")
