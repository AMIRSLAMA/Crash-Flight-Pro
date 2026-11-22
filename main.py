import csv
import math
import statistics
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
    QWidget, QSplitter,
)
from PySide6.QtWebEngineWidgets import QWebEngineView


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crash Flight Pro — Historical Analyzer")
        self.resize(1350, 820)
        self.rounds = []
        root = QWidget()
        layout = QVBoxLayout(root)
        toolbar = QHBoxLayout()
        self.address = QLineEdit()
        self.address.setPlaceholderText("https:// — enter game URL")
        self.address.returnPressed.connect(self.open_url)
        open_button = QPushButton("Open website")
        open_button.clicked.connect(self.open_url)
        toolbar.addWidget(self.address)
        toolbar.addWidget(open_button)
        layout.addLayout(toolbar)

        splitter = QSplitter()
        self.browser = QWebEngineView()
        self.browser.urlChanged.connect(
            lambda url: self.address.setText(url.toString())
        )
        splitter.addWidget(self.browser)
        sidebar = QWidget()
        side = QVBoxLayout(sidebar)
        side.addWidget(QLabel("Historical analysis — future result unknown"))
        load_button = QPushButton("Import rounds CSV")
        load_button.clicked.connect(self.load_csv)
        side.addWidget(load_button)
        self.report = QTextEdit()
        self.report.setReadOnly(True)
        self.report.setPlainText(
            "Import a CSV with a multiplier column.\n\nNext round: UNKNOWN."
        )
        side.addWidget(self.report)
        splitter.addWidget(sidebar)
        splitter.setSizes([950, 400])
        layout.addWidget(splitter)
        self.setCentralWidget(root)

    def open_url(self):
        parsed = QUrl(self.address.text().strip())
        if parsed.scheme() not in ("https", "http") or not parsed.host():
            QMessageBox.warning(self, "Invalid URL", "Enter a full http(s) URL.")
            return
        self.browser.setUrl(parsed)

    def load_csv(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import historical rounds", "", "CSV files (*.csv)"
        )
        if not filename:
            return
        try:
            with Path(filename).open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames or "multiplier" not in reader.fieldnames:
                    raise ValueError("CSV must have a multiplier column")
                values = []
                for row in reader:
                    value = float(row["multiplier"].strip().rstrip("xX"))
                    if not math.isfinite(value) or value <= 0:
                        raise ValueError("Invalid multiplier")
                    values.append(value)
            self.rounds = values
            self.update_report()
        except (ValueError, OSError, UnicodeError, KeyError) as exc:
            QMessageBox.warning(self, "Import failed", str(exc))

    def update_report(self):
        if not self.rounds:
            self.report.setPlainText("No rounds imported.\nNext round: UNKNOWN.")
            return
        rounds = self.rounds
        recent = rounds[-30:]
        self.report.setPlainText(
            f"Rounds imported: {len(rounds)}\n"
            f"Historical median: {statistics.median(rounds):.2f}x\n"
            f"Last 30 median: {statistics.median(recent):.2f}x\n"
            f"Observed below 2x: {sum(x < 2 for x in rounds) / len(rounds):.1%}\n"
            f"Observed at or above 2x: {sum(x >= 2 for x in rounds) / len(rounds):.1%}\n"
            "\nNext round: UNKNOWN\n"
            "Historical statistics cannot reveal a future random result."
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
