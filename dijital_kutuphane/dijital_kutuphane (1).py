import sys
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QStackedWidget, QFrame, QComboBox, QMessageBox, QHeaderView,
    QScrollArea, QGridLayout, QDialog, QFormLayout, QDateEdit,
    QSplitter, QTextEdit, QSpacerItem, QSizePolicy, QProgressBar,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import (
    Qt, QDate, QPropertyAnimation, QRect, QTimer, QSize, pyqtSignal, QRegExp
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QPainter, QBrush,
    QLinearGradient, QFontDatabase, QRegExpValidator, QIntValidator
)

# ─────────────────────────── VERİTABANI ────────────────────────────

def init_db():
    conn = sqlite3.connect("kutuphane.db")
    c = conn.cursor()
    # Kullanıcı hesapları tablosu
    c.execute("""CREATE TABLE IF NOT EXISTS kullanicilar (
        kullanici_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi TEXT UNIQUE NOT NULL,
        sifre         TEXT NOT NULL,
        rol           TEXT DEFAULT 'kullanici',
        uye_id        INTEGER,
        ad_soyad      TEXT,
        email         TEXT,
        kayit_tarihi  TEXT DEFAULT CURRENT_DATE,
        FOREIGN KEY(uye_id) REFERENCES uyeler(uye_id)
    )""")
    # Varsayılan admin hesabı
    c.execute("SELECT COUNT(*) FROM kullanicilar WHERE kullanici_adi='admin'")
    if c.fetchone()[0] == 0:
        c.execute("""INSERT INTO kullanicilar (kullanici_adi, sifre, rol, ad_soyad, email)
                     VALUES ('admin', 'admin123', 'admin', 'Sistem Yöneticisi', 'admin@kutuphane.com')""")
    c.execute("""CREATE TABLE IF NOT EXISTS kitaplar (
        kitap_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        ad          TEXT NOT NULL,
        yazar       TEXT NOT NULL,
        kategori    TEXT NOT NULL,
        durum       TEXT DEFAULT 'Mevcut',
        isbn        TEXT,
        yayinevi    TEXT,
        yil         INTEGER,
        aciklama    TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS uyeler (
        uye_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        ad          TEXT NOT NULL,
        email       TEXT UNIQUE NOT NULL,
        telefon     TEXT,
        adres       TEXT,
        kayit_tarihi TEXT DEFAULT CURRENT_DATE,
        aktif       INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS oduncler (
        odunc_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        kitap_id    INTEGER,
        uye_id      INTEGER,
        odunc_tarihi TEXT DEFAULT CURRENT_DATE,
        iade_tarihi  TEXT,
        gercek_iade  TEXT,
        durum        TEXT DEFAULT 'Devam Ediyor',
        FOREIGN KEY(kitap_id) REFERENCES kitaplar(kitap_id),
        FOREIGN KEY(uye_id)   REFERENCES uyeler(uye_id)
    )""")
    # Demo verisi (Sadece tablolar boşsa eklenir)
    c.execute("SELECT COUNT(*) FROM kitaplar")
    if c.fetchone()[0] == 0:
        demo_kitaplar = [
            # 30 Mevcut
            ("Suç ve Ceza", "Fyodor Dostoyevski", "Klasik", "Mevcut", "978-1", "İş Bankası", 2020, "Klasik Rus Edebiyatı"),
            ("1984", "George Orwell", "Distopya", "Mevcut", "978-2", "Can", 2019, "Distopik"),
            ("Sapiens", "Yuval Noah Harari", "Tarih", "Mevcut", "978-3", "Kolektif", 2018, "Tarih"),
            ("Şeker Portakalı", "José Mauro de Vasconcelos", "Roman", "Mevcut", "978-4", "Doğan", 2017, "Roman"),
            ("Küçük Prens", "Antoine de Saint-Exupéry", "Masal", "Mevcut", "978-5", "Kırmızı Kedi", 2022, "Masal"),
            ("Atomik Alışkanlıklar", "James Clear", "Kişisel Gelişim", "Mevcut", "978-6", "Olimpos", 2020, "Gelişim"),
            ("Sefiller", "Victor Hugo", "Klasik", "Mevcut", "978-7", "İş Bankası", 2019, "Klasik"),
            ("Dune", "Frank Herbert", "Bilim Kurgu", "Mevcut", "978-8", "İthaki", 2021, "Bilim Kurgu"),
            ("Vakıf", "Isaac Asimov", "Bilim Kurgu", "Mevcut", "978-9", "İthaki", 2020, "Bilim Kurgu"),
            ("Marslı", "Andy Weir", "Bilim Kurgu", "Mevcut", "978-10", "İthaki", 2015, "Bilim Kurgu"),
            ("Cesur Yeni Dünya", "Aldous Huxley", "Distopya", "Mevcut", "978-11", "İthaki", 2018, "Distopya"),
            ("Fahrenheit 451", "Ray Bradbury", "Distopya", "Mevcut", "978-12", "İthaki", 2019, "Distopya"),
            ("Harry Potter", "J.K. Rowling", "Çocuk", "Mevcut", "978-13", "YKY", 2001, "Çocuk"),
            ("Percy Jackson", "Rick Riordan", "Çocuk", "Mevcut", "978-14", "Doğan", 2010, "Çocuk"),
            ("Matilda", "Roald Dahl", "Çocuk", "Mevcut", "978-15", "Can", 2015, "Çocuk"),
            ("Charlie'nin Çikolata Fabrikası", "Roald Dahl", "Çocuk", "Mevcut", "978-16", "Can", 2014, "Çocuk"),
            ("Alice Harikalar Diyarında", "Lewis Carroll", "Çocuk", "Mevcut", "978-17", "İş Bankası", 2018, "Çocuk"),
            ("Tuz Yağ Asit Isı", "Samin Nosrat", "Gastronomi", "Mevcut", "978-18", "Pegasus", 2019, "Gastronomi"),
            ("Mutfak Sırları", "Anthony Bourdain", "Gastronomi", "Mevcut", "978-19", "Oğlak", 2021, "Gastronomi"),
            ("Bir Aşçının İtirafları", "Anthony Bourdain", "Gastronomi", "Mevcut", "978-20", "Oğlak", 2020, "Gastronomi"),
            ("Lezzet Atlası", "Mina Holland", "Gastronomi", "Mevcut", "978-21", "Pegasus", 2018, "Gastronomi"),
            ("Noma", "Rene Redzepi", "Gastronomi", "Mevcut", "978-22", "Phaidon", 2010, "Gastronomi"),
            ("Maus", "Art Spiegelman", "Çizgi Roman", "Mevcut", "978-23", "İletişim", 2015, "Çizgi Roman"),
            ("Watchmen", "Alan Moore", "Çizgi Roman", "Mevcut", "978-24", "İthaki", 2018, "Çizgi Roman"),
            ("Sandman", "Neil Gaiman", "Çizgi Roman", "Mevcut", "978-25", "İthaki", 2020, "Çizgi Roman"),
            ("Batman İlk Yıl", "Frank Miller", "Çizgi Roman", "Mevcut", "978-26", "JBC", 2019, "Çizgi Roman"),
            ("V for Vendetta", "Alan Moore", "Çizgi Roman", "Mevcut", "978-27", "JBC", 2017, "Çizgi Roman"),
            ("Yüzüklerin Efendisi", "J.R.R. Tolkien", "Roman", "Mevcut", "978-28", "Metis", 2020, "Roman"),
            ("Hobbit", "J.R.R. Tolkien", "Roman", "Mevcut", "978-29", "İthaki", 2019, "Roman"),
            ("Simyacı", "Paulo Coelho", "Roman", "Mevcut", "978-30", "Can", 2021, "Roman"),

            # 12 Normal Ödünçte
            ("Otostopçunun Galaksi Rehberi", "Douglas Adams", "Bilim Kurgu", "Ödünçte", "978-31", "Alfa", 2018, "Bilim Kurgu"),
            ("Körlük", "José Saramago", "Roman", "Ödünçte", "978-32", "Kırmızı Kedi", 2019, "Roman"),
            ("Sineklerin Tanrısı", "William Golding", "Roman", "Ödünçte", "978-33", "İş Bankası", 2020, "Roman"),
            ("Bülbülü Öldürmek", "Harper Lee", "Roman", "Ödünçte", "978-34", "Epsilon", 2018, "Roman"),
            ("Gurur ve Önyargı", "Jane Austen", "Klasik", "Ödünçte", "978-35", "İş Bankası", 2020, "Klasik"),
            ("Anna Karenina", "Lev Tolstoy", "Klasik", "Ödünçte", "978-36", "İş Bankası", 2019, "Klasik"),
            ("Suç ve Ceza 2", "Fyodor Dostoyevski", "Klasik", "Ödünçte", "978-37", "İş Bankası", 2021, "Klasik"),
            ("Tüfek, Mikrop ve Çelik", "Jared Diamond", "Tarih", "Ödünçte", "978-38", "Pegasus", 2017, "Tarih"),
            ("Zengin Baba Yoksul Baba", "Robert Kiyosaki", "Kişisel Gelişim", "Ödünçte", "978-39", "Pegasus", 2020, "Kişisel Gelişim"),
            ("Düşün ve Zengin Ol", "Napoleon Hill", "Kişisel Gelişim", "Ödünçte", "978-40", "Pegasus", 2019, "Kişisel Gelişim"),
            ("Zamanın Kısa Tarihi", "Stephen Hawking", "Tarih", "Ödünçte", "978-41", "Alfa", 2018, "Bilim"),
            ("Nutuk", "Mustafa Kemal Atatürk", "Tarih", "Ödünçte", "978-42", "İş Bankası", 2020, "Tarih"),

            # 3 Gecikmeli Ödünçte
            ("İçimizdeki Şeytan", "Sabahattin Ali", "Klasik", "Ödünçte", "978-43", "YKY", 2018, "Klasik"),
            ("Kürk Mantolu Madonna", "Sabahattin Ali", "Klasik", "Ödünçte", "978-44", "YKY", 2019, "Klasik"),
            ("Spider-Man Mavi", "Jeph Loeb", "Çizgi Roman", "Ödünçte", "978-45", "Marmara", 2021, "Çizgi Roman"),
        ]
        c.executemany("INSERT INTO kitaplar (ad,yazar,kategori,durum,isbn,yayinevi,yil,aciklama) VALUES (?,?,?,?,?,?,?,?)", demo_kitaplar)
        
        # Tireler telefonlardan temizlendi (Sadece Sayı Kuralı İçin)
        demo_uyeler = [
            ("Ayşe Yılmaz", "ayse@mail.com", "05321112233", "İstanbul", "2024-01-10"),
            ("Mehmet Kaya", "mehmet@mail.com", "05332223344", "Ankara", "2024-02-15"),
            ("Zeynep Demir", "zeynep@mail.com", "05343334455", "İzmir", "2024-03-20"),
            ("Ali Can", "ali@mail.com", "05354445566", "Bursa", "2024-03-25"),
            ("Fatma Şahin", "fatma@mail.com", "05365556677", "Antalya", "2024-04-01"),
            ("Ahmet Yıldız", "ahmet@mail.com", "05376667788", "Adana", "2024-04-05"),
            ("Elif Çelik", "elif@mail.com", "05387778899", "Konya", "2024-04-10"),
            ("Mustafa Kurt", "mustafa@mail.com", "05398889900", "Gaziantep", "2024-04-15"),
            ("Aykut Yılmaz", "aykut@mail.com", "05409990011", "Mersin", "2024-04-20"),
            ("Merve Özdemir", "merve@mail.com", "05411112233", "Eskişehir", "2024-04-25"),
            ("Burak Aslan", "burak@mail.com", "05422223344", "Samsun", "2024-05-01"),
            ("Ceren Kaplan", "ceren@mail.com", "05433334455", "Trabzon", "2024-05-05"),
            ("Deniz Erdoğan", "deniz@mail.com", "05444445566", "Kayseri", "2024-05-10"),
            ("Emre Polat", "emre@mail.com", "05455556677", "Erzurum", "2024-05-15"),
            ("Gizem Koç", "gizem@mail.com", "05466667788", "Diyarbakır", "2024-05-20"),
            ("Hakan Çetin", "hakan@mail.com", "05477778899", "Sivas", "2024-05-25"),
            ("İrem Şen", "irem@mail.com", "05488889900", "Malatya", "2024-05-30")
        ]
        c.executemany("INSERT INTO uyeler (ad,email,telefon,adres,kayit_tarihi) VALUES (?,?,?,?,?)", demo_uyeler)
        
        # Raporların boş kalmaması ve dashboardın dolu görünmesi için işlemler
        demo_oduncler = []
        bugun = datetime.now()

        for i in range(1, 251):
            k_id = ((i * 3) % 45) + 1
            u_id = ((i * 2) % 17) + 1
            od = (bugun - timedelta(days=30 + i)).strftime("%Y-%m-%d")
            iad = (bugun - timedelta(days=10 + i)).strftime("%Y-%m-%d")
            demo_oduncler.append((k_id, u_id, od, iad, iad, 'Tamamlandı'))

        for i in range(31, 43):
            u_id = ((i * 2) % 17) + 1
            od = bugun.strftime("%Y-%m-%d")
            iad = (bugun + timedelta(days=14)).strftime("%Y-%m-%d")
            demo_oduncler.append((i, u_id, od, iad, None, 'Devam Ediyor'))

        for i in range(43, 46):
            u_id = ((i * 2) % 17) + 1
            od = (bugun - timedelta(days=20)).strftime("%Y-%m-%d")
            iad = (bugun - timedelta(days=5)).strftime("%Y-%m-%d")
            demo_oduncler.append((i, u_id, od, iad, None, 'Devam Ediyor'))

        c.executemany("INSERT INTO oduncler (kitap_id, uye_id, odunc_tarihi, iade_tarihi, gercek_iade, durum) VALUES (?,?,?,?,?,?)", demo_oduncler)

    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect("kutuphane.db")

