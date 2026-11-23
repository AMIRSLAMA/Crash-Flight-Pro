import csv
import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QUrl
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
    QCheckBox, QWidget, QSplitter,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from analysis_engine import read_csv, summary, walk_forward
from capture_bridge import CapturePage
from event_report import build_report
from round_store import RoundStore
from live_round_store import LiveRoundStore
from upcoming_round import UpcomingRound
from pre_crash_audit import PreCrashAudit


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crash Flight Pro")
        self.resize(1350, 820)
        directory = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        path = Path(directory or str(Path.home() / ".crash-flight-pro"))
        self.store = RoundStore(path / "rounds.json")
        self.live_store = LiveRoundStore(path / "live_rounds.json")
        self.upcoming = UpcomingRound()
        self.pre_crash_audit = PreCrashAudit()

        root = QWidget()
        layout = QVBoxLayout(root)
        toolbar = QHBoxLayout()
        self.address = QLineEdit()
        self.address.setPlaceholderText("أدخل رابط اللعبة")
        self.address.returnPressed.connect(self.open_url)
        open_button = QPushButton("فتح اللعبة")
        open_button.clicked.connect(self.open_url)
        toolbar.addWidget(self.address)
        toolbar.addWidget(open_button)
        layout.addLayout(toolbar)

        splitter = QSplitter()
        self.browser = QWebEngineView()
        self.capture_page = CapturePage(
            self.browser.page().profile(),
            path / "captured_events.jsonl",
            self.browser,
        )
        self.capture_page.install_capture()
        self.capture_page.on_event = self.capture_event
        self.browser.setPage(self.capture_page)
        self.browser.urlChanged.connect(
            lambda url: self.address.setText(url.toString())
        )
        splitter.addWidget(self.browser)

        sidebar = QWidget()
        side = QVBoxLayout(sidebar)
        side.addWidget(QLabel("متابعة الجولة"))
        self.capture_toggle = QCheckBox("تشغيل متابعة أحداث اللعبة")
        self.capture_toggle.toggled.connect(self.toggle_capture)
        side.addWidget(self.capture_toggle)
        self.capture_status = QLabel("المتابعة متوقفة")
        self.capture_status.setWordWrap(True)
        side.addWidget(self.capture_status)

        self.upcoming_status = QLabel("رقم الجولة القادمة: بانتظار بيانات اللعبة")
        self.upcoming_status.setWordWrap(True)
        side.addWidget(self.upcoming_status)

        self.audit_status = QLabel("التنبيه المبكر: لا توجد إشارة موثوقة حتى الآن")
        self.audit_status.setWordWrap(True)
        side.addWidget(self.audit_status)

        report_button = QPushButton("تصدير تقرير الفحص")
        report_button.clicked.connect(self.export_event_report)
        side.addWidget(report_button)

        load_button = QPushButton("استيراد سجل سابق CSV")
        load_button.clicked.connect(self.load_csv)
        side.addWidget(load_button)

        manual = QHBoxLayout()
        self.multiplier = QLineEdit()
        self.multiplier.setPlaceholderText("مضاعف جولة انتهت")
        self.multiplier.returnPressed.connect(self.add_round)
        add_button = QPushButton("إضافة")
        add_button.clicked.connect(self.add_round)
        manual.addWidget(self.multiplier)
        manual.addWidget(add_button)
        side.addLayout(manual)

        export_button = QPushButton("تصدير CSV")
        export_button.clicked.connect(self.export_csv)
        side.addWidget(export_button)
        clear_button = QPushButton("مسح السجل المحفوظ")
        clear_button.clicked.connect(self.clear_rounds)
        side.addWidget(clear_button)

        self.report = QTextEdit()
        self.report.setReadOnly(True)
        side.addWidget(self.report)
        splitter.addWidget(sidebar)
        splitter.setSizes([1000, 350])
        layout.addWidget(splitter)
        self.setCentralWidget(root)
        self.update_report()

    def toggle_capture(self, enabled):
        self.capture_page.capture_enabled = enabled
        self.capture_status.setText(
            "المتابعة تعمل؛ أعد تحميل صفحة اللعبة لتفعيل الالتقاط."
            if enabled else "المتابعة متوقفة."
        )
        if enabled and not self.browser.url().isEmpty():
            self.browser.reload()

    def capture_event(self, record):
        self.upcoming.observe(record)
        self.pre_crash_audit.observe(record)
        self.audit_status.setText(self.pre_crash_audit.latest)
        self.upcoming_status.setText(self.upcoming.display)
        if self.live_store.add_event(record):
            self.update_report()
        self.capture_status.setText(
            f"تم رصد {self.capture_page.events_seen} حدثًا؛ "
            f"آخر حدث: {record['target']}."
        )

    def export_event_report(self):
        source = self.capture_page.store_path
        if not source.exists():
            QMessageBox.information(self, "لا توجد بيانات", "لم يتم التقاط أحداث بعد.")
            return
        destination, _ = QFileDialog.getSaveFileName(
            self, "حفظ تقرير الفحص", "event_report.json", "JSON files (*.json)"
        )
        if not destination:
            return
        try:
            import json
            report = build_report(source)
            Path(destination).write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
            QMessageBox.information(
                self, "تم", "تم حفظ التقرير محليًا. راجع محتواه قبل مشاركته."
            )
        except (OSError, ValueError, TypeError) as exc:
            QMessageBox.warning(self, "تعذر إنشاء التقرير", str(exc))

    def open_url(self):
        parsed = QUrl(self.address.text().strip())
        if parsed.scheme() not in ("https", "http") or not parsed.host():
            QMessageBox.warning(self, "رابط غير صحيح", "أدخل رابطًا يبدأ بـ http أو https.")
            return
        self.browser.setUrl(parsed)

    def load_csv(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "استيراد الجولات السابقة", "", "CSV files (*.csv)"
        )
        if not filename:
            return
        try:
            self.store.import_values(read_csv(filename))
            self.update_report()
        except (ValueError, OSError, UnicodeError, KeyError) as exc:
            QMessageBox.warning(self, "تعذر الاستيراد", str(exc))

    def add_round(self):
        try:
            self.store.add(self.multiplier.text())
            self.multiplier.clear()
            self.update_report()
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "مضاعف غير صحيح", str(exc))

    def export_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "تصدير الجولات", "rounds.csv", "CSV files (*.csv)"
        )
        if not filename:
            return
        try:
            import csv
            with Path(filename).open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["multiplier"])
                writer.writerows([[value] for value in self.store.rounds])
        except OSError as exc:
            QMessageBox.warning(self, "تعذر التصدير", str(exc))

    def clear_rounds(self):
        answer = QMessageBox.question(
            self, "تأكيد", "هل تريد حذف كل الجولات المحفوظة محليًا؟"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.store.clear()
            self.update_report()

    def update_report(self):
        combined = self.store.rounds + self.live_store.values
        stats = summary(combined)
        if stats is None:
            self.report.setPlainText(
                "لا توجد جولات محفوظة بعد.\n"
                "المضاعف القادم غير معروف؛ لا يتم توليد أرقام تجريبية على أنها توقع."
            )
            return
        evaluation = walk_forward(combined)
        lines = [
            f"عدد الجولات: {stats['count']}",
            f"الوسيط التاريخي: {stats['median']:.2f}x",
            f"وسيط آخر 30 جولة: {stats['recent_median']:.2f}x",
            f"أقل من 2x: {stats['below_2']:.1%}",
            f"2x أو أكثر: {stats['at_least_2']:.1%}",
            f"النطاق المسجل: {stats['minimum']:.2f}x – {stats['maximum']:.2f}x",
        ]
        if evaluation:
            lines.extend([
                "",
                f"اختبارات لاحقة: {evaluation['evaluated']}",
                f"خطأ الوسيط المتحرك: {evaluation['rolling_mae']:.3f}x",
                f"خطأ خط الأساس: {evaluation['baseline_mae']:.3f}x",
            ])
        lines.extend([
            "",
            "نتيجة الجولة القادمة: غير معروفة قبل ظهور دليل مباشر.",
            "لا يتم إنشاء مضاعف تجريبي أو عرضه كتنبؤ.",
        ])
        self.report.setPlainText("\n".join(lines))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = Window()
    except (ValueError, OSError) as exc:
        QMessageBox.critical(None, "خطأ في البيانات المحلية", str(exc))
        sys.exit(1)
    window.show()
    sys.exit(app.exec())
