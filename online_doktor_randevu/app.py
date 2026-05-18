from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QColor, QFont, QRegExpValidator
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import db



def _soft_shadow(widget: QWidget, blur: int = 28, dy: int = 8, alpha: int = 42) -> None:
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, dy)
    eff.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(eff)


def _polish_table(table: QTableWidget) -> None:
    table.setFrameShape(QFrame.NoFrame)
    table.verticalHeader().setVisible(False)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setWordWrap(False)
    table.setShowGrid(False)


def _msg_err(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.critical(parent, title, text)


def _msg_ok(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.information(parent, title, text)


def _confirm(parent: QWidget, title: str, text: str) -> bool:
    return QMessageBox.question(parent, title, text) == QMessageBox.Yes


def _validate_working_hours_csv(hours_csv: str) -> bool:
    parts = db.parse_hours(hours_csv)
    if not parts:
        return False
    for p in parts:
        if len(p) != 5 or p[2] != ":":
            return False
        hh, mm = p.split(":")
        if not hh.isdigit() or not mm.isdigit():
            return False
        hhv = int(hh)
        mmv = int(mm)
        if hhv < 0 or hhv > 23 or mmv < 0 or mmv > 59:
            return False
    return True


APP_STYLESHEET = """
* {
  font-family: "Segoe UI", "Segoe UI Emoji", "Segoe UI Symbol";
  font-size: 12px;
}

QToolTip {
  background: #0f172a;
  color: #f8fafc;
  border: 1px solid rgba(56, 189, 248, 0.45);
  border-radius: 8px;
  padding: 8px 11px;
}

QMessageBox {
  background: #ffffff;
}
QMessageBox QLabel {
  color: #0f172a;
  min-width: 280px;
}

QMainWindow {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 #ecfdf5, stop:0.38 #dbeafe, stop:0.72 #e0e7ff, stop:1 #f8fafc);
}

QDialog {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 #f0fdf4, stop:0.5 #eff6ff, stop:1 #eef2ff);
}

QWidget#appHeader {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 rgba(16, 185, 129, 0.72), stop:0.42 rgba(14, 165, 233, 0.62), stop:1 rgba(99, 102, 241, 0.45));
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 16px;
  min-height: 58px;
}

QLabel#appHeaderTitle {
  color: #f8fafc;
  font-size: 19px;
  font-weight: 800;
  letter-spacing: 0.35px;
}

QLabel#appHeaderSub {
  color: rgba(248, 250, 252, 0.9);
  font-size: 12px;
}

QLabel#rolePill {
  background: rgba(255, 255, 255, 0.22);
  color: #f8fafc;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 999px;
  padding: 5px 16px;
  font-weight: 800;
  font-size: 11px;
  letter-spacing: 0.08em;
}

QWidget#loginHero {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 rgba(16, 185, 129, 0.2), stop:1 rgba(14, 165, 233, 0.22));
  border: 1px solid rgba(2, 132, 199, 0.28);
  border-radius: 18px;
}

QGroupBox#loginCard {
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 #ffffff, stop:1 #f8fafc);
  border: 1px solid rgba(2, 132, 199, 0.2);
  border-radius: 18px;
  margin-top: 8px;
  padding: 18px 18px 14px 18px;
}
QGroupBox#loginCard::title {
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 0 10px;
  color: #0369a1;
  font-weight: 800;
}

QLabel#statsBar {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 rgba(255,255,255,0.95), stop:1 rgba(240,253,250,0.92));
  border: 1px solid rgba(2, 132, 199, 0.22);
  border-radius: 14px;
  padding: 11px 16px;
  color: #0f172a;
  font-weight: 700;
}

QWidget { color: #0f172a; }
QLabel { color: #0f172a; }

QGroupBox {
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(2, 132, 199, 0.2);
  border-radius: 16px;
  margin-top: 14px;
  padding: 16px 16px 12px 16px;
}
QGroupBox::title {
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 0 10px;
  color: #0369a1;
  font-weight: 800;
}

QTabWidget#mainTabs::pane {
  border: 1px solid rgba(15, 23, 42, 0.09);
  background: rgba(255, 255, 255, 0.94);
  border-radius: 16px;
  padding: 10px;
  top: -1px;
}

QTabBar#mainTabBar::tab {
  background: rgba(2, 132, 199, 0.1);
  color: #075985;
  padding: 12px 20px;
  margin-right: 5px;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  min-height: 22px;
}
QTabBar#mainTabBar::tab:selected {
  background: #ffffff;
  color: #0f172a;
  font-weight: 800;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-bottom: 0;
}
QTabBar#mainTabBar::tab:hover:!selected {
  background: rgba(16, 185, 129, 0.14);
}

QLineEdit, QComboBox, QDateEdit, QTextEdit {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid rgba(15, 23, 42, 0.14);
  border-radius: 12px;
  padding: 10px 13px;
  min-height: 22px;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
  border: 2px solid rgba(14, 165, 233, 0.85);
}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QTextEdit:hover {
  border: 1px solid rgba(2, 132, 199, 0.45);
}

QComboBox QAbstractItemView {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid rgba(2, 132, 199, 0.28);
  border-radius: 10px;
  padding: 4px;
  outline: 0;
  selection-background-color: rgba(16, 185, 129, 0.22);
  selection-color: #0f172a;
}

QPushButton#btnPrimary {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #10b981, stop:1 #0284c7);
  color: #ffffff;
  border: 0;
  border-radius: 12px;
  padding: 11px 18px;
  font-weight: 800;
}
QPushButton#btnPrimary:hover {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #059669, stop:1 #0369a1);
}
QPushButton#btnPrimary:pressed {
  background: #075985;
}

QPushButton#btnSecondary {
  background: rgba(255, 255, 255, 0.92);
  color: #0369a1;
  border: 2px solid #0284c7;
  border-radius: 12px;
  padding: 10px 16px;
  font-weight: 800;
}
QPushButton#btnSecondary:hover {
  background: rgba(2, 132, 199, 0.1);
}
QPushButton#btnSecondary:pressed {
  background: rgba(2, 132, 199, 0.16);
}

QPushButton#btnGhost {
  background: rgba(255, 255, 255, 0.82);
  color: #0369a1;
  border: 1px solid rgba(2, 132, 199, 0.35);
  border-radius: 12px;
  padding: 10px 16px;
  font-weight: 700;
}
QPushButton#btnGhost:hover {
  background: rgba(2, 132, 199, 0.12);
}

QPushButton {
  background: #0284c7;
  color: #ffffff;
  border: 0;
  border-radius: 12px;
  padding: 10px 15px;
  font-weight: 700;
}
QPushButton:hover { background: #0369a1; }
QPushButton:pressed { background: #075985; }
QPushButton:disabled { background: rgba(148, 163, 184, 0.45); color: rgba(15, 23, 42, 0.5); }

QTableWidget {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  gridline-color: transparent;
  selection-background-color: rgba(16, 185, 129, 0.28);
  selection-color: #0f172a;
  alternate-background-color: rgba(14, 165, 233, 0.055);
}
QTableView::item {
  padding: 8px 6px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.05);
}
QTableView::item:hover {
  background: rgba(14, 165, 233, 0.1);
}
QTableView::item:selected {
  background: rgba(16, 185, 129, 0.28);
}
QHeaderView::section {
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 rgba(2, 132, 199, 0.14), stop:1 rgba(2, 132, 199, 0.08));
  color: #0f172a;
  padding: 10px;
  border: 0;
  border-bottom: 2px solid rgba(2, 132, 199, 0.35);
  font-weight: 800;
}

QScrollBar:vertical {
  background: rgba(241, 245, 249, 0.9);
  width: 11px;
  margin: 2px;
  border-radius: 6px;
}
QScrollBar::handle:vertical {
  background: rgba(2, 132, 199, 0.42);
  min-height: 36px;
  border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
  background: rgba(2, 132, 199, 0.65);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; width: 0px; }

QScrollBar:horizontal {
  background: rgba(241, 245, 249, 0.9);
  height: 11px;
  margin: 2px;
  border-radius: 6px;
}
QScrollBar::handle:horizontal {
  background: rgba(2, 132, 199, 0.42);
  min-width: 36px;
  border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
  background: rgba(2, 132, 199, 0.65);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QTextEdit#reportEditor {
  font-family: "Cascadia Mono", "Consolas", "Segoe UI", monospace;
  font-size: 12px;
  line-height: 1.4;
  background: rgba(255, 255, 255, 0.97);
}

QCalendarWidget QAbstractItemView:enabled {
  font-size: 11px;
  selection-background-color: rgba(2, 132, 199, 0.55);
  selection-color: #ffffff;
}
"""


@dataclass
class DoctorRow:
    id: int
    name: str
    specialty: str
    working_hours: str


@dataclass
class PatientRow:
    id: int
    name: str
    tc: str
    phone: str


class LoginDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Online Doktor Randevu - Giris")
        self.session: Optional[db.UserSession] = None

        self.username = QLineEdit()
        self.username.setPlaceholderText("Kullanici adiniz")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Sifreniz")
        self.username.setToolTip("Kayitli kullanici adiniz")
        self.password.setToolTip("Hesap sifreniz")

        btn_login = QPushButton("Giris Yap")
        btn_login.setObjectName("btnPrimary")
        btn_login.clicked.connect(self._on_login)
        btn_register = QPushButton("Kayit Ol")
        btn_register.setObjectName("btnSecondary")
        btn_register.clicked.connect(self._on_register)
        btn_register.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        btns.addWidget(btn_login, 1)
        btns.addWidget(btn_register)

        hero_emoji = QLabel("🏥\n🩺")
        hero_emoji.setAlignment(Qt.AlignCenter)
        hero_emoji.setStyleSheet(
            "font-size: 44px; line-height: 1.05; background: transparent; padding: 8px;"
        )
        hero_title = QLabel("Online Doktor Randevu")
        hero_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; letter-spacing: 0.2px;")
        hero_sub = QLabel("Sagliginiz icin tek ekranda randevu.\nHizli giris, net takvim, guvenli kayit.")
        hero_sub.setWordWrap(True)
        hero_sub.setStyleSheet("color: rgba(15,23,42,0.72); font-size: 12px;")

        left_panel = QWidget()
        left_panel.setObjectName("loginHero")
        left = QVBoxLayout(left_panel)
        left.setContentsMargins(18, 18, 18, 18)
        left.addWidget(hero_emoji)
        left.addWidget(hero_title)
        left.addWidget(hero_sub)
        left.addStretch(1)
        tip = QLabel("💡 Ipucu: Hasta hesabi icin once Kayit Ol.")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: rgba(3,105,161,0.9); font-size: 11px;")
        left.addWidget(tip)

        card = QGroupBox("Giris bilgileri")
        card.setObjectName("loginCard")
        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("👤 Kullanici adi:", self.username)
        form.addRow("🔒 Sifre:", self.password)
        form.addRow(btns)
        card.setLayout(form)

        root = QHBoxLayout()
        root.addWidget(left_panel, 2)
        root.addWidget(card, 3)
        root.setSpacing(20)

        wrap = QWidget()
        wrap.setLayout(root)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(wrap)
        self.setLayout(layout)
        self.resize(700, 340)
        _soft_shadow(left_panel, blur=32, dy=10, alpha=38)
        _soft_shadow(card, blur=36, dy=12, alpha=48)
        app = QApplication.instance()
        if app is not None:
            self.setWindowIcon(app.windowIcon())

    def _on_login(self) -> None:
        s = db.authenticate(self.username.text(), self.password.text())
        if not s:
            _msg_err(self, "Hata", "Kullanici adi veya sifre yanlis.")
            return
        self.session = s
        self.accept()

    def _on_register(self) -> None:
        dlg = RegisterDialog(self)
        if dlg.exec_() != QDialog.Accepted or not dlg.created_username:
            return
        self.username.setText(dlg.created_username)
        self.password.clear()
        _msg_ok(self, "Basarili", "Hesap olusturuldu. Simdi giris yapabilirsiniz.")


class RegisterDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Yeni Hasta Kaydi")
        self.created_username: Optional[str] = None

        head = QLabel("📝  Yeni hasta kaydi")
        head.setObjectName("registerTitle")
        head.setStyleSheet("font-size: 17px; font-weight: 800; color: #0f172a; padding-bottom: 6px;")

        self.full_name = QLineEdit()
        self.full_name.setMaxLength(60)
        self.full_name.setValidator(
            QRegExpValidator(QRegExp(r"[A-Za-zÇĞİÖŞÜçğıöşü .'-]{0,60}"), self)
        )
        self.tc = QLineEdit()
        self.tc.setMaxLength(11)
        self.tc.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))
        self.phone = QLineEdit()
        self.phone.setMaxLength(11)
        self.phone.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))
        self.tc.setToolTip("11 haneli TC kimlik numarasi")
        self.phone.setToolTip("05 ile baslayan 11 haneli cep telefonu")

        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        btn = QPushButton("Kaydi Tamamla")
        btn.setObjectName("btnPrimary")
        btn.clicked.connect(self._submit)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("📝 Ad Soyad:", self.full_name)
        form.addRow("🪪 TC:", self.tc)
        form.addRow("📱 Telefon:", self.phone)
        form.addRow(QLabel("— 🔑 Giris Bilgileri —"))
        form.addRow("👤 Kullanici adi:", self.username)
        form.addRow("🔒 Sifre:", self.password)
        form.addRow(btn)

        outer = QVBoxLayout()
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)
        outer.addWidget(head)
        outer.addLayout(form)
        self.setLayout(outer)
        self.resize(440, 400)
        app = QApplication.instance()
        if app is not None:
            self.setWindowIcon(app.windowIcon())

    def _submit(self) -> None:
        full_name = self.full_name.text().strip()
        tc = self.tc.text().strip()
        phone = self.phone.text().strip()
        username = self.username.text().strip()
        password = self.password.text().strip()

        if not full_name or not tc or not phone or not username or not password:
            _msg_err(self, "Hata", "Tum alanlar zorunlu.")
            return
        if any(ch.isdigit() for ch in full_name):
            _msg_err(self, "Hata", "Ad Soyad alaninda sayi olamaz.")
            return
        if len(tc) != 11 or not tc.isdigit():
            _msg_err(self, "Hata", "TC 11 haneli sayi olmali.")
            return
        if len(phone) != 11 or not phone.isdigit() or not phone.startswith("05"):
            _msg_err(self, "Hata", "Telefon 11 haneli olmali ve 05 ile baslamali. Orn: 05XXXXXXXXX")
            return
        if len(username) < 3 or len(password) < 3:
            _msg_err(self, "Hata", "Kullanici adi ve sifre en az 3 karakter olmali.")
            return

        try:
            patient_id = db.create_patient(full_name, tc, phone)
            db.create_user(username, password, "hasta", None, patient_id)
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return

        self.created_username = username
        self.accept()