# ─────────────────────────── RENK & STİL ────────────────────────────

TEMALAR = {
    "dark": {
        "bg":        "#0F1117",
        "sidebar":   "#161B22",
        "card":      "#1C2128",
        "border":    "#30363D",
        "accent":    "#58A6FF",
        "accent2":   "#3FB950",
        "accent3":   "#FF7B72",
        "accent4":   "#D2A8FF",
        "text":      "#E6EDF3",
        "text_mute": "#8B949E",
        "hover":     "#21262D",
        "selected":  "#1F3A5F",
        "warning":   "#F0883E",
        "gold":      "#E3B341",
        "tema_adi":  "dark",
        "tema_ikon": "",
        "tema_yazi": "Açık Tema",
    },
    "light": {
        "bg":        "#F6F8FA",
        "sidebar":   "#FFFFFF",
        "card":      "#FFFFFF",
        "border":    "#D0D7DE",
        "accent":    "#0969DA",
        "accent2":   "#1A7F37",
        "accent3":   "#CF222E",
        "accent4":   "#8250DF",
        "text":      "#1F2328",
        "text_mute": "#656D76",
        "hover":     "#F3F4F6",
        "selected":  "#DDF4FF",
        "warning":   "#9A6700",
        "gold":      "#7D4E00",
        "tema_adi":  "light",
        "tema_ikon": "",
        "tema_yazi": "Koyu Tema",
    }
}

RENKLER = dict(TEMALAR["dark"])
AKTIF_TEMA = {"ad": "dark"}

_tema_dinleyiciler = []

def tema_kaydet(fn):
    _tema_dinleyiciler.append(fn)

def tema_degistir(app):
    yeni = "light" if AKTIF_TEMA["ad"] == "dark" else "dark"
    AKTIF_TEMA["ad"] = yeni
    RENKLER.update(TEMALAR[yeni])
    app.setStyleSheet(genel_stil_olustur())
    for fn in _tema_dinleyiciler:
        try:
            fn()
        except Exception:
            pass


def genel_stil_olustur():
    R = RENKLER
    return f"""
QWidget {{
    background-color: {R['bg']};
    color: {R['text']};
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
}}
QLineEdit, QComboBox, QTextEdit, QDateEdit {{
    background-color: {R['card']};
    border: 1px solid {R['border']};
    border-radius: 6px;
    padding: 7px 12px;
    color: {R['text']};
    font-size: 13px;
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {{
    border: 1px solid {R['accent']};
}}
QTableWidget {{
    background-color: {R['card']};
    border: 1px solid {R['border']};
    border-radius: 8px;
    gridline-color: {R['border']};
    font-size: 13px;
    selection-background-color: {R['selected']};
}}
QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {R['border']};
}}
QHeaderView::section {{
    background-color: {R['sidebar']};
    color: {R['text_mute']};
    border: none;
    border-bottom: 2px solid {R['accent']};
    padding: 10px 12px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QScrollBar:vertical {{
    background: {R['bg']};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {R['border']};
    border-radius: 3px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QMessageBox {{
    background-color: {R['card']};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {R['card']};
    border: 1px solid {R['border']};
    selection-background-color: {R['selected']};
}}
QDateEdit::up-button, QDateEdit::down-button {{
    width: 16px;
}}
QDialog {{
    background-color: {R['card']};
}}

/* TEMA GEÇİŞİ İÇİN DİNAMİK WIDGET SINIFLARI (Sorun Burada Çözüldü) */

QFrame[cssClass="card"] {{
    background-color: {R['card']};
    border: 1px solid {R['border']};
    border-radius: 12px;
    padding: 16px;
}}

QFrame[cssClass="login_card"] {{
    background-color: {R['card']};
    border: 1px solid {R['border']};
    border-radius: 16px;
}}

QLineEdit[cssClass="giris_input"] {{
    background-color: {R['bg']};
    border: 1px solid {R['border']};
    border-radius: 8px;
    padding: 10px 14px;
    color: {R['text']};
    font-size: 14px;
}}
QLineEdit[cssClass="giris_input"]:focus {{
    border: 2px solid {R['accent']};
}}

QPushButton[cssClass="btn_iptal"] {{
    background-color: {R['border']};
    color: {R['text']};
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton[cssClass="btn_iptal"]:hover {{ opacity: 0.9; }}
QPushButton[cssClass="btn_iptal"]:pressed {{ opacity: 0.7; }}

QPushButton[cssClass="menu_btn"] {{
    background: transparent;
    color: {R['text_mute']};
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 0 16px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton[cssClass="menu_btn"]:hover {{
    background-color: {R['hover']};
    color: {R['text']};
}}
QPushButton[cssClass="menu_btn"]:checked {{
    background-color: {R['selected']};
    color: {R['accent']};
    font-weight: 700;
    border-left: 3px solid {R['accent']};
}}

QLineEdit[cssClass="arama"] {{
    background-color: {R['card']};
    border: 1px solid {R['border']};
    border-radius: 19px;
    padding: 0 16px;
    color: {R['text']};
    font-size: 13px;
}}
QLineEdit[cssClass="arama"]:focus {{
    border: 1px solid {R['accent']};
}}

QPushButton[cssClass="tema_btn"] {{
    background: transparent;
    color: {R['text_mute']};
    border: 1px solid {R['border']};
    border-radius: 8px;
    padding: 0 12px;
    font-size: 12px;
    text-align: left;
}}
QPushButton[cssClass="tema_btn"]:hover {{
    background-color: {R['hover']};
    color: {R['text']};
}}

QPushButton[cssClass="cikis_btn"] {{
    background: transparent;
    color: {R['accent3']};
    border: 1px solid {R['accent3']}44;
    border-radius: 8px;
    padding: 0 12px;
    font-size: 12px;
    text-align: left;
}}
QPushButton[cssClass="cikis_btn"]:hover {{
    background-color: {R['accent3']}22;
}}

QPushButton[cssClass="btn_outline"] {{
    background: transparent;
    color: {R['accent']};
    border: 1px solid {R['accent']};
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton[cssClass="btn_outline"]:hover {{
    background: {R['selected']};
}}

QPushButton[cssClass="btn_tema2"] {{
    background: transparent;
    border: 1px solid {R['border']};
    border-radius: 8px;
    font-size: 12px;
    color: {R['text']};
}}
QPushButton[cssClass="btn_tema2"]:hover {{ background: {R['hover']}; }}
"""

GENEL_STIL = genel_stil_olustur()


def btn_style(bg=None, hover=None, text="#FFFFFF", radius=8, padding="9px 18px"):
    bg = bg or RENKLER['accent']
    hover = hover or bg
    return f"""
    QPushButton {{
        background-color: {bg};
        color: {text};
        border: none;
        border-radius: {radius}px;
        padding: {padding};
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {hover};
        opacity: 0.9;
    }}
    QPushButton:pressed {{
        opacity: 0.7;
    }}
    QPushButton:disabled {{
        background-color: {RENKLER['border']};
        color: {RENKLER['text_mute']};
    }}
    """


# ─────────────────────────── YARDIMCI WİDGET'LER ────────────────────

