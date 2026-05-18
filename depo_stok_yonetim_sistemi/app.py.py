from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QColor, QFont, QRegExpValidator
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
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
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import db



def _soft_shadow(widget: QWidget, blur: int = 30, dy: int = 10, alpha: int = 70) -> None:
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, dy)
    eff.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(eff)


def _polish_table(table: QTableWidget) -> None:
    table.setFrameShape(QFrame.NoFrame)
    if table.selectionBehavior() != QTableWidget.SelectRows:
        table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setWordWrap(False)
    table.setShowGrid(False)
    table.verticalHeader().setVisible(False)


def _msg_err(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.critical(parent, title, text)


def _msg_ok(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.information(parent, title, text)


def _confirm(parent: QWidget, title: str, text: str) -> bool:
    return QMessageBox.question(parent, title, text) == QMessageBox.Yes


APP_STYLESHEET = """
* {
  font-family: "Segoe UI", "Segoe UI Emoji", "Segoe UI Symbol";
  font-size: 12px;
}

QToolTip {
  background: #1e293b;
  color: #fef3c7;
  border: 1px solid rgba(251, 191, 36, 0.45);
  border-radius: 8px;
  padding: 8px 11px;
}

QMessageBox {
  background: #0f172a;
}
QMessageBox QLabel {
  color: #e2e8f0;
  min-width: 280px;
}

QMainWindow {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 #0a0f1a, stop:0.45 #111827, stop:0.75 #1e1b4b, stop:1 #0f172a);
}

QDialog {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 #0f172a, stop:0.55 #1e1b4b, stop:1 #172554);
}

QWidget#appHeader {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 rgba(245, 158, 11, 0.35), stop:0.5 rgba(99, 102, 241, 0.38), stop:1 rgba(30, 27, 75, 0.85));
  border: 1px solid rgba(251, 191, 36, 0.4);
  border-radius: 16px;
  min-height: 58px;
}

QLabel#appHeaderTitle {
  color: #fefce8;
  font-size: 19px;
  font-weight: 800;
  letter-spacing: 0.35px;
}

QLabel#appHeaderSub {
  color: rgba(254, 243, 199, 0.88);
  font-size: 12px;
}

QLabel#rolePill {
  background: rgba(15, 23, 42, 0.55);
  color: #fde68a;
  border: 1px solid rgba(251, 191, 36, 0.55);
  border-radius: 999px;
  padding: 5px 16px;
  font-weight: 800;
  font-size: 11px;
  letter-spacing: 0.08em;
}

QWidget#loginHero {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 rgba(251, 191, 36, 0.22), stop:1 rgba(99, 102, 241, 0.28));
  border: 1px solid rgba(251, 191, 36, 0.4);
  border-radius: 18px;
}

QGroupBox#loginCard {
  background: rgba(15, 23, 42, 0.88);
  border: 1px solid rgba(129, 140, 248, 0.35);
  border-radius: 18px;
  margin-top: 8px;
  padding: 18px 18px 14px 18px;
  color: #e2e8f0;
}
QGroupBox#loginCard::title {
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 0 10px;
  color: #fde68a;
  font-weight: 800;
}

QLabel#statsBar {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 rgba(30, 27, 75, 0.9), stop:1 rgba(15, 23, 42, 0.85));
  border: 1px solid rgba(251, 191, 36, 0.38);
  border-radius: 14px;
  padding: 11px 16px;
  color: #fef3c7;
  font-weight: 700;
}

QWidget { color: #e5e7eb; }
QLabel { color: #e5e7eb; }

QGroupBox {
  background: rgba(15, 23, 42, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  margin-top: 14px;
  padding: 16px 16px 12px 16px;
  color: #e5e7eb;
}
QGroupBox::title {
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 0 10px;
  color: #fde68a;
  font-weight: 800;
}

QTabWidget#mainTabs::pane {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(17, 24, 39, 0.78);
  border-radius: 16px;
  padding: 10px;
  top: -1px;
}

QTabBar#mainTabBar::tab {
  background: rgba(255, 255, 255, 0.06);
  color: #cbd5e1;
  padding: 12px 20px;
  margin-right: 5px;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  min-height: 22px;
}
QTabBar#mainTabBar::tab:selected {
  background: rgba(251, 191, 36, 0.2);
  color: #fffbeb;
  font-weight: 800;
  border: 1px solid rgba(251, 191, 36, 0.4);
  border-bottom: 0;
}
QTabBar#mainTabBar::tab:hover:!selected {
  background: rgba(99, 102, 241, 0.22);
  color: #e5e7eb;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit, QDateEdit {
  background: rgba(15, 23, 42, 0.72);
  color: #f1f5f9;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 10px 13px;
  min-height: 22px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus, QDateEdit:focus {
  border: 2px solid rgba(251, 191, 36, 0.75);
}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QTextEdit:hover, QDateEdit:hover {
  border: 1px solid rgba(129, 140, 248, 0.45);
}
QLineEdit::placeholder { color: rgba(226, 232, 240, 0.42); }
QComboBox::drop-down { border: 0; width: 26px; }

QComboBox QAbstractItemView {
  background: #1e293b;
  color: #f1f5f9;
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 10px;
  padding: 4px;
  outline: 0;
  selection-background-color: rgba(251, 191, 36, 0.28);
  selection-color: #0f172a;
}

QPushButton#btnPrimary {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #f59e0b, stop:1 #6366f1);
  color: #0f172a;
  border: 0;
  border-radius: 12px;
  padding: 11px 18px;
  font-weight: 800;
}
QPushButton#btnPrimary:hover {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #d97706, stop:1 #4f46e5);
  color: #fffbeb;
}
QPushButton#btnPrimary:pressed {
  background: #b45309;
  color: #ffffff;
}

QPushButton#btnSecondary {
  background: transparent;
  color: #fde68a;
  border: 2px solid rgba(251, 191, 36, 0.65);
  border-radius: 12px;
  padding: 10px 16px;
  font-weight: 800;
}
QPushButton#btnSecondary:hover {
  background: rgba(251, 191, 36, 0.14);
}

QPushButton#btnGhost {
  background: rgba(99, 102, 241, 0.2);
  color: #e0e7ff;
  border: 1px solid rgba(129, 140, 248, 0.5);
  border-radius: 12px;
  padding: 10px 16px;
  font-weight: 700;
}
QPushButton#btnGhost:hover {
  background: rgba(99, 102, 241, 0.32);
}

QPushButton {
  background: #6366f1;
  color: white;
  border: 0;
  border-radius: 12px;
  padding: 10px 15px;
  font-weight: 700;
}
QPushButton:hover { background: #4f46e5; }
QPushButton:pressed { background: #4338ca; }
QPushButton:disabled { background: rgba(148, 163, 184, 0.22); color: rgba(255, 255, 255, 0.45); }

QTableWidget {
  background: rgba(11, 18, 32, 0.9);
  color: #e5e7eb;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  gridline-color: transparent;
  selection-background-color: rgba(251, 191, 36, 0.32);
  selection-color: #0f172a;
  alternate-background-color: rgba(255, 255, 255, 0.03);
}
QTableView::item {
  padding: 8px 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
QTableView::item:hover {
  background: rgba(99, 102, 241, 0.15);
}
QTableView::item:selected {
  background: rgba(251, 191, 36, 0.32);
  color: #0f172a;
}
QHeaderView::section {
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 rgba(251, 191, 36, 0.2), stop:1 rgba(99, 102, 241, 0.12));
  color: #fef3c7;
  padding: 10px;
  border: 0;
  border-bottom: 2px solid rgba(251, 191, 36, 0.45);
  font-weight: 800;
}

QAbstractScrollArea { background: rgba(11, 18, 32, 0.9); border-radius: 16px; }
QTableCornerButton::section { background: rgba(255, 255, 255, 0.06); border: 0; }

QScrollBar:vertical {
  background: rgba(15, 23, 42, 0.6);
  width: 11px;
  margin: 2px;
  border-radius: 6px;
}
QScrollBar::handle:vertical {
  background: rgba(251, 191, 36, 0.45);
  min-height: 36px;
  border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
  background: rgba(251, 191, 36, 0.65);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; width: 0px; }

QScrollBar:horizontal {
  background: rgba(15, 23, 42, 0.6);
  height: 11px;
  margin: 2px;
  border-radius: 6px;
}
QScrollBar::handle:horizontal {
  background: rgba(251, 191, 36, 0.45);
  min-width: 36px;
  border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
  background: rgba(251, 191, 36, 0.65);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; height: 0px; }
"""


class LoginDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Depo Stok Yonetimi - Giris")
        self.session: Optional[db.UserSession] = None

        self.username = QLineEdit()
        self.username.setPlaceholderText("Kullanici adiniz")
        self.username.setToolTip("Sistemde kayitli kullanici adiniz")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Sifreniz")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setToolTip("Hesap sifreniz")

        btn_login = QPushButton("Giris Yap")
        btn_login.setObjectName("btnPrimary")
        btn_login.clicked.connect(self._on_login)
        btn_register = QPushButton("Kayit Ol")
        btn_register.setObjectName("btnSecondary")
        btn_register.clicked.connect(self._on_register)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        btns.addWidget(btn_login, 1)
        btns.addWidget(btn_register)

        hero_emoji = QLabel("📦\n🏭")
        hero_emoji.setAlignment(Qt.AlignCenter)
        hero_emoji.setStyleSheet(
            "font-size: 42px; line-height: 1.05; background: transparent; color: #fbbf24; padding: 8px;"
        )
        hero_title = QLabel("Depo & Stok Yonetimi")
        hero_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc; letter-spacing: 0.3px;")
        hero_sub = QLabel(
            "Giris / cikis hareketleri, dusuk stok uyarlari ve raporlar\n tek panelde. Personel hesabi icin Kayit Ol."
        )
        hero_sub.setWordWrap(True)
        hero_sub.setStyleSheet("color: rgba(226,232,240,0.78); font-size: 12px;")

        left_panel = QWidget()
        left_panel.setObjectName("loginHero")
        left = QVBoxLayout(left_panel)
        left.setContentsMargins(18, 18, 18, 18)
        left.addWidget(hero_emoji)
        left.addWidget(hero_title)
        left.addWidget(hero_sub)
        left.addStretch(1)
        badge = QLabel("⚡ Hizli operasyon modu")
        badge.setStyleSheet(
            "color: #0f172a; background: rgba(251,191,36,0.95); "
            "border-radius: 10px; padding: 8px 12px; font-weight: 700; font-size: 11px;"
        )
        left.addWidget(badge)

        card = QGroupBox("Giris")
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
        root.setSpacing(18)

        wrap = QWidget()
        wrap.setLayout(root)
        outer = QVBoxLayout()
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(wrap)
        self.setLayout(outer)
        self.resize(720, 340)
        _soft_shadow(left_panel, blur=34, dy=10, alpha=85)
        _soft_shadow(card, blur=38, dy=12, alpha=95)
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
        self.setWindowTitle("Yeni personel kaydi")
        self.created_username: Optional[str] = None

        head = QLabel("👷  Yeni personel kaydi")
        head.setStyleSheet("font-size: 17px; font-weight: 800; color: #fef3c7; padding-bottom: 6px;")

        self.full_name = QLineEdit()
        self.full_name.setMaxLength(60)
        self.full_name.setValidator(
            QRegExpValidator(QRegExp(r"[A-Za-zÇĞİÖŞÜçğıöşü .'-]{0,60}"), self)
        )
        self.phone = QLineEdit()
        self.phone.setMaxLength(11)
        self.phone.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))
        self.phone.setToolTip("Opsiyonel: 05 ile baslayan 11 hane")

        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        btn = QPushButton("Kaydi Tamamla")
        btn.setObjectName("btnPrimary")
        btn.clicked.connect(self._submit)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("📝 Ad Soyad:", self.full_name)
        form.addRow("📱 Telefon:", self.phone)
        form.addRow("👤 Kullanici adi:", self.username)
        form.addRow("🔒 Sifre:", self.password)
        form.addRow(btn)

        outer = QVBoxLayout()
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(10)
        outer.addWidget(head)
        outer.addLayout(form)
        self.setLayout(outer)
        self.resize(440, 360)
        app = QApplication.instance()
        if app is not None:
            self.setWindowIcon(app.windowIcon())

    def _submit(self) -> None:
        full_name = self.full_name.text().strip()
        phone = self.phone.text().strip()
        username = self.username.text().strip()
        password = self.password.text().strip()
        if not full_name:
            _msg_err(self, "Hata", "Ad Soyad zorunlu.")
            return
        if any(ch.isdigit() for ch in full_name):
            _msg_err(self, "Hata", "Ad Soyad alaninda sayi olamaz.")
            return
        if phone and (len(phone) != 11 or not phone.isdigit() or not phone.startswith("05")):
            _msg_err(self, "Hata", "Telefon 11 haneli olmali ve 05 ile baslamali. Orn: 05XXXXXXXXX")
            return
        if len(username) < 3 or len(password) < 3:
            _msg_err(self, "Hata", "Kullanici adi ve sifre en az 3 karakter olmali.")
            return
        try:
            db.create_user(username, password, "personel", full_name=full_name, phone=phone)
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        self.created_username = username
        self.accept()


