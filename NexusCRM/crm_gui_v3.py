import sys
import json
import sqlite3
import os
import subprocess
import platform
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QMessageBox, QHeaderView,
    QStackedWidget, QFrame, QScrollArea, QTextEdit,
    QDialog, QComboBox, QDateEdit, QSplitter, QListWidget,
    QListWidgetItem, QSizePolicy, QGridLayout, QSpacerItem,
    QFileDialog, QShortcut
)
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette, QPixmap, QPainter, QBrush, QKeySequence

# Matplotlib entegrasyonu
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_VAR = True
except ImportError:
    MATPLOTLIB_VAR = False

# ─── VERİTABANI YÖNETİCİSİ ───────────────────────────────────────────────────

DB_YOLU = "crm_nexus.db"

def db_baglanti():
    return sqlite3.connect(DB_YOLU)

def db_olustur():
    con = db_baglanti()
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS musteriler (
            musteri_id TEXT PRIMARY KEY,
            ad TEXT NOT NULL,
            telefon TEXT,
            email TEXT,
            sirket TEXT,
            durum TEXT DEFAULT 'Aktif'
        );
        CREATE TABLE IF NOT EXISTS firsatlar (
            firsat_id TEXT PRIMARY KEY,
            baslik TEXT NOT NULL,
            musteri_id TEXT,
            deger REAL DEFAULT 0,
            asama TEXT DEFAULT 'Prospekt',
            son_tarih TEXT,
            aciklama TEXT,
            atanan TEXT
        );
        CREATE TABLE IF NOT EXISTS gorevler (
            gorev_id TEXT PRIMARY KEY,
            baslik TEXT NOT NULL,
            firsat_id TEXT,
            son_tarih TEXT,
            durum TEXT DEFAULT 'Yapılacak',
            etiket TEXT DEFAULT 'Genel',
            atanan TEXT,
            aciklama TEXT,
            yorumlar TEXT DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS destek_talebi (
            talep_id TEXT PRIMARY KEY,
            aciklama TEXT,
            musteri_id TEXT,
            durum TEXT DEFAULT 'Açık',
            oncelik TEXT DEFAULT 'Normal'
        );
        CREATE TABLE IF NOT EXISTS aktiviteler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_id TEXT,
            tarih TEXT,
            mesaj TEXT
        );
        CREATE TABLE IF NOT EXISTS dosyalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ilgili_id TEXT,
            ilgili_tip TEXT,
            dosya_adi TEXT,
            dosya_yolu TEXT,
            ekleme_tarihi TEXT
        );
    """)
    con.commit()
    con.close()

def json_den_sqlite_goc():
    """Eski veri.json varsa SQLite'a aktar."""
    if not os.path.exists("veri.json"):
        return
    try:
        with open("veri.json", "r", encoding="utf-8") as f:
            veri = json.load(f)
        con = db_baglanti()
        cur = con.cursor()
        for m in veri.get("musteriler", []):
            try:
                cur.execute("INSERT OR IGNORE INTO musteriler VALUES (?,?,?,?,?,?)", m[:6])
            except Exception:
                pass
        for fi in veri.get("firsatlar", []):
            try:
                cur.execute("INSERT OR IGNORE INTO firsatlar VALUES (?,?,?,?,?,?,?,?)", fi[:8])
            except Exception:
                pass
        for g in veri.get("gorevler", []):
            try:
                cur.execute("INSERT OR IGNORE INTO gorevler (gorev_id,baslik,firsat_id,son_tarih,durum,etiket,atanan,aciklama) VALUES (?,?,?,?,?,?,?,?)", g[:8])
            except Exception:
                pass
        for t in veri.get("talepler", []):
            try:
                cur.execute("INSERT OR IGNORE INTO destek_talebi VALUES (?,?,?,?,?)", t[:5])
            except Exception:
                pass
        con.commit()
        con.close()
        os.rename("veri.json", "veri.json.bak")
    except Exception as e:
        print(f"Göç hatası: {e}")

# ─── VERİ MODELLERİ ──────────────────────────────────────────────────────────

class Musteri:
    def __init__(self, musteri_id, ad, telefon, email="", sirket="", durum="Aktif"):
        self.musteri_id = musteri_id
        self.ad = ad
        self.telefon = telefon
        self.email = email
        self.sirket = sirket
        self.durum = durum

    @staticmethod
    def hepsini_getir(arama=""):
        con = db_baglanti()
        cur = con.cursor()
        if arama:
            cur.execute("SELECT * FROM musteriler WHERE lower(ad) LIKE ? OR lower(email) LIKE ? OR lower(sirket) LIKE ?",
                        (f"%{arama.lower()}%",) * 3)
        else:
            cur.execute("SELECT * FROM musteriler")
        rows = cur.fetchall()
        con.close()
        return [Musteri(*r) for r in rows]

    @staticmethod
    def sayisi():
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM musteriler")
        n = cur.fetchone()[0]
        con.close()
        return n

    def kaydet(self):
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("INSERT OR REPLACE INTO musteriler VALUES (?,?,?,?,?,?)",
                    (self.musteri_id, self.ad, self.telefon, self.email, self.sirket, self.durum))
        con.commit()
        con.close()
        aktivite_ekle(self.musteri_id, f"Müşteri eklendi: {self.ad}")

    def sil(self):
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("DELETE FROM musteriler WHERE musteri_id=?", (self.musteri_id,))
        con.commit()
        con.close()

class Firsat:
    def __init__(self, firsat_id, baslik, musteri_id, deger, asama="Prospekt", son_tarih="", aciklama="", atanan=""):
        self.firsat_id = firsat_id
        self.baslik = baslik
        self.musteri_id = musteri_id
        self.deger = deger
        self.asama = asama
        self.son_tarih = son_tarih
        self.aciklama = aciklama
        self.atanan = atanan

    @staticmethod
    def hepsini_getir():
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("SELECT firsat_id,baslik,musteri_id,deger,asama,son_tarih,aciklama,atanan FROM firsatlar")
        rows = cur.fetchall()
        con.close()
        return [Firsat(*r) for r in rows]

    @staticmethod
    def sayisi():
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM firsatlar")
        n = cur.fetchone()[0]
        con.close()
        return n

    def kaydet(self):
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("INSERT OR REPLACE INTO firsatlar VALUES (?,?,?,?,?,?,?,?)",
                    (self.firsat_id, self.baslik, self.musteri_id, self.deger,
                     self.asama, self.son_tarih, self.aciklama, self.atanan))
        con.commit()
        con.close()
        if self.musteri_id:
            aktivite_ekle(self.musteri_id, f"Yeni fırsat: {self.baslik} ({self.asama})")

    def sil(self):
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("DELETE FROM firsatlar WHERE firsat_id=?", (self.firsat_id,))
        con.commit()
        con.close()

class Gorev:
    def __init__(self, gorev_id, baslik, firsat_id, son_tarih, durum="Yapılacak",
                 etiket="Genel", atanan="", aciklama="", yorumlar=None):
        self.gorev_id = gorev_id
        self.baslik = baslik
        self.firsat_id = firsat_id
        self.son_tarih = son_tarih
        self.durum = durum
        self.etiket = etiket
        self.atanan = atanan
        self.aciklama = aciklama
        self.yorumlar = yorumlar if yorumlar is not None else []

    @staticmethod
    def hepsini_getir():
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("SELECT gorev_id,baslik,firsat_id,son_tarih,durum,etiket,atanan,aciklama,yorumlar FROM gorevler")
        rows = cur.fetchall()
        con.close()
        result = []
        for r in rows:
            try:
                yorumlar = json.loads(r[8]) if r[8] else []
            except Exception:
                yorumlar = []
            g = Gorev(*r[:8], yorumlar=yorumlar)
            result.append(g)
        return result

    @staticmethod
    def acik_sayisi():
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM gorevler WHERE durum='Yapılacak'")
        n = cur.fetchone()[0]
        con.close()
        return n

    def kaydet(self):
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("""INSERT OR REPLACE INTO gorevler
                       (gorev_id,baslik,firsat_id,son_tarih,durum,etiket,atanan,aciklama,yorumlar)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (self.gorev_id, self.baslik, self.firsat_id, self.son_tarih,
                     self.durum, self.etiket, self.atanan, self.aciklama,
                     json.dumps(self.yorumlar, ensure_ascii=False)))
        con.commit()
        con.close()

    def sil(self):
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("DELETE FROM gorevler WHERE gorev_id=?", (self.gorev_id,))
        con.commit()
        con.close()

class DestekTalebi:
    def __init__(self, talep_id, aciklama, musteri_id, durum="Açık", oncelik="Normal"):
        self.talep_id = talep_id
        self.aciklama = aciklama
        self.musteri_id = musteri_id
        self.durum = durum
        self.oncelik = oncelik

    @staticmethod
    def hepsini_getir():
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("SELECT * FROM destek_talebi")
        rows = cur.fetchall()
        con.close()
        return [DestekTalebi(*r) for r in rows]

    @staticmethod
    def sayisi():
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM destek_talebi")
        n = cur.fetchone()[0]
        con.close()
        return n

    def kaydet(self):
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("INSERT OR REPLACE INTO destek_talebi VALUES (?,?,?,?,?)",
                    (self.talep_id, self.aciklama, self.musteri_id, self.durum, self.oncelik))
        con.commit()
        con.close()

    def sil(self):
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("DELETE FROM destek_talebi WHERE talep_id=?", (self.talep_id,))
        con.commit()
        con.close()

def aktivite_ekle(musteri_id, mesaj):
    tarih = datetime.now().strftime("%d %b %Y %H:%M")
    con = db_baglanti()
    cur = con.cursor()
    cur.execute("INSERT INTO aktiviteler (musteri_id, tarih, mesaj) VALUES (?,?,?)",
                (musteri_id, tarih, mesaj))
    con.commit()
    con.close()

def aktiviteleri_getir(musteri_id):
    con = db_baglanti()
    cur = con.cursor()
    cur.execute("SELECT tarih, mesaj FROM aktiviteler WHERE musteri_id=? ORDER BY id DESC LIMIT 20",
                (musteri_id,))
    rows = cur.fetchall()
    con.close()
    return rows

def dosya_ekle(ilgili_id, ilgili_tip, dosya_yolu):
    dosya_adi = os.path.basename(dosya_yolu)
    tarih = datetime.now().strftime("%d %b %Y %H:%M")
    con = db_baglanti()
    cur = con.cursor()
    cur.execute("INSERT INTO dosyalar (ilgili_id, ilgili_tip, dosya_adi, dosya_yolu, ekleme_tarihi) VALUES (?,?,?,?,?)",
                (ilgili_id, ilgili_tip, dosya_adi, dosya_yolu, tarih))
    con.commit()
    con.close()

def dosyalari_getir(ilgili_id):
    con = db_baglanti()
    cur = con.cursor()
    cur.execute("SELECT id, dosya_adi, dosya_yolu, ekleme_tarihi FROM dosyalar WHERE ilgili_id=?", (ilgili_id,))
    rows = cur.fetchall()
    con.close()
    return rows

# ─── RENK PALETİ ─────────────────────────────────────────────────────────────

BG_KOYU      = "#0f172a"
BG_ORTA      = "#1e293b"
BG_ACIK      = "#334155"
KENAR        = "#475569"
YAZI_BEYAZ   = "#f1f5f9"
YAZI_GRI     = "#94a3b8"
VURGU_YESIL  = "#22c55e"
VURGU_MAVI   = "#3b82f6"
VURGU_TURUNCU= "#f59e0b"
VURGU_KIRMIZI= "#ef4444"
VURGU_MOR    = "#a855f7"
SIDEBAR_W    = 220

# ─── ORTAK STILLER ───────────────────────────────────────────────────────────

INPUT_STYLE = f"""
    QLineEdit, QComboBox, QDateEdit, QTextEdit {{
        background: {BG_ACIK};
        color: {YAZI_BEYAZ};
        border: 1px solid {KENAR};
        border-radius: 6px;
        padding: 7px 10px;
        font-size: 13px;
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
        border: 1px solid {VURGU_MAVI};
    }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background: {BG_ORTA};
        color: {YAZI_BEYAZ};
        selection-background-color: {VURGU_MAVI};
    }}