class DoctorsTab(QWidget):
    def __init__(self, can_edit: bool) -> None:
        super().__init__()
        self.can_edit = can_edit

        self.search = QLineEdit()
        self.search.setPlaceholderText("Ara (ad / uzmanlik)...")
        self.search.textChanged.connect(self.refresh)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Ad", "Uzmanlik", "Uygun saatler"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        _polish_table(self.table)

        self.name = QLineEdit()
        self.name.setMaxLength(60)
        self.name.setValidator(
            QRegExpValidator(QRegExp(r"[A-Za-zÇĞİÖŞÜçğıöşü .'-]{0,60}"), self)
        )
        self.specialty = QLineEdit()
        self.hours = QLineEdit()
        self.hours.setPlaceholderText("Orn: 09:00,10:00,14:00")
        self.hours.setValidator(QRegExpValidator(QRegExp(r"[0-9:, ]*"), self))

        form_box = QGroupBox("🩺 Doktor bilgisi")
        form = QFormLayout()
        form.addRow("Ad:", self.name)
        form.addRow("Uzmanlik:", self.specialty)
        form.addRow("Uygun saatler:", self.hours)
        form_box.setLayout(form)

        self.btn_add = QPushButton("Ekle")
        self.btn_update = QPushButton("Guncelle")
        self.btn_delete = QPushButton("Sil")

        self.btn_add.clicked.connect(self.add_doctor)
        self.btn_update.clicked.connect(self.update_doctor)
        self.btn_delete.clicked.connect(self.delete_doctor)
        self.table.itemSelectionChanged.connect(self._fill_from_selected)

        btns = QHBoxLayout()
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_update)
        btns.addWidget(self.btn_delete)
        btns.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(self.search)
        layout.addWidget(self.table, 1)
        layout.addWidget(form_box)
        layout.addLayout(btns)
        self.setLayout(layout)

        if not self.can_edit:
            self.btn_add.setEnabled(False)
            self.btn_update.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.name.setEnabled(False)
            self.specialty.setEnabled(False)
            self.hours.setEnabled(False)

        self.refresh()

    def refresh(self) -> None:
        q = (self.search.text() or "").strip().lower()
        con = db.connect()
        try:
            rows = con.execute("SELECT * FROM doctors ORDER BY id DESC;").fetchall()
        finally:
            con.close()

        data = []
        for r in rows:
            d = DoctorRow(int(r["id"]), r["name"], r["specialty"], r["working_hours"])
            if q and (q not in d.name.lower() and q not in d.specialty.lower()):
                continue
            data.append(d)

        self.table.setRowCount(len(data))
        for i, d in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(str(d.id)))
            self.table.setItem(i, 1, QTableWidgetItem(d.name))
            self.table.setItem(i, 2, QTableWidgetItem(d.specialty))
            self.table.setItem(i, 3, QTableWidgetItem(d.working_hours))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    def _fill_from_selected(self) -> None:
        sid = self._selected_id()
        if sid is None:
            return
        row = self.table.currentRow()
        self.name.setText(self.table.item(row, 1).text())
        self.specialty.setText(self.table.item(row, 2).text())
        self.hours.setText(self.table.item(row, 3).text())

    def add_doctor(self) -> None:
        name = self.name.text().strip()
        spec = self.specialty.text().strip()
        hours = self.hours.text().strip()
        if not name or not spec or not hours:
            _msg_err(self, "Hata", "Ad, uzmanlik ve uygun saatler zorunlu.")
            return
        if not _validate_working_hours_csv(hours):
            _msg_err(self, "Hata", "Uygun saatler HH:MM,HH:MM formatinda olmali.")
            return
        con = db.connect()
        try:
            con.execute(
                "INSERT INTO doctors(name,specialty,working_hours) VALUES(?,?,?);",
                (name, spec, hours),
            )
            con.commit()
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        finally:
            con.close()
        self.refresh()
        _msg_ok(self, "Basarili", "Doktor eklendi.")

    def update_doctor(self) -> None:
        sid = self._selected_id()
        if sid is None:
            _msg_err(self, "Hata", "Guncellenecek doktoru secin.")
            return
        name = self.name.text().strip()
        spec = self.specialty.text().strip()
        hours = self.hours.text().strip()
        if not name or not spec or not hours:
            _msg_err(self, "Hata", "Ad, uzmanlik ve uygun saatler zorunlu.")
            return
        if not _validate_working_hours_csv(hours):
            _msg_err(self, "Hata", "Uygun saatler HH:MM,HH:MM formatinda olmali.")
            return
        con = db.connect()
        try:
            con.execute(
                "UPDATE doctors SET name=?, specialty=?, working_hours=? WHERE id=?;",
                (name, spec, hours, sid),
            )
            con.commit()
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        finally:
            con.close()
        self.refresh()
        _msg_ok(self, "Basarili", "Doktor guncellendi.")

    def delete_doctor(self) -> None:
        sid = self._selected_id()
        if sid is None:
            _msg_err(self, "Hata", "Silinecek doktoru secin.")
            return
        if not _confirm(self, "Onay", "Doktor silinsin mi? (Randevular da silinir)"):
            return
        con = db.connect()
        try:
            con.execute("DELETE FROM doctors WHERE id=?;", (sid,))
            con.commit()
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        finally:
            con.close()
        self.refresh()
        _msg_ok(self, "Basarili", "Doktor silindi.")