@dataclass
class SupplierRow:
    id: int
    name: str
    phone: str
    email: str


@dataclass
class ProductRow:
    id: int
    sku: str
    name: str
    category: str
    unit: str
    price: float
    stock: int
    min_stock: int
    supplier_name: str


class SuppliersTab(QWidget):
    def __init__(self, can_edit: bool) -> None:
        super().__init__()
        self.can_edit = can_edit

        self.search = QLineEdit()
        self.search.setPlaceholderText("Ara (tedarikci adi)...")
        self.search.textChanged.connect(self.refresh)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Ad", "Telefon", "E-posta"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        _polish_table(self.table)
        self.table.itemSelectionChanged.connect(self._fill_from_selected)

        self.name = QLineEdit()
        self.phone = QLineEdit()
        self.phone.setValidator(QRegExpValidator(QRegExp(r"[0-9+() -]*"), self))
        self.email = QLineEdit()

        box = QGroupBox("🚚 Tedarikci")
        form = QFormLayout()
        form.addRow("Ad:", self.name)
        form.addRow("Telefon:", self.phone)
        form.addRow("E-posta:", self.email)
        box.setLayout(form)

        self.btn_add = QPushButton("Ekle")
        self.btn_update = QPushButton("Guncelle")
        self.btn_delete = QPushButton("Sil")
        self.btn_add.clicked.connect(self.add_supplier)
        self.btn_update.clicked.connect(self.update_supplier)
        self.btn_delete.clicked.connect(self.delete_supplier)

        btns = QHBoxLayout()
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_update)
        btns.addWidget(self.btn_delete)
        btns.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(self.search)
        layout.addWidget(self.table, 1)
        layout.addWidget(box)
        layout.addLayout(btns)
        self.setLayout(layout)

        if not self.can_edit:
            for w in (self.name, self.phone, self.email, self.btn_add, self.btn_update, self.btn_delete):
                w.setEnabled(False)

        self.refresh()

    def refresh(self) -> None:
        q = (self.search.text() or "").strip().lower()
        rows = db.list_suppliers()
        data: list[SupplierRow] = []
        for r in rows:
            s = SupplierRow(int(r["id"]), r["name"], r["phone"], r["email"])
            if q and q not in s.name.lower():
                continue
            data.append(s)
        self.table.setRowCount(len(data))
        for i, s in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(str(s.id)))
            self.table.setItem(i, 1, QTableWidgetItem(s.name))
            self.table.setItem(i, 2, QTableWidgetItem(s.phone))
            self.table.setItem(i, 3, QTableWidgetItem(s.email))
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
        row = self.table.currentRow()
        if row < 0:
            return
        self.name.setText(self.table.item(row, 1).text())
        self.phone.setText(self.table.item(row, 2).text())
        self.email.setText(self.table.item(row, 3).text())

    def add_supplier(self) -> None:
        name = self.name.text().strip()
        if not name:
            _msg_err(self, "Hata", "Ad zorunlu.")
            return
        try:
            db.create_supplier(name, self.phone.text(), self.email.text())
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        self.refresh()
        _msg_ok(self, "Basarili", "Tedarikci eklendi.")

    def update_supplier(self) -> None:
        sid = self._selected_id()
        if sid is None:
            _msg_err(self, "Hata", "Guncellenecek kaydi secin.")
            return
        name = self.name.text().strip()
        if not name:
            _msg_err(self, "Hata", "Ad zorunlu.")
            return
        try:
            db.update_supplier(sid, name, self.phone.text(), self.email.text())
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        self.refresh()
        _msg_ok(self, "Basarili", "Tedarikci guncellendi.")

    def delete_supplier(self) -> None:
        sid = self._selected_id()
        if sid is None:
            _msg_err(self, "Hata", "Silinecek kaydi secin.")
            return
        if not _confirm(self, "Onay", "Tedarikci silinsin mi?"):
            return
        try:
            db.delete_supplier(sid)
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        self.refresh()
        _msg_ok(self, "Basarili", "Tedarikci silindi.")