"""

TABLO_STYLE = f"""
    QTableWidget {{
        background: {BG_ORTA};
        color: {YAZI_BEYAZ};
        border: none;
        gridline-color: {BG_ACIK};
        font-size: 13px;
        alternate-background-color: {BG_KOYU};
    }}
    QTableWidget::item {{
        padding: 8px;
        color: {YAZI_BEYAZ};
        background: transparent;
    }}
    QTableWidget::item:alternate {{
        background: {BG_KOYU};
        color: {YAZI_BEYAZ};
    }}
    QTableWidget::item:selected {{
        background: {VURGU_MAVI}33;
        color: {YAZI_BEYAZ};
    }}
    QHeaderView::section {{
        background: {BG_KOYU};
        color: {YAZI_GRI};
        border: none;
        padding: 8px;
        font-size: 12px;
        font-weight: bold;
    }}
    QScrollBar:vertical {{
        background: {BG_ACIK};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {KENAR};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
"""

# ─── YARDIMCI WİDGET'LAR ─────────────────────────────────────────────────────

def btn(metin, renk=VURGU_MAVI, ikon=""):
    b = QPushButton(f"  {ikon}  {metin}" if ikon else metin)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {renk};
            color: {'#0f172a' if renk not in [BG_ACIK, BG_ORTA] else YAZI_BEYAZ};
            border: none;
            border-radius: 6px;
            padding: 8px 18px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background: {renk}cc; }}
    """)
    return b

def etiket_badge(metin, renk):
    l = QLabel(metin)
    l.setStyleSheet(f"""
        background: {renk}33;
        color: {renk};
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: bold;
    """)
    l.setFixedHeight(22)
    return l

def bolum_baslik(metin, renk=YAZI_BEYAZ):
    l = QLabel(metin)
    l.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {renk}; padding-bottom: 4px;")
    return l

def golge_ekle(widget, blur=15, y_offset=4, alpha=80):
    from PyQt5.QtWidgets import QGraphicsDropShadowEffect
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(y_offset)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)
    return shadow

# ─── SMOOTH SCROLL AREA ───────────────────────────────────────────────────────

class SmoothScrollArea(QScrollArea):
    """Yumuşak (inertia) kaydırma destekli ScrollArea."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._velocity = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60fps
        self._timer.timeout.connect(self._tick)
        self._friction = 0.82  # Yavaşlama katsayısı

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self._velocity += delta * 0.35
        if not self._timer.isActive():
            self._timer.start()
        event.accept()

    def _tick(self):
        bar = self.verticalScrollBar()
        bar.setValue(int(bar.value() - self._velocity))
        self._velocity *= self._friction
        if abs(self._velocity) < 0.5:
            self._velocity = 0.0
            self._timer.stop()



class ToastBildirim(QFrame):
    def __init__(self, parent, mesaj, tip="basari"):
        super().__init__(parent)
        renk_map = {
            "basari": VURGU_YESIL,
            "hata": VURGU_KIRMIZI,
            "bilgi": VURGU_MAVI,
            "uyari": VURGU_TURUNCU,
        }
        renk = renk_map.get(tip, VURGU_MAVI)
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_ORTA};
                border-left: 4px solid {renk};
                border-radius: 8px;
                border: 1px solid {renk}55;
            }}
        """)
        self.setFixedWidth(300)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(10)

        ikon_map = {"basari": "✓", "hata": "✗", "bilgi": "ℹ", "uyari": "⚠"}
        ikon = QLabel(ikon_map.get(tip, "ℹ"))
        ikon.setStyleSheet(f"color: {renk}; font-size: 16px; font-weight: bold;")
        ikon.setFixedWidth(20)
        lay.addWidget(ikon)

        lbl = QLabel(mesaj)
        lbl.setStyleSheet(f"color: {YAZI_BEYAZ}; font-size: 13px;")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)

        golge_ekle(self, blur=20, y_offset=6, alpha=120)
        self.raise_()

        # Animasyon: sağdan kayarak gelsin
        self._parent = parent
        self._konumlandir()

        self.anim_giris = QPropertyAnimation(self, b"geometry")
        self.anim_giris.setDuration(300)
        self.anim_giris.setEasingCurve(QEasingCurve.OutCubic)
        baslangic = QRect(self._hedef_x() + 320, self._hedef_y(), 300, self.sizeHint().height() + 10)
        bitis = QRect(self._hedef_x(), self._hedef_y(), 300, self.sizeHint().height() + 10)
        self.anim_giris.setStartValue(baslangic)
        self.anim_giris.setEndValue(bitis)
        self.anim_giris.start()

        self.show()
        QTimer.singleShot(3000, self._cikis_animasyonu)

    def _hedef_x(self):
        return self._parent.width() - 320

    def _hedef_y(self):
        return self._parent.height() - 80

    def _konumlandir(self):
        self.setGeometry(self._hedef_x(), self._hedef_y(), 300, 60)

    def _cikis_animasyonu(self):
        self.anim_cikis = QPropertyAnimation(self, b"geometry")
        self.anim_cikis.setDuration(300)
        self.anim_cikis.setEasingCurve(QEasingCurve.InCubic)
        mevcut = self.geometry()
        bitis = QRect(mevcut.x() + 320, mevcut.y(), mevcut.width(), mevcut.height())
        self.anim_cikis.setStartValue(mevcut)
        self.anim_cikis.setEndValue(bitis)
        self.anim_cikis.finished.connect(self.deleteLater)
        self.anim_cikis.start()

# Global toast referansı
_ana_pencere_ref = None

def toast(mesaj, tip="basari"):
    if _ana_pencere_ref:
        ToastBildirim(_ana_pencere_ref, mesaj, tip)

# ─── KOMUT PALETİ (Ctrl+K) ───────────────────────────────────────────────────

