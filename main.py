import sys
import os
import time
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QProgressBar,
    QComboBox,
    QLineEdit,
    QMessageBox,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import requests


class ImageDownloader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, url, filename):
        super().__init__()
        self.url = url
        self.filename = filename

    def run(self):
        response = requests.get(self.url, stream=True)
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024
        written = 0

        with open(self.filename, "wb") as file:
            for data in response.iter_content(block_size):
                size = file.write(data)
                written += size
                if total_size > 0:
                    progress = int((written / total_size) * 100)
                    self.progress.emit(progress)

        self.finished.emit(self.filename)


class ImageGeneratorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("AI Image Generator")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f5f5f5;
                color: #333;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTextEdit, QLineEdit {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QComboBox {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                min-height: 30px;
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: #f0f0f0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
            """
        )

        main_layout = QHBoxLayout()

        # Left side
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your OpenAI API key here...")
        self.api_key_input.setEchoMode(QLineEdit.Password)

        prompt_label = QLabel("Prompt:")
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Enter your prompt here...")

        size_label = QLabel("Image Size:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["1024x1024", "1792x1024", "1024x1792"])
        self.size_combo.setCurrentIndex(0)  # Set default to 1024x1024

        quality_label = QLabel("Image Quality:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["standard", "hd"])
        self.quality_combo.setCurrentIndex(0)  # Set default to standard

        self.generate_button = QPushButton("Generate Image")
        self.generate_button.clicked.connect(self.generate_image)

        left_layout.addWidget(api_key_label)
        left_layout.addWidget(self.api_key_input)
        left_layout.addWidget(prompt_label)
        left_layout.addWidget(self.prompt_input, 1)  # Set stretch factor to 1
        left_layout.addWidget(size_label)
        left_layout.addWidget(self.size_combo)
        left_layout.addWidget(quality_label)
        left_layout.addWidget(self.quality_combo)
        left_layout.addWidget(self.generate_button)

        # Right side
        right_layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            """
            QLabel {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 10px;
            }
        """
        )
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        right_layout.addWidget(self.image_label)
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(self.progress_bar)

        # Add layouts to main layout
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        self.setLayout(main_layout)

    def generate_image(self):
        api_key = self.api_key_input.text().strip()
        prompt = self.prompt_input.toPlainText().strip()

        if not api_key:
            QMessageBox.warning(
                self, "Missing API Key", "Please enter your OpenAI API key."
            )
            return

        if not prompt:
            QMessageBox.warning(
                self, "Missing Prompt", "Please enter a prompt for image generation."
            )
            return

        self.status_label.setText("Generating image...")
        self.progress_bar.setValue(0)
        self.generate_button.setEnabled(False)

        size = self.size_combo.currentText()
        quality = self.quality_combo.currentText()
        result = self.generate_and_download_image(
            api_key, prompt, size=size, quality=quality
        )

        if result and result["image_url"]:
            self.status_label.setText("Downloading image...")
            self.downloader = ImageDownloader(result["image_url"], result["local_path"])
            self.downloader.progress.connect(self.update_progress)
            self.downloader.finished.connect(self.show_image)
            self.downloader.start()
        else:
            self.generate_button.setEnabled(True)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_image(self, filename):
        pixmap = QPixmap(filename)
        self.image_label.setPixmap(
            pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.status_label.setText("Image generated and downloaded successfully!")
        self.generate_button.setEnabled(True)

    def generate_and_download_image(
        self, api_key, prompt, n=1, quality="standard", size="1024x1024"
    ):
        url = "https://api.openai.com/v1/images/generations"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": n,
            "quality": quality,
            "size": size,
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.status_label.setText(f"Error: {str(e)}")
            return None

        result = response.json()

        created_time = result["created"]
        image_url = result["data"][0]["url"]

        os.makedirs("img", exist_ok=True)
        timestamp = int(time.time())
        image_filename = os.path.join("img", f"generated_image_{timestamp}.png")

        return {
            "created_time": created_time,
            "image_url": image_url,
            "local_path": image_filename,
        }

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image_label_size()

    def update_image_label_size(self):
        available_width = self.width() * 2 // 3  # 2/3 of the window width
        available_height = (
            self.height() - 100
        )  # Subtracting some space for other widgets
        self.image_label.setFixedSize(available_width, available_height)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageGeneratorApp()
    ex.show()
    sys.exit(app.exec_())