class PatientsTab(QWidget):
    def __init__(self, can_edit: bool) -> None:
        super().__init__()
        self.can_edit = can_edit

        self.search = QLineEdit()
        self.search.setPlaceholderText("Ara (ad / TC / telefon)...")
        self.search.textChanged.connect(self.refresh)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Ad", "TC", "Telefon"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        _polish_table(self.table)

        self.name = QLineEdit()
        self.name.setMaxLength(60)
        self.name.setValidator(
            QRegExpValidator(QRegExp(r"[A-Za-zÇĞİÖŞÜçğıöşü .'-]{0,60}"), self)
        )
        self.tc = QLineEdit()
        self.tc.setMaxLength(11)
        self.tc.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))
        self.phone = QLineEdit()
        self.phone.setMaxLength(11)
        self.phone.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))

        form_box = QGroupBox("👤 Hasta bilgisi")
        form = QFormLayout()
        form.addRow("Ad:", self.name)
        form.addRow("TC:", self.tc)
        form.addRow("Telefon:", self.phone)
        form_box.setLayout(form)

        self.btn_add = QPushButton("Ekle")
        self.btn_update = QPushButton("Guncelle")
        self.btn_delete = QPushButton("Sil")

        self.btn_add.clicked.connect(self.add_patient)
        self.btn_update.clicked.connect(self.update_patient)
        self.btn_delete.clicked.connect(self.delete_patient)
        self.table.itemSelectionChanged.connect(self._fill_from_selected)

        btns = QHBoxLayout()
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_update)
        btns.addWidget(self.btn_delete)
        btns.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(self.search)
        layout.addWidget(self.table, 1)
        layout.addWidget(form_box)
        layout.addLayout(btns)
        self.setLayout(layout)

        if not self.can_edit:
            self.btn_add.setEnabled(False)
            self.btn_update.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.name.setEnabled(False)
            self.tc.setEnabled(False)
            self.phone.setEnabled(False)

        self.refresh()

    def refresh(self) -> None:
        q = (self.search.text() or "").strip().lower()
        con = db.connect()
        try:
            rows = con.execute("SELECT * FROM patients ORDER BY id DESC;").fetchall()
        finally:
            con.close()

        data = []
        for r in rows:
            p = PatientRow(int(r["id"]), r["name"], r["tc"], r["phone"])
            if q and (q not in p.name.lower() and q not in p.tc.lower() and q not in p.phone.lower()):
                continue
            data.append(p)

        self.table.setRowCount(len(data))
        for i, p in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(str(p.id)))
            self.table.setItem(i, 1, QTableWidgetItem(p.name))
            self.table.setItem(i, 2, QTableWidgetItem(p.tc))
            self.table.setItem(i, 3, QTableWidgetItem(p.phone))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    def _fill_from_selected(self) -> None:
        sid = self._selected_id()
        if sid is None:
            return
        row = self.table.currentRow()
        self.name.setText(self.table.item(row, 1).text())
        self.tc.setText(self.table.item(row, 2).text())
        self.phone.setText(self.table.item(row, 3).text())

    def add_patient(self) -> None:
        name = self.name.text().strip()
        tc = self.tc.text().strip()
        phone = self.phone.text().strip()
        if not name or not tc or not phone:
            _msg_err(self, "Hata", "Ad, TC ve telefon zorunlu.")
            return
        if any(ch.isdigit() for ch in name):
            _msg_err(self, "Hata", "Ad alaninda sayi olamaz.")
            return
        if len(tc) != 11 or not tc.isdigit():
            _msg_err(self, "Hata", "TC 11 haneli sayi olmali.")
            return
        if len(phone) != 11 or not phone.isdigit() or not phone.startswith("05"):
            _msg_err(self, "Hata", "Telefon 11 haneli olmali ve 05 ile baslamali. Orn: 05XXXXXXXXX")
            return
        con = db.connect()
        try:
            con.execute("INSERT INTO patients(name,tc,phone) VALUES(?,?,?);", (name, tc, phone))
            con.commit()
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        finally:
            con.close()
        self.refresh()
        _msg_ok(self, "Basarili", "Hasta eklendi.")

    def update_patient(self) -> None:
        sid = self._selected_id()
        if sid is None:
            _msg_err(self, "Hata", "Guncellenecek hastayi secin.")
            return
        name = self.name.text().strip()
        tc = self.tc.text().strip()
        phone = self.phone.text().strip()
        if not name or not tc or not phone:
            _msg_err(self, "Hata", "Ad, TC ve telefon zorunlu.")
            return
        if any(ch.isdigit() for ch in name):
            _msg_err(self, "Hata", "Ad alaninda sayi olamaz.")
            return
        if len(tc) != 11 or not tc.isdigit():
            _msg_err(self, "Hata", "TC 11 haneli sayi olmali.")
            return
        if len(phone) != 11 or not phone.isdigit() or not phone.startswith("05"):
            _msg_err(self, "Hata", "Telefon 11 haneli olmali ve 05 ile baslamali. Orn: 05XXXXXXXXX")
            return
        con = db.connect()
        try:
            con.execute("UPDATE patients SET name=?, tc=?, phone=? WHERE id=?;", (name, tc, phone, sid))
            con.commit()
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        finally:
            con.close()
        self.refresh()
        _msg_ok(self, "Basarili", "Hasta guncellendi.")

    def delete_patient(self) -> None:
        sid = self._selected_id()
        if sid is None:
            _msg_err(self, "Hata", "Silinecek hastayi secin.")
            return
        if not _confirm(self, "Onay", "Hasta silinsin mi? (Randevular da silinir)"):
            return
        con = db.connect()
        try:
            con.execute("DELETE FROM patients WHERE id=?;", (sid,))
            con.commit()
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        finally:
            con.close()
        self.refresh()
        _msg_ok(self, "Basarili", "Hasta silindi.")