class KomutPaleti(QDialog):
    def __init__(self, app_ref, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.Dialog)
        self.app = app_ref
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(560)
        self._kur()

    def _kur(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        cerceve = QFrame()
        cerceve.setStyleSheet(f"""
            QFrame {{
                background: {BG_ORTA};
                border: 1px solid {KENAR};
                border-radius: 12px;
            }}
        """)
        golge_ekle(cerceve, blur=30, y_offset=10, alpha=150)
        c_lay = QVBoxLayout(cerceve)
        c_lay.setContentsMargins(0, 0, 0, 8)
        c_lay.setSpacing(0)

        # Arama kutusu
        ara_frame = QFrame()
        ara_frame.setStyleSheet(f"background: transparent; border-bottom: 1px solid {BG_ACIK};")
        ara_lay = QHBoxLayout(ara_frame)
        ara_lay.setContentsMargins(16, 12, 16, 12)
        ara_ikon = QLabel("⌘")
        ara_ikon.setStyleSheet(f"color: {YAZI_GRI}; font-size: 18px;")
        self.arama = QLineEdit()
        self.arama.setPlaceholderText("Müşteri, fırsat veya görev ara...")
        self.arama.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {YAZI_BEYAZ};
                font-size: 15px;
                padding: 0;
            }}
        """)
        self.arama.textChanged.connect(self._ara)
        ara_lay.addWidget(ara_ikon)
        ara_lay.addWidget(self.arama)
        c_lay.addWidget(ara_frame)

        # Sonuç listesi
        self.sonuc_widget = QWidget()
        self.sonuc_widget.setStyleSheet("background: transparent;")
        self.sonuc_lay = QVBoxLayout(self.sonuc_widget)
        self.sonuc_lay.setContentsMargins(8, 8, 8, 0)
        self.sonuc_lay.setSpacing(2)

        scroll = QScrollArea()
        scroll.setWidget(self.sonuc_widget)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)
        scroll.setStyleSheet("background: transparent; border: none;")
        c_lay.addWidget(scroll)

        # Kısayol ipucu
        ipucu = QLabel("↑↓ Gezin  •  Enter Seç  •  Esc Kapat")
        ipucu.setStyleSheet(f"color: {YAZI_GRI}; font-size: 11px; padding: 6px 16px 4px 16px;")
        c_lay.addWidget(ipucu)

        lay.addWidget(cerceve)
        self._hizli_komutlar()

    def _hizli_komutlar(self):
        komutlar = [
            ("👥  Müşteriler sayfasına git", lambda: self._git(1)),
            ("💼  Fırsatlar sayfasına git", lambda: self._git(2)),
            ("📋  Görevler sayfasına git", lambda: self._git(3)),
            ("🎫  Destek Talepleri sayfasına git", lambda: self._git(4)),
        ]
        self._sonuclari_goster(komutlar)

    def _ara(self, metin):
        while self.sonuc_lay.count():
            item = self.sonuc_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not metin.strip():
            self._hizli_komutlar()
            return

        sonuclar = []
        for m in Musteri.hepsini_getir(metin):
            sonuclar.append((f"👤  {m.ad} — {m.sirket}", lambda idx=1: self._git(idx)))
        for f in Firsat.hepsini_getir():
            if metin.lower() in f.baslik.lower():
                sonuclar.append((f"💼  {f.baslik} ({f.asama})", lambda idx=2: self._git(idx)))
        for g in Gorev.hepsini_getir():
            if metin.lower() in g.baslik.lower():
                sonuclar.append((f"📋  {g.baslik} [{g.durum}]", lambda idx=3: self._git(idx)))

        if not sonuclar:
            bos = QLabel("  Sonuç bulunamadı.")
            bos.setStyleSheet(f"color: {YAZI_GRI}; font-size: 13px; padding: 10px;")
            self.sonuc_lay.addWidget(bos)
        else:
            self._sonuclari_goster(sonuclar[:10])

    def _sonuclari_goster(self, liste):
        while self.sonuc_lay.count():
            item = self.sonuc_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for metin, eylem in liste:
            b = QPushButton(metin)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {YAZI_BEYAZ};
                    border: none;
                    text-align: left;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background: {BG_ACIK}; }}
            """)
            b.clicked.connect(eylem)
            self.sonuc_lay.addWidget(b)
        self.sonuc_lay.addStretch()

    def _git(self, index):
        self.app._sayfa_degis(index)
        self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)

# ─── GÖREV DETAY DİYALOĞU ────────────────────────────────────────────────────

