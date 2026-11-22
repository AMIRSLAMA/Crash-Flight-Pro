import csv
import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QUrl
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
    QWidget, QSplitter,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from analysis_engine import read_csv, summary, walk_forward, validate
from round_store import RoundStore


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crash Flight Pro — Historical Analyzer")
        self.resize(1350, 820)
        directory = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        path = Path(directory or str(Path.home() / ".crash-flight-pro"))
        self.store = RoundStore(path / "rounds.json")

        root = QWidget()
        layout = QVBoxLayout(root)
        toolbar = QHBoxLayout()
        self.address = QLineEdit()
        self.address.setPlaceholderText("Enter a full https:// website address")
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
        side.addWidget(QLabel("Historical analysis — next round unknown"))

        load_button = QPushButton("Import CSV")
        load_button.clicked.connect(self.load_csv)
        side.addWidget(load_button)

        manual = QHBoxLayout()
        self.multiplier = QLineEdit()
        self.multiplier.setPlaceholderText("Completed multiplier, e.g. 2.35")
        self.multiplier.returnPressed.connect(self.add_round)
        add_button = QPushButton("Add round")
        add_button.clicked.connect(self.add_round)
        manual.addWidget(self.multiplier)
        manual.addWidget(add_button)
        side.addLayout(manual)

        export_button = QPushButton("Export CSV")
        export_button.clicked.connect(self.export_csv)
        side.addWidget(export_button)
        clear_button = QPushButton("Clear saved rounds")
        clear_button.clicked.connect(self.clear_rounds)
        side.addWidget(clear_button)

        self.report = QTextEdit()
        self.report.setReadOnly(True)
        side.addWidget(self.report)
        splitter.addWidget(sidebar)
        splitter.setSizes([950, 400])
        layout.addWidget(splitter)
        self.setCentralWidget(root)
        self.update_report()

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
            values = read_csv(filename)
            self.store.import_values(values)
            self.update_report()
        except (ValueError, OSError, UnicodeError, KeyError) as exc:
            QMessageBox.warning(self, "Import failed", str(exc))

    def add_round(self):
        try:
            self.store.add(self.multiplier.text())
            self.multiplier.clear()
            self.update_report()
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Invalid multiplier", str(exc))

    def export_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export historical rounds", "rounds.csv", "CSV files (*.csv)"
        )
        if not filename:
            return
        try:
            with Path(filename).open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["multiplier"])
                for value in self.store.rounds:
                    writer.writerow([value])
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def clear_rounds(self):
        answer = QMessageBox.question(
            self, "Confirm", "Delete all locally saved historical rounds?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.store.clear()
            self.update_report()

    def update_report(self):
        stats = summary(self.store.rounds)
        if stats is None:
            self.report.setPlainText(
                "No historical rounds yet. Import CSV or add completed rounds.\n"
                "Next round: UNKNOWN"
            )
            return
        evaluation = walk_forward(self.store.rounds)
        lines = [
            f"Rounds: {stats['count']}",
            f"Historical median: {stats['median']:.2f}x",
            f"Last 30 median: {stats['recent_median']:.2f}x",
            f"Below 2x (observed): {stats['below_2']:.1%}",
            f"At or above 2x (observed): {stats['at_least_2']:.1%}",
            f"Observed range: {stats['minimum']:.2f}x – {stats['maximum']:.2f}x",
        ]
        if evaluation:
            lines.extend([
                "",
                f"Walk-forward rounds: {evaluation['evaluated']}",
                f"Rolling median MAE: {evaluation['rolling_mae']:.3f}x",
                f"Constant baseline MAE: {evaluation['baseline_mae']:.3f}x",
            ])
        lines.extend([
            "", "Next round: UNKNOWN",
            "Past rounds do not reveal independent random future results.",
            "No automated bets, page scraping, or hidden result extraction.",
        ])
        self.report.setPlainText("\n".join(lines))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = Window()
    except (ValueError, OSError) as exc:
        QMessageBox.critical(None, "Local data error", str(exc))
        sys.exit(1)
    window.show()
    sys.exit(app.exec())