class ProductsTab(QWidget):
    def __init__(self, can_edit: bool) -> None:
        super().__init__()
        self.can_edit = can_edit

        self.search = QLineEdit()
        self.search.setPlaceholderText("Ara (SKU / ad / kategori / tedarikci)...")
        self.search.textChanged.connect(self.refresh)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "SKU", "Ad", "Kategori", "Birim", "Fiyat", "Stok", "Min", "Tedarikci"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        _polish_table(self.table)
        self.table.itemSelectionChanged.connect(self._fill_from_selected)

        self.sku = QLineEdit()
        self.name = QLineEdit()
        self.category = QLineEdit()
        self.unit = QLineEdit()
        self.unit.setText("adet")
        self.price = QLineEdit()
        self.price.setValidator(QRegExpValidator(QRegExp(r"[0-9.]{0,20}"), self))
        self.stock = QSpinBox()
        self.stock.setRange(0, 1_000_000)
        self.min_stock = QSpinBox()
        self.min_stock.setRange(0, 1_000_000)
        self.supplier = QComboBox()
        self._reload_suppliers()

        box = QGroupBox("📦 Urun")
        form = QGridLayout()
        form.addWidget(QLabel("SKU:"), 0, 0)
        form.addWidget(self.sku, 0, 1)
        form.addWidget(QLabel("Ad:"), 1, 0)
        form.addWidget(self.name, 1, 1)
        form.addWidget(QLabel("Kategori:"), 2, 0)
        form.addWidget(self.category, 2, 1)
        form.addWidget(QLabel("Birim:"), 3, 0)
        form.addWidget(self.unit, 3, 1)
        form.addWidget(QLabel("Fiyat:"), 4, 0)
        form.addWidget(self.price, 4, 1)
        form.addWidget(QLabel("Stok:"), 5, 0)
        form.addWidget(self.stock, 5, 1)
        form.addWidget(QLabel("Min stok:"), 6, 0)
        form.addWidget(self.min_stock, 6, 1)
        form.addWidget(QLabel("Tedarikci:"), 7, 0)
        form.addWidget(self.supplier, 7, 1)
        box.setLayout(form)

        self.btn_add = QPushButton("Ekle")
        self.btn_update = QPushButton("Guncelle")
        self.btn_delete = QPushButton("Sil")
        self.btn_reload = QPushButton("Tedarikci Listesini Yenile")
        self.btn_reload.clicked.connect(self._reload_suppliers)
        self.btn_add.clicked.connect(self.add_product)
        self.btn_update.clicked.connect(self.update_product)
        self.btn_delete.clicked.connect(self.delete_product)

        btns = QHBoxLayout()
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_update)
        btns.addWidget(self.btn_delete)
        btns.addWidget(self.btn_reload)
        btns.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(self.search)
        layout.addWidget(self.table, 1)
        layout.addWidget(box)
        layout.addLayout(btns)
        self.setLayout(layout)

        if not self.can_edit:
            for w in (
                self.sku,
                self.name,
                self.category,
                self.unit,
                self.price,
                self.stock,
                self.min_stock,
                self.supplier,
                self.btn_add,
                self.btn_update,
                self.btn_delete,
            ):
                w.setEnabled(False)

        self.refresh()

    def _reload_suppliers(self) -> None:
        self.supplier.clear()
        self.supplier.addItem("-", None)
        for s in db.list_suppliers():
            self.supplier.addItem(s["name"], int(s["id"]))

    def refresh(self) -> None:
        rows = db.list_products(search=self.search.text())
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(r["sku"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["name"]))
            self.table.setItem(i, 3, QTableWidgetItem(r["category"] or ""))
            self.table.setItem(i, 4, QTableWidgetItem(r["unit"] or ""))
            self.table.setItem(i, 5, QTableWidgetItem(f"{float(r['price']):.2f}"))
            self.table.setItem(i, 6, QTableWidgetItem(str(int(r["stock"]))))
            self.table.setItem(i, 7, QTableWidgetItem(str(int(r["min_stock"]))))
            self.table.setItem(i, 8, QTableWidgetItem(r["supplier_name"] or "-"))
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
        row = self.table.currentRow()
        if row < 0:
            return
        self.sku.setText(self.table.item(row, 1).text())
        self.name.setText(self.table.item(row, 2).text())
        self.category.setText(self.table.item(row, 3).text())
        self.unit.setText(self.table.item(row, 4).text())
        self.price.setText(self.table.item(row, 5).text())
        self.stock.setValue(int(self.table.item(row, 6).text() or "0"))
        self.min_stock.setValue(int(self.table.item(row, 7).text() or "0"))

        supplier_name = self.table.item(row, 8).text()
        idx = self.supplier.findText(supplier_name)
        if idx >= 0:
            self.supplier.setCurrentIndex(idx)
        else:
            self.supplier.setCurrentIndex(0)

    def _read_price(self) -> float:
        t = (self.price.text() or "").strip()
        if not t:
            return 0.0
        return float(t)

    def add_product(self) -> None:
        sku = self.sku.text().strip()
        name = self.name.text().strip()
        if not sku or not name:
            _msg_err(self, "Hata", "SKU ve Ad zorunlu.")
            return
        try:
            db.create_product(
                sku=sku,
                name=name,
                category=self.category.text(),
                unit=self.unit.text(),
                price=self._read_price(),
                stock=int(self.stock.value()),
                min_stock=int(self.min_stock.value()),
                supplier_id=self.supplier.currentData(),
            )
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        self.refresh()
        _msg_ok(self, "Basarili", "Urun eklendi.")

    def update_product(self) -> None:
        pid = self._selected_id()
        if pid is None:
            _msg_err(self, "Hata", "Guncellenecek urunu secin.")
            return
        sku = self.sku.text().strip()
        name = self.name.text().strip()
        if not sku or not name:
            _msg_err(self, "Hata", "SKU ve Ad zorunlu.")
            return
        try:
            db.update_product(
                product_id=pid,
                sku=sku,
                name=name,
                category=self.category.text(),
                unit=self.unit.text(),
                price=self._read_price(),
                stock=int(self.stock.value()),
                min_stock=int(self.min_stock.value()),
                supplier_id=self.supplier.currentData(),
            )
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        self.refresh()
        _msg_ok(self, "Basarili", "Urun guncellendi.")

    def delete_product(self) -> None:
        pid = self._selected_id()
        if pid is None:
            _msg_err(self, "Hata", "Silinecek urunu secin.")
            return
        if not _confirm(self, "Onay", "Urun silinsin mi? (Hareketler de silinir)"):
            return
        try:
            db.delete_product(pid)
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        self.refresh()
        _msg_ok(self, "Basarili", "Urun silindi.")


