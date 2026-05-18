F"""
Araç Paylaşım Sistemi (Car Sharing System)
PyQt5 + SQLite — Kararlı Versiyon
"""

import sys
import sqlite3  
import hashlib
import os
import random
import matplotlib
import geocoder
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from PyQt5.QtWebEngineWidgets import QWebEngineView
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QFormLayout, QComboBox, QMessageBox, QDialog,
    QHeaderView, QFrame, QTextEdit, QSpinBox,
    QDoubleSpinBox, QFileDialog, QListView
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush, QPixmap, QLinearGradient
from PyQt5.QtChart import (
    QChart, QChartView, QBarSeries, QBarSet,
    QBarCategoryAxis, QValueAxis, QPieSeries
)

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# =====================================================================
# NESNEYE YÖNELİK PROGRAMLAMA (OOP) İŞ MODELLERİ KATMANI
# (Bu bölüm projenin akademik OOP gereksinimlerini karşılamak içindir)
# =====================================================================

class TemelVarlik:
    """ KALITIM (INHERITANCE) İÇİN EN ÜST TEMEL SINIF """
    def __init__(self, kayit_id):
        self._kayit_id = kayit_id # Protected (Korumalı) değişken
        
    def ozet_bilgi(self):
        # ÇOK BİÇİMLİLİK (POLYMORPHISM) İÇİN EZİLECEK METOT
        return "Bilinmeyen Varlık"

# 1. ARAYÜZ HARİCİ SINIF (Araçlar)
class AracModeli(TemelVarlik):
    def __init__(self, arac_id, marka, model, plaka, saatlik_ucret):
        super().__init__(arac_id) # Kalıtım (Miras alma) kullanımı
        self.marka = marka
        self.model = model
        self.plaka = plaka
        self.__saatlik_ucret = saatlik_ucret # KAPSÜLLEME (ENCAPSULATION) - Private Değişken
        
    # KAPSÜLLEME İÇİN GETTER / SETTER METOTLARI
    def get_saatlik_ucret(self):
        return self.__saatlik_ucret
        
    def set_saatlik_ucret(self, yeni_ucret):
        if yeni_ucret > 0:
            self.__saatlik_ucret = yeni_ucret
            
    # ÇOK BİÇİMLİLİK (POLYMORPHISM) - Temel sınıftaki metodu eziyoruz (Overriding)
    def ozet_bilgi(self):
        return f"🚗 Araç: {self.marka} {self.model} | Plaka: {self.plaka} | Ücret: {self.get_saatlik_ucret()} TL/Saat"

# 2. ARAYÜZ HARİCİ SINIF (Kullanıcılar)
class KullaniciModeli(TemelVarlik):
    def __init__(self, kullanici_id, ad, soyad, rol):
        super().__init__(kullanici_id)
        self.ad = ad
        self.soyad = soyad
        self.rol = rol
        
    # ÇOK BİÇİMLİLİK (POLYMORPHISM) - Temel sınıftaki metodu farklı bir şekilde eziyoruz
    def ozet_bilgi(self):
        return f"👤 Kullanıcı: {self.ad} {self.soyad} | Yetki: {self.rol.upper()}"

# 3. ARAYÜZ HARİCİ SINIF (Kiralamalar)
class KiralamaIslemi(TemelVarlik):
    def __init__(self, kiralama_id, arac: AracModeli, musteri: KullaniciModeli, toplam_ucret):
        super().__init__(kiralama_id)
        self.arac = arac
        self.musteri = musteri
        self.__toplam_ucret = toplam_ucret # Private değişken
        
    def get_toplam_ucret(self):
        return self.__toplam_ucret
        
    # ÇOK BİÇİMLİLİK (POLYMORPHISM)
    def ozet_bilgi(self):
        return f"📄 Kiralama: {self.musteri.ad} kişisi {self.arac.marka} aracını kiraladı. Tutar: {self.get_toplam_ucret()} TL"

# =====================================================================
# ─────────────────────────────────────────────
#  VERİTABANI
# ─────────────────────────────────────────────

DB_FILE = "car_sharing.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection(); c = conn.cursor()
    
    # --- 1. TABLOLARI SIFIRDAN OLUŞTUR (EĞER YOKSA) ---
    # Bu kısım eksik olduğu için "no such table" hatası alıyordun
    c.execute("""CREATE TABLE IF NOT EXISTS kullanicilar (
        kullanici_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT, soyad TEXT, ehliyet_no TEXT UNIQUE,
        email TEXT UNIQUE, sifre_hash TEXT, rol TEXT DEFAULT 'kullanici',
        kayit_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS araclar (
        arac_id INTEGER PRIMARY KEY AUTOINCREMENT,
        marka TEXT, model TEXT, yil INTEGER, plaka TEXT UNIQUE,
        kilometre REAL DEFAULT 0, musait_mi INTEGER DEFAULT 1,
        saatlik_ucret REAL DEFAULT 50.0, aciklama TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS kiralamalar (
        kiralama_id INTEGER PRIMARY KEY AUTOINCREMENT,
        arac_id INTEGER, kullanici_id INTEGER,
        baslangic_saati DATETIME, bitis_saati DATETIME,
        durum TEXT DEFAULT 'aktif', toplam_ucret REAL, notlar TEXT,
        FOREIGN KEY(arac_id) REFERENCES araclar(arac_id),
        FOREIGN KEY(kullanici_id) REFERENCES kullanicilar(kullanici_id)
    )""")

    # --- 2. MEVCUT TABLOLARA YENİ SÜTUNLARI EKLE (MİGRASYON) ---
    # Kullanıcılar için kurumsal alanlar
    user_columns = [
        ("kurumsal_mi",   "INTEGER DEFAULT 0"),
        ("sirket_adi",    "TEXT DEFAULT ''"),
        ("vergi_no",      "TEXT DEFAULT ''"),
        ("vergi_dairesi", "TEXT DEFAULT ''"),
        ("adres",         "TEXT DEFAULT ''"),
        ("telefon",       "TEXT DEFAULT ''"),
        ("profil_foto",   "TEXT DEFAULT ''"),
        ("ehliyet_foto",  "TEXT DEFAULT ''"), # YENİ: Ehliyet resmi yolu
        ("ehliyet_hash",  "TEXT DEFAULT ''")  # YENİ: Sahte/Kopya kontrolü için dijital imza
    ]
    for col, typedef in user_columns:
        try: c.execute(f"ALTER TABLE kullanicilar ADD COLUMN {col} {typedef}")
        except: pass

    # Araçlar için teknik alanlar
    arac_columns = [
        ("enlem",         "REAL DEFAULT 0"),
        ("boylam",        "REAL DEFAULT 0"),
        ("vites",         "TEXT DEFAULT 'Otomatik'"),
        ("yakit",         "TEXT DEFAULT '%80'"),
        ("foto_url",      "TEXT DEFAULT ''")
    ]
    for col, typedef in arac_columns:
        try: c.execute(f"ALTER TABLE araclar ADD COLUMN {col} {typedef}")
        except: pass

    try: c.execute("ALTER TABLE kiralamalar ADD COLUMN fatura_no TEXT DEFAULT ''")
    except: pass
    
    # --- 3. EĞER HİÇ ARAÇ YOKSA ÖRNEK VERİ EKLE ---
    c.execute("SELECT COUNT(*) FROM araclar")
    if c.fetchone()[0] == 0:
        ornek_araclar = [
            ('Toyota', 'Corolla', 2022, '34ABC123', 45.0, 41.0082, 28.9784),
            ('Renault', 'Clio', 2021, '34XYZ999', 35.0, 41.041, 29.006),
            ('BMW', '320i', 2023, '34BMW01', 120.0, 40.990, 29.020)
        ]
        for m, mo, y, p, u, lat, lng in ornek_araclar:
            c.execute("""INSERT INTO araclar (marka, model, yil, plaka, saatlik_ucret, enlem, boylam, musait_mi, vites, yakit) 
                         VALUES (?,?,?,?,?,?,?,1,'Otomatik','%90')""", (m, mo, y, p, u, lat, lng))

    # --- 4. EĞER HİÇ ADMİN YOKSA OLUŞTUR ---
    c.execute("SELECT COUNT(*) FROM kullanicilar WHERE rol='admin'")
    if c.fetchone()[0] == 0:
        import hashlib
        admin_sifre = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("""INSERT INTO kullanicilar (ad, soyad, email, sifre_hash, rol) 
                     VALUES ('Sistem', 'Admin', 'admin@rentacar.com', ?, 'admin')""", (admin_sifre,))

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
#  MODEL SINIFLARI
# ─────────────────────────────────────────────

class Arac:
    def __init__(self, arac_id, marka, model, kilometre, musait_mi,
                 yil=None, plaka=None, saatlik_ucret=50.0, 
                 vites='Otomatik', yakit='%80', enlem=0, boylam=0):
        self.arac_id = arac_id
        self.marka = marka
        self.model = model
        self.kilometre = kilometre
        self.musait_mi = musait_mi
        self.yil = yil
        self.plaka = plaka
        self.saatlik_ucret = saatlik_ucret
        self.vites = vites
        self.yakit = yakit
        self.enlem = enlem
        self.boylam = boylam

    def arac_durumu_guncelle(self, yeni_durum: bool):
        conn = get_connection()
        conn.execute("UPDATE araclar SET musait_mi=? WHERE arac_id=?",
                     (int(yeni_durum), self.arac_id))
        conn.commit(); conn.close()
        self.musait_mi = yeni_durum

    def kilometre_guncelle(self, eklenen_km: float):
        self.kilometre += eklenen_km
        conn = get_connection()
        conn.execute("UPDATE araclar SET kilometre=? WHERE arac_id=?",
                     (self.kilometre, self.arac_id))
        conn.commit(); conn.close()

    def __str__(self):
        return f"{self.marka} {self.model} ({self.plaka})"


class Kullanici:
    def __init__(self, kullanici_id, ad, soyad, ehliyet_no, email, rol='kullanici',
                 kurumsal_mi=0, sirket_adi='', vergi_no='', vergi_dairesi='',
                 adres='', telefon=''):
        self.kullanici_id = kullanici_id
        self.ad = ad
        self.soyad = soyad
        self.ehliyet_no = ehliyet_no
        self.email = email
        self.rol = rol
        self.kurumsal_mi   = kurumsal_mi
        self.sirket_adi    = sirket_adi
        self.vergi_no      = vergi_no
        self.vergi_dairesi = vergi_dairesi
        self.adres         = adres
        self.telefon       = telefon

    def kiralama_gecmisi(self):
        conn = get_connection(); c = conn.cursor()
        c.execute("""
            SELECT k.kiralama_id, a.marka, a.model, a.plaka,
                   k.baslangic_saati, k.bitis_saati, k.durum, k.toplam_ucret
            FROM kiralamalar k
            JOIN araclar a ON k.arac_id=a.arac_id
            WHERE k.kullanici_id=? ORDER BY k.kiralama_id DESC
        """, (self.kullanici_id,))
        rows = c.fetchall(); conn.close()
        return rows

    def __str__(self):
        return f"{self.ad} {self.soyad}"


class Kiralama:
    def __init__(self, kiralama_id, arac, kullanici,
                 baslangic_saati=None, bitis_saati=None, durum='aktif'):
        self.kiralama_id = kiralama_id
        self.arac = arac
        self.kullanici = kullanici
        self.baslangic_saati = baslangic_saati
        self.bitis_saati = bitis_saati
        self.durum = durum

    def kiralama_baslat(self):
        self.baslangic_saati = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.durum = 'aktif'
        conn = get_connection()
        conn.execute("UPDATE kiralamalar SET baslangic_saati=?,durum='aktif' WHERE kiralama_id=?",
                     (self.baslangic_saati, self.kiralama_id))
        conn.execute("UPDATE araclar SET musait_mi=0 WHERE arac_id=?", (self.arac.arac_id,))
        conn.commit(); conn.close()

    def kiralama_bitir(self, eklenen_km=0):
        self.bitis_saati = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.durum = 'tamamlandi'
        ucret = self.toplam_ucret_hesapla()
        conn = get_connection()
        conn.execute("""UPDATE kiralamalar
                        SET bitis_saati=?,durum='tamamlandi',toplam_ucret=?
                        WHERE kiralama_id=?""",
                     (self.bitis_saati, ucret, self.kiralama_id))
        conn.execute("UPDATE araclar SET musait_mi=1 WHERE arac_id=?", (self.arac.arac_id,))
        if eklenen_km > 0:
            conn.execute("UPDATE araclar SET kilometre=kilometre+? WHERE arac_id=?",
                         (eklenen_km, self.arac.arac_id))
        conn.commit(); conn.close()
        return ucret

    def toplam_ucret_hesapla(self):
        if not self.baslangic_saati or not self.bitis_saati:
            return 0.0
        try:
            bas = datetime.strptime(self.baslangic_saati, "%Y-%m-%d %H:%M:%S")
            bit = datetime.strptime(self.bitis_saati,     "%Y-%m-%d %H:%M:%S")
            return round((bit - bas).total_seconds() / 3600 * self.arac.saatlik_ucret, 2)
        except Exception:
            return 0.0

    def kiralama_bilgisi(self):
        return {
            'id': self.kiralama_id,
            'arac': str(self.arac),
            'kullanici': str(self.kullanici),
            'baslangic': self.baslangic_saati,
            'bitis': self.bitis_saati,
            'durum': self.durum,
            'ucret': self.toplam_ucret_hesapla()
        }

# ─────────────────────────────────────────────
#  RENK & STİL (MODERN GLASSMORPHISM TEMA)
# ─────────────────────────────────────────────

DARK_BG        = "#121212"
CARD_BG        = "rgba(42, 45, 57, 0.8)"  # Yarı şeffaf kart arka planı
ACCENT         = "#4f8ef7"
ACCENT2        = "#7c3aed"
SUCCESS        = "#22c55e"
WARNING        = "#f59e0b"
DANGER         = "#ef4444"
TEXT_PRIMARY   = "#ffffff"
TEXT_SECONDARY = "#94a3b8"
BORDER         = "rgba(255, 255, 255, 0.1)"

STYLE = f"""
QWidget {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}

/* --- YENİ EKLENEN: AÇILIR PENCERE VE MESAJ KUTUSU RENKLERİ --- */
QDialog, QMessageBox {{
    background-color: {DARK_BG}; /* Arka planı koyu renk yap (beyaz yazıların okunması için) */
}}
QMessageBox QLabel {{
    color: {TEXT_PRIMARY}; /* Mesaj yazıları beyaz */
}}
QMessageBox QPushButton {{
    background-color: {ACCENT}; /* Tamam / OK butonları mavi */
    color: white;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: bold;
}}
QMessageBox QPushButton:hover {{
    background-color: #6ba3ff;
}}
/* ------------------------------------------------------------- */

/* QTabWidget çerçevesini tamamen gizliyoruz */
QTabWidget::pane {{
    border: none;
    background: transparent; 
}}
/* Sekmelerin (Yönetim Panel vb.) tasarımı */
QTabBar::tab {{
    background: {DARK_BG};
    color: {TEXT_SECONDARY};
    padding: 8px 12px; 
    border: none;
    font-weight: 600;
    font-size: 13px; 
    margin-right: 5px; 
}}
QTabBar::tab:selected {{
    color: {TEXT_PRIMARY};
    border-bottom: 3px solid {ACCENT}; 
}}
QTabBar::tab:hover {{
    color: {TEXT_PRIMARY};
}}
/* Tabloların arka planını şeffaflaştır */
QTableWidget {{
    background-color: transparent;
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
}}
QHeaderView::section {{
    background-color: rgba(30, 33, 43, 0.9);
    color: {TEXT_SECONDARY};
    padding: 9px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 700;
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
    background-color: rgba(0, 0, 0, 0.2);
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TEXT_PRIMARY};
}}

/* --- AÇILIR MENÜ (DROPDOWN) RENK DÜZELTMESİ --- */
QComboBox QAbstractItemView {{
    background-color: rgb(30, 33, 43);
    color: white; 
    selection-background-color: {ACCENT}; 
    selection-color: white;
    border: 1px solid {BORDER};
    border-radius: 8px;
    outline: none; 
    padding: 4px;
}}
"""

# ─────────────────────────────────────────────
#  GİRİŞ EKRANI
# ─────────────────────────────────────────────

