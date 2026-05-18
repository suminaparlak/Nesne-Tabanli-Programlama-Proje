from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
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
        self.password.setEchoMode(QLineEdit.Password)

        btn_login = QPushButton("Giris Yap")
        btn_login.clicked.connect(self._on_login)
        btn_register = QPushButton("Kayit Ol")
        btn_register.clicked.connect(self._on_register)
        btn_register.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        btns = QHBoxLayout()
        btns.addWidget(btn_login)
        btns.addWidget(btn_register)

        hero_title = QLabel("Online Doktor Randevu")
        hero_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a;")
        hero_sub = QLabel("Hizli giris yapin ve randevunuzu yonetin.")
        hero_sub.setStyleSheet("color: rgba(15,23,42,0.75);")

        left = QVBoxLayout()
        left.addWidget(hero_title)
        left.addWidget(hero_sub)
        left.addStretch(1)

        card = QGroupBox("Giris Bilgileri")
        form = QFormLayout()
        form.addRow("Kullanici adi:", self.username)
        form.addRow("Sifre:", self.password)
        form.addRow(btns)
        card.setLayout(form)

        root = QHBoxLayout()
        root.addLayout(left, 1)
        root.addWidget(card, 2)
        root.setSpacing(18)

        wrap = QWidget()
        wrap.setLayout(root)
        layout = QVBoxLayout()
        layout.addWidget(wrap)
        self.setLayout(layout)
        self.resize(520, 220)

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
        self.setWindowTitle("Kayit Ol (Hasta)")
        self.created_username: Optional[str] = None

        self.full_name = QLineEdit()
        self.full_name.setMaxLength(60)
        self.full_name.setValidator(QRegExpValidator(QRegExp(r"[A-Za-zÇĞİÖŞÜçğıöşü .'-]{0,60}"), self))
        self.tc = QLineEdit()
        self.tc.setMaxLength(11)
        self.tc.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))
        self.phone = QLineEdit()
        self.phone.setMaxLength(11)
        self.phone.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))

        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        btn = QPushButton("Kaydi Tamamla")
        btn.clicked.connect(self._submit)

        form = QFormLayout()
        form.addRow("Ad Soyad:", self.full_name)
        form.addRow("TC:", self.tc)
        form.addRow("Telefon:", self.phone)
        form.addRow(QLabel("— Giris Bilgileri —"))
        form.addRow("Kullanici adi:", self.username)
        form.addRow("Sifre:", self.password)
        form.addRow(btn)
        self.setLayout(form)

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

        self.name = QLineEdit()
        self.name.setMaxLength(60)
        self.name.setValidator(QRegExpValidator(QRegExp(r"[A-Za-zÇĞİÖŞÜçğıöşü .'-]{0,60}"), self))
        self.specialty = QLineEdit()
        self.hours = QLineEdit()
        self.hours.setPlaceholderText("Orn: 09:00,10:00,14:00")
        self.hours.setValidator(QRegExpValidator(QRegExp(r"[0-9:, ]*"), self))

        form_box = QGroupBox("Doktor Bilgisi")
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

        self.name = QLineEdit()
        self.name.setMaxLength(60)
        self.name.setValidator(QRegExpValidator(QRegExp(r"[A-Za-zÇĞİÖŞÜçğıöşü .'-]{0,60}"), self))
        self.tc = QLineEdit()
        self.tc.setMaxLength(11)
        self.tc.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))
        self.phone = QLineEdit()
        self.phone.setMaxLength(11)
        self.phone.setValidator(QRegExpValidator(QRegExp(r"\d{0,11}"), self))

        form_box = QGroupBox("Hasta Bilgisi")
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
        top.addWidget(QLabel("Tarih:"))
        top.addWidget(self.date_filter)
        top.addStretch(1)
        top.addWidget(self.search)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Tarih", "Saat", "Doktor", "Hasta", "Not"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

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

        form_box = QGroupBox("Yeni Randevu")
        form = QGridLayout()
        form.addWidget(QLabel("Doktor:"), 0, 0)
        form.addWidget(self.doctor, 0, 1)
        form.addWidget(QLabel("Hasta:"), 1, 0)
        form.addWidget(self.patient, 1, 1)
        form.addWidget(QLabel("Tarih:"), 2, 0)
        form.addWidget(self.appt_date, 2, 1)
        form.addWidget(QLabel("Saat:"), 3, 0)
        form.addWidget(self.appt_time, 3, 1)
        form.addWidget(QLabel("Not:"), 4, 0)
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
        top.addWidget(QLabel("Tarih:"))
        top.addWidget(self.report_date)
        top.addWidget(self.btn_load)
        top.addStretch(1)
        top.addWidget(self.btn_export)

        self.text = QTextEdit()
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
        form.addRow("Kullanici adi:", self.username)
        form.addRow("Sifre:", self.password)
        form.addRow("Rol:", self.role)
        form.addRow("Doktor baglantisi:", self.doctor_combo)
        form.addRow("Hasta baglantisi:", self.patient_combo)
        form.addRow(self.btn_add)

        box = QGroupBox("Admin - Hesap Yonetimi")
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
        self.resize(1100, 700)

        tabs = QTabWidget()
        can_edit = session.role == "admin"
        if session.role == "admin":
            tabs.addTab(DoctorsTab(can_edit=True), "Doktorlar")
            tabs.addTab(PatientsTab(can_edit=True), "Hastalar")
            tabs.addTab(AppointmentsTab(can_edit=True, session=session), "Randevular")
            tabs.addTab(ReportsTab(), "Rapor")
            tabs.addTab(UsersTab(), "Kullanicilar")
        elif session.role == "doktor":
            tabs.addTab(AppointmentsTab(can_edit=False, session=session), "Randevularim")
            tabs.addTab(ReportsTab(), "Rapor")
        else:  # hasta
            tabs.addTab(AppointmentsTab(can_edit=True, session=session), "Randevu Al")

        self.stats_label = QLabel()
        self.stats_btn = QPushButton("Istatistik Yenile")
        self.stats_btn.clicked.connect(self.refresh_stats)
        self.btn_exit = QPushButton("Cikis")
        self.btn_exit.clicked.connect(self._on_exit)
        stats_row = QHBoxLayout()
        stats_row.addWidget(self.stats_label)
        stats_row.addStretch(1)
        stats_row.addWidget(self.stats_btn)
        stats_row.addWidget(self.btn_exit)

        wrap = QWidget()
        layout = QVBoxLayout()
        layout.addLayout(stats_row)
        layout.addWidget(tabs)
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
            f"Toplam Doktor: {doktor_sayisi}  |  Toplam Hasta: {hasta_sayisi}  |  Bugunku Randevu: {bugun_randevu}"
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
    app = QApplication([])
    app.setStyleSheet(
        """
        * { font-family: "Segoe UI"; font-size: 12px; }
        QMainWindow, QDialog { background: #f5f9fb; }

        /* Medical accent palette */
        QWidget { color: #0f172a; }
        QLabel { color: #0f172a; }

        QGroupBox {
          background: #ffffff;
          border: 1px solid rgba(2, 132, 199, 0.18);
          border-radius: 12px;
          margin-top: 10px;
          padding: 10px;
        }
        QGroupBox::title {
          subcontrol-origin: margin;
          subcontrol-position: top left;
          padding: 0 8px;
          color: #0369a1;
          font-weight: 600;
        }

        QTabWidget::pane {
          border: 1px solid rgba(15, 23, 42, 0.12);
          background: #ffffff;
          border-radius: 12px;
          padding: 6px;
        }
        QTabBar::tab {
          background: rgba(2, 132, 199, 0.08);
          color: #075985;
          padding: 10px 16px;
          margin-right: 6px;
          border-top-left-radius: 10px;
          border-top-right-radius: 10px;
        }
        QTabBar::tab:selected {
          background: #ffffff;
          color: #0f172a;
          font-weight: 700;
          border: 1px solid rgba(15, 23, 42, 0.12);
          border-bottom: 0;
        }

        QLineEdit, QComboBox, QDateEdit, QTextEdit {
          background: #ffffff;
          color: #0f172a;
          border: 1px solid rgba(15, 23, 42, 0.18);
          border-radius: 10px;
          padding: 8px 10px;
        }
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
          border: 1px solid rgba(2, 132, 199, 0.85);
        }

        QPushButton {
          background: #0284c7;
          color: #ffffff;
          border: 0;
          border-radius: 10px;
          padding: 8px 14px;
          font-weight: 600;
        }
        QPushButton:hover { background: #0369a1; }
        QPushButton:pressed { background: #075985; }
        QPushButton:disabled { background: rgba(148,163,184,0.55); color: rgba(15,23,42,0.65); }

        QTableWidget {
          background: #ffffff;
          color: #0f172a;
          border: 1px solid rgba(15, 23, 42, 0.12);
          border-radius: 12px;
          gridline-color: rgba(15, 23, 42, 0.08);
          selection-background-color: rgba(2, 132, 199, 0.18);
          selection-color: #0f172a;
          alternate-background-color: rgba(2, 132, 199, 0.05);
        }
        QHeaderView::section {
          background: rgba(2, 132, 199, 0.08);
          color: #0f172a;
          padding: 8px;
          border: 0;
          border-bottom: 1px solid rgba(15, 23, 42, 0.10);
        }
        """
    )

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