class StockTab(QWidget):
    def __init__(self, session: db.UserSession) -> None:
        super().__init__()
        self.session = session

        self.products = QComboBox()
        self._reload_products()

        self.move_type = QComboBox()
        self.move_type.addItems(["IN (Giris)", "OUT (Cikis)", "ADJUST (Sayim)"])

        self.qty = QSpinBox()
        self.qty.setRange(1, 1_000_000)

        self.unit_price = QLineEdit()
        self.unit_price.setValidator(QRegExpValidator(QRegExp(r"[0-9.]{0,20}"), self))

        self.note = QLineEdit()

        self.btn_apply = QPushButton("Uygula")
        self.btn_apply.clicked.connect(self.apply_move)
        self.btn_reload = QPushButton("Urun Listesini Yenile")
        self.btn_reload.clicked.connect(self._reload_products)

        box = QGroupBox("↔️ Stok hareketi")
        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("📦 Urun:", self.products)
        form.addRow("📤 Tip:", self.move_type)
        form.addRow("🔢 Miktar:", self.qty)
        form.addRow("💰 Birim fiyat (opsiyonel):", self.unit_price)
        form.addRow("📝 Not:", self.note)
        form.addRow(self.btn_apply)
        form.addRow(self.btn_reload)
        box.setLayout(form)

        self.low = QTableWidget(0, 6)
        self.low.setHorizontalHeaderLabels(["SKU", "Ad", "Stok", "Min", "Kategori", "Tedarikci"])
        self.low.setEditTriggers(QTableWidget.NoEditTriggers)
        self.low.setAlternatingRowColors(True)
        _polish_table(self.low)

        self.btn_refresh_low = QPushButton("Dusuk Stoklari Yenile")
        self.btn_refresh_low.clicked.connect(self.refresh_low_stock)

        layout = QVBoxLayout()
        layout.addWidget(box)
        layout.addWidget(QLabel("⚠️ Dusuk stok (stok <= min):"))
        layout.addWidget(self.low, 1)
        layout.addWidget(self.btn_refresh_low)
        self.setLayout(layout)

        self.refresh_low_stock()

    def _reload_products(self) -> None:
        self.products.clear()
        for p in db.list_products():
            self.products.addItem(f"{p['sku']} - {p['name']} (stok:{p['stock']})", int(p["id"]))

    def _read_price(self) -> float:
        t = (self.unit_price.text() or "").strip()
        return float(t) if t else 0.0

    def apply_move(self) -> None:
        pid = self.products.currentData()
        if pid is None:
            _msg_err(self, "Hata", "Urun secin.")
            return

        mt = self.move_type.currentText()
        move_type = "IN" if mt.startswith("IN") else ("OUT" if mt.startswith("OUT") else "ADJUST")

        try:
            db.add_stock_move(
                product_id=int(pid),
                move_type=move_type,
                qty=int(self.qty.value()),
                unit_price=self._read_price(),
                note=self.note.text(),
                username=self.session.username,
            )
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return

        self.note.clear()
        self.unit_price.clear()
        self._reload_products()
        self.refresh_low_stock()
        _msg_ok(self, "Basarili", "Stok hareketi eklendi.")

    def refresh_low_stock(self) -> None:
        rows = db.low_stock_products()
        self.low.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.low.setItem(i, 0, QTableWidgetItem(r["sku"]))
            self.low.setItem(i, 1, QTableWidgetItem(r["name"]))
            self.low.setItem(i, 2, QTableWidgetItem(str(int(r["stock"]))))
            self.low.setItem(i, 3, QTableWidgetItem(str(int(r["min_stock"]))))
            self.low.setItem(i, 4, QTableWidgetItem(r["category"] or ""))
            self.low.setItem(i, 5, QTableWidgetItem(r["supplier_name"] or "-"))
        self.low.resizeColumnsToContents()