class GorevDetayDialog(QDialog):
    def __init__(self, gorev, parent=None):
        super().__init__(parent)
        self.gorev = gorev
        self.setWindowTitle("Görev Detayı")
        self.setMinimumSize(580, 520)
        self.setStyleSheet(f"background: {BG_ORTA}; color: {YAZI_BEYAZ};")
        self._kur()

    def _kur(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        baslik = QLabel(self.gorev.baslik)
        baslik.setStyleSheet("font-size: 20px; font-weight: bold;")
        lay.addWidget(baslik)

        grid = QGridLayout()
        grid.setSpacing(10)
        metas = [
            ("Atanan", self.gorev.atanan or "—"),
            ("Fırsat", self.gorev.firsat_id),
            ("Son Tarih", self.gorev.son_tarih),
            ("Durum", self.gorev.durum),
        ]
        for i, (k, v) in enumerate(metas):
            kl = QLabel(k)
            kl.setStyleSheet(f"color: {YAZI_GRI}; font-size: 12px;")
            vl = QLabel(v)
            vl.setStyleSheet("font-size: 13px;")
            grid.addWidget(kl, i, 0)
            grid.addWidget(vl, i, 1)
        lay.addLayout(grid)

        acik_lbl = QLabel("Açıklama")
        acik_lbl.setStyleSheet(f"color: {YAZI_GRI}; font-size: 13px; font-weight: bold;")
        lay.addWidget(acik_lbl)
        acik = QLabel(self.gorev.aciklama or "Açıklama girilmemiş.")
        acik.setWordWrap(True)
        acik.setStyleSheet(f"font-size: 13px; color: {YAZI_BEYAZ};")
        lay.addWidget(acik)

        # Dosyalar
        dos_lbl = QLabel("Ekli Dosyalar")
        dos_lbl.setStyleSheet(f"color: {YAZI_GRI}; font-size: 13px; font-weight: bold; margin-top:8px;")
        lay.addWidget(dos_lbl)
        self._dosya_alani = QVBoxLayout()
        dosya_w = QWidget()
        dosya_w.setLayout(self._dosya_alani)
        lay.addWidget(dosya_w)
        self._dosyalari_goster()
        dos_ekle_btn = btn("+ Dosya Ekle", BG_ACIK)
        dos_ekle_btn.clicked.connect(self._dosya_ekle)
        lay.addWidget(dos_ekle_btn)

        yor_lbl = QLabel("Yorumlar")
        yor_lbl.setStyleSheet(f"color: {YAZI_GRI}; font-size: 13px; font-weight: bold; margin-top:8px;")
        lay.addWidget(yor_lbl)

        self.yorum_listesi = QVBoxLayout()
        scroll_w = QWidget()
        scroll_w.setLayout(self.yorum_listesi)
        scroll = QScrollArea()
        scroll.setWidget(scroll_w)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(120)
        scroll.setStyleSheet(f"background: {BG_KOYU}; border: none;")
        lay.addWidget(scroll)
        self._yorumlari_goster()

        yorum_row = QHBoxLayout()
        self.yorum_inp = QLineEdit()
        self.yorum_inp.setPlaceholderText("Yorum ekle...")
        self.yorum_inp.setStyleSheet(INPUT_STYLE)
        yorum_ekle_btn = btn("Gönder", VURGU_YESIL)
        yorum_ekle_btn.clicked.connect(self._yorum_ekle)
        yorum_row.addWidget(self.yorum_inp)
        yorum_row.addWidget(yorum_ekle_btn)
        lay.addLayout(yorum_row)

        kapat = btn("Kapat", BG_ACIK)
        kapat.clicked.connect(self.accept)
        lay.addWidget(kapat, alignment=Qt.AlignRight)

    def _dosyalari_goster(self):
        while self._dosya_alani.count():
            item = self._dosya_alani.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for fid, dosya_adi, dosya_yolu, tarih in dosyalari_getir(self.gorev.gorev_id):
            row = QHBoxLayout()
            lbl = QLabel(f"📎 {dosya_adi}")
            lbl.setStyleSheet(f"color: {VURGU_MAVI}; font-size: 12px;")
            ac_btn = QPushButton("Aç")
            ac_btn.setStyleSheet(f"color:{YAZI_GRI}; background:transparent; border:none; font-size:11px;")
            ac_btn.setCursor(Qt.PointingHandCursor)
            ac_btn.clicked.connect(lambda _, p=dosya_yolu: self._dosya_ac(p))
            row.addWidget(lbl)
            row.addWidget(ac_btn)
            row.addStretch()
            w = QWidget()
            w.setLayout(row)
            self._dosya_alani.addWidget(w)

    def _dosya_ekle(self):
        yol, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
        if yol:
            dosya_ekle(self.gorev.gorev_id, "gorev", yol)
            self._dosyalari_goster()
            toast("Dosya eklendi.", "basari")

    def _dosya_ac(self, yol):
        try:
            if platform.system() == "Windows":
                os.startfile(yol)
            elif platform.system() == "Darwin":
                subprocess.call(["open", yol])
            else:
                subprocess.call(["xdg-open", yol])
        except Exception:
            toast("Dosya açılamadı!", "hata")

    def _yorumlari_goster(self):
        while self.yorum_listesi.count():
            item = self.yorum_listesi.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for y in self.gorev.yorumlar:
            w = QLabel(y)
            w.setWordWrap(True)
            w.setStyleSheet(f"background: {BG_ACIK}; border-radius:6px; padding:6px; color:{YAZI_BEYAZ}; font-size:12px; margin:2px;")
            self.yorum_listesi.addWidget(w)

    def _yorum_ekle(self):
        t = self.yorum_inp.text().strip()
        if t:
            now = datetime.now().strftime("%d %b %H:%M")
            self.gorev.yorumlar.append(f"[{now}] {t}")
            self.gorev.kaydet()
            self.yorum_inp.clear()
            self._yorumlari_goster()

# ─── GÖREV KARTI ─────────────────────────────────────────────────────────────

class GorevKarti(QFrame):
    tiklandi = pyqtSignal(object)

    def __init__(self, gorev):
        super().__init__()
        self.gorev = gorev
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_ORTA};
                border-radius: 8px;
                border: 1px solid {BG_ACIK};
            }}
            QFrame:hover {{
                border: 1px solid {VURGU_MAVI}88;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        baslik = QLabel(gorev.baslik)
        baslik.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {YAZI_BEYAZ};")
        baslik.setWordWrap(True)
        lay.addWidget(baslik)

        firsat_l = QLabel(f"Fırsat: {gorev.firsat_id}")
        firsat_l.setStyleSheet(f"font-size: 11px; color: {YAZI_GRI};")
        lay.addWidget(firsat_l)

        tarih_l = QLabel(f"Son Tarih: {gorev.son_tarih}")
        tarih_l.setStyleSheet(f"font-size: 11px; color: {YAZI_GRI};")
        lay.addWidget(tarih_l)

        alt = QHBoxLayout()
        renk_map = {"Genel": VURGU_MAVI, "Pazarlama": VURGU_MOR, "Satış Odaklı": VURGU_TURUNCU, "Teknik": VURGU_YESIL}
        renk = renk_map.get(gorev.etiket, YAZI_GRI)
        alt.addWidget(etiket_badge(gorev.etiket, renk))
        alt.addStretch()
        if gorev.atanan:
            at = QLabel(gorev.atanan[:2].upper())
            at.setFixedSize(26, 26)
            at.setAlignment(Qt.AlignCenter)
            at.setStyleSheet(f"background:{VURGU_MAVI}; border-radius:13px; color:white; font-size:11px; font-weight:bold;")
            alt.addWidget(at)
        lay.addLayout(alt)
        golge_ekle(self, blur=10, y_offset=3, alpha=60)

    def mousePressEvent(self, e):
        self.tiklandi.emit(self.gorev)

# ─── GÖREV KANBAN SAYFASI ────────────────────────────────────────────────────

class GorevSayfasi(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app = app_ref
        self._secili_gorev = None
        self.setStyleSheet(f"background: {BG_KOYU};")
        self._kur()

    def _kur(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        ust = QHBoxLayout()
        ust.addWidget(bolum_baslik("Görev Yönetimi"))
        ust.addStretch()
        sil_btn = btn("🗑 Seçili Görevi Sil", VURGU_KIRMIZI)
        sil_btn.clicked.connect(self._gorev_sil)
        ust.addWidget(sil_btn)
        ekle_btn = btn("+ Yeni Görev", VURGU_MAVI)
        ekle_btn.clicked.connect(self._gorev_ekle_dialog)
        ust.addWidget(ekle_btn)
        lay.addLayout(ust)

        filtre_row = QHBoxLayout()
        self.filtre_durum = QComboBox()
        self.filtre_durum.addItems(["Tüm Durumlar", "Yapılacak", "Devam Ediyor", "Tamamlandı"])
        self.filtre_durum.setStyleSheet(INPUT_STYLE)
        self.filtre_durum.currentIndexChanged.connect(self.guncelle)
        filtre_row.addWidget(QLabel("Filtre:"))
        filtre_row.addWidget(self.filtre_durum)
        filtre_row.addStretch()
        lay.addLayout(filtre_row)

        kanban = QHBoxLayout()
        kanban.setSpacing(12)
        self.sutunlar = {}
        for durum, renk in [("Yapılacak", VURGU_TURUNCU), ("Devam Ediyor", VURGU_MAVI), ("Tamamlandı", VURGU_YESIL)]:
            col = self._sutun_olustur(durum, renk)
            kanban.addLayout(col["layout"])
            self.sutunlar[durum] = col
        lay.addLayout(kanban)

    def _sutun_olustur(self, baslik, renk):
        col_frame = QFrame()
        col_frame.setStyleSheet(f"background: {BG_ORTA}; border-radius: 10px;")
        golge_ekle(col_frame, blur=12, y_offset=4, alpha=70)
        col_lay = QVBoxLayout(col_frame)
        col_lay.setContentsMargins(10, 10, 10, 10)
        col_lay.setSpacing(8)

        hdr = QHBoxLayout()
        hdr_lbl = QLabel(baslik)
        hdr_lbl.setStyleSheet(f"font-size:14px; font-weight:bold; color:{renk};")
        sayac = QLabel("0")
        sayac.setStyleSheet(f"background:{renk}33; color:{renk}; border-radius:10px; padding:0px 8px; font-size:12px; font-weight:bold;")
        hdr.addWidget(hdr_lbl)
        hdr.addStretch()
        hdr.addWidget(sayac)
        col_lay.addLayout(hdr)

        scroll = SmoothScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            background: transparent; border: none;
            QScrollBar:vertical {{
                background: {BG_ACIK};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {KENAR};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        kart_widget = QWidget()
        kart_widget.setStyleSheet("background: transparent;")
        kart_lay = QVBoxLayout(kart_widget)
        kart_lay.setContentsMargins(0, 0, 0, 0)
        kart_lay.setSpacing(8)
        kart_lay.addStretch()

        scroll.setWidget(kart_widget)
        col_lay.addWidget(scroll)

        outer = QVBoxLayout()
        outer.addWidget(col_frame)

        return {
            "layout": outer,
            "kart_lay": kart_lay,
            "sayac": sayac,
            "renk": renk,
        }

    def guncelle(self):
        filtre = self.filtre_durum.currentText()
        gorevler = Gorev.hepsini_getir()
        for durum, col in self.sutunlar.items():
            kl = col["kart_lay"]
            while kl.count() > 1:
                item = kl.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            sayac = 0
            for g in gorevler:
                if g.durum != durum:
                    continue
                if filtre != "Tüm Durumlar" and g.durum != filtre:
                    continue
                kart = GorevKarti(g)
                kart.tiklandi.connect(self._gorev_detay)
                kl.insertWidget(kl.count() - 1, kart)
                sayac += 1
            col["sayac"].setText(str(sayac))

    def _gorev_detay(self, gorev):
        self._secili_gorev = gorev
        d = GorevDetayDialog(gorev, self)
        d.exec_()

    def _gorev_sil(self):
        if not self._secili_gorev:
            QMessageBox.warning(self, "Hata", "Silmek için önce bir göreve tıklayın!")
            return
        cevap = QMessageBox.question(self, "Onay",
                                     f"'{self._secili_gorev.baslik}' görevi silinsin mi?",
                                     QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            baslik = self._secili_gorev.baslik
            self._secili_gorev.sil()
            self._secili_gorev = None
            self.guncelle()
            toast(f"'{baslik}' görevi silindi.", "uyari")

    def _gorev_ekle_dialog(self):
        d = GorevEkleDialog(self)
        if d.exec_() == QDialog.Accepted:
            self.guncelle()
            toast("Yeni görev oluşturuldu!", "basari")

# ─── GÖREV EKLE DİYALOĞU ─────────────────────────────────────────────────────

class GorevEkleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Görev")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background:{BG_ORTA}; color:{YAZI_BEYAZ};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        lay.addWidget(bolum_baslik("Yeni Görev Ekle"))

        self.baslik = QLineEdit(); self.baslik.setPlaceholderText("Görev Başlığı")
        self.firsat_id = QLineEdit(); self.firsat_id.setPlaceholderText("Fırsat ID")
        self.son_tarih = QLineEdit(); self.son_tarih.setPlaceholderText("Son Tarih (örn: 23 Mayıs 2024)")
        self.atanan = QLineEdit(); self.atanan.setPlaceholderText("Atanan Kişi")
        self.aciklama = QTextEdit(); self.aciklama.setPlaceholderText("Açıklama"); self.aciklama.setFixedHeight(80)

        self.durum = QComboBox()
        self.durum.addItems(["Yapılacak", "Devam Ediyor", "Tamamlandı"])
        self.etiket = QComboBox()
        self.etiket.addItems(["Genel", "Pazarlama", "Satış Odaklı", "Teknik"])

        for w in [self.baslik, self.firsat_id, self.son_tarih, self.atanan, self.aciklama, self.durum, self.etiket]:
            w.setStyleSheet(INPUT_STYLE)
            lay.addWidget(w)

        row = QHBoxLayout()
        iptal = btn("İptal", BG_ACIK)
        iptal.clicked.connect(self.reject)
        kaydet = btn("Kaydet", VURGU_YESIL)
        kaydet.clicked.connect(self._kaydet)
        row.addWidget(iptal); row.addWidget(kaydet)
        lay.addLayout(row)

    def _kaydet(self):
        if not self.baslik.text().strip():
            QMessageBox.warning(self, "Hata", "Görev başlığı zorunludur!")
            return
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM gorevler")
        n = cur.fetchone()[0]
        con.close()
        gid = f"G{n+1:03d}"
        g = Gorev(
            gid, self.baslik.text().strip(),
            self.firsat_id.text().strip() or "—",
            self.son_tarih.text().strip() or "—",
            self.durum.currentText(),
            self.etiket.currentText(),
            self.atanan.text().strip(),
            self.aciklama.toPlainText().strip()
        )
        g.kaydet()
        self.accept()

# ─── MÜŞTERİ SAYFASI ─────────────────────────────────────────────────────────

class MusteriSayfasi(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app = app_ref
        self.setStyleSheet(f"background:{BG_KOYU};")
        self._kur()

    def _kur(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        ust = QHBoxLayout()
        ust.addWidget(bolum_baslik("Müşteri Yönetimi"))
        ust.addStretch()
        lay.addLayout(ust)

        form = QHBoxLayout()
        self.m_id = QLineEdit(); self.m_id.setPlaceholderText("Müşteri ID")
        self.m_ad = QLineEdit(); self.m_ad.setPlaceholderText("Ad Soyad")
        self.m_tel = QLineEdit(); self.m_tel.setPlaceholderText("Telefon")
        self.m_email = QLineEdit(); self.m_email.setPlaceholderText("E-posta")
        self.m_sirket = QLineEdit(); self.m_sirket.setPlaceholderText("Şirket")
        self.m_durum = QComboBox(); self.m_durum.addItems(["Aktif", "Pasif", "Potansiyel"])

        for w in [self.m_id, self.m_ad, self.m_tel, self.m_email, self.m_sirket, self.m_durum]:
            w.setStyleSheet(INPUT_STYLE)
            form.addWidget(w)

        b_ekle = btn("+ Ekle", VURGU_YESIL)
        b_ekle.clicked.connect(self._ekle)
        b_sil = btn("Sil", VURGU_KIRMIZI)
        b_sil.clicked.connect(self._sil)
        b_timeline = btn("Zaman Çizelgesi", BG_ACIK)
        b_timeline.clicked.connect(self._timeline_goster)
        form.addWidget(b_ekle); form.addWidget(b_sil); form.addWidget(b_timeline)
        lay.addLayout(form)

        ara_row = QHBoxLayout()
        self.arama = QLineEdit(); self.arama.setPlaceholderText("🔍  Müşteri ara...")
        self.arama.setStyleSheet(INPUT_STYLE)
        self.arama.textChanged.connect(self.guncelle)
        ara_row.addWidget(self.arama)
        ara_row.addStretch()
        lay.addLayout(ara_row)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(6)
        self.tablo.setHorizontalHeaderLabels(["ID", "Ad Soyad", "Telefon", "E-posta", "Şirket", "Durum"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setStyleSheet(TABLO_STYLE)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.setAlternatingRowColors(True)
        lay.addWidget(self.tablo)
        self.guncelle()

    def guncelle(self):
        arama = self.arama.text() if hasattr(self, 'arama') else ""
        self.tablo.setRowCount(0)
        renk_map = {"Aktif": VURGU_YESIL, "Pasif": YAZI_GRI, "Potansiyel": VURGU_TURUNCU}
        for m in Musteri.hepsini_getir(arama):
            r = self.tablo.rowCount()
            self.tablo.insertRow(r)
            for c, v in enumerate([m.musteri_id, m.ad, m.telefon, m.email, m.sirket, m.durum]):
                item = QTableWidgetItem(v)
                if c == 5:
                    item.setForeground(QColor(renk_map.get(v, YAZI_BEYAZ)))
                self.tablo.setItem(r, c, item)

    def _ekle(self):
        mid = self.m_id.text().strip()
        ad = self.m_ad.text().strip()
        tel = self.m_tel.text().strip()
        if not mid or not ad or not tel:
            QMessageBox.warning(self, "Hata", "ID, Ad ve Telefon zorunludur!")
            return
        m = Musteri(mid, ad, tel, self.m_email.text().strip(), self.m_sirket.text().strip(), self.m_durum.currentText())
        m.kaydet()
        for w in [self.m_id, self.m_ad, self.m_tel, self.m_email, self.m_sirket]:
            w.clear()
        self.guncelle()
        toast(f"{ad} müşterisi eklendi.", "basari")

    def _sil(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Hata", "Silmek için bir müşteri seçin!")
            return
        mid = self.tablo.item(row, 0).text()
        ad = self.tablo.item(row, 1).text()
        m = Musteri(mid, ad, "", "")
        m.sil()
        self.guncelle()
        toast(f"{ad} silindi.", "uyari")

    def _timeline_goster(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Hata", "Zaman çizelgesi için bir müşteri seçin!")
            return
        mid = self.tablo.item(row, 0).text()
        ad = self.tablo.item(row, 1).text()
        d = ZamanCizelgesiDialog(mid, ad, self)
        d.exec_()

# ─── ZAMANLİNE DİYALOĞU ──────────────────────────────────────────────────────

class ZamanCizelgesiDialog(QDialog):
    def __init__(self, musteri_id, musteri_ad, parent=None):
        super().__init__(parent)
        self.musteri_id = musteri_id
        self.setWindowTitle(f"Zaman Çizelgesi — {musteri_ad}")
        self.setMinimumSize(520, 480)
        self.setStyleSheet(f"background:{BG_ORTA}; color:{YAZI_BEYAZ};")
        self._kur(musteri_ad)

    def _kur(self, ad):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        baslik = QLabel(f"📅 {ad} — Aktivite Geçmişi")
        baslik.setStyleSheet("font-size: 17px; font-weight: bold;")
        lay.addWidget(baslik)

        # Yeni aktivite ekle
        ekle_row = QHBoxLayout()
        self.aktivite_inp = QLineEdit()
        self.aktivite_inp.setPlaceholderText("Yeni not / aktivite ekle...")
        self.aktivite_inp.setStyleSheet(INPUT_STYLE)
        ekle_btn = btn("Ekle", VURGU_YESIL)
        ekle_btn.clicked.connect(self._aktivite_ekle)
        ekle_row.addWidget(self.aktivite_inp)
        ekle_row.addWidget(ekle_btn)
        lay.addLayout(ekle_row)

        # Timeline alanı
        scroll_w = QWidget()
        self.timeline_lay = QVBoxLayout(scroll_w)
        self.timeline_lay.setContentsMargins(0, 0, 0, 0)
        self.timeline_lay.setSpacing(2)
        scroll = QScrollArea()
        scroll.setWidget(scroll_w)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background:{BG_KOYU}; border:none;")
        lay.addWidget(scroll)

        kapat = btn("Kapat", BG_ACIK)
        kapat.clicked.connect(self.accept)
        lay.addWidget(kapat, alignment=Qt.AlignRight)

        self._guncelle()

    def _guncelle(self):
        while self.timeline_lay.count():
            item = self.timeline_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        aktiviteler = aktiviteleri_getir(self.musteri_id)
        if not aktiviteler:
            bos = QLabel("  Henüz aktivite yok.")
            bos.setStyleSheet(f"color:{YAZI_GRI}; font-size:13px; padding:20px;")
            self.timeline_lay.addWidget(bos)
        else:
            for tarih, mesaj in aktiviteler:
                entry = QFrame()
                entry.setStyleSheet(f"""
                    QFrame {{
                        background: {BG_ORTA};
                        border-left: 3px solid {VURGU_MAVI};
                        border-radius: 0 6px 6px 0;
                        margin: 3px 0;
                    }}
                """)
                e_lay = QHBoxLayout(entry)
                e_lay.setContentsMargins(12, 8, 12, 8)
                tarih_lbl = QLabel(tarih)
                tarih_lbl.setStyleSheet(f"color:{YAZI_GRI}; font-size:11px; min-width:130px;")
                mesaj_lbl = QLabel(mesaj)
                mesaj_lbl.setStyleSheet(f"color:{YAZI_BEYAZ}; font-size:13px;")
                mesaj_lbl.setWordWrap(True)
                e_lay.addWidget(tarih_lbl)
                e_lay.addWidget(mesaj_lbl, 1)
                self.timeline_lay.addWidget(entry)
        self.timeline_lay.addStretch()

    def _aktivite_ekle(self):
        mesaj = self.aktivite_inp.text().strip()
        if mesaj:
            aktivite_ekle(self.musteri_id, mesaj)
            self.aktivite_inp.clear()
            self._guncelle()

# ─── FIRSAT SAYFASI ──────────────────────────────────────────────────────────

class FirsatSayfasi(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app = app_ref
        self.setStyleSheet(f"background:{BG_KOYU};")
        self._kur()

    def _kur(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        ust = QHBoxLayout()
        ust.addWidget(bolum_baslik("Fırsatlar"))
        ust.addStretch()
        sil_btn = btn("🗑 Sil", VURGU_KIRMIZI)
        sil_btn.clicked.connect(self._firsat_sil)
        ust.addWidget(sil_btn)
        ekle_btn = btn("+ Yeni Fırsat", VURGU_MOR)
        ekle_btn.clicked.connect(self._firsat_ekle_dialog)
        ust.addWidget(ekle_btn)
        lay.addLayout(ust)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(6)
        self.tablo.setHorizontalHeaderLabels(["ID", "Başlık", "Müşteri ID", "Değer (₺)", "Aşama", "Son Tarih"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setStyleSheet(TABLO_STYLE)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.doubleClicked.connect(self._detay_ac)
        lay.addWidget(self.tablo)
        self.guncelle()

    def guncelle(self):
        self.tablo.setRowCount(0)
        asama_renk = {"Prospekt": YAZI_GRI, "Teklif": VURGU_TURUNCU, "Müzakere": VURGU_MAVI, "Kazanıldı": VURGU_YESIL, "Kaybedildi": VURGU_KIRMIZI}
        for f in Firsat.hepsini_getir():
            r = self.tablo.rowCount()
            self.tablo.insertRow(r)
            for c, v in enumerate([f.firsat_id, f.baslik, f.musteri_id, f"₺{f.deger:,.0f}", f.asama, f.son_tarih]):
                item = QTableWidgetItem(str(v))
                if c == 4:
                    item.setForeground(QColor(asama_renk.get(v, YAZI_BEYAZ)))
                self.tablo.setItem(r, c, item)

    def _firsat_sil(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Hata", "Silmek için bir fırsat seçin!")
            return
        fid = self.tablo.item(row, 0).text()
        baslik = self.tablo.item(row, 1).text()
        cevap = QMessageBox.question(self, "Onay", f"'{baslik}' fırsatı silinsin mi?",
                                     QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            f = Firsat(fid, baslik, "", 0)
            f.sil()
            self.guncelle()
            toast(f"'{baslik}' fırsatı silindi.", "uyari")

    def _detay_ac(self):
        row = self.tablo.currentRow()
        if row >= 0:
            firsatlar = Firsat.hepsini_getir()
            f = firsatlar[row]
            d = FirsatDetayDialog(f, self)
            d.exec_()

    def _firsat_ekle_dialog(self):
        d = FirsatEkleDialog(self)
        if d.exec_() == QDialog.Accepted:
            self.guncelle()
            toast("Yeni fırsat oluşturuldu!", "basari")

class FirsatDetayDialog(QDialog):
    def __init__(self, firsat, parent=None):
        super().__init__(parent)
        self.firsat = firsat
        self.setWindowTitle(f"Fırsat Detayı — {firsat.baslik}")
        self.setMinimumSize(480, 420)
        self.setStyleSheet(f"background:{BG_ORTA}; color:{YAZI_BEYAZ};")
        self._kur()

    def _kur(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        baslik = QLabel(self.firsat.baslik)
        baslik.setStyleSheet("font-size: 18px; font-weight: bold;")
        lay.addWidget(baslik)

        grid = QGridLayout()
        grid.setSpacing(8)
        metas = [
            ("Müşteri ID", self.firsat.musteri_id),
            ("Değer", f"₺{self.firsat.deger:,.0f}"),
            ("Aşama", self.firsat.asama),
            ("Son Tarih", self.firsat.son_tarih),
            ("Atanan", self.firsat.atanan or "—"),
        ]
        for i, (k, v) in enumerate(metas):
            kl = QLabel(k)
            kl.setStyleSheet(f"color:{YAZI_GRI}; font-size:12px;")
            vl = QLabel(str(v))
            vl.setStyleSheet("font-size:13px;")
            grid.addWidget(kl, i, 0)
            grid.addWidget(vl, i, 1)
        lay.addLayout(grid)

        acik_lbl = QLabel("Açıklama")
        acik_lbl.setStyleSheet(f"color:{YAZI_GRI}; font-size:13px; font-weight:bold;")
        lay.addWidget(acik_lbl)
        acik = QLabel(self.firsat.aciklama or "Açıklama girilmemiş.")
        acik.setWordWrap(True)
        acik.setStyleSheet(f"color:{YAZI_BEYAZ}; font-size:13px;")
        lay.addWidget(acik)

        # Dosyalar
        dos_lbl = QLabel("Ekli Dosyalar")
        dos_lbl.setStyleSheet(f"color:{YAZI_GRI}; font-size:13px; font-weight:bold; margin-top:8px;")
        lay.addWidget(dos_lbl)
        self._dosya_alani = QVBoxLayout()
        dosya_w = QWidget()
        dosya_w.setLayout(self._dosya_alani)
        lay.addWidget(dosya_w)
        self._dosyalari_goster()
        dos_ekle = btn("+ Dosya Ekle", BG_ACIK)
        dos_ekle.clicked.connect(self._dosya_ekle)
        lay.addWidget(dos_ekle)

        kapat = btn("Kapat", BG_ACIK)
        kapat.clicked.connect(self.accept)
        lay.addWidget(kapat, alignment=Qt.AlignRight)

    def _dosyalari_goster(self):
        while self._dosya_alani.count():
            item = self._dosya_alani.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for fid, dosya_adi, dosya_yolu, tarih in dosyalari_getir(self.firsat.firsat_id):
            row = QHBoxLayout()
            lbl = QLabel(f"📎 {dosya_adi}")
            lbl.setStyleSheet(f"color:{VURGU_MAVI}; font-size:12px;")
            row.addWidget(lbl)
            row.addStretch()
            w = QWidget(); w.setLayout(row)
            self._dosya_alani.addWidget(w)

    def _dosya_ekle(self):
        yol, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
        if yol:
            dosya_ekle(self.firsat.firsat_id, "firsat", yol)
            self._dosyalari_goster()
            toast("Dosya eklendi.", "basari")

class FirsatEkleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Fırsat")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background:{BG_ORTA}; color:{YAZI_BEYAZ};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        lay.addWidget(bolum_baslik("Yeni Fırsat"))

        self.baslik = QLineEdit(); self.baslik.setPlaceholderText("Fırsat Başlığı")
        self.musteri_id = QLineEdit(); self.musteri_id.setPlaceholderText("Müşteri ID")
        self.deger = QLineEdit(); self.deger.setPlaceholderText("Değer (₺)")
        self.son_tarih = QLineEdit(); self.son_tarih.setPlaceholderText("Son Tarih")
        self.atanan = QLineEdit(); self.atanan.setPlaceholderText("Atanan")
        self.aciklama = QTextEdit(); self.aciklama.setPlaceholderText("Açıklama"); self.aciklama.setFixedHeight(70)
        self.asama = QComboBox()
        self.asama.addItems(["Prospekt", "Teklif", "Müzakere", "Kazanıldı", "Kaybedildi"])

        for w in [self.baslik, self.musteri_id, self.deger, self.son_tarih, self.atanan, self.asama, self.aciklama]:
            w.setStyleSheet(INPUT_STYLE)
            lay.addWidget(w)

        row = QHBoxLayout()
        iptal = btn("İptal", BG_ACIK); iptal.clicked.connect(self.reject)
        kaydet = btn("Kaydet", VURGU_MOR); kaydet.clicked.connect(self._kaydet)
        row.addWidget(iptal); row.addWidget(kaydet)
        lay.addLayout(row)

    def _kaydet(self):
        if not self.baslik.text().strip():
            QMessageBox.warning(self, "Hata", "Başlık zorunludur!")
            return
        con = db_baglanti()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM firsatlar")
        n = cur.fetchone()[0]
        con.close()
        fid = f"F{n+1:03d}"
        try:
            deger = float(self.deger.text().strip() or 0)
        except ValueError:
            deger = 0.0
        f = Firsat(fid, self.baslik.text().strip(), self.musteri_id.text().strip(),
                   deger, self.asama.currentText(), self.son_tarih.text().strip(),
                   self.aciklama.toPlainText().strip(), self.atanan.text().strip())
        f.kaydet()
        self.accept()

# ─── DESTEK TALEPLERİ SAYFASI ────────────────────────────────────────────────

class DestekSayfasi(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app = app_ref
        self.setStyleSheet(f"background:{BG_KOYU};")
        self._kur()

    def _kur(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        ust = QHBoxLayout()
        ust.addWidget(bolum_baslik("Destek Talepleri"))
        ust.addStretch()
        lay.addLayout(ust)

        form = QHBoxLayout()
        self.t_id = QLineEdit(); self.t_id.setPlaceholderText("Talep ID")
        self.t_aciklama = QLineEdit(); self.t_aciklama.setPlaceholderText("Açıklama")
        self.t_mid = QLineEdit(); self.t_mid.setPlaceholderText("Müşteri ID")
        self.t_durum = QComboBox(); self.t_durum.addItems(["Açık", "İşlemde", "Kapalı"])
        self.t_oncelik = QComboBox(); self.t_oncelik.addItems(["Normal", "Yüksek", "Kritik"])

        for w in [self.t_id, self.t_aciklama, self.t_mid, self.t_durum, self.t_oncelik]:
            w.setStyleSheet(INPUT_STYLE)
            form.addWidget(w)

        b_ekle = btn("+ Ekle", VURGU_MAVI)
        b_ekle.clicked.connect(self._ekle)
        b_sil = btn("Sil", VURGU_KIRMIZI)
        b_sil.clicked.connect(self._sil)
        form.addWidget(b_ekle); form.addWidget(b_sil)
        lay.addLayout(form)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(5)
        self.tablo.setHorizontalHeaderLabels(["Talep ID", "Açıklama", "Müşteri ID", "Durum", "Öncelik"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setStyleSheet(TABLO_STYLE)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.setAlternatingRowColors(True)
        lay.addWidget(self.tablo)
        self.guncelle()

    def guncelle(self):
        self.tablo.setRowCount(0)
        durum_renk = {"Açık": VURGU_KIRMIZI, "İşlemde": VURGU_TURUNCU, "Kapalı": VURGU_YESIL}
        oncelik_renk = {"Normal": YAZI_GRI, "Yüksek": VURGU_TURUNCU, "Kritik": VURGU_KIRMIZI}
        for t in DestekTalebi.hepsini_getir():
            r = self.tablo.rowCount()
            self.tablo.insertRow(r)
            for c, v in enumerate([t.talep_id, t.aciklama, t.musteri_id, t.durum, t.oncelik]):
                item = QTableWidgetItem(v)
                if c == 3:
                    item.setForeground(QColor(durum_renk.get(v, YAZI_BEYAZ)))
                if c == 4:
                    item.setForeground(QColor(oncelik_renk.get(v, YAZI_BEYAZ)))
                self.tablo.setItem(r, c, item)

    def _ekle(self):
        tid = self.t_id.text().strip()
        acik = self.t_aciklama.text().strip()
        mid = self.t_mid.text().strip()
        if not tid or not acik or not mid:
            QMessageBox.warning(self, "Hata", "ID, Açıklama ve Müşteri ID zorunludur!")
            return
        t = DestekTalebi(tid, acik, mid, self.t_durum.currentText(), self.t_oncelik.currentText())
        t.kaydet()
        for w in [self.t_id, self.t_aciklama, self.t_mid]:
            w.clear()
        self.guncelle()
        toast("Destek talebi oluşturuldu.", "bilgi")

    def _sil(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Hata", "Silmek için bir talep seçin!")
            return
        tid = self.tablo.item(row, 0).text()
        t = DestekTalebi(tid, "", "")
        t.sil()
        self.guncelle()
        toast("Talep silindi.", "uyari")

# ─── DASHBOARD – GRAFİK WİDGET'LARI ─────────────────────────────────────────

class SatisHunisiWidget(QFrame):
    """Satış hunisi (funnel) grafiği."""
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{BG_ORTA}; border-radius:10px;")
        golge_ekle(self, blur=12, y_offset=4, alpha=70)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        baslik = QLabel("📊 Satış Hunisi")
        baslik.setStyleSheet(f"font-size:14px; font-weight:bold; color:{YAZI_BEYAZ};")
        lay.addWidget(baslik)

        if MATPLOTLIB_VAR:
            self.canvas = self._grafik_olustur()
            lay.addWidget(self.canvas)
        else:
            fallback = QLabel("matplotlib kurulu değil.\npip install matplotlib")
            fallback.setStyleSheet(f"color:{YAZI_GRI}; font-size:12px;")
            fallback.setAlignment(Qt.AlignCenter)
            lay.addWidget(fallback)

    def _grafik_olustur(self):
        firsatlar = Firsat.hepsini_getir()
        asama_sayilari = {}
        for asama in ["Prospekt", "Teklif", "Müzakere", "Kazanıldı"]:
            asama_sayilari[asama] = sum(1 for f in firsatlar if f.asama == asama)

        fig = Figure(figsize=(4, 2.8), facecolor=BG_ORTA)
        ax = fig.add_subplot(111, facecolor=BG_ORTA)

        renkler = ["#3d3d3d" if v == "#a0a0a0" else v for v in ["#a0a0a0", "#f39c12", "#3498db", "#2ecc71"]]
        renkler = ["#94a3b8", "#f59e0b", "#3b82f6", "#22c55e"]
        asamalar = list(asama_sayilari.keys())
        degerler = list(asama_sayilari.values())

        bars = ax.barh(asamalar, degerler, color=renkler, height=0.55)
        for bar, val in zip(bars, degerler):
            ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                    str(val), va='center', color=YAZI_BEYAZ, fontsize=11, fontweight='bold')

        ax.set_facecolor(BG_ORTA)
        ax.tick_params(colors=YAZI_GRI, labelsize=10)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xlim(0, max(degerler + [1]) * 1.2)
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        canvas.setStyleSheet(f"background:{BG_ORTA};")
        canvas.setFixedHeight(180)
        return canvas

    def guncelle(self):
        if MATPLOTLIB_VAR and hasattr(self, 'canvas'):
            self.canvas.figure.clear()
            ax = self.canvas.figure.add_subplot(111, facecolor=BG_ORTA)
            firsatlar = Firsat.hepsini_getir()
            asama_sayilari = {}
            for asama in ["Prospekt", "Teklif", "Müzakere", "Kazanıldı"]:
                asama_sayilari[asama] = sum(1 for f in firsatlar if f.asama == asama)
            renkler = ["#94a3b8", "#f59e0b", "#3b82f6", "#22c55e"]
            asamalar = list(asama_sayilari.keys())
            degerler = list(asama_sayilari.values())
            bars = ax.barh(asamalar, degerler, color=renkler, height=0.55)
            for bar, val in zip(bars, degerler):
                ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                        str(val), va='center', color=YAZI_BEYAZ, fontsize=11, fontweight='bold')
            ax.set_facecolor(BG_ORTA)
            ax.tick_params(colors=YAZI_GRI, labelsize=10)
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.set_xlim(0, max(degerler + [1]) * 1.2)
            self.canvas.figure.tight_layout()
            self.canvas.draw()

class DurumPastaWidget(QFrame):
    """Müşteri durum dağılımı pasta grafiği."""
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{BG_ORTA}; border-radius:10px;")
        golge_ekle(self, blur=12, y_offset=4, alpha=70)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        baslik = QLabel("👥 Müşteri Durumu")
        baslik.setStyleSheet(f"font-size:14px; font-weight:bold; color:{YAZI_BEYAZ};")
        lay.addWidget(baslik)

        if MATPLOTLIB_VAR:
            self.canvas = self._grafik_olustur()
            lay.addWidget(self.canvas)
        else:
            fallback = QLabel("matplotlib kurulu değil.")
            fallback.setStyleSheet(f"color:{YAZI_GRI}; font-size:12px;")
            fallback.setAlignment(Qt.AlignCenter)
            lay.addWidget(fallback)

    def _grafik_olustur(self):
        musteriler = Musteri.hepsini_getir()
        durum_sayisi = {"Aktif": 0, "Pasif": 0, "Potansiyel": 0}
        for m in musteriler:
            if m.durum in durum_sayisi:
                durum_sayisi[m.durum] += 1

        fig = Figure(figsize=(3.5, 2.8), facecolor=BG_ORTA)
        ax = fig.add_subplot(111, facecolor=BG_ORTA)

        etiketler = [k for k, v in durum_sayisi.items() if v > 0]
        degerler = [v for v in durum_sayisi.values() if v > 0]
        renkler = {"Aktif": VURGU_YESIL, "Pasif": YAZI_GRI, "Potansiyel": VURGU_TURUNCU}
        pie_renkler = [renkler[e] for e in etiketler]

        if degerler:
            wedges, texts, autotexts = ax.pie(
                degerler, labels=etiketler, colors=pie_renkler,
                autopct='%1.0f%%', startangle=90,
                textprops={'color': YAZI_BEYAZ, 'fontsize': 10}
            )
            for at in autotexts:
                at.set_color(BG_KOYU)
                at.set_fontweight('bold')
        else:
            ax.text(0.5, 0.5, 'Veri yok', ha='center', va='center',
                    color=YAZI_GRI, fontsize=12, transform=ax.transAxes)

        fig.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet(f"background:{BG_ORTA};")
        canvas.setFixedHeight(180)
        return canvas

    def guncelle(self):
        if MATPLOTLIB_VAR and hasattr(self, 'canvas'):
            self.canvas.figure.clear()
            ax = self.canvas.figure.add_subplot(111, facecolor=BG_ORTA)
            musteriler = Musteri.hepsini_getir()
            durum_sayisi = {"Aktif": 0, "Pasif": 0, "Potansiyel": 0}
            for m in musteriler:
                if m.durum in durum_sayisi:
                    durum_sayisi[m.durum] += 1
            etiketler = [k for k, v in durum_sayisi.items() if v > 0]
            degerler = [v for v in durum_sayisi.values() if v > 0]
            renkler = {"Aktif": VURGU_YESIL, "Pasif": YAZI_GRI, "Potansiyel": VURGU_TURUNCU}
            pie_renkler = [renkler[e] for e in etiketler]
            if degerler:
                wedges, texts, autotexts = ax.pie(
                    degerler, labels=etiketler, colors=pie_renkler,
                    autopct='%1.0f%%', startangle=90,
                    textprops={'color': YAZI_BEYAZ, 'fontsize': 10}
                )
                for at in autotexts:
                    at.set_color(BG_KOYU); at.set_fontweight('bold')
            self.canvas.figure.tight_layout()
            self.canvas.draw()

# ─── DASHBOARD SAYFASI ───────────────────────────────────────────────────────

class DashboardSayfasi(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{BG_KOYU};")
        self._kur()

    def _kur(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(20)

        lay.addWidget(bolum_baslik("Dashboard"))

        kart_row = QHBoxLayout()
        kart_row.setSpacing(14)

        def stat_kart(baslik, deger_fn, renk, emoji):
            f = QFrame()
            f.setStyleSheet(f"background:{BG_ORTA}; border-radius:12px; border-left: 5px solid {renk};")
            golge_ekle(f, blur=16, y_offset=5, alpha=80)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(20, 18, 20, 18)
            e = QLabel(emoji)
            e.setStyleSheet("font-size:30px;")
            b = QLabel(baslik)
            b.setStyleSheet(f"color:{YAZI_GRI}; font-size:13px;")
            deger_etiket = QLabel(str(deger_fn()))
            deger_etiket.setStyleSheet(f"font-size:48px; font-weight:bold; color:{renk};")
            fl.addWidget(e); fl.addWidget(b); fl.addWidget(deger_etiket)
            return f, deger_etiket

        self.stat_labels = {}

        configs = [
            ("Toplam Müşteri", Musteri.sayisi, VURGU_MAVI, "👥"),
            ("Toplam Fırsat", Firsat.sayisi, VURGU_MOR, "💼"),
            ("Açık Görevler", Gorev.acik_sayisi, VURGU_TURUNCU, "📋"),
            ("Destek Talepleri", DestekTalebi.sayisi, VURGU_KIRMIZI, "🎫"),
        ]

        for baslik, fn, renk, emoji in configs:
            f, lbl = stat_kart(baslik, fn, renk, emoji)
            self.stat_labels[baslik] = (lbl, fn)
            kart_row.addWidget(f)

        lay.addLayout(kart_row)

        # Grafikler satırı
        grafik_row = QHBoxLayout()
        grafik_row.setSpacing(14)
        self.huni = SatisHunisiWidget()
        self.pasta = DurumPastaWidget()
        grafik_row.addWidget(self.huni, 3)
        grafik_row.addWidget(self.pasta, 2)
        lay.addLayout(grafik_row)

        # Son eklenen müşteriler
        son_lbl = QLabel("Son Müşteriler")
        son_lbl.setStyleSheet(f"font-size:15px; font-weight:bold; color:{YAZI_BEYAZ};")
        lay.addWidget(son_lbl)

        # Kart tabanlı scroll alanı — kalan tüm alanı kaplar
        self.son_scroll = QScrollArea()
        self.son_scroll.setWidgetResizable(True)
        self.son_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.son_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.son_scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {BG_ACIK};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {KENAR};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        self.son_kart_widget = QWidget()
        self.son_kart_widget.setStyleSheet("background: transparent;")
        self.son_kart_lay = QVBoxLayout(self.son_kart_widget)
        self.son_kart_lay.setContentsMargins(0, 4, 8, 4)
        self.son_kart_lay.setSpacing(8)
        self.son_scroll.setWidget(self.son_kart_widget)
        lay.addWidget(self.son_scroll, 1)
        self.guncelle()

    def guncelle(self):
        for baslik, (lbl, fn) in self.stat_labels.items():
            lbl.setText(str(fn()))

        # Son müşteri kartlarını temizle ve yeniden oluştur
        while self.son_kart_lay.count():
            item = self.son_kart_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        renk_map = {"Aktif": VURGU_YESIL, "Pasif": YAZI_GRI, "Potansiyel": VURGU_TURUNCU}
        durum_emoji = {"Aktif": "🟢", "Pasif": "⚫", "Potansiyel": "🟡"}
        musteriler = Musteri.hepsini_getir()
        for m in musteriler[::-1]:
            renk = renk_map.get(m.durum, YAZI_GRI)
            kart = QFrame()
            kart.setStyleSheet(f"""
                QFrame {{
                    background: {BG_ORTA};
                    border-radius: 8px;
                    border-left: 3px solid {renk};
                }}
            """)
            golge_ekle(kart, blur=8, y_offset=2, alpha=50)
            k_lay = QHBoxLayout(kart)
            k_lay.setContentsMargins(16, 12, 16, 12)
            k_lay.setSpacing(12)

            # Avatar
            av = QLabel(m.ad[0].upper() if m.ad else "?")
            av.setFixedSize(36, 36)
            av.setAlignment(Qt.AlignCenter)
            av.setStyleSheet(f"background: {renk}33; border-radius: 18px; color: {renk}; font-weight: bold; font-size: 14px;")
            k_lay.addWidget(av)

            # Ad ve Şirket
            bilgi = QVBoxLayout()
            bilgi.setSpacing(2)
            ad_lbl = QLabel(m.ad)
            ad_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {YAZI_BEYAZ};")
            sirket_lbl = QLabel(m.sirket if m.sirket else "—")
            sirket_lbl.setStyleSheet(f"font-size: 11px; color: {YAZI_GRI};")
            bilgi.addWidget(ad_lbl)
            bilgi.addWidget(sirket_lbl)
            k_lay.addLayout(bilgi, 1)

            # Durum badge
            emoji = durum_emoji.get(m.durum, "")
            durum_lbl = QLabel(f"{emoji} {m.durum}")
            durum_lbl.setStyleSheet(f"""
                background: {renk}22;
                color: {renk};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            """)
            k_lay.addWidget(durum_lbl)

            self.son_kart_lay.addWidget(kart)

        self.son_kart_lay.addStretch()

        if MATPLOTLIB_VAR:
            self.huni.guncelle()
            self.pasta.guncelle()

# ─── GLOBAL ARAMA ÇUBUĞU ─────────────────────────────────────────────────────

class GlobalAramaBar(QWidget):
    def __init__(self, app_ref):
        super().__init__()
        self.app = app_ref
        self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 8, 16, 8)
        lay.setSpacing(8)

        arama_cerceve = QFrame()
        arama_cerceve.setStyleSheet(f"""
            QFrame {{
                background: {BG_ACIK};
                border-radius: 20px;
                border: 1px solid {KENAR};
            }}
        """)
        arama_cerceve.setFixedWidth(280)
        ac_lay = QHBoxLayout(arama_cerceve)
        ac_lay.setContentsMargins(12, 6, 12, 6)

        ikon = QLabel("🔍")
        ikon.setStyleSheet("font-size: 13px;")
        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Ara...  Ctrl+K için komut paleti")
        self.inp.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {YAZI_BEYAZ};
                font-size: 13px;
            }}
        """)
        self.inp.returnPressed.connect(self._ara)
        ac_lay.addWidget(ikon)
        ac_lay.addWidget(self.inp)
        lay.addWidget(arama_cerceve)

    def _ara(self):
        metin = self.inp.text().strip()
        if metin:
            self.app._komut_paleti_ac(metin)
            self.inp.clear()

# ─── ANA UYGULAMA ─────────────────────────────────────────────────────────────

class CRMApp(QMainWindow):
    def __init__(self):
        super().__init__()
        global _ana_pencere_ref
        _ana_pencere_ref = self
        self.setWindowTitle("Nexus CRM v2")
        self.setMinimumSize(1200, 720)
        self.setStyleSheet(f"background-color: {BG_KOYU}; color: {YAZI_BEYAZ};")
        self._arayuz_kur()

    def _arayuz_kur(self):
        merkez = QWidget()
        self.setCentralWidget(merkez)
        ana = QHBoxLayout(merkez)
        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)

        # ── SIDEBAR ──────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(SIDEBAR_W)
        sidebar.setStyleSheet(f"background: {BG_ORTA}; border-right: 1px solid {BG_ACIK};")
        golge_ekle(sidebar, blur=20, y_offset=0, alpha=100)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 16)
        sb.setSpacing(0)

        logo_frame = QFrame()
        logo_frame.setStyleSheet(f"background: {BG_KOYU}; border-bottom: 1px solid {BG_ACIK};")
        logo_lay = QHBoxLayout(logo_frame)
        logo_lay.setContentsMargins(16, 14, 16, 14)
        logo_ic = QLabel("N")
        logo_ic.setFixedSize(32, 32)
        logo_ic.setAlignment(Qt.AlignCenter)
        logo_ic.setStyleSheet(f"background: {VURGU_MAVI}; border-radius: 8px; color: white; font-weight: bold; font-size: 16px;")
        logo_txt = QLabel("Nexus CRM")
        logo_txt.setStyleSheet(f"color: {YAZI_BEYAZ}; font-size: 15px; font-weight: bold; padding-left: 8px;")
        logo_lay.addWidget(logo_ic); logo_lay.addWidget(logo_txt); logo_lay.addStretch()
        sb.addWidget(logo_frame)
        sb.addSpacing(12)

        def bolum_etiket(metin):
            l = QLabel(metin.upper())
            l.setStyleSheet(f"color: {YAZI_GRI}; font-size: 10px; font-weight: bold; padding: 4px 16px 4px 16px; letter-spacing: 1px;")
            sb.addWidget(l)

        def nav_btn(ikon, metin, index):
            b = QPushButton(f"  {ikon}   {metin}")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {YAZI_GRI};
                    border: none;
                    padding: 10px 16px;
                    font-size: 13px;
                    text-align: left;
                    border-radius: 0;
                }}
                QPushButton:hover {{
                    background: {BG_ACIK}55;
                    color: {YAZI_BEYAZ};
                }}
                QPushButton:checked {{
                    background: {VURGU_MAVI}22;
                    color: {VURGU_MAVI};
                    border-left: 3px solid {VURGU_MAVI};
                }}
            """)
            b.clicked.connect(lambda: self._sayfa_degis(index))
            return b

        bolum_etiket("Ana Menü")
        self.nav_btns = []
        nav_items = [
            ("🏠", "Dashboard", 0),
            ("👥", "Müşteriler", 1),
            ("💼", "Fırsatlar", 2),
            ("📋", "Görevler", 3),
        ]
        for ikon, metin, idx in nav_items:
            b = nav_btn(ikon, metin, idx)
            sb.addWidget(b)
            self.nav_btns.append(b)

        sb.addSpacing(12)
        bolum_etiket("Destek")
        destek_btn = nav_btn("🎫", "Destek Talepleri", 4)
        sb.addWidget(destek_btn)
        self.nav_btns.append(destek_btn)
        sb.addStretch()

        alt_frame = QFrame()
        alt_frame.setStyleSheet(f"border-top: 1px solid {BG_ACIK};")
        alt_lay = QHBoxLayout(alt_frame)
        alt_lay.setContentsMargins(12, 10, 12, 10)
        avatar = QLabel("A")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"background: {VURGU_YESIL}; border-radius: 16px; color: white; font-weight: bold;")
        kullanici = QLabel("Admin\nadmin@nexus.com")
        kullanici.setStyleSheet(f"color: {YAZI_GRI}; font-size: 11px; padding-left: 8px;")
        alt_lay.addWidget(avatar); alt_lay.addWidget(kullanici); alt_lay.addStretch()
        sb.addWidget(alt_frame)

        ana.addWidget(sidebar)

        # ── SAĞ ALAN (üst bar + içerik) ──────────────────────────────────────
        sag = QVBoxLayout()
        sag.setContentsMargins(0, 0, 0, 0)
        sag.setSpacing(0)

        # Üst bar (global arama)
        ust_bar = QFrame()
        ust_bar.setFixedHeight(54)
        ust_bar.setStyleSheet(f"background: {BG_ORTA}; border-bottom: 1px solid {BG_ACIK};")
        ust_lay = QHBoxLayout(ust_bar)
        ust_lay.setContentsMargins(16, 0, 0, 0)
        ust_lay.addStretch()
        self.arama_bar = GlobalAramaBar(self)
        ust_lay.addWidget(self.arama_bar)
        sag.addWidget(ust_bar)

        # Sayfa stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {BG_KOYU};")

        self.dashboard = DashboardSayfasi()
        self.musteriler_sayfasi = MusteriSayfasi(self)
        self.firsatlar_sayfasi = FirsatSayfasi(self)
        self.gorevler_sayfasi = GorevSayfasi(self)
        self.destek_sayfasi = DestekSayfasi(self)

        for w in [self.dashboard, self.musteriler_sayfasi, self.firsatlar_sayfasi,
                  self.gorevler_sayfasi, self.destek_sayfasi]:
            self.stack.addWidget(w)

        sag.addWidget(self.stack)
        sag_widget = QWidget()
        sag_widget.setLayout(sag)
        ana.addWidget(sag_widget)

        # Ctrl+K kısayolu
        kisa = QShortcut(QKeySequence("Ctrl+K"), self)
        kisa.activated.connect(lambda: self._komut_paleti_ac())

        self._sayfa_degis(0)

    def _sayfa_degis(self, index):
        self.stack.setCurrentIndex(index)
        for i, b in enumerate(self.nav_btns):
            b.setChecked(i == index)
        pages = [self.dashboard, self.musteriler_sayfasi, self.firsatlar_sayfasi,
                 self.gorevler_sayfasi, self.destek_sayfasi]
        if hasattr(pages[index], 'guncelle'):
            pages[index].guncelle()

    def _komut_paleti_ac(self, on_metin=""):
        d = KomutPaleti(self, self)
        if on_metin:
            d.arama.setText(on_metin)
            d._ara(on_metin)
        # Ekranın ortasında göster
        x = self.x() + (self.width() - d.width()) // 2
        y = self.y() + 100
        d.move(x, y)
        d.exec_()

# ─── BAŞLATMA ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Veritabanını hazırla
    db_olustur()
    json_den_sqlite_goc()

    app = QApplication(sys.argv)

    # Yazı tipi ayarı
    font = QFont()
    for tercih in ["Inter", "Roboto", "Segoe UI", "SF Pro Display", "Helvetica Neue"]:
        font.setFamily(tercih)
        if QFont(tercih).exactMatch() or tercih in ["Segoe UI"]:
            break
    font.setPointSize(10)
    app.setFont(font)

    pencere = CRMApp()
    pencere.show()
    sys.exit(app.exec_())