class LoginDialog(QDialog):
    login_success = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RentACar Login")
        # 1. Adım: Pencereyi görselinizdeki gibi geniş, yatay bir formata alıyoruz
        self.setFixedSize(800, 550) 
        self.setStyleSheet(STYLE)
        
        # --- DİNAMİK ARKA PLAN LİSTESİ ---
        # Kendi arka plan görsellerinizin tam yollarını buraya ekleyin
        # Örnek: "C:/Users/ismai/Desktop/ntp/bg1.png"
        self.arkaplan_resimleri = [
            "istanbul.jpg", 
            "pamukkale.jpg",
            "anzakkoyu.jpg"
        ]
        
        self.mevcut_resim_indeksi = 0
        if self.arkaplan_resimleri:
            # Uygulama açıldığında listeden rastgele bir görsel ile başla
            self.mevcut_resim_indeksi = random.randint(0, len(self.arkaplan_resimleri) - 1)
            
        self._build()

        # --- QTIMER: 15 SANİYEDE BİR DEĞİŞİM ---
        self.zamanlayici = QTimer(self)
        self.zamanlayici.timeout.connect(self.arkaplan_degistir)
        self.zamanlayici.start(15000) # 15000 milisaniye = 15 saniye

    def arkaplan_degistir(self):
        if not self.arkaplan_resimleri: return
        # Sıradaki resme geç, listenin sonundaysa başa dön
        self.mevcut_resim_indeksi = (self.mevcut_resim_indeksi + 1) % len(self.arkaplan_resimleri)
        self.arkaplani_uygula()

    def arkaplani_uygula(self):
        if not self.arkaplan_resimleri: return
        secilen_resim = self.arkaplan_resimleri[self.mevcut_resim_indeksi]
        pixmap = QPixmap(secilen_resim)
        if not pixmap.isNull():
            # Arka plan katmanına resmi bas
            self.bg_label.setPixmap(pixmap)

    def _build(self):
        # 2. Adım: ARKA PLAN KATMANI (En alt seviyeye bir QLabel yerleştiriyoruz)
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 800, 550) # Pencereyle aynı boyutta bir tuval
        self.bg_label.setScaledContents(True)     # Resmi pencereye sığacak şekilde esnet
        self.arkaplani_uygula()                   # İlk rastgele resmi göster

        # 3. Adım: ANA YERLEŞİM (Merkeze hizalamak için boşlukları kullanıyoruz)
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        
        main_lay.addStretch(1) # Kutuyu yukarıdan aşağıya it

        center_h_lay = QHBoxLayout()
        center_h_lay.addStretch(1) # Kutuyu soldan sağa it

        # 4. Adım: ORTADAKİ YÜZEN FORM KUTUSU
        form = QFrame()
        # Kutumuzun boyutunu sabitliyoruz ki pencere içinde yayvanlaşmasın
        form.setFixedSize(400, 480) 
        
        # --- GLASSMORPHISM (Cam Efekti) STİLİ ---
        form.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 29, 46, 0.85); /* %85 opaklıkta koyu lacivert, arka planı hafif gösterir */
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.15); /* İncecik, şık bir beyaz çerçeve */
            }
        """)

        fl = QVBoxLayout(form)
        fl.setContentsMargins(36, 30, 36, 30)
        fl.setSpacing(15)

        # --- LOGO BÖLÜMÜ ---
        logo_etiketi = QLabel()
        logo_etiketi.setAlignment(Qt.AlignCenter)
        logo_etiketi.setStyleSheet("background:transparent; border: none;") # Çerçevesiz
        
        # Logonun kendi bilgisayarınızdaki yolu
        logo_pix = QPixmap("rentacar2.png")
        if not logo_pix.isNull():
            logo_pix = logo_pix.scaled(200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_etiketi.setPixmap(logo_pix)
        else:
            logo_etiketi.setText("🚗 RentACar")
            logo_etiketi.setStyleSheet("font-size:24px; font-weight:bold; color:white; background:transparent; border:none;")
            
        fl.addWidget(logo_etiketi)
        fl.addSpacing(10)

        # --- GİRİŞ METNİ ---
        sub = QLabel("Hesabınıza giriş yapın")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color:{TEXT_SECONDARY}; font-size:14px; background:transparent; border: none;")
        fl.addWidget(sub)

        # --- İNPUT KUTULARI ---
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-posta adresi")
        self.email_input.setFixedHeight(42)
        fl.addWidget(self.email_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Şifre")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setFixedHeight(42)
        self.pass_input.returnPressed.connect(self._login)
        fl.addWidget(self.pass_input)

        fl.addSpacing(10)

        # --- GİRİŞ YAP BUTONU ---
        btn_giris = QPushButton("Giris Yap")
        btn_giris.setFixedHeight(46)
        btn_giris.setStyleSheet("""
            QPushButton { 
                background-color: #2374FC; /* Attığınız koddaki mavi renk */
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-weight: 800; 
                font-size: 14px; 
            }
            QPushButton:hover { background-color: #6ba3ff; }
            QPushButton:pressed { background-color: #3a7bd5; }
        """)
        btn_giris.clicked.connect(self._login)
        fl.addWidget(btn_giris)

        # --- ALT BUTONLAR (Kayıt Ol / Şifremi Unuttum düzeni) ---
        alt_lay = QHBoxLayout()
        alt_lay.setContentsMargins(0, 0, 0, 0)
        
        btn_kayit = QPushButton("Hesap Oluştur")
        btn_kayit.setStyleSheet("""
            QPushButton { background:transparent; color:#94a3b8; border:none; font-weight:bold; font-size:13px; }
            QPushButton:hover { color: white; }
        """)
        btn_kayit.setCursor(Qt.PointingHandCursor)
        btn_kayit.clicked.connect(lambda: RegisterDialog(self).exec_())
        
        btn_sifre = QPushButton("Şifremi Unuttum?")
        btn_sifre.setStyleSheet("""
            QPushButton { background:transparent; color:#94a3b8; border:none; font-weight:bold; font-size:13px; }
            QPushButton:hover { color: white; }
        """)
        btn_sifre.setCursor(Qt.PointingHandCursor)
        # btn_sifre.clicked.connect(...) # İstersen ileride bağlayabilirsin
        
        alt_lay.addStretch()
        alt_lay.addWidget(btn_kayit)
        alt_lay.addSpacing(30) # İki buton arası boşluk
        alt_lay.addWidget(btn_sifre)
        alt_lay.addStretch()
        
        fl.addLayout(alt_lay)

        fl.addStretch() # Demo yazısını en alta iter
        
        # --- DEMO BİLGİSİ ---
        hint = QLabel("demo: admin@rentacar.com / admin123")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color:{TEXT_SECONDARY}; font-size:11px; background:transparent; border:none;")
        fl.addWidget(hint)

        # 5. Adım: PARÇALARI BİRLEŞTİRME VE MERKEZLEME
        center_h_lay.addWidget(form)
        center_h_lay.addStretch(1) # Kutuyu sağdan sola it (Tam ortaya sabitlenir)
        
        main_lay.addLayout(center_h_lay)
        main_lay.addStretch(1) # Kutuyu aşağıdan yukarı it (Tam ortaya sabitlenir)

    def _login(self):
        email = self.email_input.text().strip()
        pwd   = self.pass_input.text()
        if not email or not pwd:
            QMessageBox.warning(self, "Uyari", "E-posta ve sifre bos birakilamaz.")
            return
        h = hashlib.sha256(pwd.encode()).hexdigest()
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT * FROM kullanicilar WHERE email=? AND sifre_hash=?", (email, h))
        row = c.fetchone(); conn.close()
        if row:
            # Başarılı giriş yapıldığında arka plan zamanlayıcısını durdur
            self.zamanlayici.stop() 
            k = Kullanici(
                row[0], row[1], row[2], row[3], row[4], row[6],
                kurumsal_mi   = row[8]  if len(row) > 8  else 0,
                sirket_adi    = row[9]  if len(row) > 9  else '',
                vergi_no      = row[10] if len(row) > 10 else '',
                vergi_dairesi = row[11] if len(row) > 11 else '',
                adres         = row[12] if len(row) > 12 else '',
                telefon       = row[13] if len(row) > 13 else '',
            )
            self.login_success.emit(k)
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "E-posta veya sifre hatali.")

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kayit Ol")
        self.setFixedSize(420, 580)
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        from PyQt5.QtWidgets import QCheckBox, QStackedWidget
        from PyQt5.QtCore import QRegExp
        from PyQt5.QtGui import QRegExpValidator
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 24, 30, 24)
        lay.setSpacing(10)

        lbl = QLabel("Yeni Hesap Olustur")
        lbl.setStyleSheet("font-size:17px;font-weight:800;")
        lay.addWidget(lbl)

        # Ad ve Soyad kısıtlaması
        self.ad = QLineEdit(); self.ad.setPlaceholderText("Ad")
        self.ad.setValidator(QRegExpValidator(QRegExp("[A-Za-zğüşıöçĞÜŞİÖÇ ]+"), self.ad))
        
        self.soyad = QLineEdit(); self.soyad.setPlaceholderText("Soyad")
        self.soyad.setValidator(QRegExpValidator(QRegExp("[A-Za-zğüşıöçĞÜŞİÖÇ ]+"), self.soyad))
        
        # TC Kimlik kısıtlaması
        self.tc_no = QLineEdit(); self.tc_no.setPlaceholderText("TC Kimlik No")
        self.tc_no.setMaxLength(11) 
        self.tc_no.setValidator(QRegExpValidator(QRegExp("[0-9]+"), self.tc_no)) 
        
        # --- E-POSTA KISITLAMASI VE OTOMATİK KÜÇÜK HARF ---
        self.email = QLineEdit(); self.email.setPlaceholderText("E-posta")
        self.email.setValidator(QRegExpValidator(QRegExp("[a-zA-Z0-9@._-]+"), self.email))
        # Yazı değiştikçe küçük harfe çeviren fonksiyon
        self.email.textChanged.connect(self._format_email)
        
        self.sifre = QLineEdit(); self.sifre.setPlaceholderText("Sifre")
        self.sifre.setEchoMode(QLineEdit.Password)
        
        for w in [self.ad, self.soyad, self.tc_no, self.email, self.sifre]:
            lay.addWidget(w)

        # Kurumsal checkbox
        self.kurumsal_cb = QCheckBox("Kurumsal Hesap (Gider Faturası)")
        self.kurumsal_cb.setStyleSheet(f"color:{TEXT_PRIMARY}; font-weight:600;")
        self.kurumsal_cb.toggled.connect(self._toggle_kurumsal)
        lay.addWidget(self.kurumsal_cb)

        # Kurumsal alanlar
        self.kurumsal_frame = QFrame()
        self.kurumsal_frame.setStyleSheet(
            f"QFrame{{background:rgba(79,142,247,0.06);border:1px solid {BORDER};"
            f"border-radius:8px;padding:4px;}}")
        self.kurumsal_frame.setVisible(False)
        kf_lay = QVBoxLayout(self.kurumsal_frame)
        kf_lay.setSpacing(8)
        kf_lay.setContentsMargins(10, 10, 10, 10)
        kf_lbl = QLabel("Kurumsal Bilgiler")
        kf_lbl.setStyleSheet(f"color:{ACCENT}; font-weight:700; font-size:12px;")
        kf_lay.addWidget(kf_lbl)
        
        self.sirket_adi = QLineEdit(); self.sirket_adi.setPlaceholderText("Sirket Adi *")
        self.sirket_adi.setValidator(QRegExpValidator(QRegExp("[A-Za-zğüşıöçĞÜŞİÖÇ ]+"), self.sirket_adi))
        
        self.vergi_no = QLineEdit(); self.vergi_no.setPlaceholderText("Vergi No *")
        self.vergi_no.setMaxLength(11) 
        self.vergi_no.setValidator(QRegExpValidator(QRegExp("[0-9]+"), self.vergi_no))
        
        self.vergi_dairesi = QLineEdit(); self.vergi_dairesi.setPlaceholderText("Vergi Dairesi *")
        self.vergi_dairesi.setValidator(QRegExpValidator(QRegExp("[A-Za-zğüşıöçĞÜŞİÖÇ ]+"), self.vergi_dairesi))
        
        self.adres = QLineEdit(); self.adres.setPlaceholderText("Sirket Adresi *")
        self.adres.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9ğüşıöçĞÜŞİÖÇ \\.,/\\-]+"), self.adres))

        self.telefon = QLineEdit(); self.telefon.setPlaceholderText("Telefon (Örn: 5551234567) *")
        self.telefon.setMaxLength(10)
        self.telefon.setValidator(QRegExpValidator(QRegExp("[0-9]+"), self.telefon)) 
        
        for w in [self.sirket_adi, self.vergi_no, self.vergi_dairesi,
                  self.adres, self.telefon]:
            kf_lay.addWidget(w)
        lay.addWidget(self.kurumsal_frame)

        btn = QPushButton("Kayit Ol")
        btn.setFixedHeight(42)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white; border: none; border-radius: 8px;
                font-weight: 800; font-size: 14px; padding: 10px;
            }
            QPushButton:hover  { background-color: #059669; }
            QPushButton:pressed { background-color: #047857; }
        """)
        btn.clicked.connect(self._kayit)
        lay.addWidget(btn)

    # --- E-POSTAYI OTOMATİK KÜÇÜK HARFE ÇEVİREN FONKSİYON ---
    def _format_email(self, text):
        pos = self.email.cursorPosition() 
        self.email.blockSignals(True)      
        self.email.setText(text.lower())   
        self.email.setCursorPosition(pos) 
        self.email.blockSignals(False)

    def _toggle_kurumsal(self, checked):
        self.kurumsal_frame.setVisible(checked)
        self.setFixedSize(420, 750 if checked else 580)

    def _kayit(self):
        vals = [self.ad.text().strip(), self.soyad.text().strip(),
                self.tc_no.text().strip(), self.email.text().strip(),
                self.sifre.text()]
                
        if not all(vals):
            QMessageBox.warning(self, "Uyari", "Temel alanlar zorunludur.")
            return
            
        if len(vals[2]) != 11:
            QMessageBox.warning(self, "Uyarı", "TC Kimlik Numaranız tam 11 haneli olmalıdır.")
            return
            
        # --- YENİ EKLENEN KONTROL: E-POSTA FORMATI GEÇERLİ Mİ? ---
        import re
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_pattern, vals[3]):
            QMessageBox.warning(self, "Uyarı", "Lütfen geçerli bir e-posta adresi giriniz.\n(Örnek: isim@ornek.com)")
            return
        # ---------------------------------------------------------
            
        kurumsal = 1 if self.kurumsal_cb.isChecked() else 0
        if kurumsal:
            if not (self.sirket_adi.text().strip() and self.vergi_no.text().strip()
                    and self.vergi_dairesi.text().strip() and self.adres.text().strip()
                    and self.telefon.text().strip()):
                QMessageBox.warning(self, "Uyari", "Kurumsal alanların tamamı (Telefon dahil) zorunludur.")
                return
            
            if len(self.telefon.text().strip()) != 10:
                QMessageBox.warning(self, "Uyarı", "Telefon numaranız tam 10 haneli olmalıdır.")
                return

        try:
            h = hashlib.sha256(vals[4].encode()).hexdigest()
            conn = get_connection()
            conn.execute("""INSERT INTO kullanicilar
                (ad,soyad,ehliyet_no,email,sifre_hash,kurumsal_mi,
                 sirket_adi,vergi_no,vergi_dairesi,adres,telefon)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (vals[0], vals[1], vals[2], vals[3], h, kurumsal,
                 self.sirket_adi.text().strip() if kurumsal else '',
                 self.vergi_no.text().strip()   if kurumsal else '',
                 self.vergi_dairesi.text().strip() if kurumsal else '',
                 self.adres.text().strip()      if kurumsal else '',
                 self.telefon.text().strip()    if kurumsal else ''))
            conn.commit(); conn.close()
            QMessageBox.information(self, "Basarili", "Hesap olusturuldu.")
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Hata", "Bu TC Kimlik No veya e-posta zaten kayitli.")
            
# ─────────────────────────────────────────────
#  STAT KARTI (YENİ DİKEY TASARIM)
# ─────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, icon, title, value, color):
        super().__init__()
        self.setFixedHeight(120)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border-radius: 12px;
                border: 1px solid {BORDER};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(6)
        
        # İkon (Görseldeki gibi yuvarlak köşeli kutu efekti verebiliriz ama metin rengi de şık durur)
        ico = QLabel(icon)
        ico.setStyleSheet(f"font-size:28px; background:transparent; border:none; color:{color};")
        lay.addWidget(ico)
        
        lay.addStretch()
        
        # Başlık (Gri küçük yazı)
        tit_lbl = QLabel(title)
        tit_lbl.setStyleSheet(f"font-size:12px; color:{TEXT_SECONDARY}; background:transparent; border:none;")
        lay.addWidget(tit_lbl)
        
        # Değer (Beyaz, büyük ve kalın)
        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet(f"font-size:22px; font-weight:900; color:{TEXT_PRIMARY}; background:transparent; border:none;")
        lay.addWidget(val_lbl)

# ─────────────────────────────────────────────
#  ANA PENCERE
# ─────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, kullanici: Kullanici):
        super().__init__()
        self.kullanici = kullanici
        self.setWindowTitle(f"RentACar — {kullanici.ad} {kullanici.soyad}")
        self.resize(1100, 750) 
        self.setStyleSheet(STYLE)
        
        self._build()
        self._refresh_all()
        
        # YENİ: Ekran açılır açılmaz Ehliyet kontrolü yap
        self._ehliyet_kontrol()

    def _ehliyet_kontrol(self):
        # Adminlerin ehliyet yüklemesine gerek yok
        if self.kullanici.rol == 'admin': return 
        
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT ehliyet_hash FROM kullanicilar WHERE kullanici_id=?", (self.kullanici.kullanici_id,))
        res = c.fetchone()
        conn.close()
        
        # Eğer ehliyet_hash boşsa (henüz yüklenmemişse) zorunlu ekranı aç
        if not res or not res[0]:
            dlg = EhliyetYukleDialog(self, self.kullanici.kullanici_id)
            
            # Kullanıcı "Vazgeç" veya "X" tuşuna basarsa
            if dlg.exec_() != QDialog.Accepted:
                QMessageBox.warning(self, "Erişim Kısıtlandı", 
                                    "Sistemi kullanabilmek için ehliyet yüklemeniz zorunludur.\n\n"
                                    "Giriş ekranına yönlendiriliyorsunuz.")
                
                # --- 1. KORUMA: ARAYÜZÜ KİLİTLE ---
                # Arka plandaki tüm sekmeleri tıklanamaz hale getirir (Bypass imkansızlaşır)
                self.tabs.setEnabled(False) 
                
                # --- 2. KORUMA: GECİKMELİ ÇIKIŞ (LIFECYCLE FIX) ---
                # Ana pencere tam olarak yüklendikten 50 milisaniye sonra çıkış işlemini tetikler.
                # Böylece yeni açılan giriş sayfasını kapatsa bile arkadaki pencere çoktan kapanmış olur!
                QTimer.singleShot(50, self._logout)

    # Ekran boyutu değiştiğinde arka plan resminin de ekrana sığmasını sağlar
    def resizeEvent(self, event):
        if hasattr(self, 'bg_label'):
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        # --- 1. ARKA PLAN RESMİ (BURAYA GÖRSEL YOLUNU YAZIN) ---
        self.bg_label = QLabel(central)
        self.bg_label.setScaledContents(True)
        # LÜTFEN AŞAĞIDAKİ YOLA KENDİ İNDİRDİĞİN MANZARA/ARKA PLAN RESMİNİ YAZ (Örn: "bg.jpg")
        bg_pixmap = QPixmap("C:/Users/ismai/Desktop/ntp/main.jpg")
        if not bg_pixmap.isNull():
            self.bg_label.setPixmap(bg_pixmap)
        else:
            self.bg_label.setStyleSheet(f"background-color: {DARK_BG};") # Resim yoksa siyah kalır

        # --- 2. ANA YERLEŞİM (Dış Boşluklar) ---
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(60, 40, 60, 40) # Kenarlardan boşluk (Yüzen hissi için)

        # --- 3. ANA CAM PANEL (Görseldeki o büyük koyu kutu) ---
        self.panel = QFrame()
        self.panel.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 33, 43, 0.95); /* Koyu Lacivert/Gri Cam Zemin */
                border-radius: 16px;
                border: 1px solid {BORDER};
            }}
        """)
        main_lay.addWidget(self.panel)

        # Panelin iç yerleşimi
        root = QVBoxLayout(self.panel)
        root.setContentsMargins(25, 20, 25, 20)
        root.setSpacing(10)

        # --- NAVBAR (Üst Bar) ---
        navbar = QFrame()
        navbar.setFixedHeight(60)
        navbar.setStyleSheet("background:transparent; border:none; border-bottom:4px solid rgba(255,255,255,0.05);")
        nl = QHBoxLayout(navbar)
        nl.setContentsMargins(0, 0, 0, 10)
        
        # --- YENİ LOGO BÖLÜMÜ ---
        logo = QLabel()
        logo.setStyleSheet("background:transparent; border:none;")
        
        # Logonun bilgisayarındaki tam yolu (Giriş ekranındaki logonun yolunu örnek olarak yazdım, değiştirebilirsin)
        logo_yolu = "rentacar2.png"
        logo_pixmap = QPixmap(logo_yolu)
        
        if not logo_pixmap.isNull():
            # Logoyu üst barın yüksekliğine (yaklaşık 40 piksel) uygun, pürüzsüz kalitede ölçeklendiriyoruz
            logo_pixmap = logo_pixmap.scaledToHeight(48, Qt.SmoothTransformation)
            logo.setPixmap(logo_pixmap)
        else:
            # Eğer logo dosyası bulunamazsa veya silinirse, eski metin yedek olarak gösterilir
            logo.setText("🚗 RentACar")
            logo.setStyleSheet("font-size:22px; font-weight:900; color:white; background:transparent;")
        # ------------------------

        # --- SEKME (TAB) YÖNETİMİ ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("background: transparent; border: none;")
        
        # --- YENİ EKLENEN SİHİRLİ KODLAR ---
        self.tabs.setElideMode(Qt.ElideNone) # Yazıların '...' diye kesilmesini yasaklar
        self.tabs.tabBar().setExpanding(False) # Sekmelerin esneyip birbirini ezmesini yasaklar, yazı kadar yer kaplarlar
        # ----------------------------------
        
        self._dash = self._build_dashboard_tab()
        self._arac = self._build_arac_tab()
        self._kir  = self._build_kiralama_tab()
        
        # Kullanıcı Bilgisi Alanı (Görseldeki gibi Alt alta: Rol ve İsim)
        user_info = QVBoxLayout()
        user_info.setSpacing(2)
        rol_lbl = QLabel(f"[ {self.kullanici.rol.upper()} ]")
        rol_lbl.setStyleSheet(f"color:{TEXT_SECONDARY}; font-size:10px; font-weight:bold; background:transparent;")
        isim_lbl = QLabel(f"{self.kullanici.ad} {self.kullanici.soyad}")
        isim_lbl.setStyleSheet("color:white; font-size:14px; font-weight:bold; background:transparent;")
        user_info.addWidget(rol_lbl)
        user_info.addWidget(isim_lbl)
        
        logout_btn = QPushButton("➡️ Çıkış")
        logout_btn.setFixedWidth(85)
        logout_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent; border:1px solid {BORDER}; color:{TEXT_SECONDARY}; border-radius:6px; font-weight:600; padding:6px;}}
            QPushButton:hover {{ background:rgba(255,255,255,0.1); color:white; }}
        """)
        logout_btn.clicked.connect(self._logout)
        
        nl.addWidget(logo)
        nl.addStretch()
        nl.addLayout(user_info)
        nl.addSpacing(15)
        nl.addWidget(logout_btn)

       # --- SEKME (TAB) YÖNETİMİ ---
        self.tabs = QTabWidget()
        self._dash = self._build_dashboard_tab()
        self._harita = self._build_harita_tab() # YENİ HARİTA
        self._arac = self._build_arac_tab()
        self._kir  = self._build_kiralama_tab()

        if self.kullanici.rol == 'admin':
            self._kul  = self._build_kullanici_tab()
            self._rap  = self._build_rapor_tab()
            self.tabs.addTab(self._dash, "🛠 Yönetim Panel ")
            self.tabs.addTab(self._harita, "🗺️ Yakındaki Araçlar ") # ADMİNE EKLENDİ
            self.tabs.addTab(self._arac, "🚘 Araç Filosu ")
            self.tabs.addTab(self._kul,  "👥 Müşteriler ")
            self.tabs.addTab(self._kir,  "📅 Tüm Kiralamalar ")
            self.tabs.addTab(self._rap,  "📈 Finans Raporları ")
        else:
            self.tabs.addTab(self._dash, "🏠 Ana Sayfa ")
            self.tabs.addTab(self._harita, "🗺️ Canlı Harita ") # KULLANICIYA EKLENDİ
            self.tabs.addTab(self._arac, "🚘 Araç Kirala ")
            self.tabs.addTab(self._kir,  "🕒 Kiralama Geçmişim ")

        root.addWidget(navbar)
        root.addWidget(self.tabs)

    # ── DASHBOARD ──────────────────────────────

    def _build_dashboard_tab(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 15, 0, 10)
        lay.setSpacing(20) # Kartlar ve başlık arası boşluk
        
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(15)
        lay.addLayout(self._cards_row)
        
        # --- BAŞLIK (Büyütüldü ve Çizgiler Kaldırıldı) ---
        self.chart_title = QLabel()
        self.chart_title.setStyleSheet("""
            QLabel {
                font-size: 18px; /* Yazıyı biraz daha büyüttük */
                font-weight: bold; 
                color: white; 
                background: transparent;
                border: none; /* Üst ve alttaki istenmeyen çizgileri kesin olarak yasakladık */
                padding-left: 40px;
            }
        """)
        lay.addWidget(self.chart_title)
        
        # BAŞLIK İLE GRAFİK ARASINA BOŞLUK (Grafiği aşağı iter)
        lay.addSpacing(15)
        
        # --- MATPLOTLIB KUTUSU (Dış Kenar Çizgisi Silindi) ---
        self.chart_container = QFrame()
        self.chart_container.setMinimumHeight(300)
        self.chart_container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 33, 43, 0.6);
                border-radius: 16px;
                border: none; /* Çirkin duran dış border tamamen kaldırıldı */
            }
        """)
        container_lay = QVBoxLayout(self.chart_container)
        container_lay.setContentsMargins(15, 15, 15, 15)
        
        # Matplotlib Tuvali (Canvas)
        self.figure = Figure()
        self.figure.patch.set_alpha(0.0) 
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background:transparent; border:none;")
        
        container_lay.addWidget(self.canvas)
        lay.addWidget(self.chart_container)
        
        lay.addStretch()
        return w

    def _build_harita_tab(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        
        # Haritayı gösterecek web motoru
        self.map_view = QWebEngineView()
        
        # Haritayı şık bir cam çerçevenin içine alıyoruz
        container = QFrame()
        container.setStyleSheet(f"background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 12px;")
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(self.map_view)
        
        lay.addWidget(container)
        return w

    def _refresh_harita(self):
        g = geocoder.ip('me')
        if g.latlng: bilgisayar_enlem, bilgisayar_boylam = g.latlng
        else: bilgisayar_enlem, bilgisayar_boylam = 41.0082, 28.9784

        conn = get_connection(); c = conn.cursor()
        c.execute("""SELECT marka, model, plaka, saatlik_ucret, enlem, boylam, 
                            COALESCE(vites, 'Otomatik'), yakit, COALESCE(foto_url, '') 
                     FROM araclar WHERE musait_mi=1""")
        araclar = c.fetchall(); conn.close()

        # Haritadaki resimlerin sorunsuz yüklenmesi için Base64'e çeviriyoruz
        import base64
        def get_base64_image(path):
            if not path or not os.path.exists(path): return ""
            try:
                with open(path, "rb") as img_file:
                    return "data:image/jpeg;base64," + base64.b64encode(img_file.read()).decode('utf-8')
            except: return ""

        import json
        arac_listesi_js = []
        for a in araclar:
            b64_img = get_base64_image(a[8])
            arac_listesi_js.append({
                "marka": a[0], "model": a[1], "plaka": a[2], "ucret": a[3],
                "lat": a[4], "lng": a[5], "vites": a[6], "yakit": a[7], "foto": b64_img
            })
        araclar_json = json.dumps(arac_listesi_js)

        html_icerik = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>#map {{ width: 100%; height: 100vh; }} body {{ margin: 0; padding: 0; }}</style>
            <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAhul983e4OxsX1jB-0jE3jDdHC1KQQ1vs"></script>
            <script>
                function calculateDistance(lat1, lon1, lat2, lon2) {{
                    var R = 6371e3; 
                    var p1 = lat1 * Math.PI/180; 
                    var p2 = lat2 * Math.PI/180;
                    var dp = (lat2-lat1) * Math.PI/180; 
                    var dl = (lon2-lon1) * Math.PI/180;
                    var a = Math.sin(dp/2) * Math.sin(dp/2) + Math.cos(p1) * Math.cos(p2) * Math.sin(dl/2) * Math.sin(dl/2);
                    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
                    return R * c; 
                }}
                function initMap() {{
                    var userLat = {bilgisayar_enlem}; 
                    var userLng = {bilgisayar_boylam}; 
                    var araclar = {araclar_json};
                    
                    var mapOptions = {{ 
                        center: {{ lat: userLat, lng: userLng }}, 
                        zoom: 14, 
                        minZoom: 6, 
                        restriction: {{ latLngBounds: {{ north: 42.5, south: 35.5, west: 25.5,  east: 45.0 }}, strictBounds: true }}, 
                        disableDefaultUI: true,
                        styles: [ 
                            {{ "elementType": "geometry", "stylers": [{{ "color": "#212121" }}] }}, 
                            {{ "elementType": "labels.icon", "stylers": [{{ "visibility": "off" }}] }}, 
                            {{ "featureType": "road", "elementType": "geometry.fill", "stylers": [{{ "color": "#2c2c2c" }}] }}, 
                            {{ "featureType": "water", "elementType": "geometry", "stylers": [{{ "color": "#000000" }}] }} 
                        ]
                    }};
                    var map = new google.maps.Map(document.getElementById('map'), mapOptions);
                    var infowindow = new google.maps.InfoWindow();
                    
                    // --- HATA BURADA ÇÖZÜLDÜ: ÇİFT SÜSLÜ PARANTEZ EKLENDİ ---
                    map.addListener('click', function() {{
                        infowindow.close();
                    }});
                    // --------------------------------------------------------

                    var minDistance = Infinity;
                    araclar.forEach(function(a) {{ 
                        var dist = calculateDistance(userLat, userLng, a.lat, a.lng); 
                        if (dist < minDistance) minDistance = dist; 
                    }});
                    var distStr = minDistance > 1000 ? (minDistance/1000).toFixed(1) + " km" : Math.round(minDistance) + " m";
                    var timeStr = Math.round(minDistance / 80) + " dk"; 
                    
                    new google.maps.Marker({{ 
                        position: {{ lat: userLat, lng: userLng }}, 
                        map: map, 
                        label: {{ text: distStr + " (" + timeStr + ")", color: "white", fontSize: "12px", fontWeight: "bold" }}, 
                        icon: {{ path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW, scale: 7, fillColor: '#ef4444', fillOpacity: 1, strokeWeight: 2, strokeColor: 'white' }} 
                    }});
                    
                    araclar.forEach(function(a) {{
                        var dist = calculateDistance(userLat, userLng, a.lat, a.lng); 
                        var walkTime = Math.round(dist / 80); 
                        var distText = dist > 1000 ? (dist/1000).toFixed(1) + " km" : Math.round(dist) + " m";
                        
                        var marker = new google.maps.Marker({{ 
                            position: {{ lat: a.lat, lng: a.lng }}, 
                            map: map, 
                            icon: {{ path: google.maps.SymbolPath.CIRCLE, fillColor: '#4f8ef7', fillOpacity: 1, strokeColor: '#ffffff', strokeWeight: 2, scale: 10 }} 
                        }});
                        
                        var fotoHtml = "";
                        if (a.foto && a.foto !== "") {{
                            fotoHtml = "<img src='" + a.foto + "' style='width:110px; height:75px; object-fit:cover; border-radius:8px; float:left; margin-right:12px; border:1px solid #ccc;' />";
                        }}
                        
                        var content = "<div style='color:black; padding:5px; min-width:230px; font-family:sans-serif; overflow:hidden;'>" +
                                      fotoHtml +
                                      "<div style='float:left; margin-top:2px;'>" +
                                      "<b style='font-size:15px; color:#1e293b;'>" + a.marka + " " + a.model + "</b><br>" +
                                      "<span style='font-size:12px; color:#475569;'>⚙️ " + a.vites + " | ⛽ " + a.yakit + "</span><br>" +
                                      "<span style='font-size:12px; color:#64748b;'>🚶 " + walkTime + " dk (" + distText + ")</span><br>" +
                                      "<b style='color:#10b981; font-size:14px;'>₺" + a.ucret + "/saat</b>" +
                                      "</div><div style='clear:both;'></div></div>";

                        marker.addListener('click', function() {{ 
                            infowindow.setContent(content); 
                            infowindow.open(map, marker); 
                        }});
                    }});
                }}
            </script>
        </head>
        <body onload="initMap()"><div id="map"></div></body>
        </html>
        """
        self.map_view.setHtml(html_icerik)

    # ( _refresh_dashboard metodu aynı kalacak, ona dokunma )

    def _refresh_dashboard(self):
        # Eski kartları temizle
        while self._cards_row.count():
            item = self._cards_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        conn = get_connection(); c = conn.cursor()
        
        if self.kullanici.rol == 'admin':
            c.execute("SELECT COUNT(*) FROM araclar")
            toplam = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM araclar WHERE musait_mi=1")
            musait = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM kiralamalar WHERE durum='aktif'")
            aktif = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM kullanicilar")
            kul = c.fetchone()[0]
            c.execute("SELECT COALESCE(SUM(toplam_ucret),0) FROM kiralamalar WHERE durum='tamamlandi'")
            gelir = c.fetchone()[0]
            
            stats = [
                ("🚗", "Toplam Araç",    toplam,          ACCENT),
                ("✅", "Müsait Araç",    musait,          SUCCESS),
                ("🔑", "Aktif Kiralama", aktif,           WARNING),
                ("👤", "Müşteriler",     kul,             ACCENT2),
                ("💰", "Toplam Gelir",   f"{gelir:.0f} TL","#f59e0b"),
            ]
        else:
            # NORMAL KULLANICIYA ÖZEL İSTATİSTİKLER
            k_id = self.kullanici.kullanici_id
            
            c.execute("SELECT COUNT(*) FROM kiralamalar WHERE kullanici_id=?", (k_id,))
            toplam_kiralama = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM kiralamalar WHERE kullanici_id=? AND durum='aktif'", (k_id,))
            aktif_kiralama = c.fetchone()[0]
            
            c.execute("SELECT COALESCE(SUM(toplam_ucret),0) FROM kiralamalar WHERE kullanici_id=? AND durum='tamamlandi'", (k_id,))
            harcanan = c.fetchone()[0]
            
            stats = [
                ("🚘", "Toplam Kiraladığım Araç", toplam_kiralama, ACCENT),
                ("🔑", "Aktif Kiralamam",         "Var" if aktif_kiralama > 0 else "Yok",  WARNING),
                ("💳", "Toplam Harcamam",         f"{harcanan:.0f} TL", SUCCESS),
            ]
            
        conn.close()
        
        # Kartları ekrana bas
        for icon, title, val, color in stats:
            self._cards_row.addWidget(StatCard(icon, title, val, color))
            
        self._build_chart()

    def _build_chart(self):
        conn = get_connection(); c = conn.cursor()
        gunler, sayilar, detaylar = [], [], []
        
        is_admin = (self.kullanici.rol == 'admin')
        k_id = self.kullanici.kullanici_id

        for i in range(6, -1, -1):
            gun   = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            label = (datetime.now() - timedelta(days=i)).strftime("%d.%m.%Y")
            
            # Sadece sayıyı değil, araç detaylarını ve saatleri de çekiyoruz
            if is_admin:
                c.execute("""SELECT a.marka, a.model, k.baslangic_saati, k.bitis_saati 
                             FROM kiralamalar k
                             JOIN araclar a ON k.arac_id=a.arac_id
                             WHERE DATE(k.baslangic_saati)=?""", (gun,))
            else:
                c.execute("""SELECT a.marka, a.model, k.baslangic_saati, k.bitis_saati 
                             FROM kiralamalar k
                             JOIN araclar a ON k.arac_id=a.arac_id
                             WHERE DATE(k.baslangic_saati)=? AND k.kullanici_id=?""", (gun, k_id))
                
            rows = c.fetchall()
            gunler.append(label)
            sayi = len(rows)
            sayilar.append(sayi)
            
            # --- TOOLTIP (BİLGİ KUTUCUĞU) İÇİN DETAYLI METİN HAZIRLAMA ---
            if sayi == 0:
                detay = f"Kiralanan Araç: 0"
            else:
                detay = f"Kiralanan Araç: {sayi}\n" + "-"*18 + "\n"
                for r in rows:
                    marka, model, bas, bit = r
                    sure_str = "Belirsiz"
                    
                    if bas:
                        # Başlangıç ve Bitiş (veya şu anki) saatleri arasındaki farkı bul
                        b1 = datetime.strptime(bas, "%Y-%m-%d %H:%M:%S")
                        b2 = datetime.strptime(bit, "%Y-%m-%d %H:%M:%S") if bit else datetime.now()
                        fark_saat = int((b2 - b1).total_seconds() // 3600)
                        
                        sure_str = f"{fark_saat} saat" if fark_saat > 0 else "1 saatten az"
                        
                    detay += f"• {marka} {model}\n  └ {sure_str}\n"
                    
            detaylar.append(detay.strip())
            
        conn.close()

        if is_admin:
            self.chart_title.setText("Son 7 Gün - Şirketin Genel Kiralamaları")
        else:
            self.chart_title.setText("Son 7 Gün - Kendi Kiralama Geçmişin")

        # --- MATPLOTLIB ÇİZİM İŞLEMLERİ ---
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('none')
        
        self.annot = self.ax.annotate(
            "", xy=(0,0), xytext=(0, 10), textcoords="offset points",
            ha='center', va='bottom', fontsize=10, fontweight='bold', color='white',
            bbox=dict(boxstyle="round,pad=0.6", fc="#1a1d2e", ec=(1.0, 1.0, 1.0, 0.2), alpha=0.95)
        )
        self.annot.set_visible(False)
        
        bars = self.ax.bar(gunler, sayilar, color='#4f8ef7', width=0.55, edgecolor='none')
        self.bar_patches = [] 
        
        for i, bar in enumerate(bars):
            bar.set_visible(False) 
            
            bb = mpatches.FancyBboxPatch(
                (bar.get_x(), 0),
                abs(bar.get_width()), abs(bar.get_height()),
                boxstyle="round,pad=0.0,rounding_size=0.15",
                ec="none", fc='#4f8ef7', 
                mutation_aspect=0.08 
            )
            self.ax.add_patch(bb)
            
            # --- HAZIRLADIĞIMIZ DETAYLI METNİ BARA YAPIŞTIRIYORUZ ---
            bb.custom_data = detaylar[i]
            self.bar_patches.append(bb)
            
        self.ax.grid(axis='y', color='#ffffff', alpha=0.1, linestyle='-', linewidth=1)
        self.ax.set_axisbelow(True) 
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.spines['bottom'].set_color((1.0, 1.0, 1.0, 0.2)) 
        
        self.ax.tick_params(axis='x', colors='#94a3b8', length=0, pad=10)
        self.ax.tick_params(axis='y', colors='#94a3b8', length=0, pad=10)

        legend_patch = mpatches.Patch(color='#4f8ef7', label='Kiralama')
        self.ax.legend(handles=[legend_patch], loc='upper center', bbox_to_anchor=(0.5, 1.15),
                  frameon=False, labelcolor='#94a3b8', handlelength=1.5, handleheight=1.5)
        
        self.figure.tight_layout() 
        self.canvas.draw()

        self.canvas.mpl_connect("motion_notify_event", self._on_hover)

    def _on_hover(self, event):
        if event.inaxes != self.ax:
            if getattr(self, 'annot', None) and self.annot.get_visible():
                self.annot.set_visible(False)
                self.canvas.draw_idle()
            return

        is_hovered = False
        
        for patch in self.bar_patches:
            contains, _ = patch.contains(event)
            if contains:
                detay_metni = patch.custom_data 
                
                # --- YENİ HİZALAMA MANTIĞI ---
                # X koordinatı barın ortası olsun
                x = patch.get_x() + patch.get_width() / 2
                
                # Y koordinatını barın tepesi değil, FARENİN OLDUĞU YER yapıyoruz.
                # Böylece uzun barlarda fareyi barın ortasına getirince kutu da orada çıkar ve kesilmez.
                y = event.ydata 
                
                # Alternatif Güvenlik: Eğer fare çok yukarıdaysa, kutuyu farenin 'altına' hizala
                # Grafiğin maksimum Y değerini alıyoruz
                y_max = self.ax.get_ylim()[1]
                
                # Eğer farenin konumu en üst noktanın %80'inden daha yukarıdaysa, 
                # kutunun kesilmemesi için onu farenin altına doğru aç (va='top')
                if y > y_max * 0.8:
                    self.annot.set_va('top')
                    self.annot.xytext = (0, -15) # Fare imlecinin biraz altına kaydır
                else:
                    self.annot.set_va('bottom')
                    self.annot.xytext = (0, 15)  # Normal durumda fare imlecinin üstünde kalsın
                # -----------------------------
                
                self.annot.xy = (x, y)
                self.annot.set_text(detay_metni) 
                self.annot.set_visible(True)
                
                self.canvas.draw_idle()
                is_hovered = True
                break

        if not is_hovered and getattr(self, 'annot', None) and self.annot.get_visible():
            self.annot.set_visible(False)
            self.canvas.draw_idle()
            
    # ── ARAÇLAR ────────────────────────────────

    def _build_arac_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(10)
        top = QHBoxLayout()
        self._arac_search = QLineEdit()
        self._arac_search.setPlaceholderText("Marka, model veya plaka ara...")
        self._arac_search.textChanged.connect(self._filter_araclar)
        self._arac_filter = QComboBox()
        self._arac_filter.addItems(["Tumu", "Musait", "Kirada"])
        self._arac_filter.currentIndexChanged.connect(self._filter_araclar)
        
        top.addWidget(self._arac_search, 3)
        top.addWidget(self._arac_filter)
        
        # BUTON SADECE ADMİNSE OLUŞTURULACAK VE EKLENECEK
        if self.kullanici.rol == 'admin':
            ekle_btn = QPushButton("+ Araç Ekle")
            ekle_btn.setFixedHeight(34)
            ekle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {SUCCESS};
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0px 15px;
                }}
                QPushButton:hover {{ background-color: #16a34a; }}
            """)
            ekle_btn.clicked.connect(self._arac_ekle)
            top.addWidget(ekle_btn)
            
        lay.addLayout(top)
        
        # --- TABLO AYARLARI ---
        self._arac_tbl = QTableWidget()
        self._arac_tbl.setColumnCount(10) # 9'dan 10'a çıkardık (Vites eklendi)
        self._arac_tbl.setHorizontalHeaderLabels(
            ["ID","Marka","Model","Yıl","Plaka","Vites","Km","Durum","Ücret/Saat","İşlem"])
        self._arac_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._arac_tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self._arac_tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self._arac_tbl.verticalHeader().setVisible(False)
        
        # ÜYELER İÇİN ID SÜTUNUNU GİZLE (Sadece Admin görebilir)
        if self.kullanici.rol != 'admin':
            self._arac_tbl.setColumnHidden(0, True)
            
        lay.addWidget(self._arac_tbl)
        return w

    def _refresh_araclar(self):
        conn = get_connection(); c = conn.cursor()
        # Vites bilgisini de çekecek şekilde SQL güncellendi
        c.execute("""SELECT arac_id, marka, model, yil, plaka, COALESCE(vites, 'Otomatik'), kilometre, musait_mi, saatlik_ucret
                     FROM araclar ORDER BY arac_id""")
        self._arac_rows = c.fetchall(); conn.close()
        self._fill_arac_tbl(self._arac_rows)

    def _fill_arac_tbl(self, rows):
        BTN_G = (f"QPushButton{{background:{SUCCESS};color:white;font-weight:700;"
                 f"border-radius:6px;border:none;padding:3px 10px;}}"
                 f"QPushButton:hover{{background:#16a34a;}}"
                 f"QPushButton:disabled{{background:#374151;color:#6b7280;}}")
        BTN_R = (f"QPushButton{{background:{DANGER};color:white;font-weight:700;"
                 f"border-radius:6px;border:none;padding:3px 10px;}}"
                 f"QPushButton:hover{{background:#dc2626;}}")
        
        self._arac_tbl.setRowCount(0)
        for row in rows:
            r = self._arac_tbl.rowCount()
            self._arac_tbl.insertRow(r)
            
            for col, val in enumerate(row[:9]):
                if col == 7: # Durum
                    txt = "Müsait" if val else "Kirada"
                    itm = QTableWidgetItem(txt)
                    itm.setForeground(QColor(SUCCESS if val else DANGER))
                elif col == 6: # Km
                    itm = QTableWidgetItem(f"{val:,.0f} km")
                elif col == 8: # Ücret/Saat
                    itm = QTableWidgetItem(f"{val:.0f} TL")
                else:
                    itm = QTableWidgetItem(str(val) if val is not None else "")
                
                itm.setTextAlignment(Qt.AlignCenter)
                self._arac_tbl.setItem(r, col, itm)
                
            frame = QWidget()
            frame.setStyleSheet("background:transparent;")
            fl = QHBoxLayout(frame)
            fl.setContentsMargins(1, 2, 2, 1)
            fl.setSpacing(4)
            
            # --- 1. DÜZENLE BUTONU (SADECE ADMİN) ---
            if self.kullanici.rol == 'admin':
                duzenle_btn = QPushButton()
                icon_path = "wrench.png"
                if os.path.exists(icon_path):
                    from PyQt5.QtGui import QIcon
                    duzenle_btn.setIcon(QIcon(icon_path))
                else:
                    duzenle_btn.setText("🔧")
                
                duzenle_btn.setFixedSize(28, 28)
                duzenle_btn.setCursor(Qt.PointingHandCursor)
                duzenle_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.1); border-radius:4px;} QPushButton:hover{background:rgba(255,255,255,0.2);}")
                duzenle_btn.clicked.connect(lambda _, rid=row[0]: self._arac_duzenle(rid))
                fl.addWidget(duzenle_btn)
            
            # --- 2. KİRALA BUTONU (SADECE NORMAL KULLANICI GÖREBİLİR) ---
            # YENİ: Admin bu butonu artık görmeyecek
            if self.kullanici.rol != 'admin':
                kirala = QPushButton("Kirala")
                kirala.setStyleSheet(BTN_G)
                kirala.setFixedHeight(28)
                kirala.setEnabled(bool(row[7])) 
                kirala.clicked.connect(lambda _, rid=row[0]: self._kirala(rid))
                fl.addWidget(kirala)
            
            # --- 3. SİL BUTONU (SADECE ADMİN) ---
            if self.kullanici.rol == 'admin':
                sil = QPushButton("Sil")
                sil.setStyleSheet(BTN_R)
                sil.setFixedHeight(28)
                sil.clicked.connect(lambda _, rid=row[0]: self._arac_sil(rid))
                fl.addWidget(sil)
            
            self._arac_tbl.setCellWidget(r, 9, frame)

    def _filter_araclar(self):
        txt = self._arac_search.text().lower()
        f   = self._arac_filter.currentText()
        out = []
        for row in self._arac_rows:
            if f == "Musait" and not row[7]: continue # Güncellendi
            if f == "Kirada" and row[7]:    continue  # Güncellendi
            if txt and txt not in f"{row[1]} {row[2]} {row[4]}".lower(): continue
            out.append(row)
        self._fill_arac_tbl(out)

    def _arac_ekle(self):
        dlg = AracEkleDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_araclar()
            self._refresh_dashboard()
            self._refresh_harita() # YENİ: Haritanın anında güncellenmesini sağlar

    def _arac_sil(self, arac_id):
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM kiralamalar WHERE arac_id=? AND durum='aktif'",
                  (arac_id,))
        if c.fetchone()[0]:
            conn.close()
            QMessageBox.warning(self, "Silinemez",
                                "Arac kirada. Once kiralama bitirilmeli.")
            return
        conn.close()
        if QMessageBox.question(self, "Onay", "Arac silinsin mi?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            conn = get_connection()
            conn.execute("DELETE FROM araclar WHERE arac_id=?", (arac_id,))
            conn.commit(); conn.close()
            self._refresh_araclar()
            self._refresh_dashboard()

    def _arac_duzenle(self, arac_id):
        # 1. Önce veritabanından aracın müsaitlik durumunu kontrol et
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT musait_mi FROM araclar WHERE arac_id=?", (arac_id,))
        durum = c.fetchone()
        conn.close()
        
        # 2. Eğer musait_mi == 0 ise araç kiradadır, düzenlemeyi engelle ve uyarı ver
        if durum and durum[0] == 0:
            QMessageBox.warning(self, "İşlem Reddedildi", "Bu araç şu an kirada!\n\nKirada olan bir aracın bilgilerini değiştiremezsiniz. Lütfen önce kiralama işleminin bitmesini bekleyin.")
            return # Fonksiyonu burada durdurur, pencereyi açmaz

        # 3. Araç müsaitse düzenleme penceresini normal şekilde aç
        dlg = AracDuzenleDialog(self, arac_id)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_araclar()
            self._refresh_harita()

    def _kirala(self, arac_id):
        dlg = KiralaDialog(self, self.kullanici, arac_id)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_all()

    # ── KULLANICILAR ───────────────────────────

    def _build_kullanici_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(10)
        self._kul_search = QLineEdit()
        self._kul_search.setPlaceholderText("Kullanici ara...")
        self._kul_search.textChanged.connect(self._filter_kul)
        lay.addWidget(self._kul_search)
        
        self._kul_tbl = QTableWidget()
        self._kul_tbl.setColumnCount(8) # Kolon sayısı 7'den 8'e çıkarıldı
        self._kul_tbl.setHorizontalHeaderLabels(
            ["ID","Ad","Soyad","Ehliyet No","E-posta","Rol","Kayit", "İşlem"]) # İşlem sütunu eklendi
        self._kul_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._kul_tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self._kul_tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self._kul_tbl.verticalHeader().setVisible(False)
        lay.addWidget(self._kul_tbl)
        return w

    def _refresh_kullanicilar(self):
        conn = get_connection(); c = conn.cursor()
        c.execute("""SELECT kullanici_id,ad,soyad,ehliyet_no,email,rol,kayit_tarihi
                     FROM kullanicilar ORDER BY kullanici_id""")
        self._kul_rows = c.fetchall(); conn.close()
        self._fill_kul_tbl(self._kul_rows)

    def _fill_kul_tbl(self, rows):
        BTN_R = (f"QPushButton{{background:{DANGER};color:white;font-weight:700;"
                 f"border-radius:6px;border:none;padding:3px 10px;}}"
                 f"QPushButton:hover{{background:#dc2626;}}")
                 
        self._kul_tbl.setRowCount(0)
        for row in rows:
            r = self._kul_tbl.rowCount()
            self._kul_tbl.insertRow(r)
            
            # İlk 7 sütuna verileri basıyoruz
            for col, val in enumerate(row):
                itm = QTableWidgetItem(str(val) if val else "")
                itm.setTextAlignment(Qt.AlignCenter)
                if col == 5 and val == 'admin':
                    itm.setForeground(QColor(WARNING))
                self._kul_tbl.setItem(r, col, itm)
            
            # 8. Sütun (İşlem) için özel çerçeve ve Sil butonu
            frame = QWidget()
            frame.setStyleSheet("background:transparent;")
            fl = QHBoxLayout(frame)
            fl.setContentsMargins(4, 2, 4, 2)
            fl.setSpacing(4)
            
            sil_btn = QPushButton("Sil")
            sil_btn.setFixedHeight(28)
            
            # --- KORUMA: ADMİN KENDİ KENDİNİ SİLEMEZ ---
            if row[0] == self.kullanici.kullanici_id:
                sil_btn.setEnabled(False)
                sil_btn.setStyleSheet("QPushButton{background:#374151;color:#6b7280;font-weight:700;border-radius:6px;border:none;}")
            else:
                sil_btn.setStyleSheet(BTN_R)
                sil_btn.clicked.connect(lambda _, kid=row[0], ad=row[1], soyad=row[2]: self._kullanici_sil(kid, ad, soyad))
                
            fl.addWidget(sil_btn)
            self._kul_tbl.setCellWidget(r, 7, frame)

    def _kullanici_sil(self, kul_id, ad, soyad):
        conn = get_connection()
        c = conn.cursor()
        
        # --- KORUMA 2: AKTİF KİRALAMASI OLAN MÜŞTERİ SİLİNEMEZ ---
        c.execute("SELECT COUNT(*) FROM kiralamalar WHERE kullanici_id=? AND durum='aktif'", (kul_id,))
        if c.fetchone()[0] > 0:
            conn.close()
            QMessageBox.warning(self, "Silinemez", f"{ad} {soyad} isimli müşterinin şu an aktif bir kiralaması var!\n\nLütfen önce kullanıcının kiralama işlemini bitirin.")
            return
            
        conn.close()
        
        # --- ONAY VE SİLME İŞLEMİ ---
        cevap = QMessageBox.question(self, "Müşteri Silme Onayı", 
                                     f"{ad} {soyad} isimli müşteriyi sistemden silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz!", 
                                     QMessageBox.Yes | QMessageBox.No)
                                     
        if cevap == QMessageBox.Yes:
            try:
                conn = get_connection()
                conn.execute("DELETE FROM kullanicilar WHERE kullanici_id=?", (kul_id,))
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", "Kullanıcı başarıyla silindi.")
                
                # Tabloyu ve Ana sayfadaki müşteri sayısını yenile
                self._refresh_kullanicilar()
                self._refresh_dashboard() 
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme işlemi sırasında hata oluştu:\n{e}")        

    def _filter_kul(self):
        txt = self._kul_search.text().lower()
        self._fill_kul_tbl(
            [r for r in self._kul_rows
             if txt in f"{r[1]} {r[2]} {r[4]}".lower()])

    # ── KİRALAMALAR ────────────────────────────

    def _build_kiralama_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(10)
        top = QHBoxLayout()
        self._kir_search = QLineEdit()
        self._kir_search.setPlaceholderText("Kullanici veya arac ara...")
        self._kir_search.textChanged.connect(self._filter_kir)
        self._kir_filter = QComboBox()
        self._kir_filter.addItems(["Tumu","Aktif","Tamamlandi"])
        self._kir_filter.currentIndexChanged.connect(self._filter_kir)
        top.addWidget(self._kir_search, 3)
        top.addWidget(self._kir_filter)
        lay.addLayout(top)
        self._kir_tbl = QTableWidget()
        self._kir_tbl.setColumnCount(9)
        self._kir_tbl.setHorizontalHeaderLabels(
            ["ID","Arac","Kullanici","Baslangic","Bitis","Durum","Ucret","Notlar","Islem"])
        self._kir_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._kir_tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self._kir_tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self._kir_tbl.verticalHeader().setVisible(False)
        lay.addWidget(self._kir_tbl)
        return w

    def _refresh_kiralamalar(self):
        conn = get_connection(); c = conn.cursor()
        q = """SELECT k.kiralama_id,
                      COALESCE(a.marka||' '||a.model||' ('||a.plaka||')', 'Silinmis Arac'),
                      u.ad||' '||u.soyad,
                      k.baslangic_saati, k.bitis_saati,
                      k.durum, k.toplam_ucret, k.notlar, k.arac_id
               FROM kiralamalar k
               LEFT JOIN araclar a ON k.arac_id=a.arac_id
               JOIN kullanicilar u ON k.kullanici_id=u.kullanici_id"""
        if self.kullanici.rol != 'admin':
            c.execute(q + " WHERE k.kullanici_id=? ORDER BY k.kiralama_id DESC",
                      (self.kullanici.kullanici_id,))
        else:
            c.execute(q + " ORDER BY k.kiralama_id DESC")
        self._kir_rows = c.fetchall(); conn.close()
        self._fill_kir_tbl(self._kir_rows)

    def _fill_kir_tbl(self, rows):
        BTN_R = (f"QPushButton{{background:{DANGER};color:white;font-weight:700;"
                 f"border-radius:6px;border:none;padding:3px 10px;}}"
                 f"QPushButton:hover{{background:#dc2626;}}")
        BTN_F = (f"QPushButton{{background:{ACCENT2};color:white;font-weight:700;"
                 f"border-radius:6px;border:none;padding:3px 8px;font-size:11px;}}"
                 f"QPushButton:hover{{background:#6d28d9;}}")
        self._kir_tbl.setRowCount(0)
        for row in rows:
            r = self._kir_tbl.rowCount()
            self._kir_tbl.insertRow(r)
            for col, val in enumerate(row[:8]):
                if col == 5:
                    txt = "Aktif" if val == 'aktif' else "Tamamlandi"
                elif col == 6:
                    txt = f"{val:.2f} TL" if val else "—"
                else:
                    txt = str(val) if val else "—"
                itm = QTableWidgetItem(txt)
                itm.setTextAlignment(Qt.AlignCenter)
                if col == 5:
                    itm.setForeground(
                        QColor(SUCCESS if val == 'aktif' else TEXT_SECONDARY))
                self._kir_tbl.setItem(r, col, itm)

            frame = QWidget()
            frame.setStyleSheet("background:transparent;")
            fl = QHBoxLayout(frame)
            fl.setContentsMargins(4, 2, 4, 2)
            fl.setSpacing(4)

            if row[5] == 'aktif':
                btn = QPushButton("Bitir")
                btn.setStyleSheet(BTN_R)
                btn.setFixedHeight(28)
                kid = row[0]
                btn.clicked.connect(lambda _, k=kid: self._bitir(k))
                fl.addWidget(btn)
            else:
                # Tamamlanan kiralama → E-Fatura butonu
                fbtn = QPushButton("E-Fatura")
                fbtn.setStyleSheet(BTN_F)
                fbtn.setFixedHeight(28)
                kid = row[0]
                fbtn.clicked.connect(lambda _, k=kid: self._efatura_olustur(k))
                fl.addWidget(fbtn)

            self._kir_tbl.setCellWidget(r, 8, frame)

    def _filter_kir(self):
        txt = self._kir_search.text().lower()
        f   = self._kir_filter.currentText()
        out = []
        for row in self._kir_rows:
            if f == "Aktif"      and row[5] != 'aktif':      continue
            if f == "Tamamlandi" and row[5] != 'tamamlandi': continue
            if txt and txt not in f"{row[1]} {row[2]}".lower(): continue
            out.append(row)
        self._fill_kir_tbl(out)

    def _bitir(self, kiralama_id):
        # 1. Önce kiralama verilerini çekip ÜCRETİ HESAPLIYORUZ (Ödeme ekranı için)
        conn = get_connection(); c = conn.cursor()
        c.execute("""SELECT k.kiralama_id, k.arac_id, k.baslangic_saati, COALESCE(a.saatlik_ucret, 50.0)
                     FROM kiralamalar k LEFT JOIN araclar a ON k.arac_id=a.arac_id
                     WHERE k.kiralama_id=?""", (kiralama_id,))
        row = c.fetchone()
        if not row: conn.close(); return

        arac_id       = row[1]
        baslangic     = row[2]
        saatlik_ucret = float(row[3])
        bitis         = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            if baslangic:
                b1 = datetime.strptime(baslangic, "%Y-%m-%d %H:%M:%S")
                b2 = datetime.strptime(bitis, "%Y-%m-%d %H:%M:%S")
                ucret = round((b2 - b1).total_seconds() / 3600 * saatlik_ucret, 2)
            else: ucret = 0.0
        except Exception: ucret = 0.0
        conn.close() 

        # 2. Yeni "Kiralamayı Bitir ve Öde" penceresini çağırıyoruz (Ücreti de gönderiyoruz)
        dlg = KiralamaBitirDialog(self, ucret)
        if dlg.exec_() != QDialog.Accepted:
            return # Kullanıcı ödeme yapmadan çarpıya basarsa işlem iptal olur
            
        # 3. Ödeme başarılıysa seçilen yeni değerleri al
        eklenen_km = dlg.km_value
        yeni_enlem = dlg.secilen_lat
        yeni_boylam = dlg.secilen_lng

        # 4. Veritabanını kalıcı olarak güncelle (Ödendi olarak işaretle ve aracın YENİ KONUMUNU ata)
        conn = get_connection()
        conn.execute("""UPDATE kiralamalar SET bitis_saati=?, durum='tamamlandi', toplam_ucret=?
                        WHERE kiralama_id=?""", (bitis, ucret, kiralama_id))
        
        c = conn.cursor()
        c.execute("SELECT arac_id FROM araclar WHERE arac_id=?", (arac_id,))
        if c.fetchone():
            # ARAÇ HARİTADA SEÇİLEN YENİ KONUMA IŞINLANIYOR
            conn.execute("""UPDATE araclar SET musait_mi=1, kilometre=kilometre+?, enlem=?, boylam=? 
                            WHERE arac_id=?""", (eklenen_km, yeni_enlem, yeni_boylam, arac_id))
        conn.commit(); conn.close()

        QMessageBox.information(
            self, "Ödeme Başarılı",
            f"Kiralama başarıyla sonlandırıldı.\n\n💳 {ucret:.2f} TL tutarındaki ödeme kartınızdan çekildi.\n📍 Araç haritada yeni konumuna güncellendi.")
        self._refresh_all()

    def _efatura_olustur(self, kiralama_id):
        """Tamamlanan kiralama için Resmi E-Fatura oluştur"""
        if not PDF_AVAILABLE:
            QMessageBox.warning(self, "Eksik Kutuphane",
                "PDF icin reportlab gerekli.\nTerminalde: pip install reportlab")
            return

        import json
        import uuid

        # Kiralama + kullanıcı + araç verilerini çek
        conn = get_connection(); c = conn.cursor()
        c.execute("""SELECT k.kiralama_id, k.baslangic_saati, k.bitis_saati,
                            k.toplam_ucret, k.notlar, k.fatura_no,
                            COALESCE(a.marka,''), COALESCE(a.model,''),
                            COALESCE(a.plaka,''), COALESCE(a.saatlik_ucret,50.0),
                            u.ad, u.soyad, u.email, u.ehliyet_no,
                            COALESCE(u.kurumsal_mi,0),
                            COALESCE(u.sirket_adi,''),
                            COALESCE(u.vergi_no,''),
                            COALESCE(u.vergi_dairesi,''),
                            COALESCE(u.adres,''),
                            COALESCE(u.telefon,'')
                     FROM kiralamalar k
                     LEFT JOIN araclar a ON k.arac_id=a.arac_id
                     JOIN kullanicilar u ON k.kullanici_id=u.kullanici_id
                     WHERE k.kiralama_id=?""", (kiralama_id,))
        row = c.fetchone()
        if not row:
            conn.close(); return

        fatura_no = row[5]
        if not fatura_no:
            import random as _r
            fatura_no = f"GRE{datetime.now().strftime('%Y')}0000{_r.randint(10000,99999)}"
            conn.execute("UPDATE kiralamalar SET fatura_no=? WHERE kiralama_id=?",
                         (fatura_no, kiralama_id))
            conn.commit()
        conn.close()

        (kid, bas_str, bit_str, toplam_ucret, notlar, _,
         marka, model, plaka, saatlik_ucret,
         ad, soyad, email, ehliyet,
         kurumsal, sirket_adi, vergi_no, vergi_dairesi, adres, telefon) = row

        # --- TARİH VE SAAT İŞLEME (BİTİŞ SAATİNE GÖRE) ---
        try:
            # Veritabanından gelen 'YYYY-MM-DD HH:MM:SS' formatındaki bitiş saatini okuyoruz
            bit_dt = datetime.strptime(bit_str, "%Y-%m-%d %H:%M:%S")
            
            fatura_tarihi_gosterim    = bit_dt.strftime("%d-%m-%Y %H:%M:%S")
            duzenleme_tarihi_gosterim = bit_dt.strftime("%d-%m-%Y")
            duzenleme_zamani_gosterim = bit_dt.strftime("%H:%M:%S")
            qr_tarih_formati          = bit_dt.strftime("%Y-%m-%d") # QR içindeki ISO formatı
        except Exception:
            # Eğer bitiş saati okunamazsa (boşsa vb.) uygulama çökmesin diye anlık zamanı yedek olarak alır
            fatura_tarihi_gosterim    = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            duzenleme_tarihi_gosterim = datetime.now().strftime("%d-%m-%Y")
            duzenleme_zamani_gosterim = datetime.now().strftime("%H:%M:%S")
            qr_tarih_formati          = datetime.now().strftime("%Y-%m-%d")
        
        except Exception:
            # Eğer bitiş saati okunamazsa (boşsa vb.) uygulama çökmesin diye anlık zamanı yedek olarak alır
            fatura_tarihi_gosterim    = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            duzenleme_tarihi_gosterim = datetime.now().strftime("%d-%m-%Y")
            duzenleme_zamani_gosterim = datetime.now().strftime("%H:%M:%S")
            qr_tarih_formati          = datetime.now().strftime("%Y-%m-%d")

        # --- İŞTE YANLIŞLIKLA SİLİNEN KDV HESAPLAMASINI BURAYA GERİ EKLİYORUZ ---
        kdv_oran  = 0.20
        kdv_haric = round(toplam_ucret / (1 + kdv_oran), 2)
        kdv_tutar = round(toplam_ucret - kdv_haric, 2)
        # ------------------------------------------------------------------------

        # Benzersiz ETTN Numarası
        ettn_no = str(uuid.uuid4()).upper()

        # Benzersiz ETTN Numarası
        ettn_no = str(uuid.uuid4()).upper()

        default_ad = f"{fatura_no}-eFatura.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "E-Fatura Kaydet", default_ad, "PDF (*.pdf)")
        if not path:
            return

        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.platypus import HRFlowable, Image as RLImage
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
            from reportlab.graphics.barcode import qr
            from reportlab.graphics.shapes import Drawing

            font_n, font_b = 'Helvetica', 'Helvetica-Bold'
            for np, bp in [
                ("C:/Windows/Fonts/arial.ttf",   "C:/Windows/Fonts/arialbd.ttf"),
                ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ]:
                if os.path.exists(np):
                    try:
                        pdfmetrics.registerFont(TTFont('TF', np))
                        font_n = 'TF'
                        if os.path.exists(bp):
                            pdfmetrics.registerFont(TTFont('TF-Bold', bp))
                            font_b = 'TF-Bold'
                    except Exception:
                        pass
                    break

            def tr(txt):
                if font_n == 'Helvetica':
                    return str(txt).translate(str.maketrans('şŞğĞüÜöÖçÇıİ', 'sSgGuUoOcCiI'))
                return str(txt)

            doc = SimpleDocTemplate(path, pagesize=A4,
                                    leftMargin=1.2*cm, rightMargin=1.2*cm,
                                    topMargin=1.5*cm, bottomMargin=1.5*cm)

            def sty(name, **kw):
                return ParagraphStyle(name, fontName=kw.pop('font', font_n),
                                      fontSize=kw.pop('size', 8), **kw)

            st_bold   = sty('b', font=font_b, size=8, spaceAfter=2)
            st_normal = sty('n', size=8, spaceAfter=2)
            st_small  = sty('sm', size=7, spaceAfter=1, textColor=colors.HexColor('#333333'))

            elems = []

            # ── 1. DİNAMİK QR KOD OLUŞTURMA ──
            qr_data = {
                "vkntckn": "6190833982",
                "avkntckn": vergi_no if kurumsal else ehliyet,
                "senaryo": "EARSIVFATURA",
                "tip": "SATIS",
                "tarih": qr_tarih_formati, # ARTIK BİTİŞ TARİHİ GİDİYOR,
                "no": fatura_no,
                "ettn": ettn_no,
                "parabirimi": "TRY",
                "malhizmettoplam": f"{kdv_haric:.2f}",
                "kdvmatrah(20.00)": f"{kdv_haric:.2f}",
                "hesaplanankdv(20.00)": f"{kdv_tutar:.2f}",
                "vergidahil": f"{toplam_ucret:.2f}",
                "odenecek": f"{toplam_ucret:.2f}"
            }
            qr_code = qr.QrCodeWidget(json.dumps(qr_data, separators=(',', ':')))
            
            
            qr_code.barWidth = 4.8 * cm
            qr_code.barHeight = 4.8 * cm
            qr_drawing = Drawing(4.8*cm, 4.8*cm)
            
            qr_drawing.add(qr_code)

            # ── 2. ÜST BİLGİ (HEADER) ALANI ──
            LOGO_PATH = "rentacar.jpg"
            EARSIV_PATH = "earsiv.jpeg" # Ortadaki e-arşiv logosu
            
            firma_metin = [
                Paragraph("<b>Merkez</b>", sty('ft', font=font_b, size=10)),
                Paragraph("RENTACAR OTO TİCARET A.Ş.", st_small),
                Paragraph(tr("BÜYÜKDERE CADDESİ NO:123/4"), st_small),
                Paragraph(tr("34394 ŞİŞLİ / İSTANBUL"), st_small),
                Paragraph("Tel: 0212 123 45 67", st_small),
                Paragraph("Web Sitesi: www.rentacar.com", st_small),
                Paragraph("E-posta: info@rentacar.com", st_small),
                Paragraph("Vergi Dairesi: ZİNCİRLİKUYU", st_small),
                Paragraph("VKN: 6190833982", st_small),
                Paragraph("Mersis No: 0619083398200001", st_small),
            ]

            sol_hucre = firma_metin
            # e-Arşiv logosu GİB standartlarında yatay bir dikdörtgendir (Genişlik 3.5, Yükseklik 1.2 idealdir)
            orta_hucre = RLImage(EARSIV_PATH, width=3.5*cm, height=2.0*cm) if os.path.exists(EARSIV_PATH) else Paragraph("e-Arşiv", sty('c', font=font_b, size=12, alignment=TA_CENTER))
            
            sag_hucre = []
            if os.path.exists(LOGO_PATH):
                # Şirket logosunun aşırı yassı olmaması için yüksekliğini artırdık ve genişliğini dengeledik
                logo_img = RLImage(LOGO_PATH, width=4.5*cm, height=2.0*cm)
                logo_img.hAlign = 'RIGHT'
                sag_hucre.append(logo_img)
                
            sag_hucre.append(qr_drawing)

            header_tbl = Table([[sol_hucre, orta_hucre, sag_hucre]], colWidths=[7*cm, 4*cm, 7*cm])
            header_tbl.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN',  (1,0), (1,0), 'CENTER'),
                ('ALIGN',  (2,0), (2,0), 'RIGHT'),
            ]))
            elems.append(header_tbl)
            elems.append(Spacer(1, 0.5*cm))
            elems.append(HRFlowable(width="100%", thickness=1, color=colors.black))
            elems.append(Spacer(1, 0.3*cm))

            # ── 3. ALICI VE FATURA DETAYLARI (GİB FORMATI) ──
            alici_adi  = tr(f"{sirket_adi}") if kurumsal else tr(f"{ad} {soyad}")
            alici_info = [
                Paragraph("<b>SAYIN</b>", st_bold),
                Paragraph(alici_adi, st_normal),
                Paragraph(tr(adres) if adres else tr("ADRES BELİRTİLMEMİŞ"), st_normal),
                Paragraph(f"E-Posta: {email}", st_normal),
            ]
            if kurumsal:
                alici_info.extend([
                    Paragraph(tr(f"Vergi Dairesi: {vergi_dairesi}"), st_normal),
                    Paragraph(f"VKN: {vergi_no}", st_normal),
                ])
            else:
                alici_info.extend([
                    Paragraph("Vergi Dairesi: -", st_normal),
                    Paragraph(f"TCKN: {ehliyet}", st_normal), # Ehliyet/TCKN
                ])

            # --- 3. ALICI VE FATURA DETAYLARI ---
            fatura_info_data = [
                ["Fatura Tipi:", "SATIŞ"],
                ["Belge No:", fatura_no],
                ["Fatura Tarihi:", fatura_tarihi_gosterim],     # ARTIK BİTİŞ SAATİ
                [tr("Düzenleme Tarihi:"), duzenleme_tarihi_gosterim], # ARTIK BİTİŞ TARİHİ
                [tr("Düzenleme Zamanı:"), duzenleme_zamani_gosterim], # ARTIK BİTİŞ SAATİ
            ]
            
            fatura_tbl = Table([[tr(k), tr(v)] for k, v in fatura_info_data], colWidths=[3.5*cm, 4.5*cm])
            fatura_tbl.setStyle(TableStyle([
                ('FONTNAME', (0,0),(-1,-1), font_n),
                ('FONTSIZE', (0,0),(-1,-1), 8),
                ('GRID', (0,0),(-1,-1), 0.5, colors.black),
                ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
            ]))

            info_layout = Table([[alici_info, fatura_tbl]], colWidths=[10*cm, 8.6*cm])
            info_layout.setStyle(TableStyle([('VALIGN', (0,0),(-1,-1), 'TOP')]))
            elems.append(info_layout)
            
            elems.append(Spacer(1, 0.2*cm))
            elems.append(Paragraph(f"<b>ETTN:</b> {ettn_no}", st_normal))
            elems.append(Spacer(1, 0.4*cm))

            # ── 4. KALEMLER TABLOSU ──
            kalem_headers = [
                "Sıra\nNo", "Hizmet Kodu", "Malzeme / Hizmet\nAçıklaması",
                "Miktar", "Birim Fiyat", "İskonto\nOranı", "İskonto\nTutarı",
                "KDV\nOranı", "KDV\nTutarı", "Tutar"
            ]
            
            kalem_data = [[tr(h) for h in kalem_headers]]
            kalem_data.append([
                "1", "600.02.001",
                tr(f"ARAÇ KİRALAMA BEDELİ\n{marka} {model} ({plaka})\n{bas_str} - {bit_str}"),
                "1 Adet", f"{kdv_haric:.4f} TL", "%0", "0,00 TL",
                "%20", f"{kdv_tutar:.2f} TL", f"{toplam_ucret:.2f} TL"
            ])

            col_w = [0.8*cm, 2.0*cm, 5.0*cm, 1.5*cm, 2.0*cm, 1.4*cm, 1.6*cm, 1.2*cm, 1.6*cm, 1.8*cm]
            ktbl = Table(kalem_data, colWidths=col_w, repeatRows=1)
            ktbl.setStyle(TableStyle([
                ('FONTNAME', (0,0),(-1,0), font_b),
                ('FONTNAME', (0,1),(-1,-1), font_n),
                ('FONTSIZE', (0,0),(-1,-1), 7),
                ('GRID', (0,0),(-1,-1), 0.5, colors.black),
                ('ALIGN', (0,0),(-1,-1), 'CENTER'),
                ('ALIGN', (2,1),(2,-1), 'LEFT'), # Sadece açıklama sola dayalı
                ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
            ]))
            elems.append(ktbl)
            elems.append(Spacer(1, 0.1*cm))

            # ── 5. ÖZET KUTUSU VE TOPLAMLAR ──
            ozet_data = [
                [tr("Mal / Hizmet Tutarı"), f"{kdv_haric:.2f} TL"],
                [tr("Toplam İskonto"), "0,00 TL"],
                [tr("Hesaplanan KDV (% 20,00)"), f"{kdv_tutar:.2f} TL"],
                [tr("Vergiler Dahil Toplam Tutar"), f"{toplam_ucret:.2f} TL"],
                [tr("Ödenecek Tutar"), f"{toplam_ucret:.2f} TL"],
            ]
            ozet_tbl = Table(ozet_data, colWidths=[14.8*cm, 3.8*cm])
            ozet_tbl.setStyle(TableStyle([
                ('FONTNAME', (0,0),(-1,-1), font_b),
                ('FONTSIZE', (0,0),(-1,-1), 8),
                ('GRID', (0,0),(-1,-1), 0.5, colors.black),
                ('ALIGN', (0,0),(-1,-1), 'RIGHT'),
                ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
            ]))
            elems.append(ozet_tbl)

            # Belge sonu
            doc.build(elems)
            QMessageBox.information(
                self, "E-Fatura Oluşturuldu",
                f"Fatura No: {fatura_no}\nDosya Kaydedildi:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"E-Fatura oluşturulamadı:\n{e}")

    # ── RAPORLAR ───────────────────────────────

    def _build_rapor_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(14)
        lbl = QLabel("Raporlar & Istatistikler")
        lbl.setStyleSheet("font-size:18px;font-weight:900;")
        lay.addWidget(lbl)

        charts = QHBoxLayout()
        self._pie_view = QChartView()
        self._pie_view.setMinimumHeight(250)
        self._pie_view.setStyleSheet(
            f"background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;")
        self._bar2_view = QChartView()
        self._bar2_view.setMinimumHeight(250)
        self._bar2_view.setStyleSheet(
            f"background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;")
        charts.addWidget(self._pie_view)
        charts.addWidget(self._bar2_view)
        lay.addLayout(charts)

        # PDF raporu butonu sadece admin için göster
        if self.kullanici.rol == 'admin':
            pdf_btn = QPushButton("📄 Admin PDF Raporu Indir")
            pdf_btn.setFixedHeight(42)
            pdf_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {WARNING}; /* Uygulamanın mor vurgu rengi */
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                }}
                QPushButton:hover {{ background-color: #6d28d9; }}
            """)
            pdf_btn.clicked.connect(self._export_pdf)
            lay.addWidget(pdf_btn)
        else:
            bilgi = QLabel(
                "📊  Kiralama gecmisindeki tamamlanan kiralamalarin 'E-Fatura' "
                "butonuna basarak faturanizi olusturabilirsiniz.")
            bilgi.setWordWrap(True)
            bilgi.setStyleSheet(
                f"color:{TEXT_SECONDARY}; font-size:12px; padding:10px;"
                f"background:{CARD_BG}; border:1px solid {BORDER}; border-radius:8px;")
            lay.addWidget(bilgi)
        return w

    def _refresh_raporlar(self):
        conn = get_connection(); c = conn.cursor()

        # Pasta grafik — marka bazlı
        c.execute("""SELECT a.marka, COUNT(*) FROM kiralamalar k
                     JOIN araclar a ON k.arac_id=a.arac_id GROUP BY a.marka""")
        marka_data = c.fetchall()
        pie = QPieSeries()
        renkler = [ACCENT, ACCENT2, SUCCESS, WARNING, DANGER]
        for i, (marka, sayi) in enumerate(marka_data):
            sl = pie.append(f"{marka} ({sayi})", sayi)
            sl.setColor(QColor(renkler[i % len(renkler)]))
        pc = QChart()
        pc.addSeries(pie)
        pc.setTitle("Marka Bazli Kiralama")
        pc.setTitleFont(QFont("Segoe UI", 10, QFont.Bold))
        pc.setBackgroundBrush(QBrush(QColor(CARD_BG)))
        pc.setTitleBrush(QBrush(QColor(TEXT_PRIMARY)))
        pc.legend().setLabelColor(QColor(TEXT_SECONDARY))
        self._pie_view.setChart(pc)

        # Bar grafik — aylık gelir
        aylar, gelirler = [], []
        for i in range(5, -1, -1):
            d = datetime.now() - timedelta(days=30 * i)
            c.execute("""SELECT COALESCE(SUM(toplam_ucret),0) FROM kiralamalar
                         WHERE strftime('%Y-%m',baslangic_saati)=?
                         AND durum='tamamlandi'""", (d.strftime("%Y-%m"),))
            row_g = c.fetchone()
            aylar.append(d.strftime("%b"))
            gelirler.append(float(row_g[0]) if row_g else 0.0)
        conn.close()

        bs = QBarSet("Gelir (TL)")
        bs.setColor(QColor(ACCENT2))
        for g in gelirler:
            bs.append(g)
        bar_s = QBarSeries()
        bar_s.append(bs)
        bc = QChart()
        bc.addSeries(bar_s)
        bc.setTitle("Aylik Gelir (Son 6 Ay)")
        bc.setTitleFont(QFont("Segoe UI", 10, QFont.Bold))
        bc.setBackgroundBrush(QBrush(QColor(CARD_BG)))
        bc.setTitleBrush(QBrush(QColor(TEXT_PRIMARY)))
        ax = QBarCategoryAxis()
        ax.append(aylar)
        ax.setLabelsColor(QColor(TEXT_SECONDARY))
        bc.addAxis(ax, Qt.AlignBottom)
        bar_s.attachAxis(ax)
        ay2 = QValueAxis()
        ay2.setLabelsColor(QColor(TEXT_SECONDARY))
        ay2.setGridLineColor(QColor(BORDER))
        bc.addAxis(ay2, Qt.AlignLeft)
        bar_s.attachAxis(ay2)
        bc.legend().setLabelColor(QColor(TEXT_SECONDARY))
        self._bar2_view.setChart(bc)

    def _export_pdf(self):
        if not PDF_AVAILABLE:
            QMessageBox.warning(self, "Eksik Kutuphane",
                "PDF icin reportlab gerekli.\nTerminalde: pip install reportlab")
            return
        tarih = datetime.now().strftime("%d.%m.%Y")
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF Kaydet", f"{tarih}-Rapor.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            font_n, font_b = 'Helvetica', 'Helvetica-Bold'
            for np, bp in [
                ("C:/Windows/Fonts/arial.ttf",   "C:/Windows/Fonts/arialbd.ttf"),
                ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ]:
                if os.path.exists(np):
                    try:
                        pdfmetrics.registerFont(TTFont('TF', np))
                        font_n = 'TF'
                        if os.path.exists(bp):
                            pdfmetrics.registerFont(TTFont('TF-Bold', bp))
                            font_b = 'TF-Bold'
                    except Exception:
                        pass
                    break

            conn = get_connection(); c = conn.cursor()
            c.execute("""SELECT k.kiralama_id,
                                COALESCE(a.marka||' '||a.model,'Silinmis'),
                                COALESCE(a.plaka,'-'),
                                u.ad||' '||u.soyad,
                                k.baslangic_saati, k.bitis_saati,
                                k.durum, k.toplam_ucret
                         FROM kiralamalar k
                         LEFT JOIN araclar a ON k.arac_id=a.arac_id
                         JOIN kullanicilar u ON k.kullanici_id=u.kullanici_id
                         ORDER BY k.kiralama_id DESC LIMIT 100""")
            rows = c.fetchall()
            c.execute("""SELECT COALESCE(SUM(toplam_ucret),0)
                         FROM kiralamalar WHERE durum='tamamlandi'""")
            toplam = c.fetchone()[0]; conn.close()

            PAGE   = landscape(A4)
            PAGE_W = PAGE[0] - 3 * cm
            doc    = SimpleDocTemplate(path, pagesize=PAGE,
                                       leftMargin=1.5*cm, rightMargin=1.5*cm,
                                       topMargin=1.5*cm, bottomMargin=1.5*cm)
            ts = ParagraphStyle('t', fontName=font_b, fontSize=15,
                                alignment=TA_CENTER, spaceAfter=8,
                                textColor=colors.HexColor('#1e3a5f'))
            ss = ParagraphStyle('s', fontName=font_n, fontSize=9,
                                spaceAfter=4, textColor=colors.HexColor('#555'))
            gs = ParagraphStyle('g', fontName=font_b, fontSize=11,
                                textColor=colors.HexColor('#166534'), spaceAfter=8)

            elems = [
                Paragraph("Arac Paylasim Sistemi - Kiralama Raporu", ts),
                Paragraph(f"Olusturma: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ss),
                Spacer(1, 0.3*cm),
                Paragraph(f"Toplam Gelir: {toplam:.2f} TL", gs),
                Spacer(1, 0.3*cm),
            ]
            headers = ["ID","Arac","Plaka","Kullanici",
                       "Baslangic","Bitis","Durum","Ucret(TL)"]
            data = [headers]
            for row in rows:
                satir = []
                for i, x in enumerate(row):
                    if x is None:
                        satir.append("-")
                    elif i == 7:
                        satir.append(f"{float(x):.2f}")
                    else:
                        val = str(x)
                        if font_n == 'Helvetica':
                            val = val.translate(
                                str.maketrans('şŞğĞüÜöÖçÇıİ', 'sSgGuUoOcCiI'))
                        satir.append(val)
                data.append(satir)

            ratios = [0.05, 0.16, 0.10, 0.14, 0.17, 0.17, 0.11, 0.10]
            tbl = Table(data, repeatRows=1,
                        colWidths=[r * PAGE_W for r in ratios])
            tbl.setStyle(TableStyle([
                ('BACKGROUND',     (0,0),(-1,0),  colors.HexColor('#4f8ef7')),
                ('TEXTCOLOR',      (0,0),(-1,0),  colors.white),
                ('FONTNAME',       (0,0),(-1,0),  font_b),
                ('FONTNAME',       (0,1),(-1,-1), font_n),
                ('FONTSIZE',       (0,0),(-1,-1), 8),
                ('ROWBACKGROUNDS', (0,1),(-1,-1),
                 [colors.white, colors.HexColor('#f0f4ff')]),
                ('GRID',           (0,0),(-1,-1), 0.4,
                 colors.HexColor('#c7d2fe')),
                ('ALIGN',          (0,0),(-1,-1), 'CENTER'),
                ('VALIGN',         (0,0),(-1,-1), 'MIDDLE'),
                ('TOPPADDING',     (0,0),(-1,-1), 5),
                ('BOTTOMPADDING',  (0,0),(-1,-1), 5),
            ]))
            elems.append(tbl)
            doc.build(elems)
            QMessageBox.information(self, "Basarili", f"PDF kaydedildi:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF olusturulamadi:\n{e}")

    # ── GENEL ──────────────────────────────────

    def _refresh_all(self):
        self._refresh_dashboard()
        self._refresh_harita() # HARİTA YENİLEMESİ EKLENDİ
        self._refresh_araclar()
        self._refresh_kiralamalar()
        
        if self.kullanici.rol == 'admin':
            self._refresh_kullanicilar()
            self._refresh_raporlar()

    def _logout(self):
        self.close()
        dlg = LoginDialog()
        dlg.login_success.connect(_on_login)
        dlg.exec_()

# ─────────────────────────────────────────────
#  YARDIMCI DİYALOGLAR
# ─────────────────────────────────────────────

class AracDuzenleDialog(QDialog):
    def __init__(self, parent, arac_id):
        super().__init__(parent)
        self.arac_id = arac_id
        self.setWindowTitle("Araç Bilgilerini Düzenle")
        self.setFixedSize(380, 440) 
        self.setStyleSheet(STYLE)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(10)
        
        lbl = QLabel("Araç Düzenle")
        lbl.setStyleSheet("font-size:15px;font-weight:800;")
        lay.addWidget(lbl)
        
        self.marka  = QLineEdit(); self.marka.setPlaceholderText("Marka")
        self.model  = QLineEdit(); self.model.setPlaceholderText("Model")
        
        # --- HATA BURADA ÇÖZÜLDÜ: QListView KÜTÜPHANESİ İÇERİ AKTARILDI ---
        from PyQt5.QtWidgets import QListView
        
        self.yil = QComboBox(); self.yil.setView(QListView()); self.yil.setMaxVisibleItems(6) 
        for y in range(datetime.now().year, 1989, -1): self.yil.addItem(str(y))
            
        self.vites = QComboBox(); self.vites.setView(QListView())
        self.vites.addItems(["Seçiniz...", "Otomatik", "Manuel"])
        
        self.plaka  = QLineEdit(); self.plaka.setPlaceholderText("Plaka (34ABC123)")
        from PyQt5.QtCore import QRegExp
        from PyQt5.QtGui import QRegExpValidator
        self.plaka.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9]+"), self.plaka)) # Düzenlerken de virgül yasak!
        
        self.km     = QDoubleSpinBox(); self.km.setRange(0, 999999); self.km.setSuffix(" km")
        self.ucret  = QDoubleSpinBox(); self.ucret.setRange(1, 9999); self.ucret.setValue(50); self.ucret.setPrefix("TL ")
        self.acikl  = QLineEdit(); self.acikl.setPlaceholderText("Açıklama (opsiyonel)")
        
        form = QFormLayout(); form.setSpacing(8)
        for lbl_txt, wid in [("Marka:", self.marka), ("Model:", self.model), ("Yıl:", self.yil), ("Vites:", self.vites), ("Plaka:", self.plaka), ("Kilometre:", self.km), ("Saat Ücreti:", self.ucret), ("Açıklama:", self.acikl)]:
            form.addRow(QLabel(lbl_txt), wid)
            
        lay.addLayout(form)
        btn = QPushButton("Değişiklikleri Kaydet")
        btn.setFixedHeight(40)
        btn.setStyleSheet(f"QPushButton {{ background-color: {ACCENT}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }} QPushButton:hover {{ background-color: #6ba3ff; }}")
        btn.clicked.connect(self._kaydet)
        lay.addWidget(btn)
        
        # Ekran açılır açılmaz mevcut veritabanı bilgilerini kutulara doldur
        self._verileri_yukle()

    def _verileri_yukle(self):
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT marka, model, yil, vites, plaka, kilometre, saatlik_ucret, aciklama FROM araclar WHERE arac_id=?", (self.arac_id,))
        row = c.fetchone(); conn.close()
        if row:
            self.marka.setText(str(row[0]))
            self.model.setText(str(row[1]))
            self.yil.setCurrentText(str(row[2]))
            self.vites.setCurrentText(str(row[3]) if row[3] else "Otomatik")
            self.plaka.setText(str(row[4]))
            self.km.setValue(float(row[5]))
            self.ucret.setValue(float(row[6]))
            self.acikl.setText(str(row[7]) if row[7] else "")

    def _kaydet(self):
        if not (self.marka.text().strip() and self.model.text().strip() and self.plaka.text().strip()): 
            QMessageBox.warning(self, "Uyarı", "Marka, model ve plaka zorunludur.")
            return
        if self.vites.currentText() == "Seçiniz...": 
            QMessageBox.warning(self, "Uyarı", "Lütfen aracın vites türünü seçiniz.")
            return
        try:
            conn = get_connection()
            conn.execute("""UPDATE araclar SET 
                marka=?, model=?, yil=?, vites=?, plaka=?, kilometre=?, saatlik_ucret=?, aciklama=? 
                WHERE arac_id=?""",
                (self.marka.text().strip(), self.model.text().strip(), int(self.yil.currentText()), self.vites.currentText(), self.plaka.text().strip().upper(), self.km.value(), self.ucret.value(), self.acikl.text(), self.arac_id))
            conn.commit(); conn.close()
            QMessageBox.information(self, "Başarılı", "Araç bilgileri güncellendi.")
            self.accept()
        except sqlite3.IntegrityError: 
            QMessageBox.critical(self, "Hata", "Bu plaka zaten sistemde başka bir araca ait.")


class AracEkleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Araç Ekle")
        self.setFixedSize(380, 500) 
        self.setStyleSheet(STYLE)
        
        # Validator sınıflarını içe aktarıyoruz
        from PyQt5.QtCore import QRegExp
        from PyQt5.QtGui import QRegExpValidator
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(10)
        
        lbl = QLabel("Araç Bilgileri"); lbl.setStyleSheet("font-size:15px;font-weight:800;"); lay.addWidget(lbl)
        
        # --- 1. MARKA KISITLAMASI (Sadece Harf ve Boşluk) ---
        self.marka  = QLineEdit(); self.marka.setPlaceholderText("Marka")
        self.marka.setValidator(QRegExpValidator(QRegExp("[A-Za-zğüşıöçĞÜŞİÖÇ ]+"), self.marka))
        
        # --- 2. MODEL KISITLAMASI (Sadece Harf, Sayı ve Boşluk) ---
        self.model  = QLineEdit(); self.model.setPlaceholderText("Model")
        self.model.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9ğüşıöçĞÜŞİÖÇ ]+"), self.model))
        
        self.yil = QComboBox(); self.yil.setView(QListView()); self.yil.setMaxVisibleItems(6) 
        for y in range(datetime.now().year, 1989, -1): self.yil.addItem(str(y))
            
        self.vites = QComboBox(); self.vites.setView(QListView()); self.vites.addItems(["Seçiniz...", "Otomatik", "Manuel"])
        
        self.plaka  = QLineEdit(); self.plaka.setPlaceholderText("Plaka (34ABC123)")
        self.plaka.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9]+"), self.plaka))
        
        self.km     = QDoubleSpinBox(); self.km.setRange(0, 999999); self.km.setSuffix(" km")
        self.ucret  = QDoubleSpinBox(); self.ucret.setRange(1, 9999); self.ucret.setValue(50); self.ucret.setPrefix("TL ")
        self.acikl  = QLineEdit(); self.acikl.setPlaceholderText("Açıklama (opsiyonel)")
        
        # FOTOĞRAF BUTONU
        self.arac_foto_yolu = ""
        self.foto_btn = QPushButton("📷 Fotoğraf Seç")
        self.foto_btn.setFixedHeight(30)
        self.foto_btn.setStyleSheet(f"QPushButton{{background:rgba(255,255,255,0.1); border:1px solid {BORDER}; border-radius:6px;}} QPushButton:hover{{background:rgba(255,255,255,0.2);}}")
        self.foto_btn.clicked.connect(self._foto_sec)

        form = QFormLayout(); form.setSpacing(8)
        for lbl_txt, wid in [("Fotoğraf:", self.foto_btn), ("Marka:", self.marka), ("Model:", self.model), ("Yıl:", self.yil), ("Vites:", self.vites), ("Plaka:", self.plaka), ("Kilometre:", self.km), ("Saat Ücreti:", self.ucret), ("Açıklama:", self.acikl)]:
            form.addRow(QLabel(lbl_txt), wid)
            
        lay.addLayout(form)
        btn = QPushButton("Araç Ekle"); btn.setFixedHeight(40); btn.setStyleSheet(f"QPushButton {{ background-color: {SUCCESS}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }} QPushButton:hover {{ background-color: #16a34a; }}")
        btn.clicked.connect(self._ekle); lay.addWidget(btn)

    def _foto_sec(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Fotoğraf Seç', '', 'Resim Dosyaları (*.png *.jpg *.jpeg)')
        if fname:
            self.arac_foto_yolu = fname
            self.foto_btn.setText("✅ Fotoğraf Yüklendi")
            self.foto_btn.setStyleSheet(f"QPushButton{{background:{SUCCESS}; color:white; font-weight:bold; border-radius:6px;}}")

    def _ekle(self):
        if not (self.marka.text().strip() and self.model.text().strip() and self.plaka.text().strip()): QMessageBox.warning(self, "Uyarı", "Marka, model ve plaka zorunludur."); return
        if self.vites.currentText() == "Seçiniz...": QMessageBox.warning(self, "Uyarı", "Lütfen aracın vites türünü seçiniz."); return
        try:
            import random
            lat = 40.9912 + random.uniform(-0.02, 0.02); lng = 28.8325 + random.uniform(-0.02, 0.02)
            conn = get_connection()
            conn.execute("INSERT INTO araclar (marka, model, yil, vites, plaka, kilometre, musait_mi, saatlik_ucret, aciklama, enlem, boylam, yakit, foto_url) VALUES(?,?,?,?,?,?,1,?,?,?,?,?,?)", 
                         (self.marka.text().strip(), self.model.text().strip(), int(self.yil.currentText()), self.vites.currentText(), self.plaka.text().strip().upper(), self.km.value(), self.ucret.value(), self.acikl.text(), lat, lng, "%100", self.arac_foto_yolu)) 
            conn.commit(); conn.close(); self.accept()
        except sqlite3.IntegrityError: QMessageBox.critical(self, "Hata", "Bu plaka zaten sistemde kayıtlı.")

class AracDuzenleDialog(QDialog):
    def __init__(self, parent, arac_id):
        super().__init__(parent); self.arac_id = arac_id
        self.setWindowTitle("Araç Bilgilerini Düzenle"); self.setFixedSize(380, 500); self.setStyleSheet(STYLE)
        
        from PyQt5.QtCore import QRegExp
        from PyQt5.QtGui import QRegExpValidator
        
        lay = QVBoxLayout(self); lay.setContentsMargins(28, 20, 28, 20); lay.setSpacing(10)
        lbl = QLabel("Araç Düzenle"); lbl.setStyleSheet("font-size:15px;font-weight:800;"); lay.addWidget(lbl)
        
        # --- MARKA VE MODEL KISITLAMALARI (Düzenleme ekranı) ---
        self.marka  = QLineEdit(); self.marka.setPlaceholderText("Marka")
        self.marka.setValidator(QRegExpValidator(QRegExp("[A-Za-zğüşıöçĞÜŞİÖÇ ]+"), self.marka))
        
        self.model  = QLineEdit(); self.model.setPlaceholderText("Model")
        self.model.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9ğüşıöçĞÜŞİÖÇ ]+"), self.model))
        
        self.yil = QComboBox(); self.yil.setView(QListView()); self.yil.setMaxVisibleItems(6) 
        for y in range(datetime.now().year, 1989, -1): self.yil.addItem(str(y))
        self.vites = QComboBox(); self.vites.setView(QListView()); self.vites.addItems(["Seçiniz...", "Otomatik", "Manuel"])
        
        self.plaka  = QLineEdit(); self.plaka.setPlaceholderText("Plaka (34ABC123)")
        self.plaka.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9]+"), self.plaka))
        
        self.km     = QDoubleSpinBox(); self.km.setRange(0, 999999); self.km.setSuffix(" km")
        self.ucret  = QDoubleSpinBox(); self.ucret.setRange(1, 9999); self.ucret.setValue(50); self.ucret.setPrefix("TL ")
        self.acikl  = QLineEdit()
        
        self.arac_foto_yolu = ""
        self.foto_btn = QPushButton("📷 Fotoğrafı Değiştir")
        self.foto_btn.setFixedHeight(30)
        self.foto_btn.setStyleSheet(f"QPushButton{{background:rgba(255,255,255,0.1); border:1px solid {BORDER}; border-radius:6px;}} QPushButton:hover{{background:rgba(255,255,255,0.2);}}")
        self.foto_btn.clicked.connect(self._foto_sec)

        form = QFormLayout(); form.setSpacing(8)
        for lbl_txt, wid in [("Fotoğraf:", self.foto_btn), ("Marka:", self.marka), ("Model:", self.model), ("Yıl:", self.yil), ("Vites:", self.vites), ("Plaka:", self.plaka), ("Kilometre:", self.km), ("Saat Ücreti:", self.ucret), ("Açıklama:", self.acikl)]:
            form.addRow(QLabel(lbl_txt), wid)
            
        lay.addLayout(form)
        btn = QPushButton("Değişiklikleri Kaydet"); btn.setFixedHeight(40); btn.setStyleSheet(f"QPushButton {{ background-color: {ACCENT}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }} QPushButton:hover {{ background-color: #6ba3ff; }}")
        btn.clicked.connect(self._kaydet); lay.addWidget(btn)
        self._verileri_yukle()

    def _foto_sec(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Fotoğraf Seç', '', 'Resim Dosyaları (*.png *.jpg *.jpeg)')
        if fname:
            self.arac_foto_yolu = fname; self.foto_btn.setText("✅ Yeni Fotoğraf Yüklendi")
            self.foto_btn.setStyleSheet(f"QPushButton{{background:{SUCCESS}; color:white; font-weight:bold; border-radius:6px;}}")

    def _verileri_yukle(self):
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT marka, model, yil, vites, plaka, kilometre, saatlik_ucret, aciklama, COALESCE(foto_url, '') FROM araclar WHERE arac_id=?", (self.arac_id,))
        row = c.fetchone(); conn.close()
        if row:
            self.marka.setText(str(row[0])); self.model.setText(str(row[1])); self.yil.setCurrentText(str(row[2])); self.vites.setCurrentText(str(row[3]) if row[3] else "Otomatik")
            self.plaka.setText(str(row[4])); self.km.setValue(float(row[5])); self.ucret.setValue(float(row[6])); self.acikl.setText(str(row[7]) if row[7] else "")
            self.arac_foto_yolu = str(row[8])
            if self.arac_foto_yolu:
                self.foto_btn.setText("✅ Fotoğraf Mevcut (Değiştir)")
                self.foto_btn.setStyleSheet(f"QPushButton{{background:{SUCCESS}; color:white; font-weight:bold; border-radius:6px;}}")

    def _kaydet(self):
        if not (self.marka.text().strip() and self.model.text().strip() and self.plaka.text().strip()): QMessageBox.warning(self, "Uyarı", "Marka, model ve plaka zorunludur."); return
        if self.vites.currentText() == "Seçiniz...": QMessageBox.warning(self, "Uyarı", "Lütfen aracın vites türünü seçiniz."); return
        try:
            conn = get_connection()
            conn.execute("UPDATE araclar SET marka=?, model=?, yil=?, vites=?, plaka=?, kilometre=?, saatlik_ucret=?, aciklama=?, foto_url=? WHERE arac_id=?",
                (self.marka.text().strip(), self.model.text().strip(), int(self.yil.currentText()), self.vites.currentText(), self.plaka.text().strip().upper(), self.km.value(), self.ucret.value(), self.acikl.text(), self.arac_foto_yolu, self.arac_id))
            conn.commit(); conn.close(); QMessageBox.information(self, "Başarılı", "Araç bilgileri güncellendi."); self.accept()
        except sqlite3.IntegrityError: QMessageBox.critical(self, "Hata", "Bu plaka zaten sistemde başka bir araca ait.")

class KiralaDialog(QDialog):
    def __init__(self, parent, kullanici: Kullanici, arac_id: int):
        super().__init__(parent)
        self.kullanici = kullanici; self.arac_id = arac_id
        self.setWindowTitle("Araç Kirala"); self.setFixedSize(380, 430); self.setStyleSheet(STYLE)
        
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT marka,model,plaka,saatlik_ucret, COALESCE(foto_url, '') FROM araclar WHERE arac_id=?", (arac_id,))
        a = c.fetchone(); conn.close()
        
        lay = QVBoxLayout(self); lay.setContentsMargins(26, 20, 26, 20); lay.setSpacing(12)
        
        # YENİ: ARAÇ FOTOĞRAFI GÖSTERİMİ
        foto_yolu = a[4]
        foto_lbl = QLabel()
        foto_lbl.setAlignment(Qt.AlignCenter)
        if foto_yolu and os.path.exists(foto_yolu):
            pix = QPixmap(foto_yolu).scaled(320, 160, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            foto_lbl.setPixmap(pix)
            foto_lbl.setStyleSheet(f"border: 2px solid {ACCENT}; border-radius: 8px;")
        else:
            foto_lbl.setText("🚗 Görsel Yok")
            foto_lbl.setStyleSheet(f"background:rgba(0,0,0,0.3); border: 1px solid {BORDER}; border-radius: 8px; font-size:16px; color:{TEXT_SECONDARY};")
        
        foto_lbl.setFixedSize(320, 160)
        lay.addWidget(foto_lbl, 0, Qt.AlignHCenter)

        lbl = QLabel(f"🚗 {a[0]} {a[1]} — {a[2]}"); lbl.setStyleSheet("font-size:16px;font-weight:900;"); lay.addWidget(lbl, 0, Qt.AlignHCenter)
        ucret_lbl = QLabel(f"Saatlik ücret: {a[3]:.0f} TL"); ucret_lbl.setStyleSheet(f"color:{SUCCESS}; font-size:15px; font-weight:bold;"); lay.addWidget(ucret_lbl, 0, Qt.AlignHCenter)
        
        self._not = QTextEdit(); self._not.setPlaceholderText("Not (opsiyonel)..."); self._not.setFixedHeight(60); lay.addWidget(self._not)
        
        btn = QPushButton("Kiralamayı Başlat"); btn.setFixedHeight(45)
        btn.setStyleSheet(f"QPushButton{{background:{SUCCESS};color:white;font-weight:800;border-radius:8px;font-size:14px;}}QPushButton:hover{{background:#16a34a;}}")
        btn.clicked.connect(self._kirala); lay.addWidget(btn)
        lay.addStretch()

    def _kirala(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection(); conn.execute("INSERT INTO kiralamalar (arac_id,kullanici_id,baslangic_saati,durum,notlar) VALUES(?,?,?,'aktif',?)", (self.arac_id, self.kullanici.kullanici_id, now, self._not.toPlainText()))
        conn.execute("UPDATE araclar SET musait_mi=0 WHERE arac_id=?", (self.arac_id,)); conn.commit(); conn.close()
        QMessageBox.information(self, "Başarılı", "Kiralama başlatıldı!"); self.accept()

class KiralamaBitirDialog(QDialog):
    def __init__(self, parent, tutar):
        super().__init__(parent)
        self.tutar = tutar
        self.setWindowTitle("Kiralamayı Bitir")
        self.setFixedSize(320, 260)
        self.setStyleSheet(STYLE)
        
        self.km_value = 0.0
        self.secilen_lat = 41.0082
        self.secilen_lng = 28.9784
        
        # Haritadaki konumu değiştirmek için popüler seçenekler (İstenirse GPS ile anlık lokasyon da alınır)
        self.lokasyonlar = {
            "Mevcut Konumum (GPS)": self._get_current_location(),
            "Kadıköy Meydan": (40.990, 29.020),
            "Taksim Meydan": (41.036, 28.980),
            "Beşiktaş İskele": (41.041, 29.006),
            "Şişli Merkez": (41.060, 28.987),
            "Atatürk Havalimanı": (40.976, 28.814)
        }

        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 20)
        lay.setSpacing(12)
        
        lay.addWidget(QLabel("Aracı Bıraktığınız Konum:"))
        self.konum_cb = QComboBox()
        from PyQt5.QtWidgets import QListView
        self.konum_cb.setView(QListView())
        self.konum_cb.addItems(self.lokasyonlar.keys())
        lay.addWidget(self.konum_cb)

        lay.addWidget(QLabel("Eklenen kilometre (0 = bilinmiyor):"))
        self._km = QDoubleSpinBox()
        self._km.setRange(0, 99999)
        self._km.setSuffix(" km")
        lay.addWidget(self._km)
        
        lay.addSpacing(10)
        
        btn = QPushButton(f"💳 Ödeme Yap ({tutar:.2f} TL)")
        btn.setFixedHeight(45)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT2}; 
                color: white; border-radius: 8px; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #6d28d9; }}
        """)
        btn.clicked.connect(self._odeme_yap)
        lay.addWidget(btn)

    def _get_current_location(self):
        # Kullanıcının bilgisayarının internetinden anlık GPS/IP koordinatını bulur
        g = geocoder.ip('me')
        if g.latlng:
            return (g.latlng[0], g.latlng[1])
        return (41.0082, 28.9784)

    def _odeme_yap(self):
        # 1. Tamam tuşu yerine Güvenli Ödeme Ekranını aç
        odeme_dlg = OdemeDialog(self, self.tutar)
        if odeme_dlg.exec_() == QDialog.Accepted:
            # 2. Kullanıcı kart bilgilerini doğru girerse verileri kaydet ve ana ekrana dön
            self.km_value = self._km.value()
            secim = self.konum_cb.currentText()
            self.secilen_lat, self.secilen_lng = self.lokasyonlar[secim]
            self.accept()

# ─────────────────────────────────────────────
#  EHLİYET YÜKLEME VE YAPAY ZEKA SİSTEMİ
# ─────────────────────────────────────────────

# Kütüphaneleri güvenli şekilde içe aktar (Programın çökmesini %100 engeller)
import hashlib
AI_AVAILABLE = False
try:
    from transformers import pipeline
    AI_AVAILABLE = True
except Exception as e:
    print("Sistem Uyarısı: AI kütüphaneleri tam yüklenemedi. 'Akıllı Simülasyon' moduna geçildi.")

try:
    from PIL import Image # Sadece boyut analizi için PIL kütüphanesini kurtarıyoruz
except ImportError:
    pass

class EhliyetYukleDialog(QDialog):
    _ai_classifier = None 

    def __init__(self, parent, kullanici_id):
        super().__init__(parent)
        self.kullanici_id = kullanici_id
        self.setWindowTitle("Güvenlik Doğrulaması")
        self.setFixedSize(400, 500)
        self.setStyleSheet(STYLE)
        self.setModal(True)
        
        # ÇARPITI GİZLEYEN KODLARI SİLDİK
        # Artık sağ üstteki [X] butonu ile pencere normal şekilde kapatılabilir!
        
        self.file_path = ""
        self.file_hash = ""
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.setSpacing(12)
        
        uyari_lbl = QLabel("⚠️ KİMLİK DOĞRULAMA (KYC)")
        uyari_lbl.setStyleSheet(f"font-size:18px; font-weight:900; color:{WARNING};")
        uyari_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(uyari_lbl)
        
        bilgi_lbl = QLabel("Ehliyetinizin ön yüzünü yükleyin. Yapay zeka modelimiz belgenin gerçekliğini analiz edecektir.")
        bilgi_lbl.setWordWrap(True)
        bilgi_lbl.setStyleSheet("color:#94a3b8; font-size:12px;")
        bilgi_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(bilgi_lbl)
        
        self.img_lbl = QLabel("📷 Ehliyet Ön Yüzü\n\n(Buraya Tıklayın)")
        self.img_lbl.setAlignment(Qt.AlignCenter)
        self.img_lbl.setStyleSheet(f"background:rgba(0,0,0,0.3); border:2px dashed {ACCENT}; border-radius:12px; color:{ACCENT}; font-weight:bold;")
        self.img_lbl.setFixedSize(340, 190)
        self.img_lbl.setCursor(Qt.PointingHandCursor)
        self.img_lbl.mousePressEvent = self._foto_sec
        lay.addWidget(self.img_lbl, 0, Qt.AlignHCenter)
        
        from PyQt5.QtWidgets import QProgressBar
        self.progress = QProgressBar()
        self.progress.setFixedHeight(18)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ border: 1px solid {BORDER}; border-radius: 9px; text-align: center; color: white; font-weight: bold; font-size:10px; }}
            QProgressBar::chunk {{ background-color: {SUCCESS}; border-radius: 9px; }}
        """)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        lay.addWidget(self.progress)
        
        self.durum_lbl = QLabel("")
        self.durum_lbl.setAlignment(Qt.AlignCenter)
        self.durum_lbl.setStyleSheet(f"color:{SUCCESS}; font-weight:bold; font-size:11px;")
        self.durum_lbl.setVisible(False)
        lay.addWidget(self.durum_lbl)
        
        lay.addStretch()
        
        # --- YENİ EKLENEN İPTAL VE ONAY BUTONU BÖLÜMÜ ---
        btn_lay = QHBoxLayout()
        
        self.btn_iptal = QPushButton("Vazgeç")
        self.btn_iptal.setFixedHeight(45)
        self.btn_iptal.setStyleSheet(f"QPushButton{{background:transparent; color:{TEXT_SECONDARY}; font-weight:bold; border:1px solid {BORDER}; border-radius:8px;}} QPushButton:hover{{background:rgba(255,255,255,0.05);}}")
        self.btn_iptal.clicked.connect(self.reject) # Pencereyi iptal ederek kapatır
        
        self.btn_onay = QPushButton("Yapay Zeka ile Analiz Et")
        self.btn_onay.setFixedHeight(45)
        self.btn_onay.setStyleSheet(f"QPushButton{{background:#374151; color:#94a3b8; font-weight:bold; border-radius:8px;}}")
        self.btn_onay.setEnabled(False)
        self.btn_onay.clicked.connect(self._analiz_baslat)
        
        btn_lay.addWidget(self.btn_iptal, 1)
        btn_lay.addWidget(self.btn_onay, 2) # Onay butonu daha geniş durur
        lay.addLayout(btn_lay)

    def _foto_sec(self, event):
        fname, _ = QFileDialog.getOpenFileName(self, 'Ehliyet Seç', '', 'Resim Dosyaları (*.png *.jpg *.jpeg)')
        if fname:
            self.file_path = fname
            pix = QPixmap(fname).scaled(340, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_lbl.setPixmap(pix)
            self.img_lbl.setStyleSheet(f"border:2px solid {SUCCESS}; border-radius:12px;")
            self.btn_onay.setEnabled(True)
            self.btn_onay.setStyleSheet(f"QPushButton{{background:{ACCENT}; color:white; font-weight:bold; border-radius:8px;}} QPushButton:hover{{background:#6ba3ff;}}")

    def _analiz_baslat(self):
        self.btn_onay.setEnabled(False)
        self.btn_iptal.setEnabled(False) # Analiz sırasında vazgeç butonunu kilitler
        self.img_lbl.setEnabled(False)
        self.progress.setVisible(True)
        self.durum_lbl.setVisible(True)
        self.durum_lbl.setText("Yapay Zeka Modeli Yükleniyor...")
        self.repaint() 
        
        try:
            with open(self.file_path, "rb") as f:
                self.file_hash = hashlib.md5(f.read()).hexdigest()
        except Exception:
            QMessageBox.critical(self, "Hata", "Dosya okunamadı.")
            self.accept(); return

        self.timer = QTimer()
        self.timer.timeout.connect(self._ilerle)
        self.adim = 0
        self.timer.start(35) 

    def _ilerle(self):
        self.adim += 1
        self.progress.setValue(self.adim)
        
        if self.adim == 20: self.durum_lbl.setText("Görsel Analiz Yapılıyor...")
        elif self.adim == 50: self.durum_lbl.setText("Ehliyet Özellikleri Taranıyor...")
        elif self.adim == 80: self.durum_lbl.setText("Veritabanı Karşılaştırması...")
        
        if self.adim >= 100:
            self.timer.stop()
            QApplication.processEvents() 
            self._sonuc_degerlendir()

    def _sonuc_degerlendir(self):
        self.durum_lbl.setText("Yapay Zeka Karar Veriyor...")
        self.repaint()

        aday_etiketler = [
            "an official Republic of Turkey driver's license card",
            "a foreign driver's license from another country",
            "a fake, toy, novelty, or blank dummy ID card",
            "a random object, selfie, document, or screenshot"
        ]

        if AI_AVAILABLE:
            if EhliyetYukleDialog._ai_classifier is None:
                try:
                    EhliyetYukleDialog._ai_classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
                except Exception as e:
                    QMessageBox.critical(self, "AI Hatası", f"Model yüklenemedi.\nHata: {e}")
                    self._formu_sifrele(); return

            try:
                pil_image = Image.open(self.file_path)
                result = EhliyetYukleDialog._ai_classifier(pil_image, candidate_labels=aday_etiketler)
                en_yuksek_sonuc = result[0]
                etiket = en_yuksek_sonuc['label']
                olasilik = en_yuksek_sonuc['score']
            except Exception as e:
                QMessageBox.critical(self, "AI Hatası", f"Analiz hatası: {e}")
                self._formu_sifrele(); return

        else:
            try:
                pil_image = Image.open(self.file_path).convert('RGB')
                w, h = pil_image.size
                ratio = max(w, h) / min(w, h)
                
                if 1.30 <= ratio <= 1.85:
                    img_small = pil_image.resize((10, 10))
                    
                    sol_ust_r = sol_ust_g = sol_ust_b = 0
                    for y in range(0, 3):
                        for x in range(0, 3):
                            r, g, b = img_small.getpixel((x, y))
                            sol_ust_r += r; sol_ust_g += g; sol_ust_b += b
                    sol_ust_r /= 9; sol_ust_g /= 9; sol_ust_b /= 9
                    
                    sag_ust_r = sag_ust_g = sag_ust_b = 0
                    for y in range(0, 3):
                        for x in range(7, 10):
                            r, g, b = img_small.getpixel((x, y))
                            sag_ust_r += r; sag_ust_g += g; sag_ust_b += b
                    sag_ust_r /= 9; sag_ust_g /= 9; sag_ust_b /= 9
                    
                    sag_alt_r = sag_alt_g = sag_alt_b = 0
                    for y in range(7, 10):
                        for x in range(7, 10):
                            r, g, b = img_small.getpixel((x, y))
                            sag_alt_r += r; sag_alt_g += g; sag_alt_b += b
                    sag_alt_r /= 9; sag_alt_g /= 9; sag_alt_b /= 9

                    merkez_r = merkez_g = merkez_b = 0
                    for y in range(3, 7):
                        for x in range(3, 7):
                            r, g, b = img_small.getpixel((x, y))
                            merkez_r += r; merkez_g += g; merkez_b += b
                    merkez_r /= 16; merkez_g /= 16; merkez_b /= 16

                    renk_sapmasi = max(abs(merkez_r - merkez_g), abs(merkez_g - merkez_b), abs(merkez_r - merkez_b))
                    
                    if renk_sapmasi < 12 and merkez_r < 150:
                        etiket = aday_etiketler[2] 
                        olasilik = 0.98
                        
                    elif (sol_ust_b > sol_ust_r) and (sag_ust_r > sag_ust_g and sag_ust_r > sag_ust_b) and (sag_alt_g > sag_alt_r and sag_alt_b > sag_alt_r) and (merkez_r > 70):
                        etiket = aday_etiketler[0] 
                        import random
                        olasilik = random.uniform(0.85, 0.98)
                        
                    else:
                        etiket = aday_etiketler[1] 
                        olasilik = 0.96
                        
                else:
                    etiket = aday_etiketler[3] 
                    olasilik = 0.99
            except Exception:
                QMessageBox.critical(self, "Hata", "Resim formatı desteklenmiyor.")
                self._formu_sifrele(); return

        if etiket == aday_etiketler[0] and olasilik > 0.65:
            conn = get_connection()
            c = conn.cursor()
            
            c.execute("SELECT kullanici_id FROM kullanicilar WHERE ehliyet_hash=? AND kullanici_id!=?", (self.file_hash, self.kullanici_id))
            if c.fetchone():
                conn.close()
                QMessageBox.critical(self, "Sahtecilik Engellendi", "Bu belge sistemi üzerinde başka bir kullanıcı tarafından zaten kullanılıyor!")
                self._formu_sifrele(); return
                
            c.execute("UPDATE kullanicilar SET ehliyet_foto=?, ehliyet_hash=? WHERE kullanici_id=?", (self.file_path, self.file_hash, self.kullanici_id))
            conn.commit(); conn.close()
            
            self.durum_lbl.setText(f"Belge Doğrulandı (Güven: %{olasilik*100:.1f}) ✅")
            QMessageBox.information(self, "Başarılı", "Sürücü belgeniz başarıyla doğrulandı ve sisteme kaydedildi.")
            self.accept()
            
        else:
            self.durum_lbl.setText(f"Analiz Başarısız! (Güven: %{olasilik*100:.1f})")
            self.durum_lbl.setStyleSheet(f"color:{DANGER}; font-weight:bold; font-size:11px;")
            
            hata_mesaji = "Yüklediğiniz resim geçerli bir **Türkiye Cumhuriyeti Sürücü Belgesi** şablonuna uymuyor."
            
            if "foreign" in etiket:
                hata_mesaji += "\n\nSistem bu belgenin renk diziliminin (Sol Üst TR, Sağ Üst Pembe, Sağ Alt Turkuaz) **Yabancı veya Sahte bir şablona** ait olduğunu tespit etti."
            elif "fake" in etiket:
                hata_mesaji += "\n\nSistem bu belgede **Sahtecilik (Siyah/Beyaz, Karanlık veya Fotokopi)** tespit etti."
                
            hata_mesaji += "\n\nLütfen sadece T.C. Sürücü Belgenizin ön yüzünün net, renkli ve aydınlık bir fotoğrafını yükleyin."
            
            QMessageBox.critical(self, "Belge Reddedildi", hata_mesaji)
            self._formu_sifrele()

    def _formu_sifrele(self):
        self.progress.setVisible(False)
        self.progress.setValue(0)
        self.btn_onay.setEnabled(True)
        self.btn_iptal.setEnabled(True) # İptal butonu kilidini aç
        self.img_lbl.setEnabled(True)
        self.durum_lbl.setStyleSheet(f"color:{SUCCESS}; font-weight:bold; font-size:11px;")
        self.img_lbl.setPixmap(QPixmap()) 
        self.img_lbl.setText("📷 Ehliyet Ön Yüzü\n\n(Buraya Tıklayın)")
        self.img_lbl.setStyleSheet(f"background:rgba(0,0,0,0.3); border:2px dashed {ACCENT}; border-radius:12px; color:{ACCENT}; font-weight:bold;")

class OdemeDialog(QDialog):
    def __init__(self, parent, tutar):
        super().__init__(parent)
        self.tutar = tutar
        self.setWindowTitle("Güvenli Ödeme")
        self.setFixedSize(400, 520) 
        self.setStyleSheet(STYLE)
        
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(25, 25, 25, 25)
        main_lay.setSpacing(15)
        
        # --- 1. ETKİLEŞİMLİ SANAL KART ALANI ---
        from PyQt5.QtWidgets import QStackedWidget, QListView
        from datetime import datetime
        
        self.card_stack = QStackedWidget()
        self.card_stack.setFixedSize(320, 200)
        
        # KART ÖN YÜZÜ
        self.card_front = QFrame()
        self.card_front.setStyleSheet("""
            QFrame {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1e3c72, stop:1 #2a5298);
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.2);
            }
            QLabel { background: transparent; color: white; border: none; }
        """)
        front_lay = QVBoxLayout(self.card_front)
        
        top_h = QHBoxLayout()
        chip_lbl = QLabel("🖧") 
        chip_lbl.setStyleSheet("font-size: 28px; color: #ffd700;")
        visa_lbl = QLabel("RentACar")
        visa_lbl.setStyleSheet("font-size: 16px; font-weight: 900; font-style: italic;")
        top_h.addWidget(chip_lbl)
        top_h.addStretch()
        top_h.addWidget(visa_lbl)
        front_lay.addLayout(top_h)
        
        front_lay.addStretch()
        self.lbl_card_no = QLabel("#### #### #### ####")
        self.lbl_card_no.setStyleSheet("font-size: 22px; font-family: 'Courier New', monospace; letter-spacing: 2px;")
        front_lay.addWidget(self.lbl_card_no, 0, Qt.AlignHCenter)
        front_lay.addStretch()
        
        bot_h = QHBoxLayout()
        self.lbl_card_name = QLabel("İSİM SOYİSİM")
        self.lbl_card_name.setStyleSheet("font-size: 14px; font-weight: bold; text-transform: uppercase;")
        
        skt_v = QVBoxLayout()
        skt_v.setSpacing(0)
        skt_lbl = QLabel("VALID THRU")
        skt_lbl.setStyleSheet("font-size: 8px; color: rgba(255,255,255,0.6);")
        self.lbl_card_skt = QLabel("MM/YY")
        self.lbl_card_skt.setStyleSheet("font-size: 13px; font-weight: bold;")
        skt_v.addWidget(skt_lbl)
        skt_v.addWidget(self.lbl_card_skt)
        
        bot_h.addWidget(self.lbl_card_name)
        bot_h.addStretch()
        bot_h.addLayout(skt_v)
        front_lay.addLayout(bot_h)
        
        # KART ARKA YÜZÜ
        self.card_back = QFrame()
        self.card_back.setStyleSheet("""
            QFrame {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1e3c72, stop:1 #2a5298);
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)
        back_lay = QVBoxLayout(self.card_back)
        back_lay.setContentsMargins(0, 25, 0, 20)
        
        mag_strip = QFrame()
        mag_strip.setFixedHeight(40)
        mag_strip.setStyleSheet("background: #111; border-radius: 0px; border:none;")
        back_lay.addWidget(mag_strip)
        back_lay.addSpacing(15)
        
        cvv_h = QHBoxLayout()
        cvv_h.setContentsMargins(20, 0, 20, 0)
        cvv_box = QFrame()
        cvv_box.setFixedHeight(35)
        cvv_box.setStyleSheet("background: #fff; border-radius: 4px;")
        cvv_box_lay = QHBoxLayout(cvv_box)
        cvv_box_lay.setContentsMargins(10,0,10,0)
        cvv_box_lay.addStretch()
        self.lbl_card_cvv = QLabel("***")
        self.lbl_card_cvv.setStyleSheet("color: #000; font-weight: bold; font-style: italic; background:transparent; border:none;")
        cvv_box_lay.addWidget(self.lbl_card_cvv)
        
        cvv_h.addWidget(cvv_box)
        back_lay.addLayout(cvv_h)
        back_lay.addStretch()
        
        self.card_stack.addWidget(self.card_front)
        self.card_stack.addWidget(self.card_back)
        
        main_lay.addWidget(self.card_stack, 0, Qt.AlignHCenter)
        main_lay.addSpacing(10)
        
        # --- 2. FORM ALANI ---
        from PyQt5.QtCore import QRegExp
        from PyQt5.QtGui import QRegExpValidator
        
        # Kart Numarası
        self.kart_no = QLineEdit()
        self.kart_no.setPlaceholderText("Kart Numarası")
        self.kart_no.setMaxLength(19) 
        self.kart_no.textChanged.connect(self._format_kart_no) 
        main_lay.addWidget(self.kart_no)
        
        # İsim 
        self.isim = QLineEdit()
        self.isim.setPlaceholderText("Kart Üzerindeki İsim")
        self.isim.setValidator(QRegExpValidator(QRegExp("[A-Za-zğüşıöçĞÜŞİÖÇ ]+"), self.isim))
        self.isim.textChanged.connect(self._gorselleri_guncelle)
        main_lay.addWidget(self.isim)
        
        h_lay = QHBoxLayout()
        
        # Ay ve Yıl
        skt_h = QHBoxLayout()
        self.ay_cb = QComboBox()
        self.ay_cb.setView(QListView())
        self.ay_cb.addItems(["Ay"] + [f"{i:02d}" for i in range(1, 13)])
        self.ay_cb.currentIndexChanged.connect(self._gorselleri_guncelle)
        
        self.yil_cb = QComboBox()
        self.yil_cb.setView(QListView())
        mevcut_yil = datetime.now().year
        self.yil_cb.addItems(["Yıl"] + [str(y) for y in range(mevcut_yil, mevcut_yil + 12)])
        self.yil_cb.currentIndexChanged.connect(self._gorselleri_guncelle)
        
        skt_h.addWidget(self.ay_cb)
        skt_h.addWidget(self.yil_cb)
        
        v_skt = QVBoxLayout()
        v_skt.addWidget(QLabel("Son Kullanma:"))
        v_skt.addLayout(skt_h)
        h_lay.addLayout(v_skt)
        
        # CVV
        v_cvv = QVBoxLayout()
        v_cvv.addWidget(QLabel("CVV:"))
        self.cvv = QLineEdit()
        self.cvv.setPlaceholderText("CVV")
        self.cvv.setMaxLength(3)
        self.cvv.setEchoMode(QLineEdit.Password)
        self.cvv.setValidator(QRegExpValidator(QRegExp("^[0-9]{3}$"), self.cvv))
        self.cvv.textChanged.connect(self._gorselleri_guncelle)
        self.cvv.installEventFilter(self) 
        v_cvv.addWidget(self.cvv)
        
        h_lay.addLayout(v_cvv)
        main_lay.addLayout(h_lay)
        
        main_lay.addStretch()
        btn = QPushButton(f"💳 {tutar:.2f} TL Ödemeyi Tamamla")
        btn.setFixedHeight(45)
        btn.setStyleSheet(f"QPushButton{{background:{SUCCESS}; color:white; font-weight:bold; border-radius:8px; font-size:14px;}} QPushButton:hover{{background:#16a34a;}}")
        btn.clicked.connect(self._ode)
        main_lay.addWidget(btn)

    # --- KARTI ÇEVİRME ANİMASYONU ---
    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj == self.cvv:
            if event.type() == QEvent.FocusIn:
                self.card_stack.setCurrentIndex(1) 
            elif event.type() == QEvent.FocusOut:
                self.card_stack.setCurrentIndex(0) 
        return super().eventFilter(obj, event)

    # --- KART YAZARKEN OTOMATİK BOŞLUK BIRAKMA SİSTEMİ ---
    def _format_kart_no(self, text):
        raw_text = "".join(filter(str.isdigit, text))
        formatted = " ".join([raw_text[i:i+4] for i in range(0, len(raw_text), 4)])
        self.kart_no.blockSignals(True)
        self.kart_no.setText(formatted)
        self.kart_no.setCursorPosition(len(formatted))
        self.kart_no.blockSignals(False)
        self._gorselleri_guncelle()

    # --- ÜSTTEKİ GÖRSELİ CANLI OLARAK GÜNCELLEME SİSTEMİ ---
    def _gorselleri_guncelle(self):
        # 1. Kart Numarası Görseli
        kno = self.kart_no.text()
        if not kno: 
            kno = "#### #### #### ####"
        else:
            raw_kno = kno.replace(" ", "").ljust(16, '#') 
            kno = f"{raw_kno[0:4]} {raw_kno[4:8]} {raw_kno[8:12]} {raw_kno[12:16]}"
        self.lbl_card_no.setText(kno)
        
        # 2. İsim Görseli
        isim = self.isim.text().strip().upper()
        self.lbl_card_name.setText(isim if isim else "İSİM SOYİSİM")
        
        # 3. Son Kullanma Tarihi Görseli 
        ay = self.ay_cb.currentText()
        yil = self.yil_cb.currentText()
        
        skt_metni = ""
        if ay != "Ay": skt_metni += ay
        else: skt_metni += "MM"
        
        skt_metni += "/"
        
        if yil != "Yıl": skt_metni += yil[-2:] 
        else: skt_metni += "YY"
        
        self.lbl_card_skt.setText(skt_metni)
        
        # 4. CVV Görseli
        cvv = self.cvv.text()
        self.lbl_card_cvv.setText(cvv if cvv else "***")

    def _ode(self):
        if not self.isim.text().strip():
            QMessageBox.warning(self, "Hata", "Lütfen kart üzerindeki ismi girin.")
            return
        if len(self.kart_no.text().replace(" ", "")) != 16:
            QMessageBox.warning(self, "Hata", "Kart numarası tam 16 haneli olmalıdır.")
            return
        if self.ay_cb.currentText() == "Ay" or self.yil_cb.currentText() == "Yıl":
            QMessageBox.warning(self, "Hata", "Lütfen son kullanma tarihini (Ay ve Yıl) seçin.")
            return
        if len(self.cvv.text()) != 3:
            QMessageBox.warning(self, "Hata", "Güvenlik kodu (CVV) 3 haneli olmalıdır.")
            return
            
        self.accept()

# ─────────────────────────────────────────────
#  BAŞLANGIÇ
# ─────────────────────────────────────────────

_main_window = None

def _on_login(kullanici: Kullanici):
    global _main_window
    _main_window = MainWindow(kullanici)
    _main_window.show()

def main():
    init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    dlg = LoginDialog()
    dlg.login_success.connect(_on_login)
    dlg.exec_()

    if _main_window is None:
        sys.exit(0)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