class MovesTab(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Ara (urun/sku/not/kullanici)...")
        self.search.textChanged.connect(self.refresh)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(["ID", "Tarih", "Tip", "Miktar", "Birim fiyat", "SKU", "Urun", "Not", "Kullanici"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        _polish_table(self.table)

        self.btn_refresh = QPushButton("Yenile")
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_export = QPushButton("CSV Disari Aktar (gorunen)")
        self.btn_export.clicked.connect(self.export_visible)

        btns = QHBoxLayout()
        btns.addWidget(self.btn_refresh)
        btns.addWidget(self.btn_export)
        btns.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(self.search)
        layout.addWidget(self.table, 1)
        layout.addLayout(btns)
        self.setLayout(layout)

        self._rows = []
        self.refresh()

    def refresh(self) -> None:
        self._rows = db.list_stock_moves(limit=500, search=self.search.text())
        self.table.setRowCount(len(self._rows))
        for i, r in enumerate(self._rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(r["ts"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["move_type"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(int(r["qty"]))))
            self.table.setItem(i, 4, QTableWidgetItem(f"{float(r['unit_price']):.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(r["sku"]))
            self.table.setItem(i, 6, QTableWidgetItem(r["product_name"]))
            self.table.setItem(i, 7, QTableWidgetItem(r["note"] or ""))
            self.table.setItem(i, 8, QTableWidgetItem(r["username"]))
        self.table.resizeColumnsToContents()

    def export_visible(self) -> None:
        if not self._rows:
            _msg_err(self, "Hata", "Disari aktarilacak veri yok.")
            return
        suggested = f"stok_hareketleri_{Path(db.db_path()).stem}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "CSV Kaydet", suggested, "CSV Files (*.csv)")
        if not path:
            return
        try:
            db.export_moves_to_csv(path, self._rows)
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        _msg_ok(self, "Basarili", f"CSV kaydedildi: {Path(path).name}")


class UsersTab(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Kullanici", "Rol", "Ad Soyad", "Telefon"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        _polish_table(self.table)

        self.full_name = QLineEdit()
        self.full_name.setMaxLength(60)
        self.full_name.setValidator(
            QRegExpValidator(QRegExp(r"[A-Za-zÇĞİÖŞÜçğıöşü .'-]{0,60}"), self)
        )
        self.phone = QLineEdit()
        self.phone.setMaxLength(11)
        self.phone.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.role = QComboBox()
        self.role.addItems(["personel", "admin"])

        self.btn_add = QPushButton("Kullanici Ekle")
        self.btn_add.clicked.connect(self.add_user)
        self.btn_reload = QPushButton("Listeyi Yenile")
        self.btn_reload.clicked.connect(self.refresh)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("📝 Ad Soyad:", self.full_name)
        form.addRow("📱 Telefon:", self.phone)
        form.addRow("👤 Kullanici adi:", self.username)
        form.addRow("🔒 Sifre:", self.password)
        form.addRow("🏷️ Rol:", self.role)
        form.addRow(self.btn_add)

        box = QGroupBox("🔐 Admin - kullanici yonetimi")
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

    def refresh(self) -> None:
        rows = db.list_users()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["username"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["role"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["full_name"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(r["phone"] or ""))
        self.table.resizeColumnsToContents()

    def add_user(self) -> None:
        full_name = self.full_name.text().strip()
        phone = self.phone.text().strip()
        username = self.username.text().strip()
        password = self.password.text().strip()
        role = self.role.currentText()
        if not full_name:
            _msg_err(self, "Hata", "Ad Soyad zorunlu.")
            return
        if any(ch.isdigit() for ch in full_name):
            _msg_err(self, "Hata", "Ad Soyad alaninda sayi olamaz.")
            return
        if phone and (len(phone) != 11 or not phone.isdigit() or not phone.startswith("05")):
            _msg_err(self, "Hata", "Telefon 11 haneli olmali ve 05 ile baslamali. Orn: 05XXXXXXXXX")
            return
        if len(username) < 3 or len(password) < 3:
            _msg_err(self, "Hata", "Kullanici adi ve sifre en az 3 karakter olmali.")
            return
        try:
            db.create_user(username, password, role, full_name=full_name, phone=phone)
        except Exception as e:
            _msg_err(self, "Hata", str(e))
            return
        self.full_name.clear()
        self.phone.clear()
        self.username.clear()
        self.password.clear()
        self.refresh()
        _msg_ok(self, "Basarili", "Kullanici eklendi.")


class MainWindow(QMainWindow):
    def __init__(self, session: db.UserSession, on_logout) -> None:
        super().__init__()
        self.session = session
        self._on_logout = on_logout
        self.setWindowTitle(f"Depo/Stok Yonetimi - {session.username} ({session.role})")
        self.resize(1180, 780)
        app_inst = QApplication.instance()
        if app_inst is not None:
            self.setWindowIcon(app_inst.windowIcon())

        header = QWidget()
        header.setObjectName("appHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 14, 20, 14)
        left_col = QVBoxLayout()
        left_col.setSpacing(4)
        ht = QLabel("Depo & Stok Yonetimi")
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
        tabs.addTab(ProductsTab(can_edit=can_edit), "📦 Urunler")
        tabs.addTab(SuppliersTab(can_edit=can_edit), "🚚 Tedarikciler")
        tabs.addTab(StockTab(session=session), "↔️ Stok giris/cikis")
        tabs.addTab(MovesTab(), "📋 Hareketler")
        if session.role == "admin":
            tabs.addTab(UsersTab(), "🔐 Kullanicilar")

        self.info = QLabel()
        self.info.setObjectName("statsBar")
        self.btn_refresh = QPushButton("Yenile")
        self.btn_refresh.setObjectName("btnGhost")
        self.btn_refresh.clicked.connect(self._refresh_info)
        self.btn_logout = QPushButton("Cikis")
        self.btn_logout.setObjectName("btnSecondary")
        self.btn_logout.clicked.connect(self._logout)

        top = QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(self.info, 1)
        top.addWidget(self.btn_refresh)
        top.addWidget(self.btn_logout)

        wrap = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        layout.addWidget(header)
        layout.addLayout(top)
        layout.addWidget(tabs, 1)
        wrap.setLayout(layout)
        self.setCentralWidget(wrap)

        self._refresh_info()

    def _refresh_info(self) -> None:
        low = db.low_stock_products()
        self.info.setText(f"⚠️ Dusuk stok: {len(low)} kalem")

    def _logout(self) -> None:
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
    app.setApplicationName("Depo Stok Yonetimi")
    app.setFont(QFont("Segoe UI", 11))
    app.setStyleSheet(APP_STYLESHEET)

    w: Optional[MainWindow] = None

    def do_login() -> None:
        nonlocal w
        if w is not None:
            w.hide()

        dlg = LoginDialog()
        if dlg.exec_() != QDialog.Accepted or not dlg.session:
            QApplication.quit()
            return

        w = MainWindow(dlg.session, on_logout=do_login)
        w.show()

    do_login()
    app.exec_()