class StatKart(QFrame):
    def __init__(self, baslik, deger, renk_key, ikon=""):
        super().__init__()
        self.renk_key = renk_key
        self.setFixedHeight(110)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)

        top = QHBoxLayout()
        ikon_lbl = QLabel(ikon)
        ikon_lbl.setFont(QFont("Segoe UI Emoji", 22))
        ikon_lbl.setStyleSheet("background: transparent; border: none;")
        top.addWidget(ikon_lbl)
        top.addStretch()

        self.deger_lbl = QLabel(str(deger))
        self.deger_lbl.setFont(QFont("Segoe UI", 28, QFont.Bold))

        self.bas_lbl = QLabel(baslik)
        self.bas_lbl.setStyleSheet("background: transparent; border: none; font-size: 12px;")

        lay.addLayout(top)
        lay.addWidget(self.deger_lbl)
        lay.addWidget(self.bas_lbl)

        tema_kaydet(self.tema_yenile)
        self.tema_yenile()

    def tema_yenile(self):
        renk = RENKLER.get(self.renk_key, self.renk_key)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['card']};
                border: 1px solid {renk}44;
                border-left: 4px solid {renk};
                border-radius: 12px;
            }}
        """)
        self.deger_lbl.setStyleSheet(f"color: {renk}; background: transparent; border: none;")
        self.bas_lbl.setStyleSheet(f"color: {RENKLER['text_mute']}; background: transparent; border: none; font-size: 12px;")

    def guncelle(self, yeni_deger):
        self.deger_lbl.setText(str(yeni_deger))


class MenuButon(QPushButton):
    def __init__(self, ikon, metin, parent=None):
        super().__init__(parent)
        self.setText(f"  {metin}")
        self.setCheckable(True)
        self.setFixedHeight(46)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("cssClass", "menu_btn")


class SectionBaslik(QLabel):
    def __init__(self, metin):
        super().__init__(metin)
        self.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.setStyleSheet("padding-bottom: 4px; background: transparent; border: none;")


class AramaCubugu(QLineEdit):
    def __init__(self, placeholder="Ara..."):
        super().__init__()
        self.setPlaceholderText(f"  {placeholder}")
        self.setFixedHeight(38)
        self.setProperty("cssClass", "arama")


# ─────────────────────────── ANA PENCERE ────────────────────────────

class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dijital Kütüphane Yönetim Sistemi")
        self.setMinimumSize(1200, 750)
        self.resize(1350, 820)
        self.setStyleSheet(genel_stil_olustur())

        ana = QWidget()
        self.setCentralWidget(ana)
        ana_lay = QHBoxLayout(ana)
        ana_lay.setContentsMargins(0, 0, 0, 0)
        ana_lay.setSpacing(0)

        self.sol_menu = self._sol_menu_olustur()
        ana_lay.addWidget(self.sol_menu)

        self.sayfa_stack = QStackedWidget()
        ana_lay.addWidget(self.sayfa_stack)

        self.anasayfa  = AnaSayfa(self)
        self.kitap_s   = KitapSayfasi(self)
        self.uye_s     = UyeSayfasi(self)
        self.odunc_s   = OduncSayfasi(self)
        self.rapor_s   = RaporSayfasi(self)
        self.arama_s   = GelisMisAramaSayfasi(self)

        for s in [self.anasayfa, self.kitap_s, self.uye_s,
                  self.odunc_s, self.rapor_s, self.arama_s]:
            self.sayfa_stack.addWidget(s)

        self.menu_butonlari[0].setChecked(True)
        self.sayfa_stack.setCurrentIndex(0)

        tema_kaydet(self._tema_yenile)

    def _sol_menu_olustur(self):
        frame = QFrame()
        frame.setFixedWidth(230)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['sidebar']};
                border-right: 1px solid {RENKLER['border']};
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 0, 12, 16)
        lay.setSpacing(2)

        logo_frame = QFrame()
        logo_frame.setFixedHeight(72)
        logo_frame.setStyleSheet("border: none; background: transparent;")
        logo_lay = QHBoxLayout(logo_frame)
        logo_ikon = QLabel("")
        logo_ikon.setFont(QFont("Segoe UI Emoji", 22))
        logo_ikon.setStyleSheet("background: transparent;")
        logo_yazi = QLabel("KütüphaneX")
        logo_yazi.setFont(QFont("Segoe UI", 15, QFont.Bold))
        logo_yazi.setStyleSheet(f"color: {RENKLER['accent']}; background: transparent;")
        logo_lay.addWidget(logo_ikon)
        logo_lay.addWidget(logo_yazi)
        logo_lay.addStretch()
        lay.addWidget(logo_frame)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {RENKLER['border']}; border: none;")
        lay.addWidget(sep)
        lay.addSpacing(8)

        menu_items = [
            ("", "Ana Sayfa"),
            ("", "Kitaplar"),
            ("", "Üyeler"),
            ("", "Ödünç İşlemleri"),
            ("", "Raporlar"),
            ("", "Gelişmiş Arama"),
        ]
        self.menu_butonlari = []
        for i, (ikon, metin) in enumerate(menu_items):
            btn = MenuButon(ikon, metin)
            btn.clicked.connect(lambda checked, idx=i: self._sayfa_degistir(idx))
            lay.addWidget(btn)
            self.menu_butonlari.append(btn)

        lay.addStretch()

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {RENKLER['border']}; border: none;")
        lay.addWidget(sep2)
        lay.addSpacing(8)
        tarih_lbl = QLabel(f"{datetime.now().strftime('%d %b %Y')}")
        tarih_lbl.setStyleSheet(f"color: {RENKLER['text_mute']}; font-size: 11px; background: transparent; border: none;")
        lay.addWidget(tarih_lbl)

        self.tema_btn = QPushButton(f"{RENKLER['tema_yazi']}")
        self.tema_btn.setFixedHeight(36)
        self.tema_btn.setCursor(Qt.PointingHandCursor)
        self.tema_btn.setProperty("cssClass", "tema_btn")
        self.tema_btn.clicked.connect(self._tema_degistir)
        lay.addWidget(self.tema_btn)

        cikis_btn = QPushButton("Çıkış Yap")
        cikis_btn.setFixedHeight(36)
        cikis_btn.setCursor(Qt.PointingHandCursor)
        cikis_btn.setProperty("cssClass", "cikis_btn")
        cikis_btn.clicked.connect(self._cikis)
        lay.addWidget(cikis_btn)

        return frame

    def _tema_degistir(self):
        tema_degistir(QApplication.instance())

    def _tema_yenile(self):
        self.setStyleSheet(genel_stil_olustur())
        self.tema_btn.setText(f"{RENKLER['tema_yazi']}")
        self.sol_menu.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['sidebar']};
                border-right: 1px solid {RENKLER['border']};
            }}
        """)

    def _cikis(self):
        ret = QMessageBox.question(self, "Çıkış", "Oturumu kapatmak istiyor musunuz?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.close()
            import sys as _sys
            _giris_ac()

    def _sayfa_degistir(self, idx):
        for i, btn in enumerate(self.menu_butonlari):
            btn.setChecked(i == idx)
        self.sayfa_stack.setCurrentIndex(idx)
        pages = [self.anasayfa, self.kitap_s, self.uye_s,
                 self.odunc_s, self.rapor_s, self.arama_s]
        if hasattr(pages[idx], 'yukle'):
            pages[idx].yukle()


# ─────────────────────────── ANA SAYFA ──────────────────────────────

class AnaSayfa(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_win = parent
        self._ui_olustur()

    def _ui_olustur(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        bas = QHBoxLayout()
        bas_lbl = SectionBaslik("Gösterge Paneli")
        bas.addWidget(bas_lbl)
        bas.addStretch()
        tarih = QLabel(datetime.now().strftime("%d %B %Y, %H:%M"))
        tarih.setStyleSheet(f"color: {RENKLER['text_mute']}; font-size: 12px;")
        bas.addWidget(tarih)
        lay.addLayout(bas)

        stat_lay = QHBoxLayout()
        stat_lay.setSpacing(16)
        self.kart_toplam   = StatKart("Toplam Kitap",   0, "accent",  "")
        self.kart_mevcut   = StatKart("Mevcut Kitap",   0, "accent2", "")
        self.kart_odunc    = StatKart("Ödünçte",         0, "warning", "")
        self.kart_uyeler   = StatKart("Kayıtlı Üye",    0, "accent4", "")
        self.kart_gecikme  = StatKart("Gecikmeli",       0, "accent3", "")
        for k in [self.kart_toplam, self.kart_mevcut, self.kart_odunc,
                  self.kart_uyeler, self.kart_gecikme]:
            stat_lay.addWidget(k)
        lay.addLayout(stat_lay)

        alt_lay = QHBoxLayout()
        alt_lay.setSpacing(16)

        son_frame = QFrame()
        son_frame.setProperty("cssClass", "card")
        son_v = QVBoxLayout(son_frame)
        son_v.setSpacing(10)
        son_lbl = QLabel("Son Ödünç İşlemleri")
        son_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        son_lbl.setStyleSheet("background: transparent; border: none;")
        son_v.addWidget(son_lbl)
        self.son_tablo = QTableWidget()
        self.son_tablo.setColumnCount(4)
        self.son_tablo.setHorizontalHeaderLabels(["Kitap", "Üye", "Ödünç", "İade"])
        self.son_tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.son_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.son_tablo.setSelectionMode(QTableWidget.NoSelection)
        self.son_tablo.verticalHeader().setVisible(False)
        son_v.addWidget(self.son_tablo)
        alt_lay.addWidget(son_frame, 3)

        gec_frame = QFrame()
        gec_frame.setProperty("cssClass", "card")
        gec_v = QVBoxLayout(gec_frame)
        gec_v.setSpacing(10)
        gec_lbl = QLabel("Gecikmeli Kitaplar")
        gec_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        gec_lbl.setStyleSheet(f"color: {RENKLER['accent3']}; background: transparent; border: none;")
        gec_v.addWidget(gec_lbl)
        self.gec_tablo = QTableWidget()
        self.gec_tablo.setColumnCount(3)
        self.gec_tablo.setHorizontalHeaderLabels(["Kitap", "Üye", "Gün"])
        self.gec_tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.gec_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.gec_tablo.setSelectionMode(QTableWidget.NoSelection)
        self.gec_tablo.verticalHeader().setVisible(False)
        gec_v.addWidget(self.gec_tablo)
        alt_lay.addWidget(gec_frame, 2)

        lay.addLayout(alt_lay)
        self.yukle()

    def yukle(self):
        conn = get_conn()
        c = conn.cursor()
        toplam = c.execute("SELECT COUNT(*) FROM kitaplar").fetchone()[0]
        mevcut = c.execute("SELECT COUNT(*) FROM kitaplar WHERE durum='Mevcut'").fetchone()[0]
        odunct = c.execute("SELECT COUNT(*) FROM oduncler WHERE durum='Devam Ediyor'").fetchone()[0]
        uyeler = c.execute("SELECT COUNT(*) FROM uyeler WHERE aktif=1").fetchone()[0]
        gecikme = c.execute(
            "SELECT COUNT(*) FROM oduncler WHERE durum='Devam Ediyor' AND iade_tarihi < ?",
            (datetime.now().strftime("%Y-%m-%d"),)
        ).fetchone()[0]
        conn.close()

        self.kart_toplam.guncelle(toplam)
        self.kart_mevcut.guncelle(mevcut)
        self.kart_odunc.guncelle(odunct)
        self.kart_uyeler.guncelle(uyeler)
        self.kart_gecikme.guncelle(gecikme)

        self._son_oduncleri_yukle()
        self._geciken_yukle()

    def _son_oduncleri_yukle(self):
        conn = get_conn()
        rows = conn.execute("""
            SELECT k.ad, u.ad, o.odunc_tarihi, o.iade_tarihi
            FROM oduncler o
            JOIN kitaplar k ON o.kitap_id=k.kitap_id
            JOIN uyeler u ON o.uye_id=u.uye_id
            ORDER BY o.odunc_id DESC LIMIT 8
        """).fetchall()
        conn.close()
        t = self.son_tablo
        t.setRowCount(len(rows))
        for i, (kitap, uye, od, iade) in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(kitap))
            t.setItem(i, 1, QTableWidgetItem(uye))
            t.setItem(i, 2, QTableWidgetItem(od))
            t.setItem(i, 3, QTableWidgetItem(iade or "-"))

    def _geciken_yukle(self):
        conn = get_conn()
        rows = conn.execute("""
            SELECT k.ad, u.ad, o.iade_tarihi
            FROM oduncler o
            JOIN kitaplar k ON o.kitap_id=k.kitap_id
            JOIN uyeler u ON o.uye_id=u.uye_id
            WHERE o.durum='Devam Ediyor' AND o.iade_tarihi < ?
            ORDER BY o.iade_tarihi ASC
        """, (datetime.now().strftime("%Y-%m-%d"),)).fetchall()
        conn.close()
        t = self.gec_tablo
        t.setRowCount(len(rows))
        bugun = datetime.now().date()
        for i, (kitap, uye, iade) in enumerate(rows):
            gun = (bugun - datetime.strptime(iade, "%Y-%m-%d").date()).days
            item_kitap = QTableWidgetItem(kitap)
            item_uye   = QTableWidgetItem(uye)
            item_gun   = QTableWidgetItem(f"{gun} gün")
            item_gun.setForeground(QColor(RENKLER['accent3']))
            t.setItem(i, 0, item_kitap)
            t.setItem(i, 1, item_uye)
            t.setItem(i, 2, item_gun)


# ─────────────────────────── KİTAP SAYFASI ──────────────────────────

class KitapSayfasi(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_win = parent
        self._ui()

    def _ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        ust = QHBoxLayout()
        ust.addWidget(SectionBaslik("Kitap Yönetimi"))
        ust.addStretch()
        self.arama = AramaCubugu("Kitap veya yazar ara...")
        self.arama.setFixedWidth(280)
        self.arama.textChanged.connect(self.yukle)
        ust.addWidget(self.arama)
        self.kat_filtre = QComboBox()
        self.kat_filtre.addItems(["Tüm Kategoriler", "Roman", "Distopya", "Bilim Kurgu",
                                   "Tarih", "Masal", "Kişisel Gelişim", "Klasik", "Çocuk", "Gastronomi", "Çizgi Roman", "Diğer"])
        self.kat_filtre.setFixedWidth(160)
        self.kat_filtre.currentIndexChanged.connect(self.yukle)
        ust.addWidget(self.kat_filtre)
        ekle_btn = QPushButton("Kitap Ekle")
        ekle_btn.setStyleSheet(btn_style(RENKLER['accent']))
        ekle_btn.clicked.connect(self._kitap_ekle_dialog)
        ust.addWidget(ekle_btn)
        lay.addLayout(ust)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(8)
        self.tablo.setHorizontalHeaderLabels(["ID", "Kitap Adı", "Yazar", "Kategori",
                                               "Yayınevi", "Yıl", "Durum", "İşlemler"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tablo.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.setRowHeight(0, 44)
        lay.addWidget(self.tablo)
        self.yukle()

    def yukle(self):
        arama = self.arama.text().strip()
        kat = self.kat_filtre.currentText()
        conn = get_conn()
        q = "SELECT kitap_id,ad,yazar,kategori,yayinevi,yil,durum FROM kitaplar WHERE 1=1"
        params = []
        if arama:
            q += " AND (ad LIKE ? OR yazar LIKE ?)"
            params += [f"%{arama}%", f"%{arama}%"]
        if kat != "Tüm Kategoriler":
            q += " AND kategori=?"
            params.append(kat)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        self.tablo.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.tablo.setRowHeight(i, 44)
            for j, val in enumerate(row[:7]):
                item = QTableWidgetItem(str(val) if val else "-")
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if j == 6:  # Durum
                    renk = RENKLER['accent2'] if val == "Mevcut" else RENKLER['warning']
                    item.setForeground(QColor(renk))
                    item.setFont(QFont("Segoe UI", 12, QFont.Bold))
                self.tablo.setItem(i, j, item)
            islem_w = QWidget()
            islem_w.setStyleSheet(f"background: transparent;")
            islem_lay = QHBoxLayout(islem_w)
            islem_lay.setContentsMargins(4, 2, 4, 2)
            islem_lay.setSpacing(4)
            duz_btn = QPushButton("Düzenle")
            duz_btn.setFixedSize(65, 28)
            duz_btn.setStyleSheet(btn_style(RENKLER['accent'], padding="2px 4px"))
            duz_btn.clicked.connect(lambda _, r=row: self._duzenle(r))
            sil_btn = QPushButton("Sil")
            sil_btn.setFixedSize(45, 28)
            sil_btn.setStyleSheet(btn_style(RENKLER['accent3'], padding="2px 4px"))
            sil_btn.clicked.connect(lambda _, rid=row[0]: self._sil(rid))
            islem_lay.addWidget(duz_btn)
            islem_lay.addWidget(sil_btn)
            self.tablo.setCellWidget(i, 7, islem_w)

    def _kitap_ekle_dialog(self, kitap_data=None):
        dlg = KitapDialog(self, kitap_data)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            conn = get_conn()
            if kitap_data:
                conn.execute(
                    "UPDATE kitaplar SET ad=?,yazar=?,kategori=?,yayinevi=?,yil=?,isbn=?,aciklama=? WHERE kitap_id=?",
                    (d['ad'], d['yazar'], d['kategori'], d['yayinevi'],
                     d['yil'], d['isbn'], d['aciklama'], kitap_data[0])
                )
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Başarılı", "Kitap güncellendi.")
            else:
                conn.execute(
                    "INSERT INTO kitaplar (ad,yazar,kategori,yayinevi,yil,isbn,aciklama) VALUES (?,?,?,?,?,?,?)",
                    (d['ad'], d['yazar'], d['kategori'], d['yayinevi'],
                     d['yil'], d['isbn'], d['aciklama'])
                )
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Başarılı", "Kitap eklendi.")
            self.yukle()

    def _duzenle(self, row):
        conn = get_conn()
        full = conn.execute("SELECT * FROM kitaplar WHERE kitap_id=?", (row[0],)).fetchone()
        conn.close()
        self._kitap_ekle_dialog(full)

    def _sil(self, kitap_id):
        conn = get_conn()
        odunc = conn.execute(
            "SELECT COUNT(*) FROM oduncler WHERE kitap_id=? AND durum='Devam Ediyor'",
            (kitap_id,)
        ).fetchone()[0]
        conn.close()
        if odunc:
            QMessageBox.warning(self, "Uyarı", "Bu kitap şu an ödünçte, silinemez!")
            return
        ret = QMessageBox.question(self, "Onay", "Kitabı silmek istediğinize emin misiniz?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            conn = get_conn()
            conn.execute("DELETE FROM kitaplar WHERE kitap_id=?", (kitap_id,))
            conn.commit()
            conn.close()
            self.yukle()


class KitapDialog(QDialog):
    def __init__(self, parent, data=None):
        super().__init__(parent)
        self.setWindowTitle("Kitap Ekle" if not data else "Kitap Düzenle")
        self.setFixedSize(480, 460)
        
        # Tema dinleyicisi ekleyerek arkaplanın güncel kalmasını sağlıyoruz
        self.setStyleSheet(GENEL_STIL + f"QDialog{{background:{RENKLER['card']};border-radius:12px;}}")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        baslik = QLabel("Kitap Bilgileri")
        baslik.setFont(QFont("Segoe UI", 14, QFont.Bold))
        baslik.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(baslik)

        form = QFormLayout()
        form.setSpacing(10)
        self.f_ad      = QLineEdit(); self.f_ad.setPlaceholderText("Kitap adı")
        self.f_yazar   = QLineEdit(); self.f_yazar.setPlaceholderText("Yazar adı")
        self.f_kategori= QComboBox()
        self.f_kategori.addItems(["Roman", "Distopya", "Bilim Kurgu", "Tarih",
                                   "Masal", "Kişisel Gelişim", "Klasik", "Çocuk", "Gastronomi", "Çizgi Roman", "Diğer"])
        self.f_yayinevi= QLineEdit(); self.f_yayinevi.setPlaceholderText("Yayınevi")
        self.f_yil     = QLineEdit(); self.f_yil.setPlaceholderText("Yayın yılı")
        self.f_yil.setValidator(QRegExpValidator(QRegExp("^[0-9]*$"), self)) 
        self.f_isbn    = QLineEdit(); self.f_isbn.setPlaceholderText("ISBN")
        self.f_aciklama= QTextEdit(); self.f_aciklama.setPlaceholderText("Kısa açıklama..."); self.f_aciklama.setFixedHeight(70)
        
        for lbl, w in [("Kitap Adı *", self.f_ad), ("Yazar *", self.f_yazar),
                        ("Kategori *", self.f_kategori), ("Yayınevi", self.f_yayinevi),
                        ("Yıl", self.f_yil), ("ISBN", self.f_isbn), ("Açıklama", self.f_aciklama)]:
            l = QLabel(lbl)
            l.setStyleSheet(f"color:{RENKLER['text_mute']}; background: transparent; border: none;")
            form.addRow(l, w)
        lay.addLayout(form)

        if data:
            self.f_ad.setText(data[1] or "")
            self.f_yazar.setText(data[2] or "")
            idx = self.f_kategori.findText(data[3])
            if idx >= 0: self.f_kategori.setCurrentIndex(idx)
            self.f_yayinevi.setText(data[6] or "")
            self.f_yil.setText(str(data[7]) if data[7] else "")
            self.f_isbn.setText(data[5] or "")
            self.f_aciklama.setPlainText(data[8] or "")

        btn_lay = QHBoxLayout()
        iptal = QPushButton("İptal")
        iptal.setProperty("cssClass", "btn_iptal")
        iptal.clicked.connect(self.reject)
        kaydet = QPushButton("Kaydet")
        kaydet.setStyleSheet(btn_style(RENKLER['accent']))
        kaydet.clicked.connect(self._dogrula)
        btn_lay.addWidget(iptal)
        btn_lay.addWidget(kaydet)
        lay.addLayout(btn_lay)

    def _dogrula(self):
        if not self.f_ad.text().strip() or not self.f_yazar.text().strip():
            QMessageBox.warning(self, "Hata", "Kitap adı ve yazar zorunludur!")
            return
        self.accept()

    def get_data(self):
        return {
            'ad': self.f_ad.text().strip(),
            'yazar': self.f_yazar.text().strip(),
            'kategori': self.f_kategori.currentText(),
            'yayinevi': self.f_yayinevi.text().strip(),
            'yil': self.f_yil.text().strip() or None,
            'isbn': self.f_isbn.text().strip(),
            'aciklama': self.f_aciklama.toPlainText().strip(),
        }


# ─────────────────────────── ÜYE SAYFASI ────────────────────────────

class UyeSayfasi(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_win = parent
        self._ui()

    def _ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        ust = QHBoxLayout()
        ust.addWidget(SectionBaslik("Üye Yönetimi"))
        ust.addStretch()
        self.arama = AramaCubugu("İsim veya e-posta ara...")
        self.arama.setFixedWidth(280)
        self.arama.textChanged.connect(self.yukle)
        ust.addWidget(self.arama)
        ekle_btn = QPushButton("Üye Ekle")
        ekle_btn.setStyleSheet(btn_style(RENKLER['accent4']))
        ekle_btn.clicked.connect(self._uye_ekle_dialog)
        ust.addWidget(ekle_btn)
        lay.addLayout(ust)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(7)
        self.tablo.setHorizontalHeaderLabels(["ID", "Ad Soyad", "E-posta", "Telefon", "Kayıt Tarihi", "Durum", "İşlemler"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tablo.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.verticalHeader().setVisible(False)
        lay.addWidget(self.tablo)
        self.yukle()

    def yukle(self):
        arama = self.arama.text().strip()
        conn = get_conn()
        q = "SELECT uye_id,ad,email,telefon,kayit_tarihi,aktif FROM uyeler WHERE 1=1"
        params = []
        if arama:
            q += " AND (ad LIKE ? OR email LIKE ?)"
            params += [f"%{arama}%", f"%{arama}%"]
        rows = conn.execute(q, params).fetchall()
        conn.close()
        self.tablo.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.tablo.setRowHeight(i, 44)
            for j, val in enumerate(row[:5]):
                item = QTableWidgetItem(str(val) if val else "-")
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.tablo.setItem(i, j, item)
            durum = "Aktif" if row[5] else "Pasif"
            d_item = QTableWidgetItem(durum)
            d_item.setForeground(QColor(RENKLER['accent2'] if row[5] else RENKLER['accent3']))
            d_item.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.tablo.setItem(i, 5, d_item)
            w = QWidget(); w.setStyleSheet(f"background: transparent;")
            wl = QHBoxLayout(w); wl.setContentsMargins(4,2,4,2); wl.setSpacing(4)
            duz = QPushButton("Düzenle"); duz.setFixedSize(65,28)
            duz.setStyleSheet(btn_style(RENKLER['accent'], padding="2px 4px"))
            duz.clicked.connect(lambda _, r=row: self._duzenle(r))
            sil = QPushButton("Sil"); sil.setFixedSize(45,28)
            sil.setStyleSheet(btn_style(RENKLER['accent3'], padding="2px 4px"))
            sil.clicked.connect(lambda _, uid=row[0]: self._sil(uid))
            wl.addWidget(duz); wl.addWidget(sil)
            self.tablo.setCellWidget(i, 6, w)

    def _uye_ekle_dialog(self, data=None):
        dlg = UyeDialog(self, data)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            conn = get_conn()
            try:
                if data:
                    conn.execute(
                        "UPDATE uyeler SET ad=?,email=?,telefon=?,adres=? WHERE uye_id=?",
                        (d['ad'], d['email'], d['telefon'], d['adres'], data[0])
                    )
                else:
                    conn.execute(
                        "INSERT INTO uyeler (ad,email,telefon,adres) VALUES (?,?,?,?)",
                        (d['ad'], d['email'], d['telefon'], d['adres'])
                    )
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Başarılı", "Üye kaydedildi.")
                self.yukle()
            except sqlite3.IntegrityError:
                conn.close()
                QMessageBox.warning(self, "Hata", "Bu e-posta adresi zaten kayıtlı!")

    def _duzenle(self, row):
        self._uye_ekle_dialog(row)

    def _sil(self, uid):
        ret = QMessageBox.question(self, "Onay", "Üyeyi silmek istiyor musunuz?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            conn = get_conn()
            conn.execute("DELETE FROM uyeler WHERE uye_id=?", (uid,))
            # Silme işleminden sonra AUTOINCREMENT sayacını tablodaki en yüksek değere eşitle:
            conn.execute("UPDATE sqlite_sequence SET seq = (SELECT COALESCE(MAX(uye_id), 0) FROM uyeler) WHERE name = 'uyeler'")
            conn.commit()
            conn.close()
            self.yukle()


class UyeDialog(QDialog):
    def __init__(self, parent, data=None):
        super().__init__(parent)
        self.setWindowTitle("Üye Ekle" if not data else "Üye Düzenle")
        self.setFixedSize(420, 340)
        self.setStyleSheet(GENEL_STIL + f"QDialog{{background:{RENKLER['card']};border-radius:12px;}}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24,20,24,20)
        lay.setSpacing(14)
        baslik = QLabel("Üye Bilgileri")
        baslik.setFont(QFont("Segoe UI", 14, QFont.Bold))
        baslik.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(baslik)
        form = QFormLayout(); form.setSpacing(10)
        self.f_ad    = QLineEdit(); self.f_ad.setPlaceholderText("Ad Soyad")
        self.f_email = QLineEdit(); self.f_email.setPlaceholderText("ornek@mail.com")
        self.f_tel   = QLineEdit(); self.f_tel.setPlaceholderText("05xxxxxxxxx")
        self.f_tel.setValidator(QRegExpValidator(QRegExp("^[0-9]*$"), self)) 
        self.f_tel.setMaxLength(11) 
        self.f_adres = QLineEdit(); self.f_adres.setPlaceholderText("Şehir")
        for lbl, w in [("Ad Soyad *", self.f_ad), ("E-posta *", self.f_email),
                        ("Telefon", self.f_tel), ("Adres", self.f_adres)]:
            l = QLabel(lbl); l.setStyleSheet(f"color:{RENKLER['text_mute']}; background: transparent; border: none;")
            form.addRow(l, w)
        lay.addLayout(form)
        if data:
            self.f_ad.setText(data[1] or "")
            self.f_email.setText(data[2] or "")
            self.f_tel.setText(data[3] or "")
            self.f_adres.setText(data[4] or "")
        btn_lay = QHBoxLayout()
        iptal = QPushButton("İptal")
        iptal.setProperty("cssClass", "btn_iptal")
        iptal.clicked.connect(self.reject)
        kaydet = QPushButton("Kaydet"); kaydet.setStyleSheet(btn_style(RENKLER['accent4']))
        kaydet.clicked.connect(self._dogrula)
        btn_lay.addWidget(iptal); btn_lay.addWidget(kaydet)
        lay.addLayout(btn_lay)

    def _dogrula(self):
        if not self.f_ad.text().strip() or not self.f_email.text().strip():
            QMessageBox.warning(self, "Hata", "Ad ve e-posta zorunludur!")
            return
        
        tel = self.f_tel.text().strip()
        if tel:
            if len(tel) != 11 or not tel.startswith("0"):
                QMessageBox.warning(self, "Hata", "Geçersiz telefon numarası! (11 haneli olmalı ve 0 ile başlamalıdır)")
                return

        self.accept()

    def get_data(self):
        return {'ad': self.f_ad.text().strip(), 'email': self.f_email.text().strip(),
                'telefon': self.f_tel.text().strip(), 'adres': self.f_adres.text().strip()}


# ─────────────────────────── ÖDÜNÇ SAYFASI ──────────────────────────

class OduncSayfasi(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_win = parent
        self._ui()

    def _ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        ust = QHBoxLayout()
        ust.addWidget(SectionBaslik("Ödünç İşlemleri"))
        ust.addStretch()
        self.durum_filtre = QComboBox()
        self.durum_filtre.addItems(["Tüm İşlemler", "Devam Ediyor", "Tamamlandı", "Gecikmiş"])
        self.durum_filtre.setFixedWidth(160)
        self.durum_filtre.currentIndexChanged.connect(self.yukle)
        ust.addWidget(self.durum_filtre)
        yeni_btn = QPushButton("Ödünç Ver")
        yeni_btn.setStyleSheet(btn_style(RENKLER['accent2']))
        yeni_btn.clicked.connect(self._odunc_ver_dialog)
        ust.addWidget(yeni_btn)
        lay.addLayout(ust)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(8)
        self.tablo.setHorizontalHeaderLabels(
            ["ID", "Kitap", "Üye", "Ödünç Tarihi", "Son İade", "Gerçek İade", "Durum", "İşlem"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tablo.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.verticalHeader().setVisible(False)
        lay.addWidget(self.tablo)
        self.yukle()

    def yukle(self):
        filtre = self.durum_filtre.currentText()
        conn = get_conn()
        bugun = datetime.now().strftime("%Y-%m-%d")
        if filtre == "Gecikmiş":
            rows = conn.execute("""
                SELECT o.odunc_id, k.ad, u.ad, o.odunc_tarihi, o.iade_tarihi, o.gercek_iade, o.durum
                FROM oduncler o
                JOIN kitaplar k ON o.kitap_id=k.kitap_id
                JOIN uyeler u ON o.uye_id=u.uye_id
                WHERE o.durum='Devam Ediyor' AND o.iade_tarihi < ?
                ORDER BY o.odunc_id DESC
            """, (bugun,)).fetchall()
        elif filtre == "Tüm İşlemler":
            rows = conn.execute("""
                SELECT o.odunc_id, k.ad, u.ad, o.odunc_tarihi, o.iade_tarihi, o.gercek_iade, o.durum
                FROM oduncler o
                JOIN kitaplar k ON o.kitap_id=k.kitap_id
                JOIN uyeler u ON o.uye_id=u.uye_id
                ORDER BY o.odunc_id DESC
            """).fetchall()
        else:
            rows = conn.execute("""
                SELECT o.odunc_id, k.ad, u.ad, o.odunc_tarihi, o.iade_tarihi, o.gercek_iade, o.durum
                FROM oduncler o
                JOIN kitaplar k ON o.kitap_id=k.kitap_id
                JOIN uyeler u ON o.uye_id=u.uye_id
                WHERE o.durum=?
                ORDER BY o.odunc_id DESC
            """, (filtre,)).fetchall()
        conn.close()
        self.tablo.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.tablo.setRowHeight(i, 44)
            for j, val in enumerate(row[:7]):
                item = QTableWidgetItem(str(val) if val else "-")
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if j == 6:
                    gecikti = (row[4] and row[4] < bugun and val == "Devam Ediyor")
                    if gecikti:
                        item.setText("Gecikmiş")
                        item.setForeground(QColor(RENKLER['accent3']))
                    elif val == "Devam Ediyor":
                        item.setForeground(QColor(RENKLER['warning']))
                    else:
                        item.setForeground(QColor(RENKLER['accent2']))
                    item.setFont(QFont("Segoe UI", 12, QFont.Bold))
                self.tablo.setItem(i, j, item)
            w = QWidget(); w.setStyleSheet(f"background: transparent;")
            wl = QHBoxLayout(w); wl.setContentsMargins(4,2,4,2)
            if row[6] == "Devam Ediyor":
                iade_btn = QPushButton("İade")
                iade_btn.setFixedHeight(28)
                iade_btn.setStyleSheet(btn_style(RENKLER['accent2'], padding="2px 8px"))
                iade_btn.clicked.connect(lambda _, oid=row[0]: self._iade_et(oid))
                wl.addWidget(iade_btn)
            else:
                done_lbl = QLabel("Tamamlandı")
                done_lbl.setStyleSheet(f"color:{RENKLER['text_mute']}; background:transparent;")
                wl.addWidget(done_lbl)
            self.tablo.setCellWidget(i, 7, w)

    def _odunc_ver_dialog(self):
        dlg = OduncDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            conn = get_conn()
            conn.execute(
                "INSERT INTO oduncler (kitap_id,uye_id,odunc_tarihi,iade_tarihi) VALUES (?,?,?,?)",
                (d['kitap_id'], d['uye_id'], d['odunc_tarihi'], d['iade_tarihi'])
            )
            conn.execute("UPDATE kitaplar SET durum='Ödünçte' WHERE kitap_id=?", (d['kitap_id'],))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Kitap ödünç verildi.")
            self.yukle()

    def _iade_et(self, odunc_id):
        ret = QMessageBox.question(self, "İade Onayı", "Kitabı iade almak istiyor musunuz?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            today = datetime.now().strftime("%Y-%m-%d")
            conn = get_conn()
            row = conn.execute("SELECT kitap_id FROM oduncler WHERE odunc_id=?", (odunc_id,)).fetchone()
            conn.execute(
                "UPDATE oduncler SET gercek_iade=?,durum='Tamamlandı' WHERE odunc_id=?",
                (today, odunc_id)
            )
            conn.execute("UPDATE kitaplar SET durum='Mevcut' WHERE kitap_id=?", (row[0],))
            conn.commit()
            conn.close()
            self.yukle()


class OduncDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Kitap Ödünç Ver")
        self.setFixedSize(440, 360)
        self.setStyleSheet(GENEL_STIL + f"QDialog{{background:{RENKLER['card']};border-radius:12px;}}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24,20,24,20)
        lay.setSpacing(14)
        baslik = QLabel("Ödünç İşlemi")
        baslik.setFont(QFont("Segoe UI", 14, QFont.Bold))
        baslik.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(baslik)
        form = QFormLayout(); form.setSpacing(12)

        conn = get_conn()
        kitaplar = conn.execute("SELECT kitap_id,ad,yazar FROM kitaplar WHERE durum='Mevcut'").fetchall()
        uyeler   = conn.execute("SELECT uye_id,ad FROM uyeler WHERE aktif=1").fetchall()
        conn.close()

        self.kitap_cb = QComboBox()
        for k in kitaplar:
            self.kitap_cb.addItem(f"{k[1]} — {k[2]}", k[0])
        self.uye_cb = QComboBox()
        for u in uyeler:
            self.uye_cb.addItem(u[1], u[0])

        self.odunc_dt = QDateEdit(QDate.currentDate())
        self.odunc_dt.setCalendarPopup(True)
        self.iade_dt  = QDateEdit(QDate.currentDate().addDays(14))
        self.iade_dt.setCalendarPopup(True)

        for lbl, w in [("Kitap *", self.kitap_cb), ("Üye *", self.uye_cb),
                        ("Ödünç Tarihi", self.odunc_dt), ("Son İade Tarihi", self.iade_dt)]:
            l = QLabel(lbl); l.setStyleSheet(f"color:{RENKLER['text_mute']}; background: transparent; border: none;")
            form.addRow(l, w)

        if not kitaplar:
            uyari = QLabel("Mevcut kitap bulunmuyor!")
            uyari.setStyleSheet(f"color:{RENKLER['accent3']}; background: transparent; border: none;")
            lay.addWidget(uyari)

        lay.addLayout(form)
        btn_lay = QHBoxLayout()
        iptal = QPushButton("İptal")
        iptal.setProperty("cssClass", "btn_iptal")
        iptal.clicked.connect(self.reject)
        ver = QPushButton("Ödünç Ver"); ver.setStyleSheet(btn_style(RENKLER['accent2']))
        ver.clicked.connect(self.accept)
        if not kitaplar: ver.setEnabled(False)
        btn_lay.addWidget(iptal); btn_lay.addWidget(ver)
        lay.addLayout(btn_lay)

    def get_data(self):
        return {
            'kitap_id': self.kitap_cb.currentData(),
            'uye_id': self.uye_cb.currentData(),
            'odunc_tarihi': self.odunc_dt.date().toString("yyyy-MM-dd"),
            'iade_tarihi': self.iade_dt.date().toString("yyyy-MM-dd"),
        }


# ─────────────────────────── RAPOR SAYFASI ──────────────────────────

class RaporSayfasi(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_win = parent
        self._ui()

    def _ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)
        lay.addWidget(SectionBaslik("Raporlar & İstatistikler"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        ic = QWidget()
        ic.setStyleSheet("background: transparent;")
        ic_lay = QVBoxLayout(ic)
        ic_lay.setSpacing(20)

        kat_frame = self._bolumsec("Kategori Dağılımı")
        kat_v = QVBoxLayout(kat_frame)
        kat_v.setContentsMargins(16,12,16,12)
        kat_v.addWidget(self._baslik_lbl("Kategori Dağılımı"))
        self.kat_tablo = self._mini_tablo(["Kategori", "Kitap Sayısı", "%"])
        kat_v.addWidget(self.kat_tablo)
        ic_lay.addWidget(kat_frame)

        pop_frame = self._bolumsec("En Çok Ödünç Alınan Kitaplar")
        pop_v = QVBoxLayout(pop_frame)
        pop_v.setContentsMargins(16,12,16,12)
        pop_v.addWidget(self._baslik_lbl("En Çok Ödünç Alınan Kitaplar"))
        self.pop_tablo = self._mini_tablo(["Kitap", "Yazar", "Ödünç Sayısı"])
        pop_v.addWidget(self.pop_tablo)
        ic_lay.addWidget(pop_frame)

        aktif_frame = self._bolumsec("En Aktif Üyeler")
        aktif_v = QVBoxLayout(aktif_frame)
        aktif_v.setContentsMargins(16,12,16,12)
        aktif_v.addWidget(self._baslik_lbl("En Aktif Üyeler"))
        self.aktif_tablo = self._mini_tablo(["Üye", "E-posta", "Ödünç Sayısı"])
        aktif_v.addWidget(self.aktif_tablo)
        ic_lay.addWidget(aktif_frame)

        scroll.setWidget(ic)
        lay.addWidget(scroll)
        self.yukle()

    def _bolumsec(self, baslik):
        frame = QFrame()
        frame.setProperty("cssClass", "card")
        return frame

    def _baslik_lbl(self, metin):
        lbl = QLabel(metin)
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl.setStyleSheet("background: transparent; border: none; padding-bottom: 6px;")
        return lbl

    def _mini_tablo(self, basliklar):
        t = QTableWidget()
        t.setColumnCount(len(basliklar))
        t.setHorizontalHeaderLabels(basliklar)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionMode(QTableWidget.NoSelection)
        t.verticalHeader().setVisible(False)
        t.setFixedHeight(200)
        return t

    def yukle(self):
        conn = get_conn()

        rows = conn.execute("""
            SELECT kategori, COUNT(*) as cnt FROM kitaplar GROUP BY kategori ORDER BY cnt DESC
        """).fetchall()
        toplam = sum(r[1] for r in rows) or 1
        self.kat_tablo.setRowCount(len(rows))
        for i, (kat, cnt) in enumerate(rows):
            self.kat_tablo.setItem(i, 0, QTableWidgetItem(kat))
            self.kat_tablo.setItem(i, 1, QTableWidgetItem(str(cnt)))
            self.kat_tablo.setItem(i, 2, QTableWidgetItem(f"%{cnt*100//toplam}"))

        rows2 = conn.execute("""
            SELECT k.ad, k.yazar, COUNT(o.odunc_id) as cnt
            FROM kitaplar k LEFT JOIN oduncler o ON k.kitap_id=o.kitap_id
            GROUP BY k.kitap_id ORDER BY cnt DESC LIMIT 8
        """).fetchall()
        self.pop_tablo.setRowCount(len(rows2))
        for i, (ad, yazar, cnt) in enumerate(rows2):
            self.pop_tablo.setItem(i, 0, QTableWidgetItem(ad))
            self.pop_tablo.setItem(i, 1, QTableWidgetItem(yazar))
            cnt_item = QTableWidgetItem(str(cnt))
            if cnt > 0: cnt_item.setForeground(QColor(RENKLER['gold']))
            self.pop_tablo.setItem(i, 2, cnt_item)

        rows3 = conn.execute("""
            SELECT u.ad, u.email, COUNT(o.odunc_id) as cnt
            FROM uyeler u LEFT JOIN oduncler o ON u.uye_id=o.uye_id
            GROUP BY u.uye_id ORDER BY cnt DESC LIMIT 8
        """).fetchall()
        self.aktif_tablo.setRowCount(len(rows3))
        for i, (ad, email, cnt) in enumerate(rows3):
            self.aktif_tablo.setItem(i, 0, QTableWidgetItem(ad))
            self.aktif_tablo.setItem(i, 1, QTableWidgetItem(email))
            cnt_item = QTableWidgetItem(str(cnt))
            if cnt > 0: cnt_item.setForeground(QColor(RENKLER['accent4']))
            self.aktif_tablo.setItem(i, 2, cnt_item)

        conn.close()


# ─────────────────────── GELİŞMİŞ ARAMA SAYFASI ─────────────────────

class GelisMisAramaSayfasi(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_win = parent
        self._ui()

    def _ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        lay.addWidget(SectionBaslik("Gelişmiş Arama"))

        form_frame = QFrame()
        form_frame.setProperty("cssClass", "card")
        form_lay = QGridLayout(form_frame)
        form_lay.setContentsMargins(20, 16, 20, 16)
        form_lay.setSpacing(12)

        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{RENKLER['text_mute']}; background:transparent; border:none;")
            return l

        self.a_ad     = QLineEdit(); self.a_ad.setPlaceholderText("Kitap adı...")
        self.a_yazar  = QLineEdit(); self.a_yazar.setPlaceholderText("Yazar adı...")
        self.a_kat    = QComboBox()
        self.a_kat.addItems(["Tüm Kategoriler", "Roman", "Distopya", "Bilim Kurgu",
                              "Tarih", "Masal", "Kişisel Gelişim", "Klasik", "Çocuk", "Gastronomi", "Çizgi Roman", "Diğer"])
        self.a_durum  = QComboBox()
        self.a_durum.addItems(["Tüm Durumlar", "Mevcut", "Ödünçte"])
        self.a_yayinevi = QLineEdit(); self.a_yayinevi.setPlaceholderText("Yayınevi...")
        self.a_yil_min  = QLineEdit(); self.a_yil_min.setPlaceholderText("Min yıl")
        self.a_yil_min.setValidator(QRegExpValidator(QRegExp("^[0-9]*$"), self)) 
        self.a_yil_max  = QLineEdit(); self.a_yil_max.setPlaceholderText("Max yıl")
        self.a_yil_max.setValidator(QRegExpValidator(QRegExp("^[0-9]*$"), self)) 

        form_lay.addWidget(lbl("Kitap Adı"),   0, 0); form_lay.addWidget(self.a_ad,      0, 1)
        form_lay.addWidget(lbl("Yazar"),        0, 2); form_lay.addWidget(self.a_yazar,   0, 3)
        form_lay.addWidget(lbl("Kategori"),     1, 0); form_lay.addWidget(self.a_kat,     1, 1)
        form_lay.addWidget(lbl("Durum"),        1, 2); form_lay.addWidget(self.a_durum,   1, 3)
        form_lay.addWidget(lbl("Yayınevi"),     2, 0); form_lay.addWidget(self.a_yayinevi,2, 1)
        form_lay.addWidget(lbl("Yıl (Min)"),    2, 2); form_lay.addWidget(self.a_yil_min, 2, 3)
        form_lay.addWidget(lbl("Yıl (Max)"),    3, 0); form_lay.addWidget(self.a_yil_max, 3, 1)

        btn_lay = QHBoxLayout()
        temizle = QPushButton("Temizle")
        temizle.setProperty("cssClass", "btn_iptal")
        temizle.clicked.connect(self._temizle)
        ara_btn = QPushButton("Ara")
        ara_btn.setStyleSheet(btn_style(RENKLER['accent']))
        ara_btn.clicked.connect(self._ara)
        btn_lay.addStretch()
        btn_lay.addWidget(temizle)
        btn_lay.addWidget(ara_btn)
        form_lay.addLayout(btn_lay, 4, 0, 1, 4)
        lay.addWidget(form_frame)

        self.sonuc_lbl = QLabel("Arama yapmak için yukarıdaki kriterleri kullanın.")
        self.sonuc_lbl.setStyleSheet(f"color:{RENKLER['text_mute']}; font-size:13px; background:transparent; border:none;")
        lay.addWidget(self.sonuc_lbl)
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(7)
        self.tablo.setHorizontalHeaderLabels(["ID", "Kitap Adı", "Yazar", "Kategori", "Yayınevi", "Yıl", "Durum"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.verticalHeader().setVisible(False)
        lay.addWidget(self.tablo)

    def _ara(self):
        q = "SELECT kitap_id,ad,yazar,kategori,yayinevi,yil,durum FROM kitaplar WHERE 1=1"
        params = []
        if self.a_ad.text().strip():
            q += " AND ad LIKE ?"; params.append(f"%{self.a_ad.text().strip()}%")
        if self.a_yazar.text().strip():
            q += " AND yazar LIKE ?"; params.append(f"%{self.a_yazar.text().strip()}%")
        if self.a_kat.currentText() != "Tüm Kategoriler":
            q += " AND kategori=?"; params.append(self.a_kat.currentText())
        if self.a_durum.currentText() != "Tüm Durumlar":
            q += " AND durum=?"; params.append(self.a_durum.currentText())
        if self.a_yayinevi.text().strip():
            q += " AND yayinevi LIKE ?"; params.append(f"%{self.a_yayinevi.text().strip()}%")
        if self.a_yil_min.text().strip():
            q += " AND yil >= ?"; params.append(self.a_yil_min.text().strip())
        if self.a_yil_max.text().strip():
            q += " AND yil <= ?"; params.append(self.a_yil_max.text().strip())

        conn = get_conn()
        rows = conn.execute(q, params).fetchall()
        conn.close()
        self.sonuc_lbl.setText(f"{len(rows)} sonuç bulundu.")
        self.tablo.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.tablo.setRowHeight(i, 44)
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "-")
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if j == 6:
                    renk = RENKLER['accent2'] if val == "Mevcut" else RENKLER['warning']
                    item.setForeground(QColor(renk))
                self.tablo.setItem(i, j, item)

    def _temizle(self):
        self.a_ad.clear(); self.a_yazar.clear()
        self.a_yayinevi.clear(); self.a_yil_min.clear(); self.a_yil_max.clear()
        self.a_kat.setCurrentIndex(0); self.a_durum.setCurrentIndex(0)
        self.tablo.setRowCount(0)
        self.sonuc_lbl.setText("Arama yapmak için yukarıdaki kriterleri kullanın.")

    def yukle(self):
        pass


# ═══════════════════════════════════════════════════════════════════
# ─────────────────── GİRİŞ / KAYIT PENCERELERİ ─────────────────────
# ═══════════════════════════════════════════════════════════════════

class GirisPenceresi(QWidget):
    giris_basarili = pyqtSignal(str, int, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KütüphaneX — Giriş")
        self.setFixedSize(480, 560)
        self.setStyleSheet(genel_stil_olustur())
        self._ui()
        tema_kaydet(self._tema_yenile)

    def _ui(self):
        ana = QVBoxLayout(self)
        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)

        self.bg = QFrame()
        self.bg.setStyleSheet(f"background-color: {RENKLER['bg']};")
        ana.addWidget(self.bg)

        ic_lay = QVBoxLayout(self.bg)
        ic_lay.setContentsMargins(48, 40, 48, 40)
        ic_lay.setSpacing(0)

        self.kart = QFrame()
        self.kart.setProperty("cssClass", "login_card")
        kart_lay = QVBoxLayout(self.kart)
        kart_lay.setContentsMargins(36, 32, 36, 32)
        kart_lay.setSpacing(0)

        kart_lay.addSpacing(8)

        baslik = QLabel("KütüphaneX")
        baslik.setFont(QFont("Segoe UI", 22, QFont.Bold))
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet(f"color: {RENKLER['accent']}; background: transparent; border: none;")
        kart_lay.addWidget(baslik)

        kart_lay.addSpacing(4)

        alt_baslik = QLabel("Hesabınıza giriş yapın")
        alt_baslik.setAlignment(Qt.AlignCenter)
        alt_baslik.setStyleSheet(f"color: {RENKLER['text_mute']}; background: transparent; border: none; font-size: 13px;")
        kart_lay.addWidget(alt_baslik)

        kart_lay.addSpacing(20)

        k_lbl = QLabel("Kullanıcı Adı")
        k_lbl.setAlignment(Qt.AlignLeft)
        k_lbl.setFixedHeight(20)
        k_lbl.setStyleSheet(f"color: {RENKLER['text_mute']}; background:transparent; border:none; font-size:12px; font-weight:600;")
        kart_lay.addWidget(k_lbl)

        kart_lay.addSpacing(4)

        self.k_adi = QLineEdit()
        self.k_adi.setPlaceholderText("kullanıcı adınız")
        self.k_adi.setFixedHeight(44)
        self.k_adi.setProperty("cssClass", "giris_input")
        
        # --- SADECE HARF GİRİŞİ KONTROLÜ BURADA ---
        self.k_adi.setValidator(QRegExpValidator(QRegExp("^[a-zA-ZğüşıöçĞÜŞİÖÇ]*$"), self))
        
        kart_lay.addWidget(self.k_adi)

        kart_lay.addSpacing(12)

        s_lbl = QLabel("Şifre")
        s_lbl.setAlignment(Qt.AlignLeft)
        s_lbl.setFixedHeight(20)
        s_lbl.setStyleSheet(f"color: {RENKLER['text_mute']}; background:transparent; border:none; font-size:12px; font-weight:600;")
        kart_lay.addWidget(s_lbl)

        kart_lay.addSpacing(4)

        self.sifre = QLineEdit()
        self.sifre.setPlaceholderText("şifreniz")
        self.sifre.setEchoMode(QLineEdit.Password)
        self.sifre.setFixedHeight(44)
        self.sifre.setProperty("cssClass", "giris_input")
        self.sifre.returnPressed.connect(self._giris_yap)
        kart_lay.addWidget(self.sifre)

        kart_lay.addSpacing(8)

        self.hata_lbl = QLabel("")
        self.hata_lbl.setStyleSheet(f"color: {RENKLER['accent3']}; background:transparent; border:none; font-size:12px;")
        self.hata_lbl.setAlignment(Qt.AlignCenter)
        self.hata_lbl.setFixedHeight(18)
        kart_lay.addWidget(self.hata_lbl)

        kart_lay.addSpacing(8)

        giris_btn = QPushButton("Giriş Yap")
        giris_btn.setFixedHeight(46)
        giris_btn.setStyleSheet(btn_style(RENKLER['accent']))
        giris_btn.setCursor(Qt.PointingHandCursor)
        giris_btn.clicked.connect(self._giris_yap)
        kart_lay.addWidget(giris_btn)

        kart_lay.addSpacing(16)

        sep_lay = QHBoxLayout()
        sep_lay.setAlignment(Qt.AlignVCenter)
        sep1 = QFrame(); sep1.setFixedHeight(1); sep1.setStyleSheet(f"background:{RENKLER['border']}; border:none;")
        
        sep_lbl = QLabel("veya")
        sep_lbl.setAlignment(Qt.AlignCenter)
        sep_lbl.setStyleSheet(f"color:{RENKLER['text_mute']}; background:transparent; border:none; font-size:12px; padding:0 8px;")
        
        sep2 = QFrame(); sep2.setFixedHeight(1); sep2.setStyleSheet(f"background:{RENKLER['border']}; border:none;")
        sep_lay.addWidget(sep1, 1); sep_lay.addWidget(sep_lbl); sep_lay.addWidget(sep2, 1)
        kart_lay.addLayout(sep_lay)

        kart_lay.addSpacing(16)

        kayit_btn = QPushButton("Yeni Hesap Oluştur")
        kayit_btn.setFixedHeight(44)
        kayit_btn.setProperty("cssClass", "btn_outline")
        kayit_btn.setCursor(Qt.PointingHandCursor)
        kayit_btn.clicked.connect(self._kayit_ac)
        kart_lay.addWidget(kayit_btn)

        ic_lay.addWidget(self.kart)

        alt = QHBoxLayout()
        alt.setAlignment(Qt.AlignVCenter)
        
        self.tema_btn2 = QPushButton("Tema")
        self.tema_btn2.setFixedSize(45, 36)
        self.tema_btn2.setProperty("cssClass", "btn_tema2")
        self.tema_btn2.setCursor(Qt.PointingHandCursor)
        self.tema_btn2.clicked.connect(self._tema_degistir)
        self.tema_btn2.setToolTip("Temayı değiştir")
        
        alt.addWidget(self.tema_btn2)
        alt.addStretch()
        ic_lay.addSpacing(16)
        ic_lay.addLayout(alt)

    def _giris_yap(self):
        k = self.k_adi.text().strip()
        s = self.sifre.text().strip()
        if not k or not s:
            self.hata_lbl.setText("Kullanıcı adı ve şifre gerekli.")
            return
        conn = get_conn()
        row = conn.execute(
            "SELECT kullanici_id, rol, ad_soyad, uye_id FROM kullanicilar WHERE kullanici_adi=? AND sifre=?",
            (k, s)
        ).fetchone()
        conn.close()
        if row:
            self.hata_lbl.setText("")
            self.giris_basarili.emit(row[1], row[0], row[2] or k)
        else:
            self.hata_lbl.setText("Kullanıcı adı veya şifre hatalı.")

    def _kayit_ac(self):
        dlg = KayitPenceresi(self)
        dlg.exec_()

    def _tema_degistir(self):
        tema_degistir(QApplication.instance())

    def _tema_yenile(self):
        self.setStyleSheet(genel_stil_olustur())
        self.bg.setStyleSheet(f"background-color: {RENKLER['bg']};")


# ───────────── Kayıt Penceresi ─────────────

class KayitPenceresi(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KütüphaneX — Kayıt Ol")
        self.setFixedSize(480, 580)
        self.setStyleSheet(genel_stil_olustur())
        self._ui()
        tema_kaydet(self._tema_yenile)

    def _ui(self):
        self.kart = QFrame(self)
        self.kart.setGeometry(0, 0, 480, 580)
        self.kart.setStyleSheet(f"background-color: {RENKLER['card']}; border-radius:0px;")
        lay = QVBoxLayout(self.kart)
        lay.setContentsMargins(40, 32, 40, 32)
        lay.setSpacing(0)

        baslik = QLabel("Yeni Hesap Oluştur")
        baslik.setFont(QFont("Segoe UI", 16, QFont.Bold))
        baslik.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(baslik)

        lay.addSpacing(4)

        alt = QLabel("Bilgilerini doldurarak üye ol")
        alt.setStyleSheet(f"color:{RENKLER['text_mute']}; background:transparent; border:none; font-size:12px;")
        lay.addWidget(alt)
        lay.addSpacing(16)

        def lbl(t):
            l = QLabel(t)
            l.setFixedHeight(18)
            l.setStyleSheet(f"color:{RENKLER['text_mute']}; background:transparent; border:none; font-size:12px; font-weight:600;")
            return l

        self.f_ad      = QLineEdit(); self.f_ad.setPlaceholderText("Adınız Soyadınız"); self.f_ad.setFixedHeight(40)
        # Sadece harf (Türkçe karakterler dahil) ve boşluk girişine izin veren kısıtlama
        self.f_ad.setValidator(QRegExpValidator(QRegExp("^[a-zA-ZğüşıöçĞÜŞİÖÇ\s]*$"), self))

        self.f_email   = QLineEdit(); self.f_email.setPlaceholderText("ornek@mail.com"); self.f_email.setFixedHeight(40)
        self.f_kadi    = QLineEdit(); self.f_kadi.setPlaceholderText("kullanici_adi"); self.f_kadi.setFixedHeight(40)
        self.f_sifre   = QLineEdit(); self.f_sifre.setPlaceholderText("en az 4 karakter")
        self.f_sifre.setEchoMode(QLineEdit.Password); self.f_sifre.setFixedHeight(40)
        self.f_sifre2  = QLineEdit(); self.f_sifre2.setPlaceholderText("şifreyi tekrar girin")
        self.f_sifre2.setEchoMode(QLineEdit.Password); self.f_sifre2.setFixedHeight(40)
        self.f_telefon = QLineEdit(); self.f_telefon.setPlaceholderText("05xxxxxxxxx"); self.f_telefon.setFixedHeight(40)
        self.f_telefon.setValidator(QRegExpValidator(QRegExp("^[0-9]*$"), self))
        self.f_telefon.setMaxLength(11) 

        form_alanlari = [(lbl("Ad Soyad *"), self.f_ad), (lbl("E-posta *"), self.f_email),
                         (lbl("Kullanıcı Adı *"), self.f_kadi), (lbl("Şifre *"), self.f_sifre),
                         (lbl("Şifre Tekrar *"), self.f_sifre2), (lbl("Telefon"), self.f_telefon)]
        for i, (l, w) in enumerate(form_alanlari):
            lay.addWidget(l)
            lay.addSpacing(4)
            w.setProperty("cssClass", "giris_input")
            lay.addWidget(w)
            if i < len(form_alanlari) - 1:
                lay.addSpacing(10)

        self.hata_lbl = QLabel("")
        self.hata_lbl.setStyleSheet(f"color:{RENKLER['accent3']}; background:transparent; border:none; font-size:12px;")
        self.hata_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.hata_lbl)

        btn_lay = QHBoxLayout()
        iptal = QPushButton("İptal")
        iptal.setFixedHeight(42)
        iptal.setProperty("cssClass", "btn_iptal")
        iptal.clicked.connect(self.reject)
        
        kayit = QPushButton("Kayıt Ol")
        kayit.setFixedHeight(42)
        kayit.setStyleSheet(btn_style(RENKLER['accent2']))
        kayit.setCursor(Qt.PointingHandCursor)
        kayit.clicked.connect(self._kayit_ol)
        
        btn_lay.addWidget(iptal); btn_lay.addWidget(kayit)
        lay.addLayout(btn_lay)

    def _kayit_ol(self):
        ad     = self.f_ad.text().strip()
        email  = self.f_email.text().strip()
        kadi   = self.f_kadi.text().strip()
        sifre  = self.f_sifre.text().strip()
        sifre2 = self.f_sifre2.text().strip()
        tel    = self.f_telefon.text().strip()

        if not all([ad, email, kadi, sifre]):
            self.hata_lbl.setText("Zorunlu alanları doldurun."); return
        
        if tel:
            if len(tel) != 11 or not tel.startswith("0"):
                self.hata_lbl.setText("Geçersiz telefon numarası. (11 haneli)"); return

        if len(sifre) < 4:
            self.hata_lbl.setText("Şifre en az 4 karakter olmalı."); return
        if sifre != sifre2:
            self.hata_lbl.setText("Şifreler uyuşmuyor."); return

        conn = get_conn()
        
        # 1. KONTROL: Kullanıcı adına göre çakışma var mı?
        mevcut_kullanici = conn.execute(
            "SELECT ad_soyad, email FROM kullanicilar WHERE kullanici_adi=?", (kadi,)
        ).fetchone()
        
        if mevcut_kullanici:
            # Kullanıcı adı alınmış ama alan kişi tamamen aynı isim ve e-postaya mı sahip?
            if mevcut_kullanici[0] == ad and mevcut_kullanici[1] == email:
                self.hata_lbl.setText("Üyeliğiniz var.")
            else:
                self.hata_lbl.setText("Bu kullanıcı adı alınmış.")
            conn.close()
            return
            
        # 2. KONTROL: E-postaya göre çakışma var mı?
        mevcut_uye = conn.execute(
            "SELECT ad, telefon FROM uyeler WHERE email=?", (email,)
        ).fetchone()
        
        if mevcut_uye:
            # E-posta kullanımda ama kişi yine aynı kişi mi? (Telefon boş girilmiş olsa bile esnek kontrol)
            if mevcut_uye[0] == ad and (not tel or mevcut_uye[1] == tel):
                self.hata_lbl.setText("Üyeliğiniz var.")
            else:
                self.hata_lbl.setText("Bu e-posta adresi kullanımda.")
            conn.close()
            return

        try:
            conn.execute(
                "INSERT INTO uyeler (ad, email, telefon, kayit_tarihi) VALUES (?,?,?,?)",
                (ad, email, tel, datetime.now().strftime("%Y-%m-%d"))
            )
            uye_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO kullanicilar (kullanici_adi, sifre, rol, uye_id, ad_soyad, email) VALUES (?,?,?,?,?,?)",
                (kadi, sifre, 'kullanici', uye_id, ad, email)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", f"Hesabınız oluşturuldu!\nKullanıcı adı: {kadi}")
            self.accept()
        except sqlite3.IntegrityError:
            conn.close()
            self.hata_lbl.setText("Kayıt sırasında bir hata oluştu.")

    def _tema_yenile(self):
        self.setStyleSheet(genel_stil_olustur())
        self.kart.setStyleSheet(f"background-color: {RENKLER['card']}; border-radius:0px;")

# ═══════════════════════════════════════════════════════════════════
# ────────────────── KULLANICI PANELİ ────────────────────────────────
# ═══════════════════════════════════════════════════════════════════

class KullaniciPaneli(QMainWindow):
    def __init__(self, kullanici_id, ad_soyad):
        super().__init__()
        self.kullanici_id = kullanici_id
        self.ad_soyad = ad_soyad
        conn = get_conn()
        row = conn.execute("SELECT uye_id FROM kullanicilar WHERE kullanici_id=?", (kullanici_id,)).fetchone()
        conn.close()
        self.uye_id = row[0] if row else None
        self.setWindowTitle(f"KütüphaneX — {ad_soyad}")
        self.setMinimumSize(1050, 680)
        self.resize(1150, 720)
        self.setStyleSheet(genel_stil_olustur())
        self._ui()
        tema_kaydet(self._tema_yenile)

    def _ui(self):
        ana = QWidget()
        self.setCentralWidget(ana)
        ana_lay = QHBoxLayout(ana)
        ana_lay.setContentsMargins(0, 0, 0, 0)
        ana_lay.setSpacing(0)

        self.sidebar = self._sidebar_olustur()
        ana_lay.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        ana_lay.addWidget(self.stack)

        self.u_anasayfa = UKullanicianaSayfa(self.uye_id, self.ad_soyad)
        self.u_kitaplar = UKitaplarSayfasi(self.uye_id)
        self.u_odunclerim = UOdunclerimSayfasi(self.uye_id)
        self.u_profil = UProfilSayfasi(self.kullanici_id, self.uye_id, self.ad_soyad)

        for s in [self.u_anasayfa, self.u_kitaplar, self.u_odunclerim, self.u_profil]:
            self.stack.addWidget(s)

        self.menu_butonlari[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    def _sidebar_olustur(self):
        frame = QFrame()
        frame.setFixedWidth(220)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['sidebar']};
                border-right: 1px solid {RENKLER['border']};
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 0, 12, 16)
        lay.setSpacing(2)

        logo_frame = QFrame()
        logo_frame.setFixedHeight(72)
        logo_frame.setStyleSheet("border:none; background:transparent;")
        lf = QHBoxLayout(logo_frame)
        li = QLabel("")
        li.setFont(QFont("Segoe UI Emoji", 20))
        li.setStyleSheet("background:transparent;")
        ly = QLabel("KütüphaneX"); ly.setFont(QFont("Segoe UI", 14, QFont.Bold))
        ly.setStyleSheet(f"color:{RENKLER['accent']}; background:transparent;")
        lf.addWidget(li); lf.addWidget(ly); lf.addStretch()
        lay.addWidget(logo_frame)

        kullanici_frame = QFrame()
        kullanici_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['selected']};
                border-radius: 10px;
                border: 1px solid {RENKLER['accent']}44;
            }}
        """)
        kf_lay = QVBoxLayout(kullanici_frame)
        kf_lay.setContentsMargins(12, 10, 12, 10)
        kf_lay.setSpacing(2)
        avatar = QLabel(self.ad_soyad)
        avatar.setFont(QFont("Segoe UI", 11, QFont.Bold))
        avatar.setStyleSheet("background:transparent; border:none;")
        rol_lbl = QLabel("Üye")
        rol_lbl.setStyleSheet(f"color:{RENKLER['accent2']}; background:transparent; border:none; font-size:11px;")
        kf_lay.addWidget(avatar)
        kf_lay.addWidget(rol_lbl)
        lay.addWidget(kullanici_frame)
        lay.addSpacing(8)

        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{RENKLER['border']}; border:none;")
        lay.addWidget(sep)
        lay.addSpacing(8)

        items = [("", "Ana Sayfa"), ("", "Kitap Kataloğu"),
                 ("", "Ödünçlerim"), ("", "Profilim")]
        self.menu_butonlari = []
        for i, (ikon, metin) in enumerate(items):
            btn = MenuButon(ikon, metin)
            btn.clicked.connect(lambda checked, idx=i: self._sayfa_degistir(idx))
            lay.addWidget(btn)
            self.menu_butonlari.append(btn)

        lay.addStretch()

        sep2 = QFrame(); sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background:{RENKLER['border']}; border:none;")
        lay.addWidget(sep2)
        lay.addSpacing(8)

        self.tema_btn_u = QPushButton(f"{RENKLER['tema_yazi']}")
        self.tema_btn_u.setFixedHeight(36)
        self.tema_btn_u.setCursor(Qt.PointingHandCursor)
        self.tema_btn_u.setProperty("cssClass", "tema_btn")
        self.tema_btn_u.clicked.connect(self._tema_degistir)
        lay.addWidget(self.tema_btn_u)

        cikis = QPushButton("Çıkış Yap")
        cikis.setFixedHeight(36)
        cikis.setCursor(Qt.PointingHandCursor)
        cikis.setProperty("cssClass", "cikis_btn")
        cikis.clicked.connect(self._cikis)
        lay.addWidget(cikis)
        return frame

    def _sayfa_degistir(self, idx):
        for i, btn in enumerate(self.menu_butonlari):
            btn.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)
        pages = [self.u_anasayfa, self.u_kitaplar, self.u_odunclerim, self.u_profil]
        if hasattr(pages[idx], 'yukle'):
            pages[idx].yukle()

    def _tema_degistir(self):
        tema_degistir(QApplication.instance())

    def _cikis(self):
        ret = QMessageBox.question(self, "Çıkış", "Oturumu kapatmak istiyor musunuz?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.close()
            from __main__ import _giris_ac
            _giris_ac()

    def _tema_yenile(self):
        self.setStyleSheet(genel_stil_olustur())
        self.tema_btn_u.setText(f"{RENKLER['tema_yazi']}")
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['sidebar']};
                border-right: 1px solid {RENKLER['border']};
            }}
        """)


# ── Kullanıcı: Ana Sayfa ──

class UKullanicianaSayfa(QWidget):
    def __init__(self, uye_id, ad_soyad):
        super().__init__()
        self.uye_id = uye_id
        self.ad_soyad = ad_soyad
        self._ui()

    def _ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        hos = QLabel(f"Hoş geldiniz, {self.ad_soyad}!")
        hos.setFont(QFont("Segoe UI", 20, QFont.Bold))
        hos.setStyleSheet("background:transparent;")
        lay.addWidget(hos)

        stat_lay = QHBoxLayout()
        stat_lay.setSpacing(16)
        self.k_aktif   = StatKart("Aktif Ödünç",  0, "accent",  "")
        self.k_toplam  = StatKart("Toplam Ödünç", 0, "accent2", "")
        self.k_gecikme = StatKart("Gecikmeli",     0, "accent3", "")
        for k in [self.k_aktif, self.k_toplam, self.k_gecikme]:
            stat_lay.addWidget(k)
        stat_lay.addStretch()
        lay.addLayout(stat_lay)

        frame = QFrame()
        frame.setProperty("cssClass", "card")
        fv = QVBoxLayout(frame)
        fv.setContentsMargins(16, 12, 16, 12)
        fv.setSpacing(10)
        b = QLabel("Aktif Ödünçlerim")
        b.setFont(QFont("Segoe UI", 13, QFont.Bold))
        b.setStyleSheet("background:transparent; border:none;")
        fv.addWidget(b)
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(4)
        self.tablo.setHorizontalHeaderLabels(["Kitap", "Yazar", "Ödünç Tarihi", "Son İade"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setSelectionMode(QTableWidget.NoSelection)
        self.tablo.verticalHeader().setVisible(False)
        fv.addWidget(self.tablo)
        lay.addWidget(frame)
        self.yukle()

    def yukle(self):
        if not self.uye_id:
            return
        conn = get_conn()
        bugun = datetime.now().strftime("%Y-%m-%d")
        aktif  = conn.execute("SELECT COUNT(*) FROM oduncler WHERE uye_id=? AND durum='Devam Ediyor'", (self.uye_id,)).fetchone()[0]
        toplam = conn.execute("SELECT COUNT(*) FROM oduncler WHERE uye_id=?", (self.uye_id,)).fetchone()[0]
        gecikme= conn.execute("SELECT COUNT(*) FROM oduncler WHERE uye_id=? AND durum='Devam Ediyor' AND iade_tarihi<?", (self.uye_id, bugun)).fetchone()[0]
        rows   = conn.execute("""
            SELECT k.ad, k.yazar, o.odunc_tarihi, o.iade_tarihi
            FROM oduncler o JOIN kitaplar k ON o.kitap_id=k.kitap_id
            WHERE o.uye_id=? AND o.durum='Devam Ediyor'
            ORDER BY o.odunc_id DESC
        """, (self.uye_id,)).fetchall()
        conn.close()
        self.k_aktif.guncelle(aktif)
        self.k_toplam.guncelle(toplam)
        self.k_gecikme.guncelle(gecikme)
        self.tablo.setRowCount(len(rows))
        for i, (kitap, yazar, od, iade) in enumerate(rows):
            self.tablo.setRowHeight(i, 44)
            gecikti = iade and iade < bugun
            for j, val in enumerate([kitap, yazar, od, iade or "-"]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if j == 3 and gecikti:
                    item.setForeground(QColor(RENKLER['accent3']))
                self.tablo.setItem(i, j, item)


# ── Kullanıcı: Kitap Kataloğu ──

class UKitaplarSayfasi(QWidget):
    def __init__(self, uye_id):
        super().__init__()
        self.uye_id = uye_id
        self._ui()

    def _ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        ust = QHBoxLayout()
        ust.addWidget(SectionBaslik("Kitap Kataloğu"))
        ust.addStretch()
        self.arama = AramaCubugu("Kitap veya yazar ara...")
        self.arama.setFixedWidth(260)
        self.arama.textChanged.connect(self.yukle)
        ust.addWidget(self.arama)
        self.kat_cb = QComboBox()
        self.kat_cb.addItems(["Tüm Kategoriler", "Roman", "Distopya", "Bilim Kurgu",
                               "Tarih", "Masal", "Kişisel Gelişim", "Klasik", "Çocuk", "Gastronomi", "Çizgi Roman", "Diğer"])
        self.kat_cb.setFixedWidth(150)
        self.kat_cb.currentIndexChanged.connect(self.yukle)
        ust.addWidget(self.kat_cb)
        lay.addLayout(ust)

        bilgi = QLabel("Sadece 'Mevcut' kitapları ödünç alabilirsiniz.")
        bilgi.setStyleSheet(f"color:{RENKLER['text_mute']}; font-size:12px; background:transparent;")
        lay.addWidget(bilgi)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(7)
        self.tablo.setHorizontalHeaderLabels(["Kitap Adı", "Yazar", "Kategori", "Yayınevi", "Yıl", "Durum", "İşlem"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed) # İşlem sütunu genişliği sabitlendi
        self.tablo.setColumnWidth(6, 110) # Butonun tam sığması için
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.verticalHeader().setVisible(False)
        lay.addWidget(self.tablo)
        self.yukle()

    def yukle(self):
        arama = self.arama.text().strip()
        kat   = self.kat_cb.currentText()
        q = "SELECT kitap_id,ad,yazar,kategori,yayinevi,yil,durum FROM kitaplar WHERE 1=1"
        params = []
        if arama:
            q += " AND (ad LIKE ? OR yazar LIKE ?)"; params += [f"%{arama}%", f"%{arama}%"]
        if kat != "Tüm Kategoriler":
            q += " AND kategori=?"; params.append(kat)
        conn = get_conn()
        rows = conn.execute(q, params).fetchall()
        conn.close()
        self.tablo.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.tablo.setRowHeight(i, 44)
            for j, val in enumerate(row[1:7]):
                item = QTableWidgetItem(str(val) if val else "-")
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if j == 5:
                    renk = RENKLER['accent2'] if val == "Mevcut" else RENKLER['warning']
                    item.setForeground(QColor(renk))
                    item.setFont(QFont("Segoe UI", 12, QFont.Bold))
                self.tablo.setItem(i, j, item)
            w = QWidget(); w.setStyleSheet(f"background:transparent;")
            wl = QHBoxLayout(w); wl.setContentsMargins(4,2,4,2)
            if row[6] == "Mevcut":
                ob = QPushButton("Ödünç Al")
                ob.setFixedHeight(28)
                ob.setStyleSheet(btn_style(RENKLER['accent2'], padding="2px 8px"))
                ob.clicked.connect(lambda _, kid=row[0]: self._odunc_al(kid))
                wl.addWidget(ob)
            else:
                lbl = QLabel("Ödünçte")
                lbl.setStyleSheet(f"color:{RENKLER['text_mute']}; background:transparent;")
                wl.addWidget(lbl)
            self.tablo.setCellWidget(i, 6, w)

    def _odunc_al(self, kitap_id):
        if not self.uye_id:
            QMessageBox.warning(self, "Hata", "Hesabınızla ilişkili üye kaydı bulunamadı!")
            return
        conn = get_conn()
        aktif = conn.execute("SELECT COUNT(*) FROM oduncler WHERE uye_id=? AND durum='Devam Ediyor'", (self.uye_id,)).fetchone()[0]
        kitap = conn.execute("SELECT ad,yazar FROM kitaplar WHERE kitap_id=?", (kitap_id,)).fetchone()
        conn.close()
        if aktif >= 3:
            QMessageBox.warning(self, "Limit", "En fazla 3 kitap aynı anda ödünç alabilirsiniz!"); return
        ret = QMessageBox.question(
            self, "Ödünç Al",
            f"'{kitap[0]}' kitabını ödünç almak istiyor musunuz?\n"
            f"(14 gün iade süresi)",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            today = datetime.now().strftime("%Y-%m-%d")
            iade  = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
            conn  = get_conn()
            conn.execute("INSERT INTO oduncler (kitap_id,uye_id,odunc_tarihi,iade_tarihi) VALUES (?,?,?,?)",
                         (kitap_id, self.uye_id, today, iade))
            conn.execute("UPDATE kitaplar SET durum='Ödünçte' WHERE kitap_id=?", (kitap_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", f"'{kitap[0]}' ödünç alındı!\nİade tarihi: {iade}")
            self.yukle()


# ── Kullanıcı: Ödünçlerim ──

class UOdunclerimSayfasi(QWidget):
    def __init__(self, uye_id):
        super().__init__()
        self.uye_id = uye_id
        self._ui()

    def _ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        ust = QHBoxLayout()
        ust.addWidget(SectionBaslik("Ödünçlerim"))
        ust.addStretch()
        self.filtre = QComboBox()
        self.filtre.addItems(["Tüm", "Devam Ediyor", "Tamamlandı"])
        self.filtre.setFixedWidth(150)
        self.filtre.currentIndexChanged.connect(self.yukle)
        ust.addWidget(self.filtre)
        lay.addLayout(ust)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(6)
        self.tablo.setHorizontalHeaderLabels(["Kitap", "Yazar", "Ödünç Tarihi", "Son İade", "Durum", "İşlem"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Sütun genişliğini sabitleyerek butonun ve metnin tam görünmesini sağlıyoruz:
        self.tablo.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.tablo.setColumnWidth(5, 110) 
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.verticalHeader().setVisible(False)
        lay.addWidget(self.tablo)
        self.yukle()

    def yukle(self):
        if not self.uye_id:
            return
        filtre = self.filtre.currentText()
        q = """SELECT o.odunc_id, k.ad, k.yazar, o.odunc_tarihi, o.iade_tarihi, o.durum, o.kitap_id
               FROM oduncler o JOIN kitaplar k ON o.kitap_id=k.kitap_id
               WHERE o.uye_id=?"""
        params = [self.uye_id]
        if filtre != "Tüm":
            q += " AND o.durum=?"; params.append(filtre)
        q += " ORDER BY o.odunc_id DESC"
        conn = get_conn()
        rows = conn.execute(q, params).fetchall()
        conn.close()
        bugun = datetime.now().strftime("%Y-%m-%d")
        self.tablo.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.tablo.setRowHeight(i, 44)
            gecikti = row[4] and row[4] < bugun and row[5] == "Devam Ediyor"
            for j, val in enumerate([row[1], row[2], row[3], row[4] or "-", row[5]]):
                item = QTableWidgetItem(str(val) if val else "-")
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if j == 4:
                    if gecikti:
                        item.setText("Gecikmiş")
                        item.setForeground(QColor(RENKLER['accent3']))
                    elif val == "Devam Ediyor":
                        item.setForeground(QColor(RENKLER['warning']))
                    else:
                        item.setForeground(QColor(RENKLER['accent2']))
                    item.setFont(QFont("Segoe UI", 12, QFont.Bold))
                self.tablo.setItem(i, j, item)
            w = QWidget(); w.setStyleSheet(f"background:transparent;")
            wl = QHBoxLayout(w); wl.setContentsMargins(4,2,4,2)
            if row[5] == "Devam Ediyor":
                ib = QPushButton("İade")
                ib.setFixedHeight(28)
                ib.setStyleSheet(btn_style(RENKLER['accent2'], padding="2px 8px"))
                ib.clicked.connect(lambda _, oid=row[0], kid=row[6]: self._iade(oid, kid))
                wl.addWidget(ib)
            else:
                lbl = QLabel("Tamamlandı")
                lbl.setStyleSheet(f"color:{RENKLER['text_mute']}; background:transparent;")
                wl.addWidget(lbl)
            self.tablo.setCellWidget(i, 5, w)

    def _iade(self, odunc_id, kitap_id):
        ret = QMessageBox.question(self, "İade", "Kitabı iade etmek istiyor musunuz?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            today = datetime.now().strftime("%Y-%m-%d")
            conn  = get_conn()
            conn.execute("UPDATE oduncler SET gercek_iade=?,durum='Tamamlandı' WHERE odunc_id=?", (today, odunc_id))
            conn.execute("UPDATE kitaplar SET durum='Mevcut' WHERE kitap_id=?", (kitap_id,))
            conn.commit(); conn.close()
            QMessageBox.information(self, "Başarılı", "Kitap iade edildi.")
            self.yukle()


# ── Kullanıcı: Profil ──

class UProfilSayfasi(QWidget):
    def __init__(self, kullanici_id, uye_id, ad_soyad):
        super().__init__()
        self.kullanici_id = kullanici_id
        self.uye_id = uye_id
        self.ad_soyad = ad_soyad
        self._ui()

    def _ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)
        lay.addWidget(SectionBaslik("Profilim"))

        kart = QFrame()
        kart.setProperty("cssClass", "card")
        kv = QVBoxLayout(kart)
        kv.setContentsMargins(24, 20, 24, 20)
        kv.setSpacing(14)

        baslik = QLabel(self.ad_soyad)
        baslik.setFont(QFont("Segoe UI", 16, QFont.Bold))
        baslik.setStyleSheet("background:transparent; border:none;")
        kv.addWidget(baslik)

        conn = get_conn()
        ku = conn.execute("SELECT kullanici_adi,email,kayit_tarihi FROM kullanicilar WHERE kullanici_id=?", (self.kullanici_id,)).fetchone()
        uy = conn.execute("SELECT telefon,adres FROM uyeler WHERE uye_id=?", (self.uye_id,)).fetchone() if self.uye_id else None
        conn.close()

        def bilgi_satir(etiket, deger):
            row = QHBoxLayout()
            e = QLabel(f"{etiket}:")
            e.setFixedWidth(140)
            e.setStyleSheet(f"color:{RENKLER['text_mute']}; background:transparent; border:none;")
            d = QLabel(deger or "-")
            d.setStyleSheet("background:transparent; border:none; font-weight:600;")
            row.addWidget(e); row.addWidget(d); row.addStretch()
            return row

        if ku:
            kv.addLayout(bilgi_satir("Kullanıcı Adı", ku[0]))
            kv.addLayout(bilgi_satir("E-posta", ku[1]))
            kv.addLayout(bilgi_satir("Kayıt Tarihi", ku[2]))
        if uy:
            kv.addLayout(bilgi_satir("Telefon", uy[0]))
            kv.addLayout(bilgi_satir("Adres", uy[1]))

        lay.addWidget(kart)

        sifre_kart = QFrame()
        sifre_kart.setProperty("cssClass", "card")
        sv = QVBoxLayout(sifre_kart)
        sv.setContentsMargins(24, 20, 24, 20)
        sv.setSpacing(12)
        
        sv.addWidget(self._blbl("Şifre Değiştir"))
        
        sf = QFormLayout(); sf.setSpacing(10)
        self.eski_s = QLineEdit(); self.eski_s.setEchoMode(QLineEdit.Password); self.eski_s.setPlaceholderText("Mevcut şifre")
        self.yeni_s = QLineEdit(); self.yeni_s.setEchoMode(QLineEdit.Password); self.yeni_s.setPlaceholderText("Yeni şifre")
        self.yeni_s2= QLineEdit(); self.yeni_s2.setEchoMode(QLineEdit.Password); self.yeni_s2.setPlaceholderText("Yeni şifre tekrar")
        for lbl_t, w in [("Mevcut Şifre", self.eski_s), ("Yeni Şifre", self.yeni_s), ("Tekrar", self.yeni_s2)]:
            l = QLabel(lbl_t); l.setStyleSheet(f"color:{RENKLER['text_mute']};")
            sf.addRow(l, w)
        sv.addLayout(sf)
        
        guncelle_btn = QPushButton("Şifreyi Güncelle")
        guncelle_btn.setStyleSheet(btn_style(RENKLER['accent']))
        guncelle_btn.setFixedWidth(200)
        guncelle_btn.clicked.connect(self._sifre_guncelle)
        sv.addWidget(guncelle_btn)
        
        lay.addWidget(sifre_kart)
        lay.addStretch()

    def _blbl(self, t):
        l = QLabel(t); l.setFont(QFont("Segoe UI", 13, QFont.Bold))
        l.setStyleSheet("background:transparent; border:none; padding-bottom:4px;")
        return l

    def _sifre_guncelle(self):
        eski = self.eski_s.text().strip()
        yeni = self.yeni_s.text().strip()
        yeni2= self.yeni_s2.text().strip()
        
        if not all([eski, yeni, yeni2]):
            QMessageBox.warning(self, "Hata", "Tüm alanları doldurun.")
            return
            
        if yeni != yeni2:
            QMessageBox.warning(self, "Hata", "Yeni şifreler uyuşmuyor.")
            return
            
        if len(yeni) < 4:
            QMessageBox.warning(self, "Hata", "Şifre en az 4 karakter olmalı.")
            return
            
        if eski == yeni:
            QMessageBox.warning(self, "Hata", "Yeni şifre mevcut şifreyle aynı olamaz.")
            return

        conn = get_conn()
        row = conn.execute("SELECT sifre FROM kullanicilar WHERE kullanici_id=?", (self.kullanici_id,)).fetchone()
        
        if not row or row[0] != eski:
            conn.close()
            QMessageBox.warning(self, "Hata", "Mevcut şifre yanlış.")
            return
            
        conn.execute("UPDATE kullanicilar SET sifre=? WHERE kullanici_id=?", (yeni, self.kullanici_id))
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "Başarılı", "Şifreniz güncellendi.")
        self.eski_s.clear()
        self.yeni_s.clear()
        self.yeni_s2.clear()

    def yukle(self):
        pass


# ═══════════════════════════════════════════════════════════════════
# ─────────────────────── UYGULAMA GİRİŞ NOKTASI ─────────────────────
# ═══════════════════════════════════════════════════════════════════

_aktif_pencere = None

def _giris_ac():
    global _aktif_pencere
    giris = GirisPenceresi()

    def _giris_basarili(rol, kullanici_id, ad_soyad):
        global _aktif_pencere
        giris.close()
        if rol == "admin":
            pencere = AnaPencere()
            pencere.setWindowTitle(f"KütüphaneX — Admin: {ad_soyad}")
        else:
            pencere = KullaniciPaneli(kullanici_id, ad_soyad)
        _aktif_pencere = pencere
        pencere.show()

    giris.giris_basarili.connect(_giris_basarili)
    _aktif_pencere = giris
    giris.show()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(genel_stil_olustur())
    _giris_ac()
    sys.exit(app.exec_())