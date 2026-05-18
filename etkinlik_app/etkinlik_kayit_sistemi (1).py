import sys
import sqlite3
import csv
import os
import urllib.request
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QHBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDateEdit,
    QSpinBox, QComboBox, QHeaderView, QGroupBox, QStatusBar,
    QDialog, QDialogButtonBox, QTextEdit, QFileDialog, QProgressBar,
    QFrame, QSplitter, QListWidget, QListWidgetItem, QAbstractItemView,
    QGridLayout, QStackedWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QDate, QSize, QRegExp, QRect
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette, QBrush, QRegExpValidator, QPixmap

# ─────────────────────────────────────────────
#  VERİ MODELLERİ
# ─────────────────────────────────────────────

class Katilimci:
    def __init__(self, katilimci_id, ad, email):
        self.katilimci_id = katilimci_id
        self.ad = ad
        self.email = email

class Etkinlik:
    def __init__(self, etkinlik_id, ad, kategori, tarih, kapasite):
        self.etkinlik_id = etkinlik_id
        self.ad = ad
        self.kategori = kategori
        self.tarih = tarih
        self.kapasite = kapasite

class Bilet:
    def __init__(self, bilet_id, etkinlik: Etkinlik, katilimci: Katilimci):
        self.bilet_id = bilet_id
        self.etkinlik = etkinlik
        self.katilimci = katilimci
        self.olusturma_tarihi = datetime.now().strftime("%Y-%m-%d %H:%M")


# ─────────────────────────────────────────────
#  VERİTABANI YÖNETİCİSİ
# ─────────────────────────────────────────────