class AppointmentsTab(QWidget):
    def __init__(self, can_edit: bool, session: db.UserSession) -> None:
        super().__init__()
        self.can_edit = can_edit
        self.session = session

        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(date.today())
        self.date_filter.dateChanged.connect(self.refresh)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Ara (doktor / hasta / not)...")
        self.search.textChanged.connect(self.refresh)

        top = QHBoxLayout()
        top.addWidget(QLabel("📆 Tarih:"))
        top.addWidget(self.date_filter)
        top.addStretch(1)
        top.addWidget(self.search)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Tarih", "Saat", "Doktor", "Hasta", "Not"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        _polish_table(self.table)

        self.doctor = QComboBox()
        self.doctor.currentIndexChanged.connect(self._sync_time_options)
        self.patient = QComboBox()
        self.appt_date = QDateEdit()
        self.appt_date.setCalendarPopup(True)
        self.appt_date.setDate(date.today())
        self.appt_time = QComboBox()
        self.note = QLineEdit()

        self.btn_reload_lists = QPushButton("Listeleri Yenile")
        self.btn_reload_lists.clicked.connect(self._load_doctors_patients)

        self.btn_add = QPushButton("Randevu Olustur")
        self.btn_delete = QPushButton("Randevu Iptal")
        self.btn_add.clicked.connect(self.add_appt)
        self.btn_delete.clicked.connect(self.delete_appt)
        self.table.itemSelectionChanged.connect(self._sync_time_options)

        form_box = QGroupBox("📅 Yeni randevu")
        form = QGridLayout()
        form.addWidget(QLabel("🩺 Doktor:"), 0, 0)
        form.addWidget(self.doctor, 0, 1)
        form.addWidget(QLabel("👤 Hasta:"), 1, 0)
        form.addWidget(self.patient, 1, 1)
        form.addWidget(QLabel("📆 Tarih:"), 2, 0)
        form.addWidget(self.appt_date, 2, 1)
        form.addWidget(QLabel("🕐 Saat:"), 3, 0)
        form.addWidget(self.appt_time, 3, 1)
        form.addWidget(QLabel("📝 Not:"), 4, 0)
        form.addWidget(self.note, 4, 1)
        form.addWidget(self.btn_reload_lists, 5, 0, 1, 2)
        form_box.setLayout(form)

        btns = QHBoxLayout()
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_delete)
        btns.addStretch(1)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.table, 1)
        layout.addWidget(form_box)
        layout.addLayout(btns)
        self.setLayout(layout)

        if not self.can_edit or self.session.role == "doktor":
            self.btn_add.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.doctor.setEnabled(False)
            self.appt_date.setEnabled(False)
            self.appt_time.setEnabled(False)
            self.note.setEnabled(False)
        if not self.can_edit:
            self.patient.setEnabled(False)

        self._load_doctors_patients()
        self.refresh()

    def _load_doctors_patients(self) -> None:
        con = db.connect()
        try:
            docs = con.execute("SELECT id, name, specialty, working_hours FROM doctors ORDER BY name;").fetchall()
            pats = con.execute("SELECT id, name, tc FROM patients ORDER BY name;").fetchall()
        finally:
            con.close()

        self.doctor.clear()
        for d in docs:
            self.doctor.addItem(f"{d['name']} ({d['specialty']})", int(d["id"]))

        self.patient.clear()
        for p in pats:
            self.patient.addItem(f"{p['name']} - {p['tc']}", int(p["id"]))

        if self.session.role == "doktor" and self.session.doctor_id:
            idx = self.doctor.findData(int(self.session.doctor_id))
            if idx >= 0:
                self.doctor.setCurrentIndex(idx)
            self.doctor.setEnabled(False)
            self.patient.setEnabled(False)

        if self.session.role == "hasta" and self.session.patient_id:
            idx = self.patient.findData(int(self.session.patient_id))
            if idx >= 0:
                self.patient.setCurrentIndex(idx)
            self.patient.setEnabled(False)

        self._sync_time_options()

    def _sync_time_options(self) -> None:
        doctor_id = self.doctor.currentData()
        if doctor_id is None:
            self.appt_time.clear()
            return
        con = db.connect()
        try:
            row = con.execute("SELECT working_hours FROM doctors WHERE id=?;", (int(doctor_id),)).fetchone()
        finally:
            con.close()
        self.appt_time.clear()
        if not row:
            return
        for h in db.parse_hours(row["working_hours"]):
            self.appt_time.addItem(h)

    def refresh(self) -> None:
        d = self.date_filter.date().toPyDate().isoformat()
        q = (self.search.text() or "").strip().lower()
        con = db.connect()
        try:
            rows = con.execute(
                """
                SELECT a.id, a.appt_date, a.appt_time, a.note,
                       a.doctor_id, a.patient_id,
                       d.name AS doctor_name, d.specialty AS doctor_specialty,
                       p.name AS patient_name, p.tc AS patient_tc
                FROM appointments a
                JOIN doctors d ON d.id = a.doctor_id
                JOIN patients p ON p.id = a.patient_id
                WHERE a.appt_date = ?
                ORDER BY a.appt_time;
                """,
                (d,),
            ).fetchall()
        finally:
            con.close()

        filtered = []
        for r in rows:
            doctor = f"{r['doctor_name']} ({r['doctor_specialty']})"
            patient = f"{r['patient_name']} ({r['patient_tc']})"
            note = r["note"] or ""
            blob = f"{doctor} {patient} {note}".lower()
            if q and q not in blob:
                continue
            if self.session.role == "doktor" and self.session.doctor_id:
                if int(r["doctor_id"]) != int(self.session.doctor_id):
                    continue
            if self.session.role == "hasta" and self.session.patient_id:
                if int(r["patient_id"]) != int(self.session.patient_id):
                    continue
            filtered.append((r["id"], r["appt_date"], r["appt_time"], doctor, patient, note))

        self.table.setRowCount(len(filtered))
        for i, row in enumerate(filtered):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    def add_appt(self) -> None:
        doctor_id = self.doctor.currentData()
        patient_id = self.patient.currentData()
        if self.session.role == "hasta" and self.session.patient_id:
            patient_id = int(self.session.patient_id)
        if doctor_id is None or patient_id is None:
            _msg_err(self, "Hata", "Doktor ve hasta secin.")
            return
        appt_date = self.appt_date.date().toPyDate().isoformat()
        appt_time = self.appt_time.currentText().strip()
        if not appt_time:
            _msg_err(self, "Hata", "Saat secin.")
            return

        con = db.connect()
        try:
            # check chosen time is in doctor's working hours
            row = con.execute("SELECT working_hours FROM doctors WHERE id=?;", (int(doctor_id),)).fetchone()
            if not row or appt_time not in db.parse_hours(row["working_hours"]):
                _msg_err(self, "Hata", "Doktor bu saatte uygun degil.")
                return

            con.execute(
                "INSERT INTO appointments(doctor_id,patient_id,appt_date,appt_time,note) VALUES(?,?,?,?,?);",
                (int(doctor_id), int(patient_id), appt_date, appt_time, (self.note.text() or "").strip()),
            )
            con.commit()
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        finally:
            con.close()

        self.date_filter.setDate(self.appt_date.date())
        self.refresh()
        _msg_ok(self, "Basarili", "Randevu olusturuldu.")

    def delete_appt(self) -> None:
        sid = self._selected_id()
        if sid is None:
            _msg_err(self, "Hata", "Iptal edilecek randevuyu secin.")
            return
        if not _confirm(self, "Onay", "Randevu iptal edilsin mi?"):
            return
        con = db.connect()
        try:
            con.execute("DELETE FROM appointments WHERE id=?;", (sid,))
            con.commit()
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        finally:
            con.close()
        self.refresh()
        _msg_ok(self, "Basarili", "Randevu iptal edildi.")


class ReportsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.report_date = QDateEdit()
        self.report_date.setCalendarPopup(True)
        self.report_date.setDate(date.today())

        self.btn_load = QPushButton("Gunluk Listeyi Getir")
        self.btn_export = QPushButton("CSV Disari Aktar")
        self.btn_load.clicked.connect(self.load)
        self.btn_export.clicked.connect(self.export_csv)

        top = QHBoxLayout()
        top.addWidget(QLabel("📆 Tarih:"))
        top.addWidget(self.report_date)
        top.addWidget(self.btn_load)
        top.addStretch(1)
        top.addWidget(self.btn_export)

        self.text = QTextEdit()
        self.text.setObjectName("reportEditor")
        self.text.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.text, 1)
        self.setLayout(layout)

        self.load()

    def _fetch(self):
        d = self.report_date.date().toPyDate().isoformat()
        con = db.connect()
        try:
            rows = con.execute(
                """
                SELECT a.id, a.appt_date, a.appt_time, a.note,
                       d.name AS doctor_name, d.specialty AS doctor_specialty,
                       p.name AS patient_name, p.tc AS patient_tc
                FROM appointments a
                JOIN doctors d ON d.id = a.doctor_id
                JOIN patients p ON p.id = a.patient_id
                WHERE a.appt_date = ?
                ORDER BY a.appt_time;
                """,
                (d,),
            ).fetchall()
        finally:
            con.close()
        return d, rows

    def load(self) -> None:
        d, rows = self._fetch()
        if not rows:
            self.text.setPlainText(f"{d} icin randevu yok.")
            return
        lines = [f"Gunluk Randevu Listesi ({d})", "-" * 40]
        for r in rows:
            doctor = f"{r['doctor_name']} ({r['doctor_specialty']})"
            patient = f"{r['patient_name']} ({r['patient_tc']})"
            note = r["note"] or ""
            lines.append(f"#{r['id']} | {r['appt_time']} | {doctor} | {patient} | {note}")
        self.text.setPlainText("\n".join(lines))

    def export_csv(self) -> None:
        d, rows = self._fetch()
        if not rows:
            _msg_err(self, "Hata", "Disari aktarilacak veri yok.")
            return
        suggested = f"randevular_{d}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "CSV Kaydet", suggested, "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "date", "time", "doctor", "specialty", "patient", "tc", "note"])
            for r in rows:
                w.writerow(
                    [
                        r["id"],
                        r["appt_date"],
                        r["appt_time"],
                        r["doctor_name"],
                        r["doctor_specialty"],
                        r["patient_name"],
                        r["patient_tc"],
                        r["note"] or "",
                    ]
                )
        _msg_ok(self, "Basarili", f"CSV kaydedildi: {Path(path).name}")


class UsersTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Kullanici", "Rol", "Doktor", "Hasta"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        _polish_table(self.table)

        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.role = QComboBox()
        self.role.addItems(["doktor", "hasta"])
        self.role.currentTextChanged.connect(self._sync_role_fields)
        self.doctor_combo = QComboBox()
        self.patient_combo = QComboBox()
        self._reload_links()
        self._sync_role_fields(self.role.currentText())

        self.btn_add = QPushButton("Hesap Olustur")
        self.btn_add.clicked.connect(self.add_user)
        self.btn_reload = QPushButton("Listeyi Yenile")
        self.btn_reload.clicked.connect(self.refresh)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("👤 Kullanici adi:", self.username)
        form.addRow("🔒 Sifre:", self.password)
        form.addRow("🏷️ Rol:", self.role)
        form.addRow("🩺 Doktor baglantisi:", self.doctor_combo)
        form.addRow("👥 Hasta baglantisi:", self.patient_combo)
        form.addRow(self.btn_add)

        box = QGroupBox("🔐 Admin - hesap yonetimi")
        box.setLayout(form)

        top = QHBoxLayout()
        top.addWidget(self.btn_reload)
        top.addStretch(1)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.table, 1)
        layout.addWidget(box)
        self.setLayout(layout)
        self.refresh()

    def _reload_links(self) -> None:
        self.doctor_combo.clear()
        self.patient_combo.clear()
        for d in db.get_doctors():
            self.doctor_combo.addItem(f"{d['name']} ({d['specialty']})", int(d["id"]))
        for p in db.get_patients():
            self.patient_combo.addItem(f"{p['name']} ({p['tc']})", int(p["id"]))

    def _sync_role_fields(self, role: str) -> None:
        is_doc = role == "doktor"
        self.doctor_combo.setEnabled(is_doc)
        self.patient_combo.setEnabled(not is_doc)

    def add_user(self) -> None:
        username = self.username.text().strip()
        password = self.password.text().strip()
        role = self.role.currentText()
        if len(username) < 3 or len(password) < 3:
            _msg_err(self, "Hata", "Kullanici adi ve sifre en az 3 karakter olmali.")
            return
        doctor_id = int(self.doctor_combo.currentData()) if role == "doktor" else None
        patient_id = int(self.patient_combo.currentData()) if role == "hasta" else None
        try:
            db.create_user(username, password, role, doctor_id, patient_id)
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        self.username.clear()
        self.password.clear()
        self.refresh()
        _msg_ok(self, "Basarili", f"{role} hesabi olusturuldu.")

    def refresh(self) -> None:
        self._reload_links()
        rows = db.list_users()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["username"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["role"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["doctor_name"] or "-"))
            self.table.setItem(i, 3, QTableWidgetItem(r["patient_name"] or "-"))
        self.table.resizeColumnsToContents()


class MainWindow(QMainWindow):
    def __init__(self, session: db.UserSession, on_logout) -> None:
        super().__init__()
        self.session = session
        self._on_logout = on_logout
        self.setWindowTitle(f"Online Doktor Randevu - {session.username} ({session.role})")
        self.resize(1120, 720)
        app_inst = QApplication.instance()
        if app_inst is not None:
            self.setWindowIcon(app_inst.windowIcon())

        header = QWidget()
        header.setObjectName("appHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 14, 20, 14)
        left_col = QVBoxLayout()
        left_col.setSpacing(4)
        ht = QLabel("Online Doktor Randevu")
        ht.setObjectName("appHeaderTitle")
        hs = QLabel(f"Hos geldin, {session.username}")
        hs.setObjectName("appHeaderSub")
        left_col.addWidget(ht)
        left_col.addWidget(hs)
        hl.addLayout(left_col, 1)
        role_lbl = QLabel(session.role.upper())
        role_lbl.setObjectName("rolePill")
        hl.addWidget(role_lbl, alignment=Qt.AlignRight | Qt.AlignVCenter)

        tabs = QTabWidget()
        tabs.setObjectName("mainTabs")
        tabs.tabBar().setObjectName("mainTabBar")
        tabs.setDocumentMode(True)
        can_edit = session.role == "admin"
        if session.role == "admin":
            tabs.addTab(DoctorsTab(can_edit=True), "🩺 Doktorlar")
            tabs.addTab(PatientsTab(can_edit=True), "👥 Hastalar")
            tabs.addTab(AppointmentsTab(can_edit=True, session=session), "📅 Randevular")
            tabs.addTab(ReportsTab(), "📊 Rapor")
            tabs.addTab(UsersTab(), "🔐 Kullanicilar")
        elif session.role == "doktor":
            tabs.addTab(AppointmentsTab(can_edit=False, session=session), "📅 Randevularim")
            tabs.addTab(ReportsTab(), "📊 Rapor")
        else:  # hasta
            tabs.addTab(AppointmentsTab(can_edit=True, session=session), "📅 Randevu Al")

        self.stats_label = QLabel()
        self.stats_label.setObjectName("statsBar")
        self.stats_btn = QPushButton("Istatistik Yenile")
        self.stats_btn.setObjectName("btnGhost")
        self.stats_btn.clicked.connect(self.refresh_stats)
        self.btn_exit = QPushButton("Cikis")
        self.btn_exit.setObjectName("btnSecondary")
        self.btn_exit.clicked.connect(self._on_exit)
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        stats_row.addWidget(self.stats_label, 1)
        stats_row.addWidget(self.stats_btn)
        stats_row.addWidget(self.btn_exit)

        wrap = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        layout.addWidget(header)
        layout.addLayout(stats_row)
        layout.addWidget(tabs, 1)
        wrap.setLayout(layout)
        self.setCentralWidget(wrap)
        self.refresh_stats()

    def refresh_stats(self) -> None:
        con = db.connect()
        try:
            doktor_sayisi = int(con.execute("SELECT COUNT(*) AS c FROM doctors;").fetchone()["c"])
            hasta_sayisi = int(con.execute("SELECT COUNT(*) AS c FROM patients;").fetchone()["c"])
            bugun = date.today().isoformat()
            bugun_randevu = int(
                con.execute("SELECT COUNT(*) AS c FROM appointments WHERE appt_date=?;", (bugun,)).fetchone()["c"]
            )
        finally:
            con.close()
        self.stats_label.setText(
            f"🩺 Doktor: {doktor_sayisi}   ·   👤 Hasta: {hasta_sayisi}   ·   📆 Bugun: {bugun_randevu} randevu"
        )

    def _on_exit(self) -> None:
        if not _confirm(self, "Onay", "Oturum kapatilsin mi?"):
            return
        try:
            self._on_logout()
        finally:
            self.close()


def run() -> None:
    db.init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Online Doktor Randevu")
    base = QFont("Segoe UI", 11)
    app.setFont(base)
    app.setStyleSheet(APP_STYLESHEET)

    w: Optional[MainWindow] = None

    def do_logout() -> None:
        nonlocal w
        if w is not None:
            w.hide()

        dlg = LoginDialog()
        if dlg.exec_() != QDialog.Accepted or not dlg.session:
            QApplication.quit()
            return

        w = MainWindow(dlg.session, on_logout=do_logout)
        w.show()

    do_logout()
    app.exec_()