class VeritabaniYoneticisi:
    def __init__(self, db_yolu="etkinlikapp_sunum.db"):
        self.baglanti = sqlite3.connect(db_yolu)
        self.baglanti.row_factory = sqlite3.Row
        self._tablolari_olustur()

    def _tablolari_olustur(self):
        cur = self.baglanti.cursor()
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT NOT NULL UNIQUE,
            sifre TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'üye'
        )
        """)
        
        if cur.execute("SELECT COUNT(*) FROM kullanicilar").fetchone()[0] == 0:
            cur.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES ('admin', '1234', 'admin')")

        cur.executescript("""
        CREATE TABLE IF NOT EXISTS etkinlikler (
            etkinlik_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad          TEXT NOT NULL,
            kategori    TEXT NOT NULL DEFAULT 'Sinema',
            tarih       TEXT NOT NULL,
            kapasite    INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS katilimcilar (
            katilimci_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad           TEXT NOT NULL,
            email        TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS biletler (
            bilet_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            etkinlik_id  INTEGER NOT NULL,
            katilimci_id INTEGER NOT NULL,
            tur          TEXT DEFAULT 'Standart',
            fiyat        INTEGER DEFAULT 0,
            koltuk       TEXT DEFAULT '-',
            olusturma_tarihi TEXT NOT NULL,
            FOREIGN KEY (etkinlik_id)  REFERENCES etkinlikler(etkinlik_id),
            FOREIGN KEY (katilimci_id) REFERENCES katilimcilar(katilimci_id)
        );
        """)
        
        kayit_sayisi = cur.execute("SELECT COUNT(*) FROM etkinlikler").fetchone()[0]
        if kayit_sayisi == 0:
            ornek_etkinlikler = [
                ("Spider-Man: Beyond the Spider-Verse", "Sinema", "2026-07-15", 100),
                ("The Batman - Part II", "Sinema", "2026-10-02", 100),
                ("Mortal Kombat 2", "Sinema", "2026-10-24", 100),
                ("Star Wars: Mandalorian ve Grogu", "Sinema", "2026-05-22", 100),
                ("Dolu Kadehi Ters Tut Konseri", "Konser", "2026-08-10", 500),
                ("maNga 20. Yıl Turnesi", "Konser", "2026-08-15", 500), 
                ("Manifest Yaz Festivali", "Konser", "2026-09-01", 1000),
                ("Edis Sahne Performansı", "Konser", "2026-09-20", 800),
                ("Adana Lezzet Festivali", "Türkiyeden Günler", "2026-10-05", 300),
                ("Gaziantep Gastronomi Festivali", "Türkiyeden Günler", "2026-09-12", 400),
                ("Hatay Yöresel Yemek Günleri", "Türkiyeden Günler", "2026-11-20", 350),
                ("Trabzon Lezzet Günleri", "Türkiyeden Günler", "2026-08-25", 250)
            ]
            cur.executemany("INSERT INTO etkinlikler (ad, kategori, tarih, kapasite) VALUES (?,?,?,?)", ornek_etkinlikler)

        katilimci_sayisi = cur.execute("SELECT COUNT(*) FROM katilimcilar").fetchone()[0]
        if katilimci_sayisi == 0:
            ornek_katilimcilar = [(f"Katılımcı {i}", f"kullanici{i}@mail.com") for i in range(1, 21)]
            cur.executemany("INSERT INTO katilimcilar (ad, email) VALUES (?,?)", ornek_katilimcilar)

        self.baglanti.commit()

    def kullanici_kontrol(self, k_adi, sifre):
        return self.baglanti.execute("SELECT id, rol FROM kullanicilar WHERE kullanici_adi=? AND sifre=?", (k_adi, sifre)).fetchone()

    def kullanici_ekle(self, k_adi, sifre, rol="üye"):
        try:
            self.baglanti.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?,?,?)", (k_adi, sifre, rol))
            self.baglanti.execute("INSERT INTO katilimcilar (ad, email) VALUES (?,?)", (k_adi, f"{k_adi}@mail.com"))
            self.baglanti.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def etkinlik_ekle(self, ad, kategori, tarih, kapasite):
        cur = self.baglanti.cursor()
        cur.execute("INSERT INTO etkinlikler (ad, kategori, tarih, kapasite) VALUES (?,?,?,?)", (ad, kategori, tarih, kapasite))
        self.baglanti.commit()
        return cur.lastrowid

    def etkinlikleri_getir(self):
        return self.baglanti.execute("SELECT * FROM etkinlikler ORDER BY tarih").fetchall()
        
    def etkinlik_getir_id(self, eid):
        return self.baglanti.execute("SELECT * FROM etkinlikler WHERE etkinlik_id=?", (eid,)).fetchone()

    def etkinlik_sil(self, etkinlik_id):
        self.baglanti.execute("DELETE FROM biletler WHERE etkinlik_id=?", (etkinlik_id,))
        self.baglanti.execute("DELETE FROM etkinlikler WHERE etkinlik_id=?", (etkinlik_id,))
        self.baglanti.commit()

    def katilimci_ekle(self, ad, email):
        try:
            cur = self.baglanti.cursor()
            cur.execute("INSERT INTO katilimcilar (ad, email) VALUES (?,?)", (ad, email))
            self.baglanti.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def katilimcilari_getir(self):
        return self.baglanti.execute("SELECT * FROM katilimcilar ORDER BY ad").fetchall()

    def katilimci_sil(self, katilimci_id):
        self.baglanti.execute("DELETE FROM biletler WHERE katilimci_id=?", (katilimci_id,))
        self.baglanti.execute("DELETE FROM katilimcilar WHERE katilimci_id=?", (katilimci_id,))
        self.baglanti.commit()

    def dolu_koltuklari_getir(self, etkinlik_id, tur_kodu=None):
        if tur_kodu:
            sorgu_kodu = tur_kodu + "%"
            sonuclar = self.baglanti.execute("SELECT koltuk FROM biletler WHERE etkinlik_id=? AND tur LIKE ? AND koltuk != '-'", (etkinlik_id, sorgu_kodu)).fetchall()
        else:
            sonuclar = self.baglanti.execute("SELECT koltuk FROM biletler WHERE etkinlik_id=? AND koltuk != '-'", (etkinlik_id,)).fetchall()
        return [row["koltuk"] for row in sonuclar if row["koltuk"]]

    def bilet_olustur(self, etkinlik_id, katilimci_id, tur="Standart", fiyat=0, koltuk="-"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cur = self.baglanti.cursor()
        cur.execute(
            "INSERT INTO biletler (etkinlik_id, katilimci_id, tur, fiyat, koltuk, olusturma_tarihi) VALUES (?,?,?,?,?,?)",
            (etkinlik_id, katilimci_id, tur, fiyat, koltuk, now))
        self.baglanti.commit()
        return cur.lastrowid, "OK"

    def biletleri_getir(self, etkinlik_id=None):
        q = """SELECT b.bilet_id, e.ad AS etkinlik, k.ad AS katilimci,
                      k.email, b.tur, b.fiyat, b.koltuk, b.olusturma_tarihi, e.tarih
               FROM biletler b
               JOIN etkinlikler e ON b.etkinlik_id = e.etkinlik_id
               JOIN katilimcilar k ON b.katilimci_id = k.katilimci_id"""
        if etkinlik_id:
            return self.baglanti.execute(q + " WHERE b.etkinlik_id=?", (etkinlik_id,)).fetchall()
        return self.baglanti.execute(q + " ORDER BY b.olusturma_tarihi DESC").fetchall()

    def bilet_iptal(self, bilet_id):
        self.baglanti.execute("DELETE FROM biletler WHERE bilet_id=?", (bilet_id,))
        self.baglanti.commit()

    def katilimci_raporu(self):
        return self.baglanti.execute("""
            SELECT e.ad, e.tarih, e.kapasite,
                   COUNT(b.bilet_id) AS kayitli,
                   e.kapasite - COUNT(b.bilet_id) AS bos
            FROM etkinlikler e
            LEFT JOIN biletler b ON e.etkinlik_id = b.etkinlik_id
            GROUP BY e.etkinlik_id
            ORDER BY e.tarih
        """).fetchall()


# ─────────────────────────────────────────────
#  RENK VE STİL (EtkinlikApp MOR TEMA)
# ─────────────────────────────────────────────

KOYU    = "#0f172a" 
PANEL   = "#1e293b" 
KART    = "#334155"
VURGU   = "#8b5cf6" 
BEYAZ   = "#f8fafc"
GRI     = "#94a3b8"
KIRMIZI = "#ef4444"
TURUNCU = "#f59e0b"
YESIL   = "#10b981" 

STIL = f"""
QMainWindow, QWidget {{
    background-color: {KOYU};
    color: {BEYAZ};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}
QTabWidget::pane {{ border: 1px solid {VURGU}; background: {PANEL}; border-radius: 6px; top: -1px; }}
QTabBar::tab {{ background: {KART}; color: {GRI}; padding: 10px 15px; min-width: 170px; border-radius: 6px 6px 0 0; margin-right: 4px; font-weight: bold; font-size: 14px; text-align: center; }}
QTabBar::tab:selected {{ background: {VURGU}; color: white; }}
QGroupBox {{ border: 1px solid {VURGU}; border-radius: 8px; margin-top: 25px; padding: 15px 10px 10px 10px; font-weight: bold; color: {VURGU}; }}
QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 15px; top: 0px; padding: 0 5px; }}
QLineEdit, QSpinBox, QDateEdit, QComboBox {{ background: {KOYU}; border: 1px solid {KART}; border-radius: 6px; padding: 10px 14px; color: {BEYAZ}; font-size: 14px; }}
QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QComboBox:focus {{ border: 1px solid {VURGU}; }}
QPushButton {{ background: {VURGU}; color: white; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; font-size: 13px; min-width: 100px; }}
QPushButton:hover {{ background: #7c3aed; }}
QPushButton:disabled {{ background: {KART}; color: {GRI}; }}
QPushButton#yesilBtn {{ background: {VURGU}; color: white; }}
QPushButton#silBtn {{ background: {KIRMIZI}; }}
QPushButton#silBtn:hover {{ background: #dc2626; }}
QTableWidget {{ background: {PANEL}; border: 1px solid {GRI}; border-radius: 6px; gridline-color: {KART}; color: {BEYAZ}; }}
QTableWidget::item:selected {{ background: {VURGU}; color: white; }}
QHeaderView::section {{ background: {KART}; color: {VURGU}; font-weight: bold; padding: 8px; border: none; }}
QScrollBar:vertical {{ background: {KOYU}; width: 12px; margin: 0px; }}
QScrollBar::handle:vertical {{ background: {KART}; min-height: 20px; border-radius: 6px; }}
QProgressBar {{ border: 1px solid {GRI}; border-radius: 5px; background: {KART}; text-align: center; color: white; font-weight: bold; height: 18px; }}
QProgressBar::chunk {{ background: {VURGU}; border-radius: 4px; }}
QStatusBar {{ background: {KART}; color: {GRI}; }}
"""

def tablo_satir_ekle(tablo: QTableWidget, veriler: list, renkler=None):
    tablo.insertRow(tablo.rowCount())
    r = tablo.rowCount() - 1
    for c, v in enumerate(veriler):
        item = QTableWidgetItem(str(v))
        item.setTextAlignment(Qt.AlignCenter)
        if renkler and c in renkler:
            item.setForeground(QColor(renkler[c]))
        tablo.setItem(r, c, item)

def adim_header_olustur(aktif_adim):
    header = QFrame()
    header.setFixedHeight(80)
    header.setStyleSheet(f"background: {KOYU}; border-bottom: 2px solid {PANEL};")
    hl = QHBoxLayout(header)
    hl.setContentsMargins(40, 0, 40, 0)
    
    adims = [(1, "Seans Seç"), (2, "Koltuk Seçimi"), (3, "Ödeme")]
    for n, t in adims:
        container = QWidget()
        cl = QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(10)
        
        lbl_num = QLabel(str(n))
        lbl_num.setFixedSize(36, 36)
        lbl_num.setAlignment(Qt.AlignCenter)
        lbl_text = QLabel(t)
        
        if n == aktif_adim:
            lbl_num.setStyleSheet(f"border: 2px solid {VURGU}; border-radius: 18px; color: {VURGU}; font-size: 16px; font-weight: bold; background: transparent;")
            lbl_text.setStyleSheet(f"color: white; font-size: 16px; font-weight: bold;")
        else:
            lbl_num.setStyleSheet(f"border: 2px solid {GRI}; border-radius: 18px; color: {GRI}; font-size: 16px; font-weight: bold; background: transparent;")
            lbl_text.setStyleSheet(f"color: {GRI}; font-size: 16px; font-weight: bold;")
            
        cl.addWidget(lbl_num)
        cl.addWidget(lbl_text)
        hl.addWidget(container)
        
        if n != 3:
            hl.addStretch()
            
    return header


# ─────────────────────────────────────────────
#  GİRİŞ EKRANI VE KAYIT
# ─────────────────────────────────────────────

class KayitDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Yeni Üye Kaydı")
        self.setFixedSize(380, 300)
        self.setStyleSheet(STIL)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)

        baslik = QLabel("Yeni Üye Hesabı Oluştur")
        baslik.setStyleSheet(f"font-size:18px; font-weight:bold; color:{VURGU};")
        baslik.setAlignment(Qt.AlignCenter)
        layout.addWidget(baslik)
        layout.addSpacing(10)

        self.k_adi = QLineEdit(); self.k_adi.setPlaceholderText("Kullanıcı Adı")
        self.sifre = QLineEdit(); self.sifre.setPlaceholderText("Şifre"); self.sifre.setEchoMode(QLineEdit.Password)
        self.sifre_tekrar = QLineEdit(); self.sifre_tekrar.setPlaceholderText("Şifre (Tekrar)"); self.sifre_tekrar.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.k_adi); layout.addWidget(self.sifre); layout.addWidget(self.sifre_tekrar)
        
        self.btn_onay = QPushButton("Hesabı Oluştur")
        self.btn_onay.clicked.connect(self.kayit_islemi)
        layout.addWidget(self.btn_onay)

    def kayit_islemi(self):
        ka = self.k_adi.text().strip(); s1 = self.sifre.text().strip(); s2 = self.sifre_tekrar.text().strip()
        if not ka or not s1: return QMessageBox.warning(self, "Uyarı", "Kullanıcı adı ve şifre boş bırakılamaz.")
        if s1 != s2: return QMessageBox.warning(self, "Hata", "Şifreler birbiriyle uyuşmuyor!")
        
        if self.db.kullanici_ekle(ka, s1, "üye"):
            QMessageBox.information(self, "Başarılı", "Kayıt başarıyla tamamlandı. Otomatik giriş yapılıyor...")
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Bu kullanıcı adı zaten sistemde kayıtlı!")

class KullaniciGiris(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db; self.rol = None  
        self.setWindowTitle("EtkinlikApp Giriş")
        self.setFixedSize(550, 400) 
        self.setStyleSheet(STIL)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.bg_frame = QFrame()
        bg_layout = QVBoxLayout(self.bg_frame)
        bg_layout.setAlignment(Qt.AlignCenter)
        
        self.icerik_frame = QFrame()
        self.icerik_frame.setFixedSize(380, 280)
        self.icerik_frame.setStyleSheet(f"background-color: {PANEL}; border-radius: 15px;")
        
        icerik_layout = QVBoxLayout(self.icerik_frame)
        baslik = QLabel("EtkinlikApp'e Hoşgeldiniz")
        baslik.setStyleSheet(f"font-size:22px; font-weight:bold; color:{VURGU};")
        baslik.setAlignment(Qt.AlignCenter)

        self.kullanici_adi = QLineEdit(); self.kullanici_adi.setPlaceholderText("Kullanıcı Adı")
        self.sifre = QLineEdit(); self.sifre.setPlaceholderText("Şifre"); self.sifre.setEchoMode(QLineEdit.Password)

        icerik_layout.addWidget(baslik); icerik_layout.addWidget(self.kullanici_adi); icerik_layout.addWidget(self.sifre)

        btn_layout = QHBoxLayout()
        self.kayit_btn = QPushButton("Kayıt Ol (Üye)"); self.kayit_btn.setStyleSheet(f"background: {KART}; border: 1px solid {VURGU};")
        self.kayit_btn.clicked.connect(self.kayit_ekrani_ac)
        self.giris_btn = QPushButton("Giriş Yap")
        self.giris_btn.clicked.connect(self.kontrol_et)

        btn_layout.addWidget(self.kayit_btn); btn_layout.addWidget(self.giris_btn)
        icerik_layout.addLayout(btn_layout)
        bg_layout.addWidget(self.icerik_frame)
        main_layout.addWidget(self.bg_frame)

    def kontrol_et(self):
        kullanici = self.db.kullanici_kontrol(self.kullanici_adi.text().strip(), self.sifre.text().strip())
        if kullanici:
            self.rol = kullanici["rol"]  
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Hatalı kullanıcı adı veya şifre!")

    def kayit_ekrani_ac(self):
        kayit_penceresi = KayitDialog(self.db, self)
        if kayit_penceresi.exec_() == QDialog.Accepted:
            self.kullanici_adi.setText(kayit_penceresi.k_adi.text().strip())
            self.sifre.setText(kayit_penceresi.sifre.text().strip())
            self.kontrol_et()


# ─────────────────────────────────────────────
#  YATAY KONSER KARTI (GÖRSEL SOLDA, TARİHLER SAĞDA)
# ─────────────────────────────────────────────

class YatayKonserKarti(QFrame):
    def __init__(self, grup_adi, etkinlikler, satin_al_cb):
        super().__init__()
        self.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        self.setMinimumHeight(240)
        self.setMaximumWidth(900)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 25, 0)
        layout.setSpacing(25)
        
        dosya_kok = ""
        grup_lower = grup_adi.lower()
        if "dktt" in grup_lower or "dolu kadehi" in grup_lower: dosya_kok = "dktt"
        elif "manga" in grup_lower: dosya_kok = "manga"
        elif "manifest" in grup_lower: dosya_kok = "manifest"
        elif "edis" in grup_lower: dosya_kok = "edis"
        
        tam_yol = ""
        if dosya_kok:
            try: base_dir = os.path.dirname(os.path.abspath(__file__))
            except NameError: base_dir = os.getcwd()
            for uzanti in [".png", ".jpg", ".jpeg", ".PNG", ".JPG"]:
                olasi_yol = os.path.join(base_dir, dosya_kok + uzanti)
                if os.path.exists(olasi_yol):
                    tam_yol = olasi_yol
                    break
        
        afis_lbl = QLabel()
        afis_lbl.setFixedSize(220, 240)
        
        if tam_yol:
            orijinal_pix = QPixmap(tam_yol)
            scaled_pix = orijinal_pix.scaled(220, 240, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            
            x_offset = (scaled_pix.width() - 220) // 2
            y_offset = (scaled_pix.height() - 240) // 2
            crop_rect = QRect(x_offset, y_offset, 220, 240)
            cropped_pix = scaled_pix.copy(crop_rect)
            
            afis_lbl.setPixmap(cropped_pix)
            afis_lbl.setStyleSheet("border-radius: 12px 0 0 12px; border: none;")
        else:
            afis_lbl.setText("Görsel Yok\nKlasöre '.png' veya '.jpg'\nolarak yüklenmeli")
            afis_lbl.setAlignment(Qt.AlignCenter)
            afis_lbl.setStyleSheet(f"background: {KART}; color: {BEYAZ}; border-radius: 12px 0 0 12px; font-size:11px; border:none;")
            
        layout.addWidget(afis_lbl)
        
        right_widget = QWidget()
        right_widget.setStyleSheet("border: none; background: transparent;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 25, 10, 25)
        
        baslik = QLabel(grup_adi)
        baslik.setStyleSheet("font-weight: 900; font-size: 22px; color: #0f172a; border: none;")
        right_layout.addWidget(baslik)
        
        cizgi = QFrame()
        cizgi.setFrameShape(QFrame.HLine)
        cizgi.setStyleSheet("background-color: #e2e8f0; margin: 10px 0;")
        right_layout.addWidget(cizgi)
        
        for e in etkinlikler:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(15)
            
            try:
                t_obj = datetime.strptime(e['tarih'], "%Y-%m-%d")
                aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
                gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
                tarih_metni = f"{t_obj.day} {aylar[t_obj.month-1]} {t_obj.year} - {gunler[t_obj.weekday()]}"
            except:
                tarih_metni = e['tarih']
                
            tarih_lbl = QLabel(tarih_metni)
            tarih_lbl.setStyleSheet("font-size: 15px; color: #475569; font-weight: bold; border: none;")
            row_layout.addWidget(tarih_lbl)
            
            row_layout.addStretch()
            
            btn = QPushButton("Biletler")
            btn.setFixedSize(110, 40)
            btn.setStyleSheet("background: #10b981; color: white; border-radius: 20px; font-weight: 800; font-size: 14px; border: none;")
            btn.clicked.connect(lambda ch, eid=e['etkinlik_id'], ad=e['ad']: satin_al_cb(eid, ad))
            row_layout.addWidget(btn)
            
            right_layout.addLayout(row_layout)
            
        right_layout.addStretch()
        layout.addWidget(right_widget, 1)


# ─────────────────────────────────────────────
#  EtkinlikApp GÖMÜLÜ SİNEMA PORTALI (WIDGET)
# ─────────────────────────────────────────────

class FilmKartiSinema(QWidget):
    def __init__(self, ad, tarih):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        dosya_kok = ""
        ad_lower = ad.lower()
        if "spider-man" in ad_lower: dosya_kok = "spiderman"
        elif "batman" in ad_lower: dosya_kok = "batman2"
        elif "mortal kombat" in ad_lower: dosya_kok = "mortal kombat 2"
        elif "mandalorian" in ad_lower: dosya_kok = "mandalorian"
        
        tam_yol = ""
        if dosya_kok:
            try: base_dir = os.path.dirname(os.path.abspath(__file__))
            except NameError: base_dir = os.getcwd()
            for uzanti in [".jpg", ".jpeg", ".png", ".JPG", ".PNG"]:
                olasi_yol = os.path.join(base_dir, dosya_kok + uzanti)
                if os.path.exists(olasi_yol):
                    tam_yol = olasi_yol
                    break
        
        self.afis = QLabel()
        self.afis.setFixedSize(70, 100)
        self.afis.setAlignment(Qt.AlignCenter)
        
        if tam_yol:
            pix = QPixmap(tam_yol).scaled(70, 100, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.afis.setPixmap(pix)
            self.afis.setStyleSheet("border-radius: 5px;")
        else:
            self.afis.setText("Afiş\nBekleniyor")
            self.afis.setStyleSheet(f"background: {KOYU}; border-radius: 5px; color: {GRI}; font-size: 10px;")
        
        bilgi = QVBoxLayout()
        self.t = QLabel(ad)
        self.t.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        self.t.setWordWrap(True)
        self.d = QLabel(f"Vizyon: {tarih}"); self.d.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        bilgi.addWidget(self.t); bilgi.addWidget(self.d); bilgi.addStretch()
        
        layout.addWidget(self.afis); layout.addLayout(bilgi)
        self.setStyleSheet("background: transparent; margin: 2px;") 

class SinemaPortaliWidget(QWidget):
    def __init__(self, db, guncelle_cb, parent=None):
        super().__init__(parent)
        self.db = db
        self.guncelle_cb = guncelle_cb
        
        self.secili_eid = None
        self.secilen_salon = None
        self.secilen_seans = None
        self.secilen_tarih = "Bugün"
        self.tarih_butonlari = []
        self.secilen_koltuklar = []
        self.fiyat_tam = 0
        self.fiyat_ogr = 0
        self.fiyat_carpan = 1
        
        self.sehir_salon_haritasi = {
            "İstanbul Avrupa": ["EtkinlikApp Zorlu", "EtkinlikApp Cevahir", "EtkinlikApp Kanyon", "EtkinlikApp Forum"],
            "İstanbul Anadolu": ["EtkinlikApp Akasya", "EtkinlikApp Palladium", "EtkinlikApp Meydan"],
            "Ankara": ["EtkinlikApp Ankamall", "EtkinlikApp Panora", "EtkinlikApp Cepa"],
            "İzmir": ["EtkinlikApp Optimum", "EtkinlikApp İstinyePark", "EtkinlikApp Agora"]
        }
        
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(0, 0, 0, 0)
        ana_layout.setSpacing(0)
        
        self.header_area = QWidget()
        self.header_layout = QVBoxLayout(self.header_area)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        ana_layout.addWidget(self.header_area)
        
        self.stack = QStackedWidget()
        
        self.sayfa_seans = QWidget()
        self.sayfa_koltuk = QWidget()
        self.sayfa_odeme = QWidget()
        
        self.stack.addWidget(self.sayfa_seans)
        self.stack.addWidget(self.sayfa_koltuk)
        self.stack.addWidget(self.sayfa_odeme)
        
        ana_layout.addWidget(self.stack)
        
        self._sayfa1_seans_kur()
        self._sayfa2_koltuk_kur()
        self._sayfa3_odeme_kur()
        
        self._adim_guncelle(1)
        self.stack.currentChanged.connect(self._butonlari_denetle)

    def _adim_guncelle(self, adim):
        for i in reversed(range(self.header_layout.count())): 
            widget = self.header_layout.itemAt(i).widget()
            if widget: widget.deleteLater()
            
        self.header_layout.addWidget(adim_header_olustur(adim))
        self._butonlari_denetle()

    def _butonlari_denetle(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            if hasattr(self, 'btn_seans_devam') and self.btn_seans_devam:
                self.btn_seans_devam.setEnabled(self.secilen_seans is not None)
        elif idx == 1:
            if hasattr(self, 'btn_koltuk_devam') and self.btn_koltuk_devam:
                self.btn_koltuk_devam.setEnabled(len(self.secilen_koltuklar) > 0)

    def _ileri_git(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            self._koltuk_sayfasina_gec()
        elif idx == 1:
            self._odeme_sayfasina_gec()

    # ─── SAYFA 1: SEANS SEÇİMİ ───
    def _sayfa1_seans_kur(self):
        icerik = QHBoxLayout(self.sayfa_seans); icerik.setContentsMargins(20, 20, 20, 20); icerik.setSpacing(20)
        
        s1 = QFrame(); s1.setStyleSheet(f"background: {PANEL}; border-radius: 15px;"); l1 = QVBoxLayout(s1)
        l1.addWidget(QLabel("<b style='font-size:16px;'>Film Seçimi</b>"))
        self.film_list = QListWidget(); self.film_list.setStyleSheet(f"QListWidget {{ background: transparent; border: none; outline:none; }} QListWidget::item:selected {{ background: {VURGU}; border-radius: 10px; }}")
        l1.addWidget(self.film_list); icerik.addWidget(s1, 1)

        s2 = QFrame(); s2.setStyleSheet(f"background: {PANEL}; border-radius: 15px;"); l2 = QVBoxLayout(s2)
        l2.addWidget(QLabel("<b style='font-size:16px;'>Sinema Seçimi</b>"))
        
        filtre_layout = QHBoxLayout()
        self.sehir_cb = QComboBox()
        self.sehir_cb.addItems(list(self.sehir_salon_haritasi.keys()))
        self.format_cb = QComboBox()
        self.format_cb.addItems(["Standart", "GOLD CLASS", "IMAX", "4DX", "ScreenX"])
        filtre_layout.addWidget(self.sehir_cb); filtre_layout.addWidget(self.format_cb)
        l2.addLayout(filtre_layout)

        self.salon_list = QListWidget(); self.salon_list.setStyleSheet(f"QListWidget::item {{ background: white; color: black; border-radius: 8px; margin-bottom: 8px; padding: 15px; font-weight: bold; font-size:14px; }} QListWidget::item:selected {{ background: {VURGU}; color: white; }}")
        l2.addWidget(self.salon_list); icerik.addWidget(s2, 1)

        s3 = QFrame(); s3.setStyleSheet(f"background: {PANEL}; border-radius: 15px;"); l3 = QVBoxLayout(s3)
        l3.addWidget(QLabel("<b style='font-size:16px;'>Tarih ve Seans Seçimi</b>"))
        
        tarih_layout = QHBoxLayout()
        for t in ["Bugün", "Yarın", "Pazar"]:
            btn = QPushButton(t)
            btn.setStyleSheet(f"background: {BEYAZ}; color: black; border-radius: 4px; padding: 10px; font-weight:bold;")
            if t == "Bugün":
                btn.setStyleSheet(f"background: {VURGU}; color: white; border-radius: 4px; padding: 10px; font-weight:bold;")
            btn.clicked.connect(lambda checked, text=t, b=btn: self._tarih_secildi(text, b))
            tarih_layout.addWidget(btn)
            self.tarih_butonlari.append(btn)
        l3.addLayout(tarih_layout)

        l3.addSpacing(15)
        self.seans_lbl = QLabel("Önce Film ve Salon Seçiniz")
        self.seans_lbl.setStyleSheet(f"color: {GRI}; font-size:14px;")
        l3.addWidget(self.seans_lbl)

        self.seans_grid = QGridLayout(); self.seans_btns = []
        l3.addLayout(self.seans_grid); l3.addStretch()
        
        # ── MOR KUTU (DEVAM ET BUTONU) ──
        self.seans_kutu = QFrame()
        self.seans_kutu.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(139, 92, 246, 0.15); 
                border: 2px solid {VURGU}; 
                border-radius: 12px;
            }}
        """)
        sk_lay = QVBoxLayout(self.seans_kutu)
        sk_lay.setContentsMargins(15, 15, 15, 15)
        
        self.btn_seans_devam = QPushButton("Devam Et (Koltuk Seçimi)")
        self.btn_seans_devam.setFixedHeight(50)
        self.btn_seans_devam.setEnabled(False)
        self.btn_seans_devam.setStyleSheet(f"""
            QPushButton {{ background-color: {VURGU}; color: white; border-radius: 8px; font-size: 15px; font-weight: bold; border: none; }}
            QPushButton:disabled {{ background-color: {KART}; color: {GRI}; }}
        """)
        self.btn_seans_devam.clicked.connect(self._ileri_git)
        sk_lay.addWidget(self.btn_seans_devam)
        l3.addWidget(self.seans_kutu)

        icerik.addWidget(s3, 1)

        self.film_list.itemSelectionChanged.connect(self._durum_guncelle)
        self.salon_list.itemSelectionChanged.connect(self._durum_guncelle)
        self.format_cb.currentIndexChanged.connect(self._durum_guncelle)
        self.sehir_cb.currentIndexChanged.connect(self._sehir_degisti)

    def _tarih_secildi(self, tarih, secilen_btn):
        self.secilen_tarih = tarih
        for btn in self.tarih_butonlari:
            btn.setStyleSheet(f"background: {BEYAZ}; color: black; border-radius: 4px; padding: 10px; font-weight:bold;")
        secilen_btn.setStyleSheet(f"background: {VURGU}; color: white; border-radius: 4px; padding: 10px; font-weight:bold;")
        self._durum_guncelle()
        
    def icerik_yukle(self):
        self.stack.setCurrentIndex(0)
        self._adim_guncelle(1)
        self.film_list.blockSignals(True)
        self.film_list.clear()
        filmler = [e for e in self.db.etkinlikleri_getir() if e['kategori'] == "Sinema"]
        for f in filmler:
            item = QListWidgetItem(self.film_list)
            item.setData(Qt.UserRole, f['etkinlik_id']); item.setSizeHint(QSize(300, 120))
            self.film_list.setItemWidget(item, FilmKartiSinema(f['ad'], f['tarih']))
        self.film_list.blockSignals(False)
        if self.film_list.count() > 0: self.film_list.setCurrentRow(0)
        self._sehir_degisti()

    def _sehir_degisti(self):
        self.salon_list.blockSignals(True)
        self.salon_list.clear()
        secilen_sehir = self.sehir_cb.currentText()
        salonlar = self.sehir_salon_haritasi.get(secilen_sehir, ["EtkinlikApp Standart"])
        for s in salonlar: self.salon_list.addItem(s)
        self.salon_list.blockSignals(False)
        if self.salon_list.count() > 0: self.salon_list.setCurrentRow(0)
        self._durum_guncelle()

    def _durum_guncelle(self):
        for i in reversed(range(self.seans_grid.count())): 
            widget = self.seans_grid.itemAt(i).widget()
            if widget: 
                widget.deleteLater()
                
        self.seans_btns.clear()
        self.btn_seans_devam.setEnabled(False)
        self.secilen_seans = None
        self._butonlari_denetle()
        
        film_items = self.film_list.selectedItems()
        salon_items = self.salon_list.selectedItems()
        
        if not film_items or not salon_items:
            self.seans_lbl.setText("Film ve Salon seçimi bekleniyor...")
            return

        self.secili_eid = film_items[0].data(Qt.UserRole)
        self.secilen_salon = f"{salon_items[0].text()} ({self.format_cb.currentText()})"
        self.seans_lbl.setText(f"Mevcut Seanslar ({self.secilen_tarih}):")
        
        seanslar = ["11:15", "14:30", "17:45", "21:00"]
        for i, s in enumerate(seanslar):
            btn = QPushButton(s)
            btn.setFixedSize(80, 40)
            btn.setStyleSheet(f"background: {KART}; color: white; border-radius: 20px; font-weight:bold; font-size:14px;")
            btn.clicked.connect(lambda ch, x=s, b=btn: self._seans_tikla(x, b))
            self.seans_grid.addWidget(btn, i // 2, i % 2)
            self.seans_btns.append(btn)

    def _seans_tikla(self, s, b):
        self.secilen_seans = s
        for x in self.seans_btns: 
            x.setStyleSheet(f"background: {KART}; color: white; border-radius: 20px; font-weight:bold; font-size:14px;")
        b.setStyleSheet(f"background: {VURGU}; color: white; border-radius: 20px; border: 2px solid white; font-weight:bold; font-size:14px;")
        self.btn_seans_devam.setEnabled(True)
        self._butonlari_denetle()

    # ─── SAYFA 2: KOLTUK SEÇİMİ ───
    def _sayfa2_koltuk_kur(self):
        self.layout_koltuk = QVBoxLayout(self.sayfa_koltuk)
        self.layout_koltuk.setContentsMargins(50, 20, 50, 20)
        
    def _koltuk_sayfasina_gec(self):
        for i in reversed(range(self.layout_koltuk.count())): 
            item = self.layout_koltuk.itemAt(i)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget(): child.widget().deleteLater()
                item.layout().deleteLater()
                
        katilimcilar = self.db.katilimcilari_getir()
        if not katilimcilar:
            return QMessageBox.warning(self, "Uyarı", "Sistemde kayıtlı katılımcı bulunmuyor. Lütfen önce Katılımcılar sekmesinden ekleme yapın.")
            
        film_verisi = self.db.etkinlik_getir_id(self.secili_eid)
        tam_seans = f"{self.secilen_tarih} {self.secilen_seans}"
        self.tur_kodu = f"{tam_seans} - {self.secilen_salon}"
        dolu_koltuklar = self.db.dolu_koltuklari_getir(self.secili_eid, self.tur_kodu)
        self.secilen_koltuklar = []
        
        self.fiyat_carpan = 3 if any(f in self.secilen_salon for f in ["GOLD CLASS", "IMAX", "4DX", "ScreenX"]) else 1
        self.fiyat_tam = 250 * self.fiyat_carpan
        self.fiyat_ogr = 150 * self.fiyat_carpan

        baslik = QLabel(f"Koltuk Seçimi - {film_verisi['ad']} ({tam_seans} / {self.secilen_salon})")
        baslik.setStyleSheet(f"color: {VURGU}; font-size: 18px; font-weight: bold; margin-bottom:10px;")
        baslik.setAlignment(Qt.AlignCenter)
        self.layout_koltuk.addWidget(baslik)

        form = QFormLayout()
        self.katilimci_cb = QComboBox()
        for k in katilimcilar: self.katilimci_cb.addItem(f"{k['ad']} <{k['email']}>", k["katilimci_id"])
        form.addRow("Bilet Sahibi (Ana Hesap):", self.katilimci_cb)
        self.layout_koltuk.addLayout(form)

        perde_lbl = QLabel("P E R D E")
        perde_lbl.setAlignment(Qt.AlignCenter)
        perde_lbl.setStyleSheet(f"background-color: {KART}; color: {GRI}; font-size: 16px; font-weight: bold; padding: 15px; border-radius: 8px; margin-top: 10px;")
        self.layout_koltuk.addWidget(perde_lbl)

        grid = QGridLayout()
        grid.setSpacing(6)
        satirlar = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        
        grid_container = QHBoxLayout()
        grid_container.addStretch()
        
        for i, satir in enumerate(satirlar):
            for j in range(1, 11):
                koltuk_adi = f"{satir}{j}"
                btn = QPushButton(koltuk_adi)
                btn.setFixedSize(35, 35)
                
                if koltuk_adi in dolu_koltuklar:
                    btn.setStyleSheet(f"background-color: {KIRMIZI}; color: white; border-radius: 6px; font-weight: bold; font-size: 11px;")
                    btn.setEnabled(False)
                else:
                    btn.setStyleSheet(f"background-color: {KART}; color: {BEYAZ}; border-radius: 6px; font-weight: bold; font-size: 11px;")
                    btn.clicked.connect(lambda checked, b=btn: self._koltuk_tiklandi(b))
                
                col_index = j
                if j > 3: col_index += 1
                if j > 7: col_index += 1
                grid.addWidget(btn, i, col_index)

        grid.setColumnMinimumWidth(4, 25)
        grid.setColumnMinimumWidth(9, 25)
        grid_container.addLayout(grid)
        grid_container.addStretch()
        self.layout_koltuk.addLayout(grid_container)
        self.layout_koltuk.addSpacing(10)

        self.lbl_secim = QLabel("Seçilen Koltuklar: Yok")
        self.lbl_secim.setStyleSheet(f"color: {BEYAZ}; font-weight: bold; font-size: 13px;")
        self.lbl_secim.setAlignment(Qt.AlignCenter)
        self.layout_koltuk.addWidget(self.lbl_secim)

        self.btn_koltuk_devam = QPushButton("Devam Et (Ödeme Adımı)")
        self.btn_koltuk_devam.setFixedHeight(45)
        self.btn_koltuk_devam.setEnabled(False)
        self.btn_koltuk_devam.clicked.connect(self._ileri_git)
        self.layout_koltuk.addWidget(self.btn_koltuk_devam)
        self.layout_koltuk.addStretch()

        self.stack.setCurrentIndex(1)
        self._adim_guncelle(2)

    def _koltuk_tiklandi(self, secilen_btn):
        koltuk_adi = secilen_btn.text()
        if koltuk_adi in self.secilen_koltuklar:
            self.secilen_koltuklar.remove(koltuk_adi)
            secilen_btn.setStyleSheet(f"background-color: {KART}; color: {BEYAZ}; border-radius: 6px; font-weight: bold; font-size: 11px;")
        else:
            self.secilen_koltuklar.append(koltuk_adi)
            secilen_btn.setStyleSheet(f"background-color: {VURGU}; color: white; font-weight: bold; border: 2px solid {BEYAZ}; border-radius: 6px; font-size: 11px;")
            
        self.lbl_secim.setText(f"Seçilen Koltuklar: {', '.join(self.secilen_koltuklar) if self.secilen_koltuklar else 'Yok'}")
        self.btn_koltuk_devam.setEnabled(len(self.secilen_koltuklar) > 0)
        self._butonlari_denetle()


    # ─── SAYFA 3: ÖDEME SAYFASI ───
    def _sayfa3_odeme_kur(self):
        self.layout_odeme = QVBoxLayout(self.sayfa_odeme)
        self.layout_odeme.setContentsMargins(0, 0, 0, 0)
        
    def _odeme_sayfasina_gec(self):
        for i in reversed(range(self.layout_odeme.count())): 
            item = self.layout_odeme.itemAt(i)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget(): child.widget().deleteLater()
                item.layout().deleteLater()

        tam_seans = f"{self.secilen_tarih} {self.secilen_seans}"
        detay = f"{len(self.secilen_koltuklar)} Adet Bilet ({tam_seans} / {self.secilen_salon})"

        orta_widget = QWidget()
        orta_widget.setMaximumWidth(450)
        orta_layout = QVBoxLayout(orta_widget)

        bilgi_lbl = QLabel(f"{detay}\nÖdeme Ekranı")
        bilgi_lbl.setAlignment(Qt.AlignCenter)
        bilgi_lbl.setStyleSheet(f"color: {VURGU}; font-size:18px; font-weight: bold; margin-bottom: 15px;")
        orta_layout.addWidget(bilgi_lbl)

        logic_layout = QHBoxLayout()
        self.bilet_cb = QComboBox()
        self.bilet_cb.addItems(["Tam", "Öğrenci"])
        self.bilet_cb.currentIndexChanged.connect(self._odeme_hesapla)
        logic_layout.addWidget(QLabel("Bilet Türü:"))
        logic_layout.addWidget(self.bilet_cb)
            
        self.dogum_tarihi_edit = QDateEdit()
        self.dogum_tarihi_edit.setDisplayFormat("dd/MM/yyyy")
        self.dogum_tarihi_edit.setDate(QDate(2000, 1, 1))
        self.dogum_tarihi_edit.setMaximumDate(QDate(2026, 12, 31))
        self.dogum_tarihi_edit.setCalendarPopup(True)
        logic_layout.addWidget(QLabel("Doğum Tarihi:"))
        logic_layout.addWidget(self.dogum_tarihi_edit)
        logic_layout.addStretch()
        orta_layout.addLayout(logic_layout)

        orta_layout.addWidget(QLabel("<hr>")) 

        self.kart_tipi = QComboBox()
        self.kart_tipi.addItems(["Visa", "Mastercard", "Troy"])
        orta_layout.addWidget(self.kart_tipi)
        
        harf_validator = QRegExpValidator(QRegExp(r"^[a-zA-ZğüşıöçĞÜŞİÖÇ\s]+$"))  
        sayi_validator = QRegExpValidator(QRegExp(r"^[0-9]+$"))                  

        card_layout = QHBoxLayout()
        v_card_num = QVBoxLayout()
        v_card_num.addWidget(QLabel("Kart numarası"))
        self.kart_no_edit = QLineEdit()
        self.kart_no_edit.setValidator(sayi_validator)  
        self.kart_no_edit.setMaxLength(16)               
        v_card_num.addWidget(self.kart_no_edit)
        card_layout.addLayout(v_card_num)
        
        card_layout.addSpacing(10)
        
        v_exp = QVBoxLayout()
        v_exp.addWidget(QLabel("SKT (Ay/Yıl)"))
        h_exp = QHBoxLayout()
        self.ay_cb = QComboBox()
        self.ay_cb.addItems([f"{i:02d}" for i in range(1, 13)])
        self.yil_cb = QComboBox()
        current_year = QDate.currentDate().year()
        self.yil_cb.addItems([str(i) for i in range(current_year, current_year+15)])
        h_exp.addWidget(self.ay_cb)
        h_exp.addWidget(self.yil_cb)
        v_exp.addLayout(h_exp)
        card_layout.addLayout(v_exp)
        
        v_cvv = QVBoxLayout()
        v_cvv.addWidget(QLabel("CVV"))
        h_cvv = QHBoxLayout()
        self.cvv_edit = QLineEdit()
        self.cvv_edit.setMaxLength(3)                   
        self.cvv_edit.setValidator(sayi_validator)      
        self.cvv_edit.setFixedWidth(50)
        h_cvv.addWidget(self.cvv_edit)
        v_cvv.addLayout(h_cvv)
        card_layout.addLayout(v_cvv)
        
        orta_layout.addLayout(card_layout)
        orta_layout.addSpacing(10)

        lbl_fatura = QLabel("FATURA BİLGİSİ")
        lbl_fatura.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        orta_layout.addWidget(lbl_fatura)
        
        fatura_grid = QGridLayout()
        fatura_grid.setSpacing(10)
        
        fatura_grid.addWidget(QLabel("Ad"), 0, 0)
        fatura_grid.addWidget(QLabel("Soyadı"), 0, 1)
        
        self.ad_edit = QLineEdit(); self.ad_edit.setValidator(harf_validator) 
        self.soyad_edit = QLineEdit(); self.soyad_edit.setValidator(harf_validator) 
        
        fatura_grid.addWidget(self.ad_edit, 1, 0)
        fatura_grid.addWidget(self.soyad_edit, 1, 1)

        fatura_grid.addWidget(QLabel("Şehir"), 2, 0)
        fatura_grid.addWidget(QLabel("Zip veya posta kodu"), 2, 1)
        self.sehir_edit = QLineEdit(); self.sehir_edit.setValidator(harf_validator) 
        self.zip_edit = QLineEdit(); self.zip_edit.setValidator(sayi_validator); self.zip_edit.setMaxLength(5)                  
        
        fatura_grid.addWidget(self.sehir_edit, 3, 0)
        fatura_grid.addWidget(self.zip_edit, 3, 1)

        fatura_grid.addWidget(QLabel("Telefon numarası"), 4, 0, 1, 2)
        self.telefon_edit = QLineEdit(); self.telefon_edit.setValidator(sayi_validator); self.telefon_edit.setMaxLength(11)              
        fatura_grid.addWidget(self.telefon_edit, 5, 0, 1, 2)
        
        orta_layout.addLayout(fatura_grid)
        orta_layout.addSpacing(15)

        self.tutar_lbl = QLabel()
        self.tutar_lbl.setAlignment(Qt.AlignCenter)
        self.tutar_lbl.setStyleSheet(f"color: {TURUNCU}; font-size: 20px; font-weight: bold; margin: 10px 0;")
        orta_layout.addWidget(self.tutar_lbl)

        btn_ode = QPushButton("Ödemeyi Tamamla ve Biletleri Al")
        btn_ode.setFixedHeight(45)
        btn_ode.setStyleSheet(f"background-color: {YESIL}; font-size: 14px;")
        btn_ode.clicked.connect(self._odeme_tamamla)
        orta_layout.addWidget(btn_ode)

        self.layout_odeme.addWidget(orta_widget, 0, Qt.AlignHCenter)

        self._odeme_hesapla()
        self.stack.setCurrentIndex(2)
        self._adim_guncelle(3)

    def _odeme_hesapla(self):
        fiyat = self.fiyat_tam if self.bilet_cb.currentText() == "Tam" else self.fiyat_ogr
        self.guncel_tutar = fiyat * len(self.secilen_koltuklar)
        self.tutar_lbl.setText(f"Ödenecek Toplam Tutar: {self.guncel_tutar} TL")

    def _odeme_tamamla(self):
        if not self.kart_no_edit.text() or not self.cvv_edit.text() or \
           not self.ad_edit.text() or not self.soyad_edit.text() or \
           not self.sehir_edit.text() or not self.telefon_edit.text() or \
           not self.zip_edit.text():
            return QMessageBox.warning(self, "Hata", "Lütfen tüm ödeme ve fatura bilgilerini eksiksiz doldurun.")
            
        if len(self.kart_no_edit.text()) < 16: return QMessageBox.warning(self, "Hata", "Kart Numarası 16 haneli olmalıdır.")
        if len(self.cvv_edit.text()) < 3: return QMessageBox.warning(self, "Hata", "CVV 3 haneli olmalıdır.")
            
        dt = self.dogum_tarihi_edit.date(); bugun = QDate.currentDate()
        yas = bugun.year() - dt.year()
        if bugun.month() < dt.month() or (bugun.month() == dt.month() and bugun.day() < dt.day()): yas -= 1
            
        is_ogrenci = self.bilet_cb.currentText() == "Öğrenci"
        if is_ogrenci and yas > 25: 
            return QMessageBox.critical(self, "Kural İhlali", "25 yaşından büyük kullanıcılar Öğrenci Bileti alamaz!\nLütfen Tam bilet seçiniz veya bilgilerinizi kontrol ediniz.")
            
        kid = self.katilimci_cb.currentData()
        bilet_tipi = self.bilet_cb.currentText()
        tekil_fiyat = self.fiyat_tam if bilet_tipi == "Tam" else self.fiyat_ogr
        
        bilet_id_list = []
        for koltuk in self.secilen_koltuklar:
            kayit_turu = f"{self.tur_kodu} ({bilet_tipi})"
            bid, mesaj = self.db.bilet_olustur(self.secili_eid, kid, kayit_turu, tekil_fiyat, koltuk)
            if bid: bilet_id_list.append(str(bid))
                
        QMessageBox.information(self, "Başarılı", f"Ödeme alındı!\n{len(bilet_id_list)} bilet oluşturuldu.\nNo: #{', #'.join(bilet_id_list)}")
        
        self.guncelle_cb()
        self.icerik_yukle() 


# ─────────────────────────────────────────────
#  KONSER BİLETİ AÇILIR PENCERELER
# ─────────────────────────────────────────────

class KonserBiletDialog(QDialog):
    def __init__(self, ad, katilimcilar, parent=None):
        super().__init__(parent); self.setWindowTitle(f"Konser Bileti: {ad}"); self.setFixedSize(500, 320); self.setStyleSheet(STIL)
        self.fiyatlar = {"Genel Giriş": 1000, "Ayakta": 1500, "Sahne Önü": 3000, "VIP": 5000, "Loca": 15000}
        
        ml = QHBoxLayout(self)
        
        dosya_kok = ""
        ad_lower = ad.lower()
        if "dktt" in ad_lower or "dolu kadehi" in ad_lower: dosya_kok = "dktt"
        elif "manga" in ad_lower: dosya_kok = "manga"
        elif "manifest" in ad_lower: dosya_kok = "manifest"
        elif "edis" in ad_lower: dosya_kok = "edis"
        
        tam_yol = ""
        if dosya_kok:
            try: base_dir = os.path.dirname(os.path.abspath(__file__))
            except NameError: base_dir = os.getcwd()
            for u in [".png", ".jpg", ".jpeg", ".PNG", ".JPG"]:
                p = os.path.join(base_dir, dosya_kok + u)
                if os.path.exists(p): tam_yol = p; break
                
        self.afis = QLabel(); self.afis.setFixedSize(130, 200); self.afis.setAlignment(Qt.AlignCenter)
        if tam_yol: 
            orijinal_pix = QPixmap(tam_yol)
            scaled_pix = orijinal_pix.scaled(130, 200, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x_offset = (scaled_pix.width() - 130) // 2
            y_offset = (scaled_pix.height() - 200) // 2
            crop_rect = QRect(x_offset, y_offset, 130, 200)
            cropped_pix = scaled_pix.copy(crop_rect)
            self.afis.setPixmap(cropped_pix)
            self.afis.setStyleSheet("border-radius: 8px;")
        else: 
            self.afis.setText("Afiş\nBekleniyor")
            self.afis.setStyleSheet(f"background:{KOYU}; border-radius:8px; color:{GRI}")
            
        ml.addWidget(self.afis)
        
        sl = QVBoxLayout(); f = QFormLayout()
        self.k_cb = QComboBox()
        for k in katilimcilar: self.k_cb.addItem(f"{k['ad']} <{k['email']}>", k["katilimci_id"])
        
        self.t_cb = QComboBox(); self.t_cb.addItems(list(self.fiyatlar.keys())); self.t_cb.currentIndexChanged.connect(self._u)
        self.f_l = QLabel(f"Tutar: 1000 TL"); self.f_l.setStyleSheet(f"color:{TURUNCU}; font-size:20px; font-weight:bold; margin:15px 0;")
        
        f.addRow("Katılımcı:", self.k_cb); f.addRow("Bilet Türü:", self.t_cb); sl.addLayout(f); sl.addWidget(self.f_l, alignment=Qt.AlignCenter)
        b = QPushButton("Ödemeye Geç"); b.setFixedHeight(45); b.clicked.connect(self.accept); sl.addWidget(b); ml.addLayout(sl)
        
    def _u(self): self.f_l.setText(f"Tutar: {self.fiyatlar[self.t_cb.currentText()]} TL")
    def get_katilimci_id(self): return self.k_cb.currentData()
    def get_secim(self): return self.t_cb.currentText(), self.fiyatlar[self.t_cb.currentText()]

class OdemeDialogPopup(QDialog):
    def __init__(self, detay, sabit_tutar=0, konser_tur="", parent=None):
        super().__init__(parent); self.setWindowTitle("Güvenli Ödeme"); self.setFixedSize(450, 680); self.setStyleSheet(STIL); self.sabit_tutar = sabit_tutar; self.konser_tur = konser_tur
        l = QVBoxLayout(self); lbl = QLabel(f"{detay}\nÖdeme Ekranı"); lbl.setAlignment(Qt.AlignCenter); lbl.setStyleSheet(f"color: {VURGU}; font-size:16px; font-weight: bold; margin-bottom: 15px;"); l.addWidget(lbl)
        ll = QHBoxLayout(); self.dt = QDateEdit(); self.dt.setDisplayFormat("dd/MM/yyyy"); self.dt.setDate(QDate(2000, 1, 1)); self.dt.setMaximumDate(QDate(2026, 12, 31)); self.dt.setCalendarPopup(True)
        ll.addWidget(QLabel("Doğum Tarihi (Yaş Doğrulaması):")); ll.addWidget(self.dt); ll.addStretch(); l.addLayout(ll); l.addWidget(QLabel("<hr>"))
        self.kt = QComboBox(); self.kt.addItems(["Visa", "Mastercard", "Troy"]); l.addWidget(self.kt)
        hv = QRegExpValidator(QRegExp(r"^[a-zA-ZğüşıöçĞÜŞİÖÇ\s]+$")); sv = QRegExpValidator(QRegExp(r"^[0-9]+$"))
        cl = QHBoxLayout(); vl = QVBoxLayout(); vl.addWidget(QLabel("Kart numarası")); self.kn = QLineEdit(); self.kn.setValidator(sv); self.kn.setMaxLength(16); vl.addWidget(self.kn); cl.addLayout(vl); cl.addSpacing(10)
        vel = QVBoxLayout(); vel.addWidget(QLabel("SKT (Ay/Yıl)")); hl = QHBoxLayout(); self.ay = QComboBox(); self.ay.addItems([f"{i:02d}" for i in range(1, 13)]); self.yil = QComboBox(); cy = QDate.currentDate().year(); self.yil.addItems([str(i) for i in range(cy, cy+15)]); hl.addWidget(self.ay); hl.addWidget(self.yil); vel.addLayout(hl); cl.addLayout(vel)
        vc = QVBoxLayout(); vc.addWidget(QLabel("CVV")); hc = QHBoxLayout(); self.cv = QLineEdit(); self.cv.setMaxLength(3); self.cv.setValidator(sv); self.cv.setFixedWidth(50); hc.addWidget(self.cv); vc.addLayout(hc); cl.addLayout(vc); l.addLayout(cl); l.addSpacing(15)
        fl = QLabel("FATURA BİLGİSİ"); fl.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;"); l.addWidget(fl)
        fg = QGridLayout(); fg.setSpacing(10); fg.addWidget(QLabel("Ad"), 0, 0); fg.addWidget(QLabel("Soyadı"), 0, 1)
        self.ad = QLineEdit(); self.ad.setValidator(hv); self.soyad = QLineEdit(); self.soyad.setValidator(hv); fg.addWidget(self.ad, 1, 0); fg.addWidget(self.soyad, 1, 1)
        fg.addWidget(QLabel("Şehir"), 2, 0); fg.addWidget(QLabel("Zip kodu"), 2, 1); self.sehir = QLineEdit(); self.sehir.setValidator(hv); self.zip = QLineEdit(); self.zip.setValidator(sv); self.zip.setMaxLength(5); fg.addWidget(self.sehir, 3, 0); fg.addWidget(self.zip, 3, 1)
        fg.addWidget(QLabel("Telefon numarası"), 4, 0, 1, 2); self.tel = QLineEdit(); self.tel.setValidator(sv); self.tel.setMaxLength(11); fg.addWidget(self.tel, 5, 0, 1, 2); l.addLayout(fg); l.addSpacing(20)
        self.tl = QLabel(f"Ödenecek Toplam Tutar: {sabit_tutar} TL"); self.tl.setAlignment(Qt.AlignCenter); self.tl.setStyleSheet(f"color: {TURUNCU}; font-size: 20px; font-weight: bold; margin: 10px 0;"); l.addWidget(self.tl)
        btn = QPushButton("Ödemeyi Tamamla"); btn.setFixedHeight(45); btn.clicked.connect(self._ode); l.addWidget(btn)
        
    def _ode(self):
        if not self.kn.text() or not self.cv.text() or not self.ad.text() or not self.soyad.text() or not self.sehir.text() or not self.tel.text() or not self.zip.text(): return QMessageBox.warning(self, "Hata", "Eksik bilgi.")
        if len(self.kn.text()) < 16: return QMessageBox.warning(self, "Hata", "Kart Numarası 16 haneli olmalıdır.")
        if len(self.cv.text()) < 3: return QMessageBox.warning(self, "Hata", "CVV 3 haneli olmalıdır.")
        yas = QDate.currentDate().year() - self.dt.date().year()
        if self.konser_tur == "Öğrenci" and yas > 40: return QMessageBox.critical(self, "Kural İhlali", "40 yaşından büyükler Öğrenci alamaz!")
        self.accept()


# ─────────────────────────────────────────────
#  ANA ETKİNLİK SEKMESİ (SEÇİM YÖNETİCİSİ)
# ─────────────────────────────────────────────

class EtkinlikSekme(QWidget):
    def __init__(self, db: VeritabaniYoneticisi, guncelle_cb, rol="üye"):
        super().__init__()
        self.db = db
        self.guncelle_cb = guncelle_cb
        self.rol = rol
        self.kategoriler = ["Sinema", "Konser", "Türkiyeden Günler"]
            
        self.aktif_kategori = "Sinema"
        self.kategori_butonlari = []
        
        self._ui_kur()
        self.yenile()

    def _ui_kur(self):
        ana = QVBoxLayout(self)
        
        kategori_layout = QHBoxLayout()
        kategori_layout.setContentsMargins(0, 0, 0, 0)
        kategori_layout.setSpacing(15)
        kategori_layout.setAlignment(Qt.AlignLeft)

        for kat in self.kategoriler:
            btn = QPushButton(kat)
            btn.setStyleSheet(f"background: transparent; color: {GRI}; border: none; border-bottom: 2px solid transparent; font-weight: bold; font-size: 15px; padding: 5px 12px;")
            btn.setCheckable(True)
            if kat == "Sinema": 
                btn.setChecked(True)
                btn.setStyleSheet(f"background: transparent; color: {VURGU}; border: none; border-bottom: 2px solid {VURGU}; font-weight: bold; font-size: 15px; padding: 5px 12px;")
            btn.clicked.connect(lambda checked, k=kat, b=btn: self.kategori_secildi(k, b))
            kategori_layout.addWidget(btn); self.kategori_butonlari.append(btn)

        cizgi = QFrame(); cizgi.setFrameShape(QFrame.HLine); cizgi.setFrameShadow(QFrame.Sunken); cizgi.setStyleSheet(f"background-color: {KART}; margin-bottom: 10px;")
        ana.addLayout(kategori_layout); ana.addWidget(cizgi)

        self.stack = QStackedWidget()
        
        # TAB 0: SİNEMA PORTALI
        self.sinema_portal = SinemaPortaliWidget(self.db, self.guncelle_cb, self)
        self.stack.addWidget(self.sinema_portal)
        
        # TAB 1: DİĞER ETKİNLİKLER (TABLO GÖRÜNÜMÜ)
        self.diger_etkinlikler = QWidget()
        diger_layout = QVBoxLayout(self.diger_etkinlikler)
        diger_layout.setContentsMargins(0,0,0,0)
        
        self.arama = QLineEdit(); self.arama.setPlaceholderText("Etkinlik ara..."); self.arama.textChanged.connect(self.filtrele)
        self.tablo = QTableWidget(); self.tablo.setColumnCount(7); self.tablo.setHorizontalHeaderLabels(["ID", "Ad", "Kategori", "Tarih", "Kapasite", "Kayıtlı", "Doluluk"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows); self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo.itemSelectionChanged.connect(self._buton_metni_guncelle)

        alt_buton_layout = QHBoxLayout()
        self.btn_aksiyon = QPushButton("Bilet Al"); self.btn_aksiyon.hide(); self.btn_aksiyon.clicked.connect(self.bilet_satis_sureci)
        btn_sil = QPushButton("Seçili Etkinliği Sil"); btn_sil.setObjectName("silBtn"); btn_sil.clicked.connect(self.etkinlik_sil)
        btn_csv = QPushButton("CSV Dışa Aktar"); btn_csv.clicked.connect(self.csv_disari)

        if self.rol == "üye": btn_sil.hide(); btn_csv.hide()
        alt_buton_layout.addWidget(self.btn_aksiyon); alt_buton_layout.addWidget(btn_sil); alt_buton_layout.addWidget(btn_csv)

        diger_layout.addWidget(self.arama); diger_layout.addWidget(self.tablo); diger_layout.addLayout(alt_buton_layout)
        self.stack.addWidget(self.diger_etkinlikler)
        
        # TAB 2: KONSER VİTRİNİ (YENİ SÜTUNSUZ DÜZEN - TEK SIRA ALT ALTA)
        self.konser_portali = QScrollArea()
        self.konser_portali.setWidgetResizable(True)
        self.konser_portali.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.konser_icerik = QWidget()
        self.konser_icerik.setStyleSheet("background: transparent;")
        self.konser_grid = QGridLayout(self.konser_icerik)
        self.konser_grid.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.konser_grid.setSpacing(25)
        self.konser_portali.setWidget(self.konser_icerik)
        self.stack.addWidget(self.konser_portali)

        ana.addWidget(self.stack)

    def kategori_secildi(self, kategori, secilen_btn):
        self.aktif_kategori = kategori
        for btn in self.kategori_butonlari:
            btn.setStyleSheet(f"background: transparent; color: {GRI}; border: none; border-bottom: 2px solid transparent; font-weight: bold; font-size: 15px; padding: 5px 12px;")
            btn.setChecked(False)
            
        secilen_btn.setChecked(True)
        secilen_btn.setStyleSheet(f"background: transparent; color: {VURGU}; border: none; border-bottom: 2px solid {VURGU}; font-weight: bold; font-size: 15px; padding: 5px 12px;")
        
        if kategori == "Sinema":
            self.stack.setCurrentIndex(0)
            self.sinema_portal.icerik_yukle()
        elif kategori == "Konser":
            self.stack.setCurrentIndex(2)
            self._konserleri_yukle()
        else:
            self.stack.setCurrentIndex(1)
            self.yenile()

    def _buton_metni_guncelle(self):
        row = self.tablo.currentRow()
        if row < 0: 
            self.btn_aksiyon.hide()
            return
            
        kategori = self.tablo.item(row, 2).text()
        if kategori == "Türkiyeden Günler":
            self.btn_aksiyon.hide()
        else:
            self.btn_aksiyon.setText("Bilet Al")
            self.btn_aksiyon.show()

    def _konserleri_yukle(self):
        for i in reversed(range(self.konser_grid.count())): 
            widget = self.konser_grid.itemAt(i).widget()
            if widget: widget.deleteLater()
            
        konserler = [e for e in self.db.etkinlikleri_getir() if e['kategori'] == "Konser"]
        
        for i, k in enumerate(konserler):
            kart = YatayKonserKarti(k['ad'], [k], self._konser_bilet_al)
            self.konser_grid.addWidget(kart, i, 0, Qt.AlignHCenter)

    def _konser_bilet_al(self, eid, ad):
        katilimcilar = self.db.katilimcilari_getir()
        if not katilimcilar: return QMessageBox.warning(self, "Uyarı", "Sistemde kayıtlı katılımcı bulunmuyor.")
        
        secim_dialog = KonserBiletDialog(ad, katilimcilar, self)
        if secim_dialog.exec_() == QDialog.Accepted:
            kid = secim_dialog.get_katilimci_id()
            tur, fiyat = secim_dialog.get_secim()

            odeme_dialog = OdemeDialogPopup(detay=f"Konser ({tur}) Bileti", sabit_tutar=fiyat, konser_tur=tur, parent=self)
            if odeme_dialog.exec_() == QDialog.Accepted:
                bid, mesaj = self.db.bilet_olustur(eid, kid, tur, fiyat, "-")
                if not bid: QMessageBox.warning(self, "Hata", "Bilet oluşturulamadı")
                else:
                    QMessageBox.information(self, "Başarılı", f"Ödeme alındı!\nKonser Bilet #{bid} oluşturuldu.")
                    self.guncelle_cb()

    def yenile(self):
        if self.stack.currentIndex() == 1:
            self.tablo.setRowCount(0); self.btn_aksiyon.hide()
            for row in self.db.etkinlikleri_getir():
                if row["kategori"] != self.aktif_kategori: continue
                
                kayitli = self.db.baglanti.execute("SELECT COUNT(*) FROM biletler WHERE etkinlik_id=?", (row["etkinlik_id"],)).fetchone()[0]
                oran = int(kayitli / row["kapasite"] * 100) if row["kapasite"] else 0
                renk = YESIL if oran < 70 else TURUNCU if oran < 100 else KIRMIZI
                tablo_satir_ekle(self.tablo, [row["etkinlik_id"], row["ad"], row["kategori"], row["tarih"], row["kapasite"], kayitli, f"%{oran}"], {6: renk})
        elif self.stack.currentIndex() == 0:
            self.sinema_portal.icerik_yukle()
        elif self.stack.currentIndex() == 2:
            self._konserleri_yukle()

    def filtrele(self, metin):
        for r in range(self.tablo.rowCount()):
            satir_metni = " ".join(self.tablo.item(r, c).text() for c in range(self.tablo.columnCount()))
            self.tablo.setRowHidden(r, metin.lower() not in satir_metni.lower())

    def _secili_id(self):
        row = self.tablo.currentRow()
        if row < 0: return QMessageBox.warning(self, "Uyarı", "Lütfen bir etkinlik seçin."), None
        return int(self.tablo.item(row, 0).text())

    def etkinlik_sil(self):
        eid = self._secili_id()
        if eid is None or type(eid) is tuple: return
        if QMessageBox.question(self, "Onayla", "Etkinlik ve tüm biletleri silinecek. Devam edilsin mi?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.etkinlik_sil(eid); self.yenile(); self.guncelle_cb()

    def bilet_satis_sureci(self):
        row = self.tablo.currentRow()
        if row < 0: return
        eid = int(self.tablo.item(row, 0).text())
        ad = self.tablo.item(row, 1).text()
        kategori = self.tablo.item(row, 2).text()
        
        # Yemek festivallerinde satın alma sürecini tamamen blokla
        if kategori == "Türkiyeden Günler":
            QMessageBox.information(self, "Bilgi", "Bu etkinlik ücretsiz ve halka açıktır, bilet alımına gerek yoktur.")
            return
        
        katilimcilar = self.db.katilimcilari_getir()
        if not katilimcilar: return QMessageBox.warning(self, "Uyarı", "Sistemde kayıtlı katılımcı bulunmuyor.")

        odeme_dialog = OdemeDialogPopup(detay=f"{ad} Giriş Bileti", sabit_tutar=150, parent=self)
        if odeme_dialog.exec_() == QDialog.Accepted:
            bid, mesaj = self.db.bilet_olustur(eid, katilimcilar[0]['katilimci_id'], "Standart", 150, "-")
            if not bid: QMessageBox.warning(self, "Hata", "Bilet oluşturulamadı")
            else:
                QMessageBox.information(self, "Başarılı", f"Ödeme alındı!\nBilet #{bid} oluşturuldu.")
                self.yenile(); self.guncelle_cb()

    def csv_disari(self):
        yol, _ = QFileDialog.getSaveFileName(self, "Kaydet", "etkinlikler.csv", "CSV (*.csv)")
        if not yol: return
        with open(yol, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ID", "Ad", "Kategori", "Tarih", "Kapasite", "Kayıtlı", "Doluluk"])
            for r in range(self.tablo.rowCount()): w.writerow([self.tablo.item(r, c).text() for c in range(7)])
        QMessageBox.information(self, "Başarılı", f"CSV kaydedildi:\n{yol}")


class KatilimciSekme(QWidget):
    def __init__(self, db: VeritabaniYoneticisi, guncelle_cb):
        super().__init__()
        self.db = db; self.guncelle_cb = guncelle_cb
        self._ui_kur(); self.yenile()

    def _ui_kur(self):
        ana = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        sol = QWidget(); form_layout = QVBoxLayout(sol)
        grup = QGroupBox("Yeni Katılımcı"); form = QFormLayout(grup)
        self.ad_edit = QLineEdit(); self.ad_edit.setPlaceholderText("Ad Soyad")
        self.email_edit = QLineEdit(); self.email_edit.setPlaceholderText("ornek@mail.com")
        form.addRow("Ad:", self.ad_edit); form.addRow("E-posta:", self.email_edit)
        btn_ekle = QPushButton("Katılımcı Ekle"); btn_ekle.clicked.connect(self.katilimci_ekle)
        form.addRow(btn_ekle)
        btn_sil = QPushButton("Seçiliyi Sil"); btn_sil.setObjectName("silBtn"); btn_sil.clicked.connect(self.katilimci_sil)
        form_layout.addWidget(grup); form_layout.addWidget(btn_sil); form_layout.addStretch()

        sag = QWidget(); sag_layout = QVBoxLayout(sag)
        self.arama = QLineEdit(); self.arama.setPlaceholderText("Ara..."); self.arama.textChanged.connect(self.filtrele)
        self.tablo = QTableWidget(); self.tablo.setColumnCount(3); self.tablo.setHorizontalHeaderLabels(["ID", "Ad", "E-posta"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows); self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.toplam_lbl = QLabel()
        sag_layout.addWidget(self.arama); sag_layout.addWidget(self.tablo); sag_layout.addWidget(self.toplam_lbl)

        splitter.addWidget(sol); splitter.addWidget(sag); splitter.setSizes([350, 850])
        ana.addWidget(splitter)

    def yenile(self):
        self.tablo.setRowCount(0)
        for row in self.db.katilimcilari_getir(): tablo_satir_ekle(self.tablo, [row["katilimci_id"], row["ad"], row["email"]])
        self.toplam_lbl.setText(f"Toplam: {self.tablo.rowCount()} katılımcı")

    def filtrele(self, metin):
        for r in range(self.tablo.rowCount()):
            satir_metni = " ".join(self.tablo.item(r, c).text() for c in range(self.tablo.columnCount()))
            self.tablo.setRowHidden(r, metin.lower() not in satir_metni.lower())

    def katilimci_ekle(self):
        ad = self.ad_edit.text().strip(); email = self.email_edit.text().strip()
        if not ad or not email: return QMessageBox.warning(self, "Hata", "Zorunlu!")
        if self.db.katilimci_ekle(ad, email) is None: return QMessageBox.warning(self, "Hata", "Kayıtlı!")
        self.ad_edit.clear(); self.email_edit.clear(); self.yenile(); self.guncelle_cb()

    def katilimci_sil(self):
        row = self.tablo.currentRow()
        if row < 0: return
        if QMessageBox.question(self, "Onay", "Sil?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.katilimci_sil(int(self.tablo.item(row, 0).text())); self.yenile(); self.guncelle_cb()

class BiletSekme(QWidget):
    def __init__(self, db: VeritabaniYoneticisi, guncelle_cb):
        super().__init__()
        self.db = db; self.guncelle_cb = guncelle_cb
        self._ui_kur(); self.yenile()

    def _ui_kur(self):
        ana = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        sol = QWidget(); form_layout = QVBoxLayout(sol)
        grup = QGroupBox("Hızlı Bilet"); form = QFormLayout(grup)
        self.etkinlik_cb = QComboBox(); self.katilimci_cb = QComboBox()
        form.addRow("Etkinlik:", self.etkinlik_cb); form.addRow("Katılımcı:", self.katilimci_cb)
        self.doluluk_bar = QProgressBar(); self.doluluk_bar.setRange(0, 100)
        form.addRow("Doluluk:", self.doluluk_bar); self.etkinlik_cb.currentIndexChanged.connect(self._doluluk_guncelle)
        btn_ekle = QPushButton("Oluştur"); btn_ekle.clicked.connect(self.bilet_olustur); form.addRow(btn_ekle)
        btn_iptal = QPushButton("İptal Et"); btn_iptal.setObjectName("silBtn"); btn_iptal.clicked.connect(self.bilet_iptal)
        form_layout.addWidget(grup); form_layout.addWidget(btn_iptal); form_layout.addStretch()

        sag = QWidget(); sag_layout = QVBoxLayout(sag)
        self.filtre_cb = QComboBox(); self.filtre_cb.addItem("-- Tüm Etkinlikler --", None); self.filtre_cb.currentIndexChanged.connect(self.yenile)
        self.tablo = QTableWidget(); self.tablo.setColumnCount(8); self.tablo.setHorizontalHeaderLabels(["Bilet No", "Etkinlik", "Katılımcı", "E-posta", "Tür (Seans)", "Fiyat", "Koltuk", "Kayıt Tarihi"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows); self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        sag_layout.addWidget(QLabel("Filtrele:")); sag_layout.addWidget(self.filtre_cb); sag_layout.addWidget(self.tablo)

        splitter.addWidget(sol); splitter.addWidget(sag); splitter.setSizes([350, 850])
        ana.addWidget(splitter)

    def combolar_yukle(self):
        self.etkinlik_cb.clear(); self.katilimci_cb.clear()
        self.filtre_cb.blockSignals(True)
        secili = self.filtre_cb.currentData(); self.filtre_cb.clear(); self.filtre_cb.addItem("-- Tüm Etkinlikler --", None)
        for e in self.db.etkinlikleri_getir(): self.etkinlik_cb.addItem(f"{e['ad']} ({e['tarih']})", e["etkinlik_id"]); self.filtre_cb.addItem(e["ad"], e["etkinlik_id"])
        for k in self.db.katilimcilari_getir(): self.katilimci_cb.addItem(f"{k['ad']} <{k['email']}>", k["katilimci_id"])
        for i in range(self.filtre_cb.count()):
            if self.filtre_cb.itemData(i) == secili: self.filtre_cb.setCurrentIndex(i); break
        self.filtre_cb.blockSignals(False); self._doluluk_guncelle()

    def _doluluk_guncelle(self):
        eid = self.etkinlik_cb.currentData()
        if eid is None: return
        kayitli = self.db.baglanti.execute("SELECT COUNT(*) FROM biletler WHERE etkinlik_id=?", (eid,)).fetchone()[0]
        kapasite = self.db.baglanti.execute("SELECT kapasite FROM etkinlikler WHERE etkinlik_id=?", (eid,)).fetchone()
        if kapasite:
            oran = int(kayitli / kapasite[0] * 100)
            self.doluluk_bar.setValue(oran); self.doluluk_bar.setFormat(f"%{oran}  ({kayitli}/{kapasite[0]})")
            stil = KIRMIZI if oran >= 100 else TURUNCU if oran >= 70 else YESIL
            self.doluluk_bar.setStyleSheet(f"QProgressBar::chunk {{ background: {stil}; border-radius:4px; }}")

    def yenile(self):
        self.tablo.setRowCount(0); eid = self.filtre_cb.currentData()
        for row in self.db.biletleri_getir(eid): tablo_satir_ekle(self.tablo, [row["bilet_id"], row["etkinlik"], row["katilimci"], row["email"], row["tur"], f"{row['fiyat']} TL" if row['fiyat']>0 else "Ücretsiz", row["koltuk"], row["olusturma_tarihi"]])
        self.combolar_yukle()

    def bilet_olustur(self):
        eid = self.etkinlik_cb.currentData(); kid = self.katilimci_cb.currentData()
        if eid is None or kid is None: return
        bid, mesaj = self.db.bilet_olustur(eid, kid, "Standart", 0, "-")
        if bid: QMessageBox.information(self, "Başarılı", f"Bilet #{bid}"); self.yenile(); self.guncelle_cb()

    def bilet_iptal(self):
        row = self.tablo.currentRow()
        if row < 0: return
        if QMessageBox.question(self, "Onay", "İptal?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.bilet_iptal(int(self.tablo.item(row, 0).text())); self.yenile(); self.guncelle_cb()

class RaporSekme(QWidget):
    def __init__(self, db: VeritabaniYoneticisi):
        super().__init__()
        self.db = db; self._ui_kur(); self.yenile()

    def _ui_kur(self):
        ana = QVBoxLayout(self)
        baslik = QLabel("Etkinlik Katılımcı Raporu"); baslik.setStyleSheet(f"font-size:16px; font-weight:bold; color:{VURGU}; padding:8px;")
        ana.addWidget(baslik)

        self.tablo = QTableWidget(); self.tablo.setColumnCount(5); self.tablo.setHorizontalHeaderLabels(["Etkinlik", "Tarih", "Kapasite", "Kayıtlı", "Boş Yer"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        ana.addWidget(self.tablo)

        istat_grup = QGroupBox("Genel İstatistikler"); istat_layout = QHBoxLayout(istat_grup)
        self.toplam_etkinlik_lbl = self._kart_lbl("Toplam Etkinlik", "0")
        self.toplam_katilimci_lbl = self._kart_lbl("Toplam Bilet", "0")
        self.en_dolu_lbl = self._kart_lbl("En Yoğun Etkinlik", "-")
        self.en_bos_lbl = self._kart_lbl("En Boş Etkinlik", "-")
        for w in [self.toplam_etkinlik_lbl, self.toplam_katilimci_lbl, self.en_dolu_lbl, self.en_bos_lbl]: istat_layout.addWidget(w)
        ana.addWidget(istat_grup)

        grafik_grup = QGroupBox("Doluluk Grafiği"); grafik_layout = QVBoxLayout(grafik_grup)
        self.grafik_alan = QTextEdit(); self.grafik_alan.setReadOnly(True); self.grafik_alan.setFixedHeight(160)
        grafik_layout.addWidget(self.grafik_alan); ana.addWidget(grafik_grup)

        btn_yenile = QPushButton("Raporu Yenile"); btn_yenile.clicked.connect(self.yenile)
        btn_csv = QPushButton("Raporu CSV Kaydet"); btn_csv.clicked.connect(self.csv_kaydet)
        alt = QHBoxLayout(); alt.addWidget(btn_yenile); alt.addWidget(btn_csv); ana.addLayout(alt)

    def _kart_lbl(self, baslik, deger):
        w = QWidget(); w.setStyleSheet(f"background:{KART}; border-radius:8px; padding:8px;")
        v = QVBoxLayout(w)
        lbl_b = QLabel(baslik); lbl_b.setStyleSheet(f"color:{GRI}; font-size:11px;")
        lbl_d = QLabel(deger); lbl_d.setStyleSheet(f"color:{VURGU}; font-size:18px; font-weight:bold;"); lbl_d.setObjectName("deger")
        v.addWidget(lbl_b); v.addWidget(lbl_d)
        return w

    def _kart_deger_guncelle(self, kart, deger):
        lbl = kart.findChild(QLabel, "deger")
        if lbl: lbl.setText(deger)

    def yenile(self):
        self.tablo.setRowCount(0); rapor = self.db.katilimci_raporu()
        for row in rapor:
            oran = int(row["kayitli"] / row["kapasite"] * 100) if row["kapasite"] else 0
            renk = YESIL if oran < 70 else TURUNCU if oran < 100 else KIRMIZI
            tablo_satir_ekle(self.tablo, [row["ad"], row["tarih"], row["kapasite"], row["kayitli"], row["bos"]], {3: renk})

        top_etkinlik = len(rapor); top_bilet = sum(r["kayitli"] for r in rapor)
        en_dolu = max(rapor, key=lambda r: r["kayitli"] / r["kapasite"] if r["kapasite"] else 0, default=None)
        en_bos = min(rapor, key=lambda r: r["kayitli"] / r["kapasite"] if r["kapasite"] else 1, default=None)
        self._kart_deger_guncelle(self.toplam_etkinlik_lbl, str(top_etkinlik)); self._kart_deger_guncelle(self.toplam_katilimci_lbl, str(top_bilet))
        self._kart_deger_guncelle(self.en_dolu_lbl, en_dolu["ad"] if en_dolu else "-"); self._kart_deger_guncelle(self.en_bos_lbl, en_bos["ad"] if en_bos else "-")

        satirlar = []
        for row in rapor:
            oran = int(row["kayitli"] / row["kapasite"] * 50) if row["kapasite"] else 0
            bar = "█" * oran + "░" * (50 - oran); yuzde = int(row["kayitli"] / row["kapasite"] * 100) if row["kapasite"] else 0
            satirlar.append(f"{row['ad'][:20]:<20} {bar} %{yuzde:>3} ({row['kayitli']}/{row['kapasite']})")
        self.grafik_alan.setPlainText("\n".join(satirlar) if satirlar else "Veri yok.")

    def csv_kaydet(self):
        yol, _ = QFileDialog.getSaveFileName(self, "Kaydet", "rapor.csv", "CSV (*.csv)")
        if not yol: return
        with open(yol, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Etkinlik", "Tarih", "Kapasite", "Kayıtlı", "Boş Yer"])
            for r in range(self.tablo.rowCount()): w.writerow([self.tablo.item(r, c).text() for c in range(5)])
        QMessageBox.information(self, "Başarılı", f"Rapor kaydedildi:\n{yol}")

# ─────────────────────────────────────────────
#  ANA PENCERE
# ─────────────────────────────────────────────

class AnaPencere(QMainWindow):
    def __init__(self, db, rol="üye"):
        super().__init__()
        self.rol = rol 
        self.setWindowTitle(f"Etkinlik Yönetim Portalı ({self.rol.upper()} MODU)")
        self.setMinimumSize(1250, 800) 
        self.setStyleSheet(STIL)
        self.db = db

        self.sekmeler = QTabWidget()
        self.sekmeler.setElideMode(Qt.ElideNone)
        
        self.etkinlik_sekme = EtkinlikSekme(self.db, self._genel_yenile, self.rol)
        self.sekmeler.addTab(self.etkinlik_sekme, "Etkinlikler")

        if self.rol == "admin":
            self.katilimci_sekme = KatilimciSekme(self.db, self._genel_yenile)
            self.bilet_sekme = BiletSekme(self.db, self._genel_yenile)
            self.rapor_sekme = RaporSekme(self.db)

            self.sekmeler.addTab(self.katilimci_sekme, "Katılımcılar")
            self.sekmeler.addTab(self.bilet_sekme, "Bilet Satış Raporu")
            self.sekmeler.addTab(self.rapor_sekme, "Genel Rapor")

        self.setCentralWidget(self.sekmeler)
        self.durum_cubugu = QStatusBar(); self.setStatusBar(self.durum_cubugu); self._durum_guncelle()

    def _genel_yenile(self):
        self.etkinlik_sekme.yenile()
        if self.rol == "admin": 
            self.katilimci_sekme.yenile()
            self.bilet_sekme.yenile()
            self.rapor_sekme.yenile()
        self._durum_guncelle()

    def _durum_guncelle(self):
        self.durum_cubugu.showMessage(f"  {len(self.db.etkinlikleri_getir())} Etkinlik   |   {len(self.db.katilimcilari_getir())} Katılımcı   |   {len(self.db.biletleri_getir())} Bilet")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("EtkinlikApp Kayıt Sistemi")
    db = VeritabaniYoneticisi()
    giris_ekrani = KullaniciGiris(db)
    
    if giris_ekrani.exec_() == QDialog.Accepted:
        pencere = AnaPencere(db, giris_ekrani.rol)
        pencere.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)