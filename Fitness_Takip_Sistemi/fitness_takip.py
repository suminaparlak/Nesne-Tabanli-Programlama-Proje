import sys
import sqlite3
import hashlib
import os
from datetime import datetime, date, timedelta

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QFrame, QMessageBox, QCheckBox,
    QComboBox, QDoubleSpinBox, QScrollArea, QGridLayout, QSizePolicy,
    QDateEdit, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QProgressBar, QFileDialog, QAbstractItemView, QDialog, QHeaderView, QGraphicsDropShadowEffect
)

from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer, QThread, QSize, QPoint
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap, QPainter, QPainterPath

# Dosyanın çalıştığı ana klasörü bulur ve QSS (CSS) formatına uygun hale getirir
ANA_KLASOR = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")

# Resimlerin tam yollarını dinamik olarak oluşturur
LOGO_YOLU = f"{ANA_KLASOR}/logo.png"
YUKARI_YOLU = f"{ANA_KLASOR}/yukari.png"
ASAGI_YOLU = f"{ANA_KLASOR}/asagi.png"

def resmi_yuvarla(resim_yolu, boyut):
    hedef = QPixmap(boyut, boyut)
    hedef.fill(Qt.transparent)
    orjinal = QPixmap(resim_yolu)
    if not orjinal.isNull():
        kucultulmus = orjinal.scaled(boyut, boyut, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        painter = QPainter(hedef)
        painter.setRenderHint(QPainter.Antialiasing)
        yol = QPainterPath()
        yol.addEllipse(0, 0, boyut, boyut)
        painter.setClipPath(yol)
        painter.drawPixmap((boyut - kucultulmus.width()) // 2, (boyut - kucultulmus.height()) // 2, kucultulmus)
        painter.end()
    return hedef

# ==========================================
# 0. ANA İŞ MANTIĞI SINIFLARI
# Hoca gereksinimi: en az 3 ana sınıf, her birinde
# attributes + metodlar açıkça tanımlanmalıdır.
# Bu sınıflar veritabanıyla entegre çalışır ve
# DashboardWidget tarafından doğrudan kullanılır.
# ==========================================

class Sporcu:
    """
    Sisteme kayıtlı bir sporcuyu temsil eder.
    Attributes: sporcu_id, ad, kilo, boy, hedef_kilo
    """

    def __init__(self, sporcu_id: int, ad: str, kilo: float, boy: float, hedef_kilo: float = 0):
        self.sporcu_id   = sporcu_id
        self.ad          = ad
        self.kilo        = kilo        # kg
        self.boy         = boy         # cm
        self.hedef_kilo  = hedef_kilo  # kg

    # ── Metodlar ──────────────────────────────────────────
    def ilerleme_kaydet(self, yeni_kilo: float) -> dict:
        """
        Sporcunun yeni kilosunu veritabanına kaydeder ve
        hedefe olan mesafeyi döndürür.
        Döner: {'eski_kilo': float, 'yeni_kilo': float,
                'fark': float, 'hedefe_kalan': float}
        """
        conn = sqlite3.connect("fitness_data.db")
        conn.execute(
            "UPDATE sporcular SET kilo=? WHERE sporcu_id=?",
            (yeni_kilo, self.sporcu_id)
        )
        conn.commit()
        conn.close()

        fark          = round(yeni_kilo - self.kilo, 1)
        hedefe_kalan  = round(yeni_kilo - self.hedef_kilo, 1)
        eski          = self.kilo
        self.kilo     = yeni_kilo
        return {
            'eski_kilo'    : eski,
            'yeni_kilo'    : yeni_kilo,
            'fark'         : fark,
            'hedefe_kalan' : hedefe_kalan,
        }

    def bmi_hesapla(self) -> float:
        """Boy ve kiloya göre BMI değerini hesaplar."""
        if self.boy <= 0:
            return 0.0
        return round(self.kilo / (self.boy / 100) ** 2, 1)

    @staticmethod
    def veritabanindan_yukle(sporcu_id: int) -> "Sporcu | None":
        """Veritabanından sporcu_id'ye göre Sporcu nesnesi döndürür."""
        conn = sqlite3.connect("fitness_data.db")
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT sporcu_id, ad, kilo, boy, hedef_kilo FROM sporcular WHERE sporcu_id=?",
            (sporcu_id,)
        ).fetchone()
        conn.close()
        if row:
            return Sporcu(
                sporcu_id  = row["sporcu_id"],
                ad         = row["ad"] or "",
                kilo       = row["kilo"] or 0,
                boy        = row["boy"] or 0,
                hedef_kilo = row["hedef_kilo"] or 0,
            )
        return None


class Antrenman:
    """
    Tek bir antrenman seansını temsil eder.
    Attributes: antrenman_id, tur, sure, tarih
    """

    # Egzersiz türüne göre dakika başı ortalama kalori tablosu (Dictionary)
    KALORI_TABLOSU: dict = {
        "Koşu/Kardio"       : 10.0,
        "Ağırlık/Güç"       : 6.0,
        "Bisiklet/Spinning" : 9.0,
        "Yüzme"             : 8.0,
        "Yoga/Esneme"       : 3.5,
        "Diğer"             : 5.0,
    }

    def __init__(self, antrenman_id: int, tur: str, sure: int, tarih: str = ""):
        self.antrenman_id = antrenman_id
        self.tur          = tur    # egzersiz kategorisi
        self.sure         = sure   # dakika cinsinden
        self.tarih        = tarih or datetime.now().strftime("%Y-%m-%d")

    # ── Metodlar ──────────────────────────────────────────
    def kalori_hesapla(self) -> float:
        """
        Antrenman türü ve süresine göre yakılan kaloriyi hesaplar.
        Döner: float  (kcal)
        """
        oran = self.KALORI_TABLOSU.get(self.tur, 5.0)
        return round(oran * self.sure, 1)

    def ozet(self) -> str:
        """Antrenman özetini okunabilir metin olarak döndürür."""
        return (
            f"{self.tarih} | {self.tur} | "
            f"{self.sure} dk | {self.kalori_hesapla()} kcal"
        )

    @staticmethod
    def haftanin_antrenman_sayisi(sporcu_id: int) -> int:
        """Son 7 günde gerçekten loglanan antrenman sayısını döndürür."""
        baslangic = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        conn = sqlite3.connect("fitness_data.db")
        sayi = conn.execute(
            "SELECT COUNT(*) FROM antrenman_loglari "
            "WHERE sporcu_id=? AND tarih >= ?",
            (sporcu_id, baslangic)
        ).fetchone()[0]
        conn.close()
        return sayi


class Takip:
    """
    Sporcunun haftalık aktivite geçmişini takip eder.
    Attributes: sporcu_id, kayitlar (List[dict])
    """

    def __init__(self, sporcu_id: int):
        self.sporcu_id = sporcu_id
        self.kayitlar: list = []   # List veri yapısı (hoca gereksinimi)

    # ── Metodlar ──────────────────────────────────────────
    def haftalik_veri_yukle(self) -> list:
        """
        Son 7 günün tarih ve gerçekten loglanan antrenman sayısını
        veritabanından çekip self.kayitlar listesine yazar.
        Döner: [{'tarih': str, 'adet': int, 'gun': str}, ...]
        """
        GUNLER = {
            0: "Pzt", 1: "Sal", 2: "Çar",
            3: "Per", 4: "Cum", 5: "Cmt", 6: "Paz"
        }
        conn = sqlite3.connect("fitness_data.db")
        self.kayitlar = []
        for gun_geri in range(6, -1, -1):   # 6 gün öncesinden bugüne
            hedef = (datetime.now() - timedelta(days=gun_geri))
            tarih_str = hedef.strftime("%Y-%m-%d")
            adet = conn.execute(
                "SELECT COUNT(*) FROM antrenman_loglari "
                "WHERE sporcu_id=? AND tarih=?",
                (self.sporcu_id, tarih_str)
            ).fetchone()[0]
            self.kayitlar.append({
                "tarih": tarih_str,
                "adet" : adet,
                "gun"  : GUNLER[hedef.weekday()],
            })
        conn.close()
        return self.kayitlar

    def toplam_bu_hafta(self) -> int:
        """Yüklenen kayıtlardaki toplam antrenman sayısını döndürür."""
        return sum(k["adet"] for k in self.kayitlar)

    def en_aktif_gun(self) -> str:
        """Bu haftanın en çok antrenman yapılan gününü döndürür."""
        if not self.kayitlar:
            return "-"
        en_cok = max(self.kayitlar, key=lambda k: k["adet"])
        return en_cok["gun"] if en_cok["adet"] > 0 else "-"

    def kayit_ekle(self, tarih: str, kalori: float) -> None:
        """
        Takip listesine manuel kayıt ekler.
        (List kullanımı — hoca gereksinimi)
        """
        self.kayitlar.append({"tarih": tarih, "kalori": kalori})


# ==========================================
# 0a. SÜRÜKLENEBİLİR SCROLL ALANI
# Mouse ile tutup sürükleme + tekerlek kaydırma destekli,
# ince Apple tarzı scrollbar'lı QScrollArea alt sınıfı.
# ==========================================
class SuruklenebilirScroll(QScrollArea):
    """
    Hareket listesi gibi scroll'lanabilir grid'ler için:
    - Sol tık basılı tutup fare ile sürükleyerek kaydırma
    - Tekerlek ile dikey kaydırma
    - Daima görünür, ince (8px) Apple tarzı dikey scrollbar
    """

    SCROLLBAR_STYLE = f"""
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 4px 2px 4px 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: #C7C7CC;
            border-radius: 4px;
            min-height: 28px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #8E8E93;
        }}
        QScrollBar::handle:vertical:pressed {{
            background: #636366;
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollArea {{
            border: none;
            background: transparent;
        }}
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._surukluyor = False
        self._surukle_baslangic = QPoint()
        self._scrollbar_baslangic = 0
        self.setFrameShape(QScrollArea.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setStyleSheet(self.SCROLLBAR_STYLE)
        self.viewport().setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._surukluyor = True
            self._surukle_baslangic = event.globalPos()
            self._scrollbar_baslangic = self.verticalScrollBar().value()
            self.viewport().setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._surukluyor:
            fark = event.globalPos().y() - self._surukle_baslangic.y()
            self.verticalScrollBar().setValue(self._scrollbar_baslangic - fark)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._surukluyor = False
            self.viewport().setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)


# ==========================================
# 0c. GÜNLÜK MOTİVASYON ALINTILARI
# Her gün farklı bir spor/sağlık alıntısı gösterilir.
# Yıl içindeki gün numarasına göre döngüsel seçim yapılır.
# ==========================================
MOTIVASYON_ALINTILARI = [
    ("Bugün acı çekip çekmeyeceğini seçemezsin; ama bunun seni güçlendirip güçlendirmeyeceğini seçebilirsin.", "Arnold Schwarzenegger"),
    ("Başarı, her gün tekrarlanan küçük çabaların toplamıdır.", "Robert Collier"),
    ("Vücudun her şeyi yapabilir; zihnini ikna etmen gerekiyor.", "Bilinmiyor"),
    ("Antrenman yapmak için motivasyon bekleme. Antrenman yap, motivasyon gelsin.", "Bilinmiyor"),
    ("Ağrı geçicidir. Teslim olmak sonsuzdur.", "Lance Armstrong"),
    ("Sınırlarını ancak onları zorlayarak öğrenirsin.", "Jim Rohn"),
    ("Güçlü olmak bir seçimdir. Her gün yeniden seçilmesi gereken bir seçim.", "Bilinmiyor"),
    ("Vücudun yapabileceklerini hafife alma. Zihnin genellikle ilk pes edendir.", "Bilinmiyor"),
    ("Bugün yapmaktan kaçındığın şey, yarın daha da zor olacak.", "Bilinmiyor"),
    ("Antrenman sonrasında pişman olmak diye bir şey yoktur.", "Bilinmiyor"),
    ("Büyük işler, büyük niyetlerle değil; tutarlı küçük adımlarla yapılır.", "Lao Tzu"),
    ("İstediğin vücuda sahip olmak istiyorsan, önce istemeyi bırak ve yapmaya başla.", "Bilinmiyor"),
    ("Uyku, beslenme ve antrenman — bu üçünden birini ihmal edersen ikisini de boşa harcarsın.", "Bilinmiyor"),
    ("Disiplin, motivasyon olmadığında devreye giren şeydir.", "Bilinmiyor"),
    ("Bugün kendinize yatırım yapın. Yarınki versiyonunuz teşekkür edecek.", "Bilinmiyor"),
    ("En iyi egzersiz, yaptığın egzersizdir.", "Bilinmiyor"),
    ("Bir yıl önce başlamış olmayı dileyeceksin. Bugün başla.", "Karen Lamb"),
    ("Vücut sökülemez, sadece geçici olarak kapatılır.", "Bilinmiyor"),
    ("Spor yapmak için zamanın olmadığını düşünüyorsan, hasta olmak için zaman ayırmak zorunda kalacaksın.", "Edward Stanley"),
    ("Her antrenman bir depozito, her atlanan gün bir çekimdir.", "Bilinmiyor"),
    ("Kendinize inanın ve yarı yolda olduğunuzu anlayacaksınız.", "Theodore Roosevelt"),
    ("İlerleme mükemmellikten iyidir.", "Bilinmiyor"),
    ("Bedenin en büyük düşmanı hareketsizliktir.", "Hippokrates"),
    ("Güç, fiziksel kapasiteden değil; iradeden gelir.", "Mahatma Gandhi"),
    ("Hiç pişman olmadım bir antrenman yaptığım için, ama yapmadığım için çok pişman oldum.", "Bilinmiyor"),
    ("Sağlık bir hedef değil; her gün verilen bir karardır.", "Bilinmiyor"),
    ("Kas acısı geçer, gurur kalır.", "Bilinmiyor"),
    ("Ne kadar zor olduğunu sorma. Yap ve bittiğinde ne kadar güçlü hissettiğini gör.", "Bilinmiyor"),
    ("Vücudunuza iyi bakın; oturmak zorunda olduğunuz tek yerdir.", "Jim Rohn"),
    ("Zirveye çıkmanın kolay yolu yoktur.", "Bilinmiyor"),
    ("Başlamak, yarıyı bitirmektir.", "Aristotle"),
    ("Yarın değil, şimdi.", "Bilinmiyor"),
    ("Antrenman yapmak bir ceza değil, bir ayrıcalıktır.", "Bilinmiyor"),
    ("Kendinizi zorlamadığınız sürece hiçbir şey değişmez.", "Bilinmiyor"),
    ("Küçük ilerlemeler de ilerlemedir.", "Bilinmiyor"),
    ("Sağlıklı olmak bir varış noktası değil, bir yaşam biçimidir.", "Bilinmiyor"),
    ("Vücudunuzu dinleyin ama zihninizdeki bahaneleri susturun.", "Bilinmiyor"),
    ("Her gün biraz daha iyi olmak yeterlidir.", "Bilinmiyor"),
    ("Ter, zayıflığın vücudunuzu terk edişidir.", "Bilinmiyor"),
    ("Güçlü bir beden, güçlü bir zihin inşa eder.", "Bilinmiyor"),
    ("Sonuçları görmeden önce süreci sevmeyi öğren.", "Bilinmiyor"),
    ("Hedefin ne olursa olsun, ilk adım her zaman aynıdır: başlamak.", "Bilinmiyor"),
    ("Vücut değişimi zihin değişimiyle başlar.", "Bilinmiyor"),
    ("Daha iyi hissetmek için beklemene gerek yok; hareket et ve iyi hisset.", "Bilinmiyor"),
    ("İnsan bedeni harekete göre tasarlanmıştır.", "Hippokrates"),
    ("Düzenli egzersiz en güçlü ilaçtır.", "Bilinmiyor"),
    ("Bugünkü terleriniz yarınki güçünüzdür.", "Bilinmiyor"),
    ("Spor bir seçim değil, bir sorumluluktur — kendinize karşı.", "Bilinmiyor"),
    ("Başarı sabah 5'te başlar.", "Bilinmiyor"),
    ("Rahat kalmak ilerlemeyi öldürür.", "Bilinmiyor"),
    ("Sonunda pişman olmayacağın seçimler yap.", "Bilinmiyor"),
    ("Bir günde değil, her gün.", "Bilinmiyor"),
    ("Bedeniniz yapabilir. Sadece zihninizi ikna etmeniz gerekiyor.", "Bilinmiyor"),
    ("Motivasyon sizi başlatır, alışkanlık ise devam ettirir.", "Jim Ryun"),
    ("Güçlü olmak için önce kırılmayı göze almalısın.", "Bilinmiyor"),
    ("Kendinizle rekabet edin, başkalarıyla değil.", "Bilinmiyor"),
    ("Her kilometre sayılır.", "Bilinmiyor"),
    ("Antrenman günleri ne zaman gelir? Her gün.", "Bilinmiyor"),
    ("Hedefinizi unutmayın; acı geçici, başarı kalıcıdır.", "Bilinmiyor"),
    ("İlk adım her zaman en zor olanıdır.", "Bilinmiyor"),
    ("Sizi geriye çeken şeyleri bırakın ve ilerleyin.", "Bilinmiyor"),
    ("Zor olan her şey, bir gün kolay hale gelir.", "Bilinmiyor"),
    ("Bugün yapabileceğini yarına bırakma.", "Benjamin Franklin"),
    ("Spor bedenin şarkısıdır.", "Bilinmiyor"),
    ("Sağlıklı bir yaşam için harekete geçin, bekleyin değil.", "Bilinmiyor"),
]

def gunun_alintisi() -> tuple:
    """Yıl içindeki gün numarasına göre her gün farklı alıntı döndürür."""
    gun_no = datetime.now().timetuple().tm_yday  # 1–365
    idx = (gun_no - 1) % len(MOTIVASYON_ALINTILARI)
    return MOTIVASYON_ALINTILARI[idx]


# ==========================================
# 0b. HAREKET TİPİ HARİTASI
# Her hareket için hangi alanların gösterileceğini belirler:
#   'agirlik'   → Set + Tekrar + Ağırlık (Süre gizli)
#   'vucutagirlik' → Set + Tekrar         (Ağırlık + Süre gizli)
#   'kardiyo'   → Sadece Süre             (Set + Tekrar + Ağırlık gizli)
#   'izometrik' → Set + Süre             (Tekrar + Ağırlık gizli)
# ==========================================
HAREKET_TIPI = {
    # --- Ağırlık/Güç (Set + Tekrar + Ağırlık) ---
    "Bench Press":            "agirlik",
    "İncline Bench Press":    "agirlik",
    "Dumbbell Flye":          "agirlik",
    "Squat":                  "agirlik",
    "Leg Press":              "agirlik", 
    "Leg Extension":          "agirlik",
    "Leg Curl":               "agirlik",
    "Deadlift":               "agirlik",
    "Romanian Deadlift":      "agirlik",
    "Lat Pulldown":           "agirlik",
    "Seated Cable Row":       "agirlik",
    "Barbell Row":            "agirlik",
    "Overhead Press":         "agirlik",
    "Dumbbell Lateral Raise": "agirlik",
    "Face Pull":              "agirlik",
    "Barbell Curl":           "agirlik",
    "Dumbbell Curl":          "agirlik",
    "Hammer Curl":            "agirlik",
    "Triceps Pushdown":       "agirlik",
    "Skull Crusher":          "agirlik",
    "Dips":                   "agirlik",
    "Hip Thrust":             "agirlik",
    "Cable Crunch":           "agirlik",
    "Calf Raise":             "agirlik",
    "Russian Twist":          "agirlik",
    # --- Vücut Ağırlığı (Set + Tekrar, Ağırlık/Süre gizli) ---
    "Pull-Up":                "vucutagirlik",
    "Push-Up":                "vucutagirlik",
    "Crunch":                 "vucutagirlik",
    "Leg Raise":              "vucutagirlik",
    "Lunge":                  "vucutagirlik",
    "Glute Bridge":           "vucutagirlik",
    "Burpee":                 "vucutagirlik",
    "Jumping Jacks":          "vucutagirlik",
    # --- Kardiyo (Sadece Süre) ---
    "Koşu":                   "kardiyo",
    "Yürüyüş":                "kardiyo",
    "Bisiklet":               "kardiyo",
    "Rowing":                 "kardiyo",
    "HIIT":                   "kardiyo",
    "Stretching / Esneme":    "kardiyo",
    # --- İzometrik (Set + Süre) ---
    "Plank":                  "izometrik",
    "Mountain Climber":       "izometrik",
}

def hareket_tipi_al(egzersiz_adi: str) -> str:
    """Egzersiz adına göre form tipini döndürür. Bilinmeyenler 'agirlik' kabul edilir."""
    return HAREKET_TIPI.get(egzersiz_adi, "agirlik")


# ==========================================
# 1. TEMA VE STİL DOSYALARI (APPLE KONSEPTİ)
# ==========================================
COLORS = {
    # --- Yeni Giriş Ekranı ve Apple Tasarımı İçin ---
    'bg_app': '#F2F2F7',          
    'bg_card': '#FFFFFF',         
    'bg_input': '#F0F0F5',        
    'text_main': '#1C1C1E',       
    'text_sub': '#8E8E93',        
    
    # --- Ortak Kullanılan Renkler ---
    'accent': '#F05A5A',          # Logonuzdaki somon/kırmızımsı renk
    'accent_hover': '#D94D4D',    
    'border': '#E5E5EA',          
    'success': '#34C759',         # Apple Yeşili
    'danger': '#FF3B30',          # Apple Kırmızısı
    
    # --- Eski Kodların Çökmemesi İçin (Eski İsimlere Apple Renkleri Atadık) ---
    'bg_primary': '#F2F2F7',      
    'bg_secondary': '#FFFFFF',    
    'bg_tertiary': '#E5E5EA',     
    'text_primary': '#1C1C1E',    
    'text_secondary': '#8E8E93',  
    'accent_secondary': '#FF8A8A',
    'warning': '#FF9F0A',         # Apple Turuncusu
    'info': '#007AFF',            # Apple Mavisi
}

APPLE_THEME = f"""
QMainWindow, QDialog, QWidget {{ 
    background-color: {COLORS['bg_app']}; 
    color: {COLORS['text_main']}; 
    font-family: '-apple-system', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
}}

/* Bembeyaz ve yuvarlak hatlı Apple Kartları */
QFrame#appleCard {{
    background-color: {COLORS['bg_card']};
    border-radius: 24px;
    border: 1px solid rgba(0,0,0,0.04);
}}

/* --- STANDART BUTONLAR --- */
QPushButton {{ 
    background-color: {COLORS['accent']}; 
    color: white; 
    border: none; 
    padding: 12px; 
    border-radius: 18px; 
    font-size: 16px; 
    font-weight: bold; 
}}
QPushButton:hover {{ background-color: {COLORS['accent_hover']}; }}
QPushButton:pressed {{ background-color: #BD3D3D; }}

/* --- ŞEFFAF (YAZI) BUTONLAR --- */
QPushButton#linkBtn {{
    background-color: transparent;
    color: {COLORS['text_main']};
    font-weight: normal;
    font-size: 14px;
}}
QPushButton#linkBtn:hover {{ color: {COLORS['accent']}; }}

/* Standart Inputlar (Giriş ekranı dışındaki yerler için) */
QLineEdit, QTextEdit, QComboBox {{ 
    background-color: {COLORS['bg_input']}; 
    color: {COLORS['text_main']}; 
    border: none; 
    border-radius: 12px; 
    padding: 12px 16px; 
    font-size: 15px; 
}}
QLineEdit:focus {{ border: 2px solid {COLORS['accent']}; padding: 10px 14px; }}
"""

# ==========================================
# 1b. ÖZEL APPLE MESAJ DİYALOĞU
# ==========================================
# QMessageBox yerine kullanılan, temaya tam uyumlu diyalog.
#
# Gerekli görsel dosyaları (ANA_KLASOR içinde olmalı):
#   msg_basari.png  — yeşil onay ikonu   (36×36 px, PNG)
#   msg_uyari.png   — turuncu ünlem ikonu (36×36 px, PNG)
#   msg_hata.png    — kırmızı çarpı ikonu (36×36 px, PNG)
#   msg_soru.png    — mavi soru işareti   (36×36 px, PNG)
#
# ==========================================
# GÖRSEL ZOOM DİYALOĞU
# Egzersiz görsellerine tıklanınca büyütülmüş
# hâlde gösterir. Herhangi bir yere tıklayınca kapanır.
# ==========================================
class GorselZoomDialog(QDialog):
    """Verilen QPixmap'i tam boyutlu olarak gösterir. Tıklanınca kapanır."""

    def __init__(self, pixmap: "QPixmap", baslik: str = "", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self._setup_ui(pixmap, baslik)

    def _setup_ui(self, pixmap, baslik):
        dis_lay = QVBoxLayout(self)
        dis_lay.setContentsMargins(20, 20, 20, 20)

        kart = QFrame()
        kart.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 24px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        golge = QGraphicsDropShadowEffect()
        golge.setBlurRadius(80)
        golge.setColor(QColor(0, 0, 0, 80))
        golge.setOffset(0, 16)
        kart.setGraphicsEffect(golge)

        ic = QVBoxLayout(kart)
        ic.setContentsMargins(20, 20, 20, 20)
        ic.setSpacing(12)

        # Görsel
        gorsel_lbl = QLabel()
        gorsel_lbl.setAlignment(Qt.AlignCenter)
        gorsel_lbl.setStyleSheet("background: transparent; border: none;")
        if not pixmap.isNull():
            buyuk = pixmap.scaled(480, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            gorsel_lbl.setPixmap(buyuk)
        ic.addWidget(gorsel_lbl)

        # Başlık (varsa)
        if baslik:
            baslik_lbl = QLabel(baslik)
            baslik_lbl.setAlignment(Qt.AlignCenter)
            baslik_lbl.setStyleSheet(
                f"font-size: 16px; font-weight: 800; color: {COLORS['text_main']}; "
                f"background: transparent; border: none;"
            )
            ic.addWidget(baslik_lbl)

        # Kapat ipucu
        ipucu = QLabel("Kapatmak için herhangi bir yere tıklayın")
        ipucu.setAlignment(Qt.AlignCenter)
        ipucu.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_sub']}; background: transparent; border: none;"
        )
        ic.addWidget(ipucu)

        dis_lay.addWidget(kart, alignment=Qt.AlignCenter)

    def mousePressEvent(self, event):
        self.accept()

    @staticmethod
    def goster(pixmap, baslik="", parent=None):
        """Pixmap varsa zoom dialogu açar, yoksa hiçbir şey yapmaz."""
        if pixmap and not pixmap.isNull():
            d = GorselZoomDialog(pixmap, baslik, parent)
            d.exec_()


class AppleMesajDialog(QDialog):

    Kabul = 1
    Red   = 0

    def __init__(self, ebeveyn, tur, baslik, mesaj, butonlar=None):
        super().__init__(ebeveyn)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.sonuc = self.Red

        self.tur           = tur       # 'basari' | 'uyari' | 'hata' | 'soru'
        self.baslik_metni  = baslik
        self.mesaj_metni   = mesaj
        # butonlar: liste of (metin, deger, stil)
        # stil: 'primary' | 'danger' | 'success' | 'secondary'
        self.butonlar = butonlar or [('Tamam', self.Kabul, 'primary')]
        self._setup_ui()

    # ── Renk / dosya yardımcıları ───────────────────────────────────────────
    def _renk(self):
        return {
            'basari': COLORS['success'],
            'uyari':  COLORS['warning'],
            'hata':   COLORS['danger'],
            'soru':   COLORS['info'],
        }.get(self.tur, COLORS['accent'])

    def _ikon_yolu(self):
        dosya = {
            'basari': 'msg_basari.png',
            'uyari':  'msg_uyari.png',
            'hata':   'msg_hata.png',
            'soru':   'msg_soru.png',
        }.get(self.tur, 'msg_soru.png')
        return f"{ANA_KLASOR}/{dosya}"

    # ── Arayüz kurulumu ─────────────────────────────────────────────────────
    def _setup_ui(self):
        self.setFixedWidth(420)

        dis_lay = QVBoxLayout(self)
        dis_lay.setContentsMargins(0, 0, 0, 0)

        # Beyaz kart
        kart = QFrame()
        kart.setObjectName("appleMesajKart")
        kart.setStyleSheet(f"""
            QFrame#appleMesajKart {{
                background-color: {COLORS['bg_card']};
                border-radius: 24px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        golge = QGraphicsDropShadowEffect()
        golge.setBlurRadius(70)
        golge.setColor(QColor(0, 0, 0, 45))
        golge.setOffset(0, 14)
        kart.setGraphicsEffect(golge)

        kart_lay = QVBoxLayout(kart)
        kart_lay.setContentsMargins(32, 32, 32, 28)
        kart_lay.setSpacing(0)

        renk = self._renk()

        # ── İkon dairesi ────────────────────────────────────────────────────
        ikon_cerceve = QFrame()
        ikon_cerceve.setFixedSize(68, 68)
        ikon_cerceve.setStyleSheet(f"""
            QFrame {{
                background-color: {renk}1A;
                border-radius: 34px;
                border: 2px solid {renk}44;
            }}
        """)
        ikon_ic = QHBoxLayout(ikon_cerceve)
        ikon_ic.setContentsMargins(0, 0, 0, 0)

        ikon_lbl = QLabel()
        ikon_lbl.setAlignment(Qt.AlignCenter)
        ikon_lbl.setStyleSheet("background: transparent; border: none;")

        yol = self._ikon_yolu()
        if os.path.exists(yol):
            pix = QPixmap(yol)
            if not pix.isNull():
                ikon_lbl.setPixmap(
                    pix.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
        else:
            # Görsel yoksa yedek sembol
            sembol = {'basari': '✓', 'uyari': '!', 'hata': '✕', 'soru': '?'}
            ikon_lbl.setText(sembol.get(self.tur, 'i'))
            ikon_lbl.setStyleSheet(
                f"background: transparent; border: none; "
                f"color: {renk}; font-size: 26px; font-weight: 900;"
            )

        ikon_ic.addWidget(ikon_lbl)
        kart_lay.addWidget(ikon_cerceve, alignment=Qt.AlignLeft)
        kart_lay.addSpacing(22)

        # ── Başlık ──────────────────────────────────────────────────────────
        baslik_lbl = QLabel(self.baslik_metni)
        baslik_lbl.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {COLORS['text_main']}; "
            f"background: transparent; border: none; letter-spacing: -0.3px;"
        )
        kart_lay.addWidget(baslik_lbl)
        kart_lay.addSpacing(8)

        # ── Mesaj ───────────────────────────────────────────────────────────
        mesaj_lbl = QLabel(self.mesaj_metni)
        mesaj_lbl.setWordWrap(True)
        mesaj_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 400; color: {COLORS['text_sub']}; "
            f"background: transparent; border: none;"
        )
        kart_lay.addWidget(mesaj_lbl)
        kart_lay.addSpacing(28)

        # ── Buton satırı ────────────────────────────────────────────────────
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(10)

        stiller = {
            'primary': f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: white; border: none; border-radius: 14px;
                    font-size: 14px; font-weight: 700; padding: 12px 22px;
                }}
                QPushButton:hover {{ background-color: {COLORS['accent_hover']}; }}
            """,
            'danger': f"""
                QPushButton {{
                    background-color: {COLORS['danger']};
                    color: white; border: none; border-radius: 14px;
                    font-size: 14px; font-weight: 700; padding: 12px 22px;
                }}
                QPushButton:hover {{ background-color: #D92020; }}
            """,
            'success': f"""
                QPushButton {{
                    background-color: {COLORS['success']};
                    color: white; border: none; border-radius: 14px;
                    font-size: 14px; font-weight: 700; padding: 12px 22px;
                }}
                QPushButton:hover {{ background-color: #28A845; }}
            """,
            'secondary': f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['text_main']}; border: none; border-radius: 14px;
                    font-size: 14px; font-weight: 600; padding: 12px 22px;
                }}
                QPushButton:hover {{ background-color: {COLORS['bg_tertiary']}; }}
            """,
        }

        for (metin, deger, stil) in self.butonlar:
            b = QPushButton(metin)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(stiller.get(stil, stiller['primary']))
            b.clicked.connect(lambda _, d=deger: self._kapat(d))
            btn_lay.addWidget(b)

        kart_lay.addLayout(btn_lay)
        dis_lay.addWidget(kart)

    def _kapat(self, deger):
        self.sonuc = deger
        self.accept()

    # ── Statik kısayol metodları (eski QMessageBox çağrılarının yerine) ────

    @staticmethod
    def bilgi(ebeveyn, baslik, mesaj):
        """QMessageBox.information() yerine kullan."""
        AppleMesajDialog(
            ebeveyn, 'basari', baslik, mesaj,
            [('Tamam', AppleMesajDialog.Kabul, 'primary')]
        ).exec_()

    @staticmethod
    def uyari(ebeveyn, baslik, mesaj):
        """QMessageBox.warning() yerine kullan."""
        AppleMesajDialog(
            ebeveyn, 'uyari', baslik, mesaj,
            [('Tamam', AppleMesajDialog.Kabul, 'primary')]
        ).exec_()

    @staticmethod
    def hata(ebeveyn, baslik, mesaj):
        """QMessageBox.critical() yerine kullan."""
        AppleMesajDialog(
            ebeveyn, 'hata', baslik, mesaj,
            [('Tamam', AppleMesajDialog.Kabul, 'primary')]
        ).exec_()

    @staticmethod
    def soru(ebeveyn, baslik, mesaj):
        """QMessageBox.question() yerine kullan — True döner Evet'e basılınca."""
        d = AppleMesajDialog(
            ebeveyn, 'soru', baslik, mesaj, [
                ('Vazgeç', AppleMesajDialog.Red,   'secondary'),
                ('Evet',   AppleMesajDialog.Kabul, 'primary'),
            ]
        )
        d.exec_()
        return d.sonuc == AppleMesajDialog.Kabul

    @staticmethod
    def kaydedilmemis_degisiklikler(ebeveyn):
        """
        3 seçenekli 'Kaydedilmemiş Değişiklikler' diyaloğu.
        Döner: 'kaydet' | 'iptal' | 'geri'
        """
        d = AppleMesajDialog(
            ebeveyn, 'uyari',
            "Kaydedilmemiş Değişiklikler",
            "Profilde kaydedilmemiş değişiklikler var. Ne yapmak istersiniz?",
            [
                ('Geri Dön',          'geri',   'secondary'),
                ('Vazgeç', 'iptal',  'danger'),
                (' Kaydet ve Geç ',     'kaydet', 'primary'),
            ]
        )
        d.exec_()
        return d.sonuc


# ==========================================
# 2. VERİTABANI YÖNETİMİ (database.py)
# ==========================================
class db:
    DB_PATH = "fitness_data.db"

    @staticmethod
    def get_connection():
        conn = sqlite3.connect(db.DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @staticmethod
    def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

    @staticmethod
    def initialize_db():
        conn = db.get_connection(); c = conn.cursor()
        
        c.execute("""CREATE TABLE IF NOT EXISTS kullanicilar (kullanici_id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, sifre_hash TEXT, rol TEXT DEFAULT 'sporcu', olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS sporcular (sporcu_id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici_id INTEGER UNIQUE, ad TEXT, soyad TEXT, kilo REAL, boy REAL, dogum_tarihi TEXT, cinsiyet TEXT, hedef_kilo REAL, avatar TEXT DEFAULT '👤', setup_tamamlandi INTEGER DEFAULT 0, FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS antrenman_programi (id INTEGER PRIMARY KEY AUTOINCREMENT, sporcu_id INTEGER, antrenor_id INTEGER, tarih TEXT, program_detay TEXT, FOREIGN KEY (sporcu_id) REFERENCES sporcular(sporcu_id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS antrenor_basvurulari (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici_id INTEGER, tc_no TEXT, deneyim_yili INTEGER, bolum TEXT, durum TEXT DEFAULT 'beklemede', FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS sporcu_antrenor (sporcu_id INTEGER PRIMARY KEY, antrenor_id INTEGER, FOREIGN KEY (sporcu_id) REFERENCES sporcular(sporcu_id), FOREIGN KEY (antrenor_id) REFERENCES kullanicilar(kullanici_id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS sistem_loglari (id INTEGER PRIMARY KEY AUTOINCREMENT, islem TEXT, detay TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("CREATE TABLE IF NOT EXISTS egzersizler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, kategori TEXT, aciklama TEXT, kalori_dakika REAL, zorluk TEXT, kas_grubu TEXT, met_katsayi REAL)")
        c.execute("""CREATE TABLE IF NOT EXISTS antrenman_loglari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sporcu_id INTEGER,
            tarih TEXT,
            egzersiz_id INTEGER,
            egzersiz_ad TEXT,
            set_sayisi INTEGER,
            tekrar_sayisi INTEGER,
            agirlik_kg REAL,
            sure_dakika INTEGER,
            kalori REAL,
            notlar TEXT,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("CREATE TABLE IF NOT EXISTS rozet_tanimlari (rozet_id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, aciklama TEXT, ikon TEXT, kosul_turu TEXT, kosul_deger INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS kazanilan_rozetler (id INTEGER PRIMARY KEY AUTOINCREMENT, sporcu_id INTEGER, rozet_id INTEGER, kazanma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        
        db._seed_egzersizler(c)
        db._seed_rozetler(c)
        
        # ---> ADMIN HESABINI OTOMATİK OLUŞTURMA ÇÖZÜMÜ <---
        c.execute("SELECT COUNT(*) FROM kullanicilar WHERE email='admin@sistem.com'")
        if c.fetchone()[0] == 0:
            sifre_hash = db.hash_password("admin123")
            c.execute("INSERT INTO kullanicilar (email, sifre_hash, rol) VALUES (?,?,?)", ("admin@sistem.com", sifre_hash, "admin"))
            admin_id = c.lastrowid
            c.execute("INSERT INTO sporcular (kullanici_id, ad, soyad, setup_tamamlandi) VALUES (?,?,?,?)", (admin_id, "Sistem", "Yöneticisi", 1))
        
        conn.commit(); conn.close()

    @staticmethod
    def _seed_egzersizler(c):
        c.execute("SELECT COUNT(*) FROM egzersizler")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO egzersizler (ad, kategori, aciklama, kalori_dakika, zorluk, kas_grubu, met_katsayi) VALUES (?,?,?,?,?,?,?)",
                          [
                            ("Bench Press", "Ağırlık/Güç", "Düz banka üzerinde barbell veya dumbbell ile göğüs bölgesini çalıştırır. Sırt yerde, barı göğse indirip itin.", 6.0, "Orta", "Göğüs, Triceps, Ön Omuz", 5.0),
                            ("İncline Bench Press", "Ağırlık/Güç", "30-45° eğimli bankta yapılan bench press. Üst göğsü ve ön omuzu vurgular.", 6.5, "Orta", "Üst Göğüs, Ön Omuz, Triceps", 5.0),
                            ("Dumbbell Flye", "Ağırlık/Güç", "Bankta yatarak kolları yanlara açıp kapatarak göğsü izole çalıştırır.", 5.5, "Orta", "Göğüs, Ön Omuz", 4.5),
                            ("Squat", "Ağırlık/Güç", "Omuzda barbell ile dizleri 90° büküp kalkarken bacak ve kalça kaslarını çalıştırır. Sırt düz kalmalı.", 7.0, "Orta", "Quadriceps, Hamstring, Kalça, Core", 6.0),
                            ("Leg Press", "Ağırlık/Güç", "Makinede ayaklarla plakayı iterek bacakları çalıştırır. Dizlere dikkat et.", 5.5, "Kolay", "Quadriceps, Hamstring, Kalça", 4.5),
                            ("Leg Extension", "Ağırlık/Güç", "Makinede ayak bileklerini uzatarak ön bacak kasını izole çalıştırır.", 4.5, "Kolay", "Quadriceps", 3.5),
                            ("Leg Curl", "Ağırlık/Güç", "Makinede ayak bileklerini bükerek arka bacak kasını izole çalıştırır.", 4.5, "Kolay", "Hamstring", 3.5),
                            ("Deadlift", "Ağırlık/Güç", "Yerden barbell kaldırarak sırt, kalça ve bacak kaslarını birlikte çalıştırır. Form çok önemli.", 8.0, "Zor", "Sırt, Kalça, Hamstring, Core", 6.0),
                            ("Romanian Deadlift", "Ağırlık/Güç", "Dizler hafif bükük, kalça geriye çekilerek arka bacak ve alt sırtı çalıştırır.", 6.5, "Orta", "Hamstring, Kalça, Alt Sırt", 5.5),
                            ("Pull-Up", "Ağırlık/Güç", "Bardan vücut ağırlığıyla çeneyi yukarı çekerek sırt ve biceps çalıştırır.", 8.0, "Zor", "Sırt, Biceps, Core", 8.0),
                            ("Lat Pulldown", "Ağırlık/Güç", "Makinede barı göğse çekerek sırt kaslarını çalıştırır.", 6.0, "Orta", "Latissimus, Biceps, Arka Omuz", 5.0),
                            ("Seated Cable Row", "Ağırlık/Güç", "Kablo makinede oturarak tutacağı karına çekerek orta sırtı çalıştırır.", 5.5, "Orta", "Orta Sırt, Biceps, Arka Omuz", 4.5),
                            ("Barbell Row", "Ağırlık/Güç", "Öne eğilerek barbell'ı karına çekerek sırt kaslarını çalıştırır.", 7.0, "Orta", "Sırt, Biceps, Core", 5.5),
                            ("Overhead Press", "Ağırlık/Güç", "Omuzda barbell'ı kafanın üstüne iterek omuz kaslarını çalıştırır.", 6.0, "Orta", "Omuz, Triceps, Core", 5.0),
                            ("Dumbbell Lateral Raise", "Ağırlık/Güç", "Kolları yanlara kaldırarak orta omuz kasını izole çalıştırır.", 4.5, "Kolay", "Orta Omuz", 3.5),
                            ("Face Pull", "Ağırlık/Güç", "Kablo makinede ip tutacağını yüze doğru çekerek arka omuz ve rotator cuff'ı çalıştırır.", 4.5, "Kolay", "Arka Omuz, Üst Sırt", 3.5),
                            ("Barbell Curl", "Ağırlık/Güç", "Barbell ile dirsekler sabit tutularak biceps çalıştırılır.", 4.5, "Kolay", "Biceps", 3.5),
                            ("Dumbbell Curl", "Ağırlık/Güç", "Dumbbell ile tek tek ya da çift kollu biceps egzersizi.", 4.5, "Kolay", "Biceps", 3.5),
                            ("Hammer Curl", "Ağırlık/Güç", "Nötr tutuşla dumbbell curl. Biceps ve brachialis kasını çalıştırır.", 4.5, "Kolay", "Biceps, Brachialis", 3.5),
                            ("Triceps Pushdown", "Ağırlık/Güç", "Kablo makinede barı aşağıya iterek triceps kasını izole çalıştırır.", 4.5, "Kolay", "Triceps", 3.5),
                            ("Skull Crusher", "Ağırlık/Güç", "Bankta yatarak barbell'ı alna doğru indirip kaldırarak triceps çalıştırır.", 5.0, "Orta", "Triceps", 4.0),
                            ("Dips", "Ağırlık/Güç", "Paralel barlarda vücudu aşağı-yukarı iterek göğüs ve triceps çalıştırır.", 7.0, "Orta", "Triceps, Göğüs, Ön Omuz", 7.0),
                            ("Plank", "Core/Karın", "Ön kollar yerde, vücudu düz tutarak core kaslarını izometrik çalıştırır.", 3.5, "Kolay", "Core, Karın, Sırt", 3.5),
                            ("Crunch", "Core/Karın", "Sırtüstü yatarak üst gövdeyi kaldırarak karın kaslarını çalıştırır.", 4.0, "Kolay", "Karın", 3.5),
                            ("Leg Raise", "Core/Karın", "Sırtüstü yatarak bacakları kaldırıp indirerek alt karın kasını çalıştırır.", 4.5, "Orta", "Alt Karın, Core", 4.0),
                            ("Russian Twist", "Core/Karın", "Oturarak gövdeyi sağa-sola çevirerek oblique kaslarını çalıştırır.", 5.0, "Orta", "Oblique, Core", 4.5),
                            ("Koşu", "Kardiyo", "Sabit tempoda koşu. Tüm vücudu çalıştıran temel kardiyo egzersizi.", 10.0, "Orta", "Tüm Vücut", 8.0),
                            ("Yürüyüş", "Kardiyo", "Hafif tempolu yürüyüş. Başlangıç seviyesi için ideal kardiyo.", 4.0, "Kolay", "Bacak, Core", 3.5),
                            ("HIIT", "Kardiyo", "Yüksek yoğunluklu interval antrenman. Kısa sürede maksimum kalori yakar.", 14.0, "Zor", "Tüm Vücut", 12.0),
                            ("Jumping Jacks", "Kardiyo", "Ayakları açıp kapatarak kolları yukarı kaldırma hareketi. Isınma için idealdir.", 8.0, "Kolay", "Tüm Vücut", 7.0),
                            ("Burpee", "Kardiyo", "Squat, push-up ve zıplama kombinasyonu. Çok yorucu ama etkili.", 12.0, "Zor", "Tüm Vücut", 10.0),
                            ("Bisiklet", "Kardiyo", "Sabit bisiklette pedal çevirme. Eklem dostu kardiyo.", 7.0, "Kolay", "Bacak, Core", 6.0),
                            ("Rowing", "Kardiyo", "Kürek makinesi. Hem kardiyo hem de sırt ve kolları çalıştırır.", 9.0, "Orta", "Sırt, Kol, Core", 7.0),
                            ("Push-Up", "Vücut Ağırlığı", "Yere paralel pozisyonda kolları büküp açarak göğüs ve triceps çalıştırır.", 6.0, "Kolay", "Göğüs, Triceps, Ön Omuz", 5.0),
                            ("Lunge", "Vücut Ağırlığı", "Öne adım atarak diz yere yaklaşana dek inerek quadriceps ve kalça çalıştırır.", 6.0, "Kolay", "Quadriceps, Kalça, Hamstring", 5.0),
                            ("Glute Bridge", "Vücut Ağırlığı", "Sırtüstü yatarak kalçayı yukarı iterek kalça ve hamstring çalıştırır.", 4.0, "Kolay", "Kalça, Hamstring, Core", 3.5),
                            ("Mountain Climber", "Vücut Ağırlığı", "Şınav pozisyonundan diz karna çekerek kardiyo ve core antrenmanı.", 10.0, "Orta", "Core, Omuz, Bacak", 8.0),
                            ("Hip Thrust", "Ağırlık/Güç", "Banka dayalı pozisyonda kalçayı yukarı iterek kalça kaslarını çalıştırır.", 6.0, "Orta", "Kalça, Hamstring", 5.0),
                            ("Cable Crunch", "Core/Karın", "Kablo makinede diz çökerek gövdeyi aşağı çekerek karın kaslarını çalıştırır.", 5.0, "Orta", "Karın, Core", 4.0),
                            ("Calf Raise", "Ağırlık/Güç", "Ayak parmaklarında yükselerek baldır kasını çalıştırır.", 4.0, "Kolay", "Baldır", 3.0),
                            ("Stretching / Esneme", "Esneklik", "Antrenman sonrası kasları uzatarak esnekliği artırır ve yaralanma riskini azaltır.", 2.5, "Kolay", "Tüm Vücut", 2.5),
                          ])

    @staticmethod
    def _seed_rozetler(c):
        c.execute("SELECT COUNT(*) FROM rozet_tanimlari")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO rozet_tanimlari (ad, aciklama, ikon, kosul_turu, kosul_deger) VALUES (?,?,?,?,?)",
                          [("İlk Adım", "İlk antrenmanını tamamladın!", "🏃", "antrenman_sayisi", 1),
                           ("Haftalık Kahraman", "7 gün üst üste antrenman yaptın!", "🔥", "streak_gun", 7),
                           ("Kalori Yakıcı", "Tek seansta 500+ kalori yaktın!", "🔥", "tek_kalori", 500)])

    @staticmethod
    def egzersizleri_getir(kategori=None):
        conn = db.get_connection()
        if kategori:
            rows = conn.execute("SELECT * FROM egzersizler WHERE kategori=? ORDER BY ad", (kategori,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM egzersizler ORDER BY kategori, ad").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def egzersiz_kategorileri():
        conn = db.get_connection()
        rows = conn.execute("SELECT DISTINCT kategori FROM egzersizler ORDER BY kategori").fetchall()
        conn.close()
        return [r[0] for r in rows]

    @staticmethod
    def antrenman_logu_ekle(sporcu_id, tarih, egzersiz_id, egzersiz_ad, set_sayisi, tekrar_sayisi, agirlik_kg, sure_dakika, kalori, notlar=""):
        conn = db.get_connection()
        conn.execute("""INSERT INTO antrenman_loglari
            (sporcu_id, tarih, egzersiz_id, egzersiz_ad, set_sayisi, tekrar_sayisi, agirlik_kg, sure_dakika, kalori, notlar)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (sporcu_id, tarih, egzersiz_id, egzersiz_ad, set_sayisi, tekrar_sayisi, agirlik_kg, sure_dakika, round(kalori, 1), notlar))
        conn.commit(); conn.close()

    @staticmethod
    def antrenman_loglari_getir(sporcu_id, tarih=None):
        conn = db.get_connection()
        if tarih:
            rows = conn.execute("SELECT * FROM antrenman_loglari WHERE sporcu_id=? AND tarih=? ORDER BY olusturma_tarihi DESC", (sporcu_id, tarih)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM antrenman_loglari WHERE sporcu_id=? ORDER BY tarih DESC, olusturma_tarihi DESC", (sporcu_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def antrenman_logu_sil(log_id):
        conn = db.get_connection()
        conn.execute("DELETE FROM antrenman_loglari WHERE id=?", (log_id,))
        conn.commit(); conn.close()

    @staticmethod
    def toplam_kalori_getir(sporcu_id):
        conn = db.get_connection()
        row = conn.execute("SELECT COALESCE(SUM(kalori), 0) as toplam FROM antrenman_loglari WHERE sporcu_id=?", (sporcu_id,)).fetchone()
        conn.close()
        return row[0] if row else 0

    @staticmethod
    def log_ekle(islem, detay):
        conn = db.get_connection()
        conn.execute("INSERT INTO sistem_loglari (islem, detay) VALUES (?,?)", (islem, detay))
        conn.commit(); conn.close()

    @staticmethod
    def loglari_getir():
        conn = db.get_connection(); rows = conn.execute("SELECT * FROM sistem_loglari ORDER BY tarih DESC LIMIT 100").fetchall()
        conn.close(); return [dict(r) for r in rows]

    @staticmethod
    def onayli_antrenorleri_getir():
        conn = db.get_connection()
        # Sorguya s.avatar eklendi
        rows = conn.execute("""
            SELECT k.kullanici_id, s.ad, s.soyad, s.avatar, b.bolum, b.deneyim_yili 
            FROM kullanicilar k 
            JOIN sporcular s ON k.kullanici_id = s.kullanici_id 
            JOIN antrenor_basvurulari b ON k.kullanici_id = b.kullanici_id 
            WHERE k.rol='antrenor'
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def antrenor_sec(sporcu_id, antrenor_id):
        conn = db.get_connection(); conn.execute("INSERT OR REPLACE INTO sporcu_antrenor (sporcu_id, antrenor_id) VALUES (?,?)", (sporcu_id, antrenor_id))
        conn.commit(); conn.close()

    @staticmethod
    def mevcut_antrenor_id(sporcu_id):
        conn = db.get_connection(); row = conn.execute("SELECT antrenor_id FROM sporcu_antrenor WHERE sporcu_id=?", (sporcu_id,)).fetchone()
        conn.close(); return row[0] if row else None

    @staticmethod
    def kullanici_kayit(email, sifre, ad="", soyad="", kilo=0, boy=0):
        conn = None # Başlangıçta boş tanımlıyoruz ki hata verirse kapatabilelim
        try:
            conn = db.get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO kullanicilar (email, sifre_hash) VALUES (?,?)", (email, db.hash_password(sifre)))
            yeni_id = c.lastrowid 
            c.execute("INSERT INTO sporcular (kullanici_id, ad, soyad, kilo, boy) VALUES (?,?,?,?,?)", (yeni_id, ad, soyad, kilo, boy))
            
            c.execute("INSERT INTO sistem_loglari (islem, detay) VALUES (?,?)", ("Yeni Kayıt", f"{email} adresli kullanıcı sisteme katıldı."))
            
            conn.commit()
            return True, "Kayıt başarılı!"
            
        except Exception as e:
            print(f"Sistem Hatası: {e}")
            return False, "E-posta kullanımda veya kayıt başarısız."
            
        finally:
            # ÇÖZÜM: Hata olsa da olmasa da açık kalan bağlantıyı zorla kapatır, kilitlenmeyi engeller.
            if conn:
                conn.close()

    @staticmethod
    def kullanici_giris(email, sifre):
        conn = db.get_connection()
        # s.setup_tamamlandi sütunu da sorguya eklendi
        row = conn.execute("SELECT k.*, s.sporcu_id, s.setup_tamamlandi FROM kullanicilar k LEFT JOIN sporcular s ON k.kullanici_id = s.kullanici_id WHERE k.email=? AND k.sifre_hash=?", (email, db.hash_password(sifre))).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def sporcu_guncelle(sid, ad, soyad, kilo, boy, dt="", cns="", hk=0, avatar="👤"):
        conn = db.get_connection()
        conn.execute("UPDATE sporcular SET ad=?, soyad=?, kilo=?, boy=?, dogum_tarihi=?, cinsiyet=?, hedef_kilo=?, avatar=? WHERE sporcu_id=?", (ad, soyad, kilo, boy, dt, cns, hk, avatar, sid))
        conn.commit(); conn.close()

    def sporcu_getir(sid):
        conn = db.get_connection(); row = conn.execute("SELECT * FROM sporcular WHERE sporcu_id=?", (sid,)).fetchone()
        conn.close(); return dict(row) if row else None

    @staticmethod
    def antrenman_istatistik(sid):
        conn = db.get_connection()
        toplam = conn.execute("SELECT COUNT(*) FROM antrenman_loglari WHERE sporcu_id=?", (sid,)).fetchone()[0]
        bugun = datetime.now().strftime("%Y-%m-%d")
        hafta_bas = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        bu_hafta = conn.execute("SELECT COUNT(*) FROM antrenman_loglari WHERE sporcu_id=? AND tarih >= ?", (sid, hafta_bas)).fetchone()[0]
        conn.close()
        return {'toplam': toplam, 'bu_hafta': bu_hafta, 'bu_ay': 0, 'toplam_sure': 0}

    @staticmethod
    def kalori_istatistik(sid):
        toplam = db.toplam_kalori_getir(sid)
        return {'toplam_kalori': toplam}
    @staticmethod
    def rozetler_getir(sid): 
        conn = db.get_connection()
        rows = conn.execute("SELECT r.*, kr.kazanma_tarihi FROM rozet_tanimlari r LEFT JOIN kazanilan_rozetler kr ON r.rozet_id = kr.rozet_id AND kr.sporcu_id=? ORDER BY kr.kazanma_tarihi DESC NULLS LAST", (sid,)).fetchall()
        conn.close(); return [dict(r) for r in rows]
    @staticmethod
    def streak_hesapla(sid):
        """
        Sporcunun bugünden geriye doğru kaç gün üst üste
        antrenman_loglari tablosuna kayıt girdiğini döndürür.
        Bugün log yoksa dün kontrol eder (gün henüz bitmemiş olabilir).
        """
        conn = db.get_connection()
        # Distinct günleri azalan sırayla al
        rows = conn.execute(
            "SELECT DISTINCT tarih FROM antrenman_loglari "
            "WHERE sporcu_id=? ORDER BY tarih DESC",
            (sid,)
        ).fetchall()
        conn.close()

        if not rows:
            return 0

        gunler = [r['tarih'] for r in rows]
        bugun  = datetime.now().date()
        dun    = bugun - timedelta(days=1)

        # Başlangıç noktasını belirle: bugün log varsa bugünden, yoksa dünden başla
        ilk = datetime.strptime(gunler[0], "%Y-%m-%d").date()
        if ilk == bugun:
            beklenen = bugun
        elif ilk == dun:
            beklenen = dun
        else:
            return 0  # En son log ikiden daha eski → seri kırılmış

        streak = 0
        for tarih_str in gunler:
            gun = datetime.strptime(tarih_str, "%Y-%m-%d").date()
            if gun == beklenen:
                streak += 1
                beklenen -= timedelta(days=1)
            elif gun < beklenen:
                break  # Boşluk var, seri bitti

        return streak
    @staticmethod
    def antrenmanlar_getir(sporcu_id, tur_filtre=None, baslangic=None, bitis=None): return []
    @staticmethod
    def antrenman_sil(antrenman_id): pass

    @staticmethod
    def ogrencileri_getir(antrenor_id):
        conn = db.get_connection()
        # --- ADMİNE PROGRAM YAZMAYI ENGELLEYEN FİLTRE ---
        # "AND k.rol='sporcu'" komutu sayesinde listeye sadece gerçek sporcular düşer, adminler engellenir.
        rows = conn.execute("SELECT s.*, k.email FROM sporcular s JOIN kullanicilar k ON s.kullanici_id = k.kullanici_id JOIN sporcu_antrenor sa ON s.sporcu_id = sa.sporcu_id WHERE sa.antrenor_id=? AND k.rol='sporcu'", (antrenor_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def takvim_program_ekle(sid, aid, tarih, detay):
        conn = db.get_connection()
        # Eski programın üzerine yazma (UPDATE) mantığı kaldırıldı.
        # Artık aynı güne yazılan her program yeni bir kayıt olarak ekleniyor.
        conn.execute("INSERT INTO antrenman_programi (sporcu_id, antrenor_id, tarih, program_detay) VALUES (?,?,?,?)", (sid, aid, tarih, detay))
        conn.commit()
        conn.close() 
        
        # Kilit açıldıktan sonra log ekleniyor
        db.log_ekle("Program Yazma", f"Antrenör (ID:{aid}), Sporcu (ID:{sid}) için {tarih} tarihine program yazdı.")

    @staticmethod
    def takvim_programlari_getir(sid, yil_ay):
        conn = db.get_connection()
        rows = conn.execute("SELECT tarih, program_detay FROM antrenman_programi WHERE sporcu_id=? AND tarih LIKE ?", (sid, f"{yil_ay}%")).fetchall()
        conn.close()
        
        # Programları birleştirmiyoruz, aynı güne ait olanları bir liste (dizi) içine atıyoruz
        programlar = {}
        for r in rows:
            tarih = r['tarih']
            if tarih not in programlar:
                programlar[tarih] = []
            programlar[tarih].append(r['program_detay'])
            
        return programlar

    @staticmethod
    def program_guncelle(program_id, yeni_detay):
        conn = db.get_connection()
        conn.execute("UPDATE antrenman_programi SET program_detay=? WHERE id=?", (yeni_detay, program_id))
        conn.commit()
        conn.close()

    @staticmethod
    def program_sil(program_id):
        conn = db.get_connection()
        conn.execute("DELETE FROM antrenman_programi WHERE id=?", (program_id))
        conn.commit()
        conn.close()

class CustomInput(QFrame):
    """İçinde sol tarafta ikon, sağ tarafta yazı alanı olan özel Apple tarzı Input"""
    def __init__(self, ikon_yolu, placeholder, is_password=False, regex=None):
        super().__init__()
        self.setStyleSheet("QFrame { background-color: #E5E5EA; border-radius: 14px; border: none; }")
        self.setFixedHeight(50) 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(12)
        
        self.ikon_lbl = QLabel()
        pixmap = QPixmap(ikon_yolu)
        if not pixmap.isNull():
            self.ikon_lbl.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.ikon_lbl.setText("[]") 
        self.ikon_lbl.setStyleSheet("background: transparent; border: none;")
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setStyleSheet(f"background: transparent; border: none; color: #1C1C1E; font-size: 15px;")
        if is_password:
            self.line_edit.setEchoMode(QLineEdit.Password)
            
        # ---> ÇÖZÜM BURADA: Kuralın silinmemesi için 'self._validator' kullanıldı 
        # ve self.line_edit ebeveyn olarak atandı <---
        if regex:
            from PyQt5.QtGui import QRegExpValidator
            from PyQt5.QtCore import QRegExp
            self._validator = QRegExpValidator(QRegExp(regex), self.line_edit)
            self.line_edit.setValidator(self._validator)
            
        layout.addWidget(self.ikon_lbl)
        layout.addWidget(self.line_edit)

    def text(self): return self.line_edit.text()
    def returnPressed(self): return self.line_edit.returnPressed

class LoginWidget(QWidget):
    giris_basarili = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("loginAnaSayfa")
        self.setStyleSheet("QWidget#loginAnaSayfa { background-color: #FFFFFF; }")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(25)

        # --- ÜST KISIM: LOGO VE BAŞLIK ---
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_layout.setSpacing(8)
        
        logo_label = QLabel()
        pixmap = QPixmap(LOGO_YOLU) 
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        
        title = QLabel("FitTrack Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: 900; color: #4A4A4A; font-family: 'Segoe UI', sans-serif; background: transparent;")
        
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(title)
        main_layout.addLayout(logo_layout)

        # --- KART ALANI ---
        card = QFrame()
        card.setFixedWidth(390)
        # 2. HEDEF: Kartı beyaz arka plandan nazikçe ayıracak gri tonu
        card.setStyleSheet("QFrame { background-color: #d2d2d6; border-radius: 24px; }")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 15)) 
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 30, 35, 35) 
        card_layout.setSpacing(18)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.stack.addWidget(self._giris_sayfasi())
        self.stack.addWidget(self._kayit_sayfasi())
        card_layout.addWidget(self.stack)
        
        main_layout.addWidget(card, alignment=Qt.AlignCenter)
        
        demo_bilgi = QLabel("👑 Demo Admin: admin@sistem.com | Şifre: admin123")
        demo_bilgi.setAlignment(Qt.AlignCenter)
        demo_bilgi.setStyleSheet("color: #8E8E93; font-size: 13px; margin-top: 15px; background: transparent;")
        main_layout.addWidget(demo_bilgi)

    def _giris_sayfasi(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18) 
        
        header_lay = QHBoxLayout()
        giris_lbl = QLabel("Giriş Yap")
        giris_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #2C2C2E; background: transparent;")
        
        roket_lbl = QLabel()
        roket_pix = QPixmap(f"{ANA_KLASOR}/roket_ikon.png")
        if not roket_pix.isNull():
            roket_lbl.setPixmap(roket_pix.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        roket_lbl.setStyleSheet("background: transparent;")
            
        header_lay.addWidget(giris_lbl)
        header_lay.addStretch()
        header_lay.addWidget(roket_lbl)
        
        cizgi = QFrame(); cizgi.setFrameShape(QFrame.HLine)
        cizgi.setStyleSheet("background-color: #E5E5EA; max-height: 1px; margin-bottom: 5px; margin-top: -5px;")
        
        layout.addLayout(header_lay)
        layout.addWidget(cizgi)

        # E-posta kuralı: Sadece harf, rakam, nokta, alt çizgi, @ ve tire işaretine izin verir. / ve boşluk yasaktır.
        email_kurali = r"^[a-zA-Z0-9_.@\-]+$"
        self.giris_email = CustomInput(f"{ANA_KLASOR}/mail_ikon.png", "E-Posta Adresi", regex=email_kurali)

        def giris_email_kucult(txt):
            if any(c.isupper() for c in txt):
                pos = self.giris_email.line_edit.cursorPosition()
                self.giris_email.line_edit.setText(txt.lower())
                self.giris_email.line_edit.setCursorPosition(pos)
        self.giris_email.line_edit.textChanged.connect(giris_email_kucult)

        self.giris_sifre = CustomInput(f"{ANA_KLASOR}/kilit_ikon.png", "Şifre", is_password=True)
        self.giris_email.returnPressed().connect(self._giris_yap)
        self.giris_sifre.returnPressed().connect(self._giris_yap)
        
        giris_btn = QPushButton("🚀 Giriş Yap")
        giris_btn.setFixedHeight(50)
        giris_btn.setCursor(Qt.PointingHandCursor)
        giris_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {COLORS['accent']}; color: white; border: none; border-radius: 25px; font-size: 16px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {COLORS['accent_hover']}; }}
        """)
        giris_btn.clicked.connect(self._giris_yap)
        
        self.giris_hata = QLabel("")
        self.giris_hata.setStyleSheet(f"color: {COLORS['danger']}; font-size: 13px; font-weight: 500; background: transparent;")
        self.giris_hata.setAlignment(Qt.AlignCenter)
        self.giris_hata.hide() 
        
        # 3. HEDEF: Kırpılma/Kayma sorununu çözen yeni alt link yapısı (Buton yerine tıklanabilir QLabel)
        kayit_link = QLabel("<span style='color:#4A4A4A;'>Üye Değil misiniz? </span><span style='color:#F05A5A; font-weight:bold;'>Kayıt Ol.</span>")
        kayit_link.setAlignment(Qt.AlignCenter)
        kayit_link.setCursor(Qt.PointingHandCursor)
        kayit_link.setStyleSheet("font-size: 14px; background: transparent;")
        kayit_link.mousePressEvent = lambda e: self._sekme_degistir(1)
        
        layout.addWidget(self.giris_email)
        layout.addWidget(self.giris_sifre)
        layout.addSpacing(5)
        layout.addWidget(self.giris_hata)
        layout.addWidget(giris_btn)
        layout.addWidget(kayit_link)
        
        return w

    def _kayit_sayfasi(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        header_lay = QHBoxLayout()
        kayit_lbl = QLabel("Kayıt Ol")
        kayit_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #2C2C2E; background: transparent;")
        header_lay.addWidget(kayit_lbl); header_lay.addStretch()
        
        cizgi = QFrame(); cizgi.setFrameShape(QFrame.HLine)
        cizgi.setStyleSheet("background-color: #E5E5EA; max-height: 1px; margin-bottom: 5px; margin-top: -5px;")
        
        layout.addLayout(header_lay)
        layout.addWidget(cizgi)
        
        # Ad/Soyad kuralı: Sadece büyük/küçük harfler (Türkçe dahil) ve boşluğa izin verir. Sayı ve sembol yasak!
        ad_kurali = r"^[a-zA-ZğüşıöçĞÜŞİÖÇ ]+$"
        email_kurali = r"^[a-zA-Z0-9_.@\-]+$"
        
        self.kayit_ad = CustomInput(f"{ANA_KLASOR}/profil_ikon.png", "Ad", regex=ad_kurali)
        self.kayit_soyad = CustomInput(f"{ANA_KLASOR}/profil_ikon.png", "Soyad", regex=ad_kurali)
        self.kayit_email = CustomInput(f"{ANA_KLASOR}/mail_ikon.png", "E-Posta Adresi", regex=email_kurali)

        def kayit_email_kucult(txt):
            if any(c.isupper() for c in txt):
                pos = self.kayit_email.line_edit.cursorPosition()
                self.kayit_email.line_edit.setText(txt.lower())
                self.kayit_email.line_edit.setCursorPosition(pos)
        self.kayit_email.line_edit.textChanged.connect(kayit_email_kucult)

        self.kayit_sifre = CustomInput(f"{ANA_KLASOR}/kilit_ikon.png", "Şifre", is_password=True)
        
        kayit_btn = QPushButton("Hesap Oluştur")
        kayit_btn.setFixedHeight(50)
        kayit_btn.setCursor(Qt.PointingHandCursor)
        kayit_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {COLORS['accent']}; color: white; border: none; border-radius: 25px; font-size: 16px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {COLORS['accent_hover']}; }}
        """)
        kayit_btn.clicked.connect(self._kayit_ol)
        
        self.kayit_mesaj = QLabel("")
        self.kayit_mesaj.setStyleSheet("background: transparent; font-size: 13px; font-weight: 500;")
        self.kayit_mesaj.setAlignment(Qt.AlignCenter)
        self.kayit_mesaj.hide()
        
        # Kırpılmayı önleyen yeni tıklanabilir metin yapısı
        geri_link = QLabel("<span style='color:#4A4A4A;'>Zaten üye misiniz? </span><span style='color:#F05A5A; font-weight:bold;'>Giriş Yap.</span>")
        geri_link.setAlignment(Qt.AlignCenter)
        geri_link.setCursor(Qt.PointingHandCursor)
        geri_link.setStyleSheet("font-size: 14px; background: transparent;")
        geri_link.mousePressEvent = lambda e: self._sekme_degistir(0)
        
        layout.addWidget(self.kayit_ad)
        layout.addWidget(self.kayit_soyad)
        layout.addWidget(self.kayit_email)
        layout.addWidget(self.kayit_sifre)
        layout.addSpacing(5)
        layout.addWidget(self.kayit_mesaj)
        layout.addWidget(kayit_btn)
        layout.addWidget(geri_link)
        
        return w

    def _sekme_degistir(self, index):
        self.giris_hata.hide()
        self.kayit_mesaj.hide()
        self.stack.setCurrentIndex(index)

    def _kayit_ol(self):
        ad = self.kayit_ad.text().strip()
        soyad = self.kayit_soyad.text().strip()
        email = self.kayit_email.text().strip()
        sifre = self.kayit_sifre.text().strip()

        if not ad or not soyad or not email or not sifre:
            self.kayit_mesaj.setText("Lütfen tüm alanları doldurun.")
            self.kayit_mesaj.setStyleSheet(f"color: {COLORS['danger']}; background: transparent;")
            self.kayit_mesaj.show()
            return
        
        basarili, mesaj = db.kullanici_kayit(email, sifre, ad, soyad)
        if basarili:
            self.kayit_mesaj.setText(mesaj)
            self.kayit_mesaj.setStyleSheet(f"color: {COLORS['success']}; background: transparent;")
            self.kayit_mesaj.show()
            QTimer.singleShot(1500, lambda: self._sekme_degistir(0))
        else:
            self.kayit_mesaj.setText(mesaj)
            self.kayit_mesaj.setStyleSheet(f"color: {COLORS['danger']}; background: transparent;")
            self.kayit_mesaj.show()

    def _giris_yap(self):
        kullanici = db.kullanici_giris(self.giris_email.text().strip(), self.giris_sifre.text().strip())
        if kullanici:
            self.giris_basarili.emit(kullanici)
        else:
            self.giris_hata.setText("E-Posta veya şifre hatalı.")
            self.giris_hata.show()


# ==========================================
# 4. DASHBOARD EKRANI (APPLE HEALTH KONSEPTİ)
# ==========================================
class StatCard(QFrame):
    def __init__(self, ikon_yolu, baslik, deger, renk_hex):
        super().__init__()
        # 1. HEDEF: Apple Health Tarzı Bembeyaz ve Yuvarlak Kart
        self.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_card']}; border-radius: 24px; }}")
        self.setFixedHeight(150)
        
        # Yumuşak Gölge Efekti (Kartın havada durmasını sağlar)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 10)) # %4 saydamlıkta siyah gölge
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        # Üst Kısım: İkon ve Başlık
        top_lay = QHBoxLayout()
        top_lay.setSpacing(10)
        
        self.ikon_lbl = QLabel()
        pix = QPixmap(ikon_yolu)
        if not pix.isNull():
            self.ikon_lbl.setPixmap(pix.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.ikon_lbl.setText("[]")
        self.ikon_lbl.setStyleSheet("background: transparent;")
        
        baslik_lbl = QLabel(baslik)
        # Apple tarzı soluk gri ve kalın başlık
        baslik_lbl.setStyleSheet(f"color: {COLORS['text_sub']}; font-size: 15px; font-weight: 700; background: transparent;")
        
        top_lay.addWidget(self.ikon_lbl)
        top_lay.addWidget(baslik_lbl)
        top_lay.addStretch()
        
        layout.addLayout(top_lay)
        layout.addSpacing(10)
        
        # Alt Kısım: Büyük Değer
        self.deger_label = QLabel(str(deger))
        self.deger_label.setStyleSheet(f"color: {renk_hex}; font-size: 34px; font-weight: 900; font-family: 'Segoe UI', sans-serif; background: transparent;")
        layout.addWidget(self.deger_label)
        layout.addStretch()

    def guncelle(self, deger):
        self.deger_label.setText(str(deger))

class RozetMiniCard(QFrame):
    def __init__(self, rozet):
        super().__init__()
        self.setFixedSize(100, 110)
        kazanildi = rozet.get('kazanma_tarihi') is not None
        
        # Kazanılmışsa beyaz kart, kazanılmamışsa gri kart
        bg_color = COLORS['bg_card'] if kazanildi else COLORS['bg_input']
        border_color = COLORS['accent'] if kazanildi else "rgba(0,0,0,0.05)"
        text_color = COLORS['text_main'] if kazanildi else COLORS['text_sub']
        
        self.setStyleSheet(f"QFrame {{ background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 18px; }}")
        
        if kazanildi:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15); shadow.setColor(QColor(0,0,0,10)); shadow.setOffset(0,4)
            self.setGraphicsEffect(shadow)
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Veritabanında emoji kayıtlı olduğu için şimdilik emojileri mecburen koruyoruz
        ikon_lbl = QLabel(rozet['ikon']) 
        ikon_lbl.setAlignment(Qt.AlignCenter)
        ikon_lbl.setStyleSheet(f"font-size: 34px; background: transparent; {'opacity: 1;' if kazanildi else 'color: gray; opacity: 0.3;'}")
        
        ad_lbl = QLabel(rozet['ad'])
        ad_lbl.setAlignment(Qt.AlignCenter)
        ad_lbl.setWordWrap(True)
        ad_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {text_color}; background: transparent; border: none;")
        
        layout.addWidget(ikon_lbl)
        layout.addWidget(ad_lbl)

class DashboardWidget(QWidget):
    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici
        self.sporcu_id = kullanici['sporcu_id']
        self._setup_ui()
        self._yukle()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(25)
        
        # --- ÜST BAŞLIK BÖLÜMÜ ---
        header = QHBoxLayout()
        sporcu = db.sporcu_getir(self.sporcu_id) or {}
        ad_bilgisi = sporcu.get('ad', 'Kullanıcı')
        
        hosgeldin_lay = QVBoxLayout()
        _TURKCE_AYLAR_TAM = {1:"Ocak",2:"Şubat",3:"Mart",4:"Nisan",5:"Mayıs",
                             6:"Haziran",7:"Temmuz",8:"Ağustos",9:"Eylül",
                             10:"Ekim",11:"Kasım",12:"Aralık"}
        _TURKCE_GUNLER = {0:"Pazartesi",1:"Salı",2:"Çarşamba",3:"Perşembe",
                          4:"Cuma",5:"Cumartesi",6:"Pazar"}
        _simdi = datetime.now()
        _tarih_str = f"{_simdi.day} {_TURKCE_AYLAR_TAM[_simdi.month]} {_TURKCE_GUNLER[_simdi.weekday()]}".upper()
        tarih_lbl = QLabel(_tarih_str)
        tarih_lbl.setStyleSheet(f"color: {COLORS['text_sub']}; font-size: 13px; font-weight: 700;")
        self.hosgeldin = QLabel(f"Özet")
        self.hosgeldin.setStyleSheet(f"color: {COLORS['text_main']}; font-size: 32px; font-weight: 900;")
        
        hosgeldin_lay.addWidget(tarih_lbl)
        hosgeldin_lay.addWidget(self.hosgeldin)
        
        # Bildirim butonu (sağ üst)
        self.bildirim_btn = QPushButton()
        self.bildirim_btn.setFixedSize(44, 44)
        self.bildirim_btn.setCursor(Qt.PointingHandCursor)
        _zil_yolu = f"{ANA_KLASOR}/bildirim_ikon.png"
        if os.path.exists(_zil_yolu):
            self.bildirim_btn.setIcon(QIcon(_zil_yolu))
            self.bildirim_btn.setIconSize(QSize(22, 22))
        else:
            self.bildirim_btn.setText("🔔")
            self.bildirim_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_card']};
                    border: 1.5px solid {COLORS['border']};
                    border-radius: 22px;
                    font-size: 18px;
                    color: {COLORS['text_main']};
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_tertiary']};
                    border-color: {COLORS['accent']};
                }}
            """)
        if os.path.exists(_zil_yolu):
            self.bildirim_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_card']};
                    border: 1.5px solid {COLORS['border']};
                    border-radius: 22px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_tertiary']};
                    border-color: {COLORS['accent']};
                }}
            """)
        self.bildirim_btn.clicked.connect(self._bildirim_paneli_ac)

        # Bildirim noktası (okunmamış varsa gösterilecek kırmızı nokta)
        self._bildirim_nokta = QLabel()
        self._bildirim_nokta.setFixedSize(10, 10)
        self._bildirim_nokta.setStyleSheet(f"""
            background-color: {COLORS['danger']};
            border-radius: 5px;
            border: 2px solid {COLORS['bg_app']};
        """)
        self._bildirim_nokta.setVisible(False)

        # Buton + nokta için container
        _zil_container = QWidget(); _zil_container.setFixedSize(48, 48)
        _zil_container.setStyleSheet("background:transparent;")
        _zil_lay = QVBoxLayout(_zil_container); _zil_lay.setContentsMargins(0,0,0,0)
        _zil_lay.addWidget(self.bildirim_btn)
        self._bildirim_nokta.setParent(_zil_container)
        self._bildirim_nokta.move(30, 2)

        header.addLayout(hosgeldin_lay)
        header.addStretch()
        header.addWidget(_zil_container, alignment=Qt.AlignTop)
        self.main_layout.addLayout(header)

        # --- APPLE WIDGET KARTLARI (GRID) ---
        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(20)
        
        self.card_toplam = StatCard(f"{ANA_KLASOR}/antrenman_ikon.png", "Toplam Antrenman", "0", COLORS['text_main'])
        self.card_hafta  = StatCard(f"{ANA_KLASOR}/takvim_ikon.png",   "Bu Hafta",          "0", COLORS['info'])
        self.card_kalori = StatCard(f"{ANA_KLASOR}/kalori_ikon.png",   "Toplam Kalori",     "0 kcal", COLORS['accent'])
        
        self.cards_grid.addWidget(self.card_toplam, 0, 0)
        self.cards_grid.addWidget(self.card_hafta,  0, 1)
        self.cards_grid.addWidget(self.card_kalori, 0, 2)
        self.main_layout.addLayout(self.cards_grid)

        # ── Alt satır: Haftalık Grafik + Günlük Hedef ──────────────
        alt_row = QHBoxLayout()
        alt_row.setSpacing(20)

        # --- HAFTALIK AKTİVİTE GRAFİĞİ KARTI ---
        grafik_kart = QFrame()
        grafik_kart.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 24px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        sh1 = QGraphicsDropShadowEffect()
        sh1.setBlurRadius(30); sh1.setColor(QColor(0,0,0,10)); sh1.setOffset(0,5)
        grafik_kart.setGraphicsEffect(sh1)

        grafik_ic = QVBoxLayout(grafik_kart)
        grafik_ic.setContentsMargins(22, 18, 22, 18)
        grafik_ic.setSpacing(10)

        grafik_baslik_row = QHBoxLayout()
        grafik_baslik = QLabel("Haftalık Aktivite")
        grafik_baslik.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLORS['text_main']}; background: transparent; border: none;")
        self.en_aktif_lbl = QLabel("")
        self.en_aktif_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_sub']}; background: transparent; border: none;")
        grafik_baslik_row.addWidget(grafik_baslik)
        grafik_baslik_row.addStretch()
        grafik_baslik_row.addWidget(self.en_aktif_lbl)
        grafik_ic.addLayout(grafik_baslik_row)

        # Matplotlib figürü — küçük ve şeffaf
        self.fig = Figure(figsize=(4, 1.8), facecolor='none')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background: transparent;")
        grafik_ic.addWidget(self.canvas)

        alt_row.addWidget(grafik_kart, stretch=3)

        # --- GÜNLÜK HEDEF KARTI ---
        hedef_kart = QFrame()
        hedef_kart.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 24px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        sh2 = QGraphicsDropShadowEffect()
        sh2.setBlurRadius(30); sh2.setColor(QColor(0,0,0,10)); sh2.setOffset(0,5)
        hedef_kart.setGraphicsEffect(sh2)

        hedef_ic = QVBoxLayout(hedef_kart)
        hedef_ic.setContentsMargins(22, 18, 22, 18)
        hedef_ic.setSpacing(14)

        hedef_baslik = QLabel("Günlük Hedef")
        hedef_baslik.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLORS['text_main']}; background: transparent; border: none;")
        hedef_ic.addWidget(hedef_baslik)

        # Program hedefi progress
        prog_lbl1 = QLabel("Günlük Program")
        prog_lbl1.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['text_sub']}; background: transparent; border: none;")
        hedef_ic.addWidget(prog_lbl1)
        self.progress_program = QProgressBar()
        self.progress_program.setRange(0, 3)
        self.progress_program.setValue(0)
        self.progress_program.setFixedHeight(10)
        self.progress_program.setTextVisible(False)
        self.progress_program.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_input']};
                border-radius: 5px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['info']};
                border-radius: 5px;
            }}
        """)
        hedef_ic.addWidget(self.progress_program)
        self.progress_program_lbl = QLabel("0 / 3 program")
        self.progress_program_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_sub']}; background: transparent; border: none;")
        hedef_ic.addWidget(self.progress_program_lbl)

        # BMI göstergesi
        cizgi2 = QFrame(); cizgi2.setFrameShape(QFrame.HLine)
        cizgi2.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px; border: none;")
        hedef_ic.addWidget(cizgi2)

        bmi_lbl = QLabel("Vücut Kitle Endeksi")
        bmi_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['text_sub']}; background: transparent; border: none;")
        hedef_ic.addWidget(bmi_lbl)

        self.bmi_deger_lbl = QLabel("--")
        self.bmi_deger_lbl.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {COLORS['accent']}; background: transparent; border: none;")
        hedef_ic.addWidget(self.bmi_deger_lbl)

        self.bmi_durum_lbl = QLabel("")
        self.bmi_durum_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['text_sub']}; background: transparent; border: none;")
        hedef_ic.addWidget(self.bmi_durum_lbl)

        hedef_ic.addStretch()
        alt_row.addWidget(hedef_kart, stretch=2)

        self.main_layout.addLayout(alt_row)

        # --- MOTİVASYON ALINTISI KARTI (tam genişlik, alt) ---
        self.motivasyon_kart = QFrame()
        self.motivasyon_kart.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['accent']}, stop:1 #C0392B);
                border-radius: 20px;
                border: none;
            }}
        """)
        sh3 = QGraphicsDropShadowEffect()
        sh3.setBlurRadius(25); sh3.setColor(QColor(240,90,90,60)); sh3.setOffset(0,6)
        self.motivasyon_kart.setGraphicsEffect(sh3)

        mot_lay = QVBoxLayout(self.motivasyon_kart)
        mot_lay.setContentsMargins(28, 20, 28, 20)
        mot_lay.setSpacing(6)

        self.mot_yazi = QLabel()
        self.mot_yazi.setWordWrap(True)
        self.mot_yazi.setStyleSheet("font-size: 14px; font-weight: 600; color: white; background: transparent; border: none;")
        mot_lay.addWidget(self.mot_yazi)

        self.mot_kisi = QLabel()
        self.mot_kisi.setStyleSheet("font-size: 12px; font-weight: 700; color: rgba(255,255,255,0.75); background: transparent; border: none;")
        mot_lay.addWidget(self.mot_kisi, alignment=Qt.AlignRight)

        # Alıntıyı hemen doldur (setup sırasında da görünsün)
        _yazi, _kisi = gunun_alintisi()
        self.mot_yazi.setText(f"\u201c {_yazi} \u201d")
        self.mot_kisi.setText(f"— {_kisi}")

        self.main_layout.addWidget(self.motivasyon_kart)
        self.main_layout.addStretch()

    def _bildirim_paneli_ac(self):
        """Bildirim panelini açar: bugünün antrenör programı + streak bilgisi."""

        # ── Yardımcı: ikon label üretir (img varsa img, yoksa emoji fallback) ──
        def _ikon_lbl(dosya_adi, fallback_emoji, boyut=36, renk_hex=None):
            lbl = QLabel()
            lbl.setFixedSize(boyut, boyut)
            lbl.setAlignment(Qt.AlignCenter)
            yol = f"{ANA_KLASOR}/{dosya_adi}"
            if os.path.exists(yol):
                lbl.setPixmap(QIcon(yol).pixmap(QSize(boyut - 8, boyut - 8)))
                lbl.setStyleSheet(
                    f"background-color:{renk_hex if renk_hex else 'transparent'};"
                    f"border-radius:{boyut//2}px;border:none;"
                )
            else:
                lbl.setText(fallback_emoji)
                lbl.setStyleSheet(
                    f"font-size:{boyut - 14}px;"
                    f"background-color:{renk_hex if renk_hex else 'transparent'};"
                    f"border-radius:{boyut//2}px;border:none;"
                )
            return lbl

        panel = QDialog(self)
        panel.setWindowTitle("Bildirimler")
        panel.setFixedWidth(380)
        panel.setStyleSheet(APPLE_THEME)
        panel.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        panel.setAttribute(Qt.WA_TranslucentBackground)

        dis_lay = QVBoxLayout(panel)
        dis_lay.setContentsMargins(10, 10, 10, 10)

        kart = QFrame()
        kart.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 22px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        golge = QGraphicsDropShadowEffect()
        golge.setBlurRadius(50); golge.setColor(QColor(0,0,0,30)); golge.setOffset(0,8)
        kart.setGraphicsEffect(golge)
        ic_lay = QVBoxLayout(kart)
        ic_lay.setContentsMargins(0, 0, 0, 18)
        ic_lay.setSpacing(0)
        dis_lay.addWidget(kart)

        # ── Başlık barı ──────────────────────────────────────────────
        baslik_bar = QFrame()
        baslik_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-top-left-radius: 22px;
                border-top-right-radius: 22px;
                border-bottom: 1px solid {COLORS['border']};
                border-left: none; border-right: none; border-top: none;
            }}
        """)
        bb_lay = QHBoxLayout(baslik_bar)
        bb_lay.setContentsMargins(20, 16, 16, 16)

        # Başlık ikonu
        baslik_ikon = _ikon_lbl("bildirim_ikon.png", "🔔", 28,
                                 renk_hex=f"{COLORS['accent']}15")
        baslik_ikon.setFixedSize(28, 28)

        baslik_lbl = QLabel("Bildirimler")
        baslik_lbl.setStyleSheet(f"""
            font-size: 17px; font-weight: 800;
            color: {COLORS['text_main']}; background: transparent;
        """)

        kapat_btn = QPushButton("✕")
        kapat_btn.setFixedSize(30, 30)
        kapat_btn.setCursor(Qt.PointingHandCursor)
        kapat_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']}; color: {COLORS['text_sub']};
                border: none; border-radius: 15px;
                font-size: 12px; font-weight: 800;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_tertiary']}; color: {COLORS['text_main']};
            }}
        """)
        kapat_btn.clicked.connect(panel.accept)

        bb_lay.addWidget(baslik_ikon)
        bb_lay.addSpacing(8)
        bb_lay.addWidget(baslik_lbl)
        bb_lay.addStretch()
        bb_lay.addWidget(kapat_btn)
        ic_lay.addWidget(baslik_bar)

        # ── İçerik scroll alanı ─────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 4px; background: transparent; }
            QScrollBar::handle:vertical { background: #C7C7CC; border-radius: 2px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        scroll.setMaximumHeight(420)

        scroll_ic = QWidget(); scroll_ic.setStyleSheet("background: transparent;")
        liste_lay = QVBoxLayout(scroll_ic)
        liste_lay.setContentsMargins(16, 14, 16, 4)
        liste_lay.setSpacing(10)
        scroll.setWidget(scroll_ic)
        ic_lay.addWidget(scroll)

        # ── Bildirim öğesi üretici ───────────────────────────────────
        def _bildirim_ogesi(ikon_dosya, fallback_emoji, ikon_renk,
                            baslik_metni, alt_metni,
                            sol_serit_renk, alt_widget=None):
            """Tek bir bildirim satırı üretir."""
            cerceve = QFrame()
            cerceve.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_app']};
                    border-radius: 16px;
                    border: 1px solid {COLORS['border']};
                }}
            """)
            c_lay = QHBoxLayout(cerceve)
            c_lay.setContentsMargins(0, 0, 16, 0)
            c_lay.setSpacing(0)

            # Sol renkli şerit
            serit = QFrame()
            serit.setFixedWidth(4)
            serit.setStyleSheet(f"""
                QFrame {{
                    background-color: {sol_serit_renk};
                    border-top-left-radius: 16px;
                    border-bottom-left-radius: 16px;
                    border: none;
                }}
            """)
            c_lay.addWidget(serit)
            c_lay.addSpacing(14)

            # İkon
            ikon = _ikon_lbl(ikon_dosya, fallback_emoji, 40, renk_hex=ikon_renk)
            c_lay.addWidget(ikon)
            c_lay.addSpacing(12)

            # Metin sütunu
            metin_lay = QVBoxLayout()
            metin_lay.setSpacing(3)
            metin_lay.setContentsMargins(0, 14, 0, 14)

            b_lbl = QLabel(baslik_metni)
            b_lbl.setStyleSheet(f"""
                font-size: 13px; font-weight: 800;
                color: {COLORS['text_main']}; background: transparent; border: none;
            """)
            metin_lay.addWidget(b_lbl)

            a_lbl = QLabel(alt_metni)
            a_lbl.setWordWrap(True)
            a_lbl.setStyleSheet(f"""
                font-size: 12px; color: {COLORS['text_sub']};
                background: transparent; border: none;
            """)
            metin_lay.addWidget(a_lbl)

            if alt_widget:
                metin_lay.addSpacing(6)
                metin_lay.addWidget(alt_widget)

            c_lay.addLayout(metin_lay, stretch=1)
            return cerceve

        # ── 1. Streak bildirimi ─────────────────────────────────────
        streak_val = db.streak_hesapla(self.sporcu_id)
        streak_baslik = f"{streak_val} Günlük Seri"
        streak_alt = "Harika gidiyorsun, devam et! 💪" if streak_val > 0 else "Bugün antrenman yaparak seriyi başlat."
        streak_ikon_renk = f"{COLORS['warning']}20"
        streak_serit = COLORS['warning']

        liste_lay.addWidget(_bildirim_ogesi(
            "seri_ikon.png", "🔥", streak_ikon_renk,
            streak_baslik, streak_alt, streak_serit
        ))

        # ── 2. Antrenör programı bildirimi ──────────────────────────
        bugun = datetime.now().strftime("%Y-%m-%d")
        conn = db.get_connection()
        prog_rows = conn.execute(
            "SELECT program_detay FROM antrenman_programi WHERE sporcu_id=? AND tarih=? ORDER BY id",
            (self.sporcu_id, bugun)
        ).fetchall()
        conn.close()

        if prog_rows:
            # Hareketleri alt widget olarak göster
            hareketler_w = QWidget(); hareketler_w.setStyleSheet("background:transparent;")
            hareketler_lay = QVBoxLayout(hareketler_w)
            hareketler_lay.setContentsMargins(0,0,0,0); hareketler_lay.setSpacing(4)
            for pr in prog_rows[:3]:
                h_lbl = QLabel(f"· {pr['program_detay']}")
                h_lbl.setStyleSheet(f"font-size:12px;color:{COLORS['text_sub']};background:transparent;border:none;")
                h_lbl.setWordWrap(True)
                hareketler_lay.addWidget(h_lbl)
            if len(prog_rows) > 3:
                daha_lbl = QLabel(f"+{len(prog_rows)-3} hareket daha")
                daha_lbl.setStyleSheet(f"font-size:11px;font-weight:700;color:{COLORS['accent']};background:transparent;border:none;")
                hareketler_lay.addWidget(daha_lbl)

            prog_baslik = f"Bugün {len(prog_rows)} hareket programlandı"
            prog_alt = "Antrenörün hazırladı — Logunuza ekleyin."
            liste_lay.addWidget(_bildirim_ogesi(
                "program_ikon.png", "📋", f"{COLORS['info']}20",
                prog_baslik, prog_alt,
                COLORS['info'], alt_widget=hareketler_w
            ))
        else:
            liste_lay.addWidget(_bildirim_ogesi(
                "program_ikon.png", "📋", f"{COLORS['bg_tertiary']}",
                "Bugün program yok",
                "Antrenörün henüz program eklemedi.",
                COLORS['border']
            ))

        liste_lay.addStretch()

        # ── Bildirimi okundu say → nokta kaybolsun ──────────────────
        self._bildirim_nokta.setVisible(False)

        # ── Paneli butonun altında göster ───────────────────────────
        btn_global = self.bildirim_btn.mapToGlobal(QPoint(0, self.bildirim_btn.height() + 8))
        panel.move(max(0, btn_global.x() - 360 + self.bildirim_btn.width()), btn_global.y())
        panel.exec_()

    def _yukle(self):
        # ── Stat kartları ──────────────────────────────────────────
        stats        = db.antrenman_istatistik(self.sporcu_id)
        kalori_stats = db.kalori_istatistik(self.sporcu_id)
        
        self.card_toplam.guncelle(stats['toplam'])
        self.card_hafta.guncelle(stats['bu_hafta'])
        self.card_kalori.guncelle(
            f"{int(kalori_stats['toplam_kalori']):,} kcal".replace(',', '.')
        )
        # Bildirim noktasını güncelle: bugün antrenörden program var ama log girilmemişse göster
        _bugun = datetime.now().strftime("%Y-%m-%d")
        _conn  = db.get_connection()
        _program_var = _conn.execute(
            "SELECT COUNT(*) FROM antrenman_programi WHERE sporcu_id=? AND tarih=?",
            (self.sporcu_id, _bugun)
        ).fetchone()[0]
        _log_var = _conn.execute(
            "SELECT COUNT(*) FROM antrenman_loglari WHERE sporcu_id=? AND tarih=?",
            (self.sporcu_id, _bugun)
        ).fetchone()[0]
        _conn.close()
        self._bildirim_nokta.setVisible(_program_var > 0 and _log_var == 0)

        # ── Takip sınıfı → Haftalık grafik ────────────────────────
        takip = Takip(self.sporcu_id)
        takip.haftalik_veri_yukle()

        en_aktif = takip.en_aktif_gun()
        self.en_aktif_lbl.setText(
            f"En aktif: {en_aktif}" if en_aktif != "-" else "Henüz antrenman yok"
        )
        self._grafik_ciz(takip.kayitlar)

        # ── Günlük program progress ────────────────────────────────
        bugun = datetime.now().strftime("%Y-%m-%d")
        bugun_adet = db.get_connection().execute(
            "SELECT COUNT(*) FROM antrenman_loglari WHERE sporcu_id=? AND tarih=?",
            (self.sporcu_id, bugun)
        ).fetchone()[0]

        hedef = 3
        tamamlandi = bugun_adet >= hedef
        gosterilen = min(bugun_adet, hedef)
        self.progress_program.setValue(gosterilen)

        if tamamlandi:
            # Progress bar yeşil + dolu
            self.progress_program.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_input']};
                    border-radius: 5px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background-color: {COLORS['success']};
                    border-radius: 5px;
                }}
            """)
            self.progress_program_lbl.setText("✅  Günlük hedef tamamlandı!")
            self.progress_program_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['success']}; background: transparent; border: none;")
        else:
            self.progress_program.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_input']};
                    border-radius: 5px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background-color: {COLORS['info']};
                    border-radius: 5px;
                }}
            """)
            self.progress_program_lbl.setText(f"{bugun_adet} / {hedef} antrenman")
            self.progress_program_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_sub']}; background: transparent; border: none;")

        # ── Motivasyon alıntısını güncelle ────────────────────────
        _yazi, _kisi = gunun_alintisi()
        self.mot_yazi.setText(f"\u201c {_yazi} \u201d")
        self.mot_kisi.setText(f"— {_kisi}")

        # ── Sporcu sınıfı → BMI ────────────────────────────────────
        sporcu_obj = Sporcu.veritabanindan_yukle(self.sporcu_id)
        if sporcu_obj and sporcu_obj.boy > 0:
            bmi = sporcu_obj.bmi_hesapla()
            self.bmi_deger_lbl.setText(str(bmi))
            if bmi < 18.5:
                durum, renk = "Zayıf",        COLORS['info']
            elif bmi < 25:
                durum, renk = "Normal",        COLORS['success']
            elif bmi < 30:
                durum, renk = "Fazla Kilolu",  COLORS['warning']
            else:
                durum, renk = "Obez",          COLORS['danger']
            self.bmi_deger_lbl.setStyleSheet(
                f"font-size: 28px; font-weight: 900; color: {renk}; "
                f"background: transparent; border: none;"
            )
            self.bmi_durum_lbl.setText(durum)
        else:
            self.bmi_deger_lbl.setText("--")
            self.bmi_durum_lbl.setText("Profili tamamla")

    def _grafik_ciz(self, kayitlar: list):
        """Takip.kayitlar listesinden haftalık bar grafik çizer."""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('none')
        self.fig.patch.set_alpha(0)

        gunler = [k["gun"]  for k in kayitlar]
        adetler= [k["adet"] for k in kayitlar]

        renkler = []
        for a in adetler:
            renkler.append(COLORS['accent'] if a > 0 else COLORS['bg_input'])

        bars = ax.bar(gunler, adetler, color=renkler, width=0.55,
                      zorder=3, linewidth=0)

        # Değer etiketi (sadece > 0 olanlar)
        for bar, adet in zip(bars, adetler):
            if adet > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.05,
                    str(adet),
                    ha='center', va='bottom',
                    fontsize=8, fontweight='bold',
                    color=COLORS['text_main']
                )

        ax.set_ylim(0, max(max(adetler) + 1, 4))
        ax.yaxis.set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(COLORS['border'])
        ax.tick_params(colors=COLORS['text_sub'], labelsize=9)
        ax.grid(axis='y', color=COLORS['border'], linestyle='--',
                linewidth=0.5, zorder=0)

        self.fig.tight_layout(pad=0.3)
        self.canvas.draw()

    def yenile(self): 
        self._yukle()


# ==========================================
# Avatar Seçici
# ==========================================

# ==========================================
# Avatar Seçici (APPLE KONSEPTİ)
# ==========================================
class AvatarSeciciDialog(QDialog):
    def __init__(self, ebeveyn):
        super().__init__(ebeveyn)
        self.setWindowTitle("Profil Fotoğrafı")
        self.setFixedSize(460, 420)
        self.secilen_avatar = "varsayilan.png"
        self.aktif_btn = None
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_app']};
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(0)

        # --- BAŞLIK ALANI ---
        baslik_lay = QHBoxLayout()
        baslik_lay.setSpacing(0)

        baslik = QLabel("Memoji Seç")
        baslik.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLORS['text_main']}; letter-spacing: -0.5px;")

        iptal_btn = QPushButton("✕")
        iptal_btn.setFixedSize(32, 32)
        iptal_btn.setCursor(Qt.PointingHandCursor)
        iptal_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_sub']};
                border: none;
                border-radius: 16px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #D1D1D6;
                color: {COLORS['text_main']};
            }}
        """)
        iptal_btn.clicked.connect(self.reject)

        baslik_lay.addWidget(baslik)
        baslik_lay.addStretch()
        baslik_lay.addWidget(iptal_btn)
        layout.addLayout(baslik_lay)
        layout.addSpacing(6)

        alt_baslik = QLabel("Seni en iyi yansıtan avatarı seç")
        alt_baslik.setStyleSheet(f"font-size: 13px; color: {COLORS['text_sub']}; font-weight: 500;")
        layout.addWidget(alt_baslik)
        layout.addSpacing(24)

        # --- KART (GRID İÇİN) ---
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 24px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30); shadow.setColor(QColor(0, 0, 0, 12)); shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(0)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setAlignment(Qt.AlignCenter)

        memojiler = [
            "memoji1.png", "memoji2.png", "memoji3.jpg", "memoji4.jpg",
            "memoji5.jpg", "memoji6.jpg", "memoji7.webp", "memoji8.png"
        ]

        self.avatar_butonlari = {}
        row, col = 0, 0
        for m in memojiler:
            btn = self._avatar_btn_olustur(m)
            self.avatar_butonlari[m] = btn
            grid.addWidget(btn, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

        card_layout.addLayout(grid)
        layout.addWidget(card)
        layout.addSpacing(20)

        # --- SEÇ BUTONU ---
        self.sec_btn = QPushButton("✓  Seçimi Onayla")
        self.sec_btn.setFixedHeight(50)
        self.sec_btn.setCursor(Qt.PointingHandCursor)
        self.sec_btn.setEnabled(False)
        self.sec_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #C7C7CC;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 0.2px;
            }}
        """)
        self.sec_btn.clicked.connect(self.accept)
        layout.addWidget(self.sec_btn)

    def _avatar_btn_olustur(self, m):
        btn = QPushButton()
        btn.setFixedSize(80, 80)
        btn.setCursor(Qt.PointingHandCursor)

        tam_yol = f"{ANA_KLASOR}/{m}"
        if os.path.exists(tam_yol):
            orj = QPixmap(tam_yol)
            if not orj.isNull():
                boyut = 72
                hedef = QPixmap(boyut, boyut)
                hedef.fill(Qt.transparent)
                kucuk = orj.scaled(boyut, boyut, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                cizer = QPainter(hedef)
                cizer.setRenderHint(QPainter.Antialiasing)
                yol = QPainterPath()
                yol.addEllipse(0, 0, boyut, boyut)
                cizer.setClipPath(yol)
                cizer.drawPixmap((boyut - kucuk.width()) // 2, (boyut - kucuk.height()) // 2, kucuk)
                cizer.end()
                btn.setIcon(QIcon(hedef))
                btn.setIconSize(QSize(boyut, boyut))

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    border-radius: 40px;
                    border: 3px solid transparent;
                }}
                QPushButton:hover {{
                    background-color: #E5E5EA;
                    border: 3px solid {COLORS['accent']}55;
                }}
            """)
        else:
            # Görsel yoksa zarif placeholder
            btn.setText("👤")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['text_sub']};
                    border-radius: 40px;
                    border: 3px solid transparent;
                    font-size: 28px;
                }}
                QPushButton:hover {{
                    background-color: #E5E5EA;
                    border: 3px solid {COLORS['accent']}55;
                }}
            """)

        btn.clicked.connect(lambda _, av=m: self._secim_yap(av, btn))
        return btn

    def _secim_yap(self, avatar, btn):
        # Önceki seçili butonu sıfırla
        if self.aktif_btn and self.aktif_btn is not btn:
            self.aktif_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    border-radius: 40px;
                    border: 3px solid transparent;
                }}
                QPushButton:hover {{
                    background-color: #E5E5EA;
                    border: 3px solid {COLORS['accent']}55;
                }}
            """)

        # Yeni seçili butonu vurgula
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']}18;
                border-radius: 40px;
                border: 3px solid {COLORS['accent']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']}22;
                border: 3px solid {COLORS['accent']};
            }}
        """)
        self.aktif_btn = btn
        self.secilen_avatar = avatar

        # Seç butonunu aktifleştir
        self.sec_btn.setEnabled(True)
        self.sec_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 0.2px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)

# ==========================================
# 5. SPORCU PROFİL EKRANI (APPLE HEALTH KONSEPTİ - GÜNCELLENDİ)
# ==========================================
from PyQt5.QtWidgets import QFormLayout

class SporcuWidget(QWidget):
    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici
        self.sporcu_id = kullanici['sporcu_id']
        self.secili_avatar = "varsayilan.png" 
        self.sayfa_durumu = {"degisiklik_yapildi": False}
        self._setup_ui()
        self._yukle()
        self.sayfa_durumu.update({"degisiklik_yapildi": False})

    def _setup_ui(self):
        # --- DIŞ LAYOUT: Başlık sabit kalır, sadece içerik kayar ---
        dis_layout = QVBoxLayout(self)
        dis_layout.setContentsMargins(0, 0, 0, 0)
        dis_layout.setSpacing(0)

        # Apple Tarzı Başlık (ScrollArea dışında, her zaman görünür)
        baslik_container = QWidget()
        baslik_container.setStyleSheet(f"background-color: {COLORS['bg_app']};")
        baslik_ic = QHBoxLayout(baslik_container)
        baslik_ic.setContentsMargins(30, 30, 30, 10)
        baslik = QLabel("Profilim")
        baslik.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {COLORS['text_main']}; background: transparent;")
        baslik_ic.addWidget(baslik)
        baslik_ic.addStretch()
        dis_layout.addWidget(baslik_container)

        # --- SCROLL AREA (İçerik kayarken başlık sabit kalır) ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #C7C7CC;
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        # Scroll içindeki ana widget
        ic_widget = QWidget()
        ic_widget.setStyleSheet(f"background-color: {COLORS['bg_app']};")
        main_layout = QVBoxLayout(ic_widget)
        main_layout.setContentsMargins(30, 10, 30, 30)
        main_layout.setSpacing(25)

        # --- ANA PROFİL KARTI (GÖLGELİ VE YUVARLAK) ---
        card = QFrame()
        card.setObjectName("appleCard")
        card.setStyleSheet(f"QFrame#appleCard {{ background-color: {COLORS['bg_card']}; border-radius: 28px; }}")
        
        # Yumuşak Gölge Efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40); shadow.setColor(QColor(0, 0, 0, 15)); shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(0)

        # --- 1. AVATAR BÖLÜMÜ (HİZALAMA DÜZELTİLDİ) ---
        avatar_container = QVBoxLayout()
        avatar_container.setAlignment(Qt.AlignCenter)
        
        self.avatar_btn = QPushButton() 
        self.avatar_btn.setFixedSize(110, 110)
        self.avatar_btn.setCursor(Qt.PointingHandCursor)
        self.avatar_btn.setStyleSheet(f"background-color: {COLORS['bg_input']}; border-radius: 55px; border: 2px dashed {COLORS['border']};")
        self.avatar_btn.clicked.connect(self._avatar_sec)
        
        avatar_container.addWidget(self.avatar_btn, alignment=Qt.AlignCenter)
        avatar_container.addSpacing(15)
        
        avatar_alt_metin = QLabel("Profil Fotoğrafını Değiştir")
        avatar_alt_metin.setStyleSheet("color: #007AFF; font-size: 14px; font-weight: 700; background: transparent;")
        avatar_container.addWidget(avatar_alt_metin, alignment=Qt.AlignCenter)
        
        card_layout.addLayout(avatar_container)
        card_layout.addSpacing(25)
        
        cizgi = QFrame(); cizgi.setFrameShape(QFrame.HLine)
        cizgi.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        card_layout.addWidget(cizgi)
        card_layout.addSpacing(25)

        # --- 2. FORM ALANI (QFormLayout ile Kusursuz Hizalama) ---
        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        
        input_style = f"""
            QLineEdit, QDoubleSpinBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_main']};
                border: 2px solid transparent;
                border-radius: 12px;
                padding: 10px 15px; 
                font-size: 15px;
                font-weight: 600;
                min-height: 24px;
            }}
            QLineEdit:focus, QDoubleSpinBox:focus {{
                border: 2px solid {COLORS['accent']}44;
                background-color: #FFFFFF;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; }}
        """

        # Validatorler (Sayı yasağı için)
        from PyQt5.QtGui import QRegExpValidator
        from PyQt5.QtCore import QRegExp
        harf_validator = QRegExpValidator(QRegExp(r"^[a-zA-ZğüşıöçĞÜŞİÖÇ ]+$"), self)

        # Giriş Kutuları
        self.ad_input = QLineEdit(); self.ad_input.setValidator(harf_validator)
        self.soyad_input = QLineEdit(); self.soyad_input.setValidator(harf_validator)
        self.kilo_input = QDoubleSpinBox(); self.kilo_input.setRange(20, 300); self.kilo_input.setSuffix(" kg")
        self.boy_input = QDoubleSpinBox(); self.boy_input.setRange(100, 250); self.boy_input.setSuffix(" cm")

        for inp in [self.ad_input, self.soyad_input, self.kilo_input, self.boy_input]:
            inp.setStyleSheet(input_style)

        # Etiket Stilleri
        lbl_style = f"color: {COLORS['text_sub']}; font-weight: 700; font-size: 14px; margin-right: 15px;"
        def label_olustur(txt):
            l = QLabel(txt); l.setStyleSheet(lbl_style); return l

        form_layout.addRow(label_olustur("Ad"), self.ad_input)
        form_layout.addRow(label_olustur("Soyad"), self.soyad_input)
        form_layout.addRow(label_olustur("Kilo"), self.kilo_input)
        form_layout.addRow(label_olustur("Boy"), self.boy_input)
        
        card_layout.addLayout(form_layout)
        card_layout.addSpacing(30)

        # Kaydet Butonu
        self.kaydet_btn = QPushButton("💾 Profili Kaydet")
        self.kaydet_btn.setCursor(Qt.PointingHandCursor); self.kaydet_btn.setFixedHeight(54)
        self.kaydet_btn.setStyleSheet(f"QPushButton {{ background-color: {COLORS['accent']}; color: white; border-radius: 27px; font-size: 16px; font-weight: 800; }} QPushButton:hover {{ background-color: {COLORS['accent_hover']}; }}")
        self.kaydet_btn.clicked.connect(self._kaydet)
        card_layout.addWidget(self.kaydet_btn)
        
        main_layout.addWidget(card)
        main_layout.addWidget(self._antrenor_paneli())
        main_layout.addStretch()

        scroll.setWidget(ic_widget)
        dis_layout.addWidget(scroll)

        # Değişiklik Dinleyicileri
        self.ad_input.textChanged.connect(lambda: self.sayfa_durumu.update({"degisiklik_yapildi": True}))
        self.soyad_input.textChanged.connect(lambda: self.sayfa_durumu.update({"degisiklik_yapildi": True}))
        self.kilo_input.valueChanged.connect(lambda: self.sayfa_durumu.update({"degisiklik_yapildi": True}))
        self.boy_input.valueChanged.connect(lambda: self.sayfa_durumu.update({"degisiklik_yapildi": True}))

    def _avatar_sec(self):
        dialog = AvatarSeciciDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.secili_avatar = dialog.secilen_avatar
            self._yukle_avatar_gorunumu()
            db.sporcu_guncelle(self.sporcu_id, self.ad_input.text(), self.soyad_input.text(), self.kilo_input.value(), self.boy_input.value(), avatar=self.secili_avatar)

    def _yukle_avatar_gorunumu(self):
        tam_yol = f"{ANA_KLASOR}/{self.secili_avatar}".replace("\\", "/")
        if os.path.exists(tam_yol):
            pix = QPixmap(tam_yol)
            if not pix.isNull():
                hedef = QPixmap(110, 110); hedef.fill(Qt.transparent)
                painter = QPainter(hedef); painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath(); path.addEllipse(0, 0, 110, 110); painter.setClipPath(path)
                painter.drawPixmap(0, 0, pix.scaled(110, 110, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                painter.end()
                self.avatar_btn.setIcon(QIcon(hedef)); self.avatar_btn.setIconSize(QSize(110, 110))
                self.avatar_btn.setText("")
        else:
            self.avatar_btn.setText("📸\nFoto Seç")

    def _yukle(self):
        sporcu = db.sporcu_getir(self.sporcu_id)
        if sporcu:
            self.ad_input.setText(sporcu.get('ad', ''))
            self.soyad_input.setText(sporcu.get('soyad', '')) 
            self.kilo_input.setValue(sporcu.get('kilo', 70) or 70)
            self.boy_input.setValue(sporcu.get('boy', 170) or 170)
            self.secili_avatar = sporcu.get('avatar') or "varsayilan.png"
            self._yukle_avatar_gorunumu()

    def _kaydet(self):
        """
        Profil bilgilerini kaydeder.
        Sporcu sınıfının ilerleme_kaydet() metodu aracılığıyla
        kilo değişimini takip eder.
        """
        yeni_kilo = self.kilo_input.value()

        # Sporcu nesnesi üzerinden ilerleme_kaydet() çağrısı
        sporcu_obj = Sporcu.veritabanindan_yukle(self.sporcu_id)
        if sporcu_obj:
            sporcu_obj.ilerleme_kaydet(yeni_kilo)

        db.sporcu_guncelle(
            self.sporcu_id,
            self.ad_input.text(),
            self.soyad_input.text(),
            yeni_kilo,
            self.boy_input.value(),
            avatar=self.secili_avatar
        )
        AppleMesajDialog.bilgi(self, "Başarılı", "Profiliniz başarıyla kaydedildi.")
        self.sayfa_durumu.update({"degisiklik_yapildi": False})

    def yenile(self): 
        self._yukle()
        self._basvuru_durumunu_kontrol_et()

    def _antrenor_paneli(self):
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: 24px;")
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(20); sh.setColor(QColor(0,0,0,10)); sh.setOffset(0,4)
        panel.setGraphicsEffect(sh)
        l = QVBoxLayout(panel); l.setContentsMargins(35, 25, 35, 25); l.setSpacing(12)
        l.addWidget(QLabel("🎓 Antrenör Başvurusu", styleSheet=f"font-size: 18px; font-weight: 800; color: {COLORS['text_main']}; border:none; background:transparent;"))
        
        self.basvuru_durum_lbl = QLabel("Durum: Başvuru yapılmadı")
        # Okunabilirlik için renk koyulaştırıldı
        self.basvuru_durum_lbl.setStyleSheet("color: #3A3A3C; font-size: 14px; font-weight: 700; border:none; background:transparent;")
        l.addWidget(self.basvuru_durum_lbl)
        
        self.hizli_basvuru_btn = QPushButton("🚀 Hemen Başvuru Yap")
        self.hizli_basvuru_btn.setCursor(Qt.PointingHandCursor); self.hizli_basvuru_btn.setFixedHeight(48)
        self.hizli_basvuru_btn.setStyleSheet(f"QPushButton {{ background-color: #007AFF; color: white; border-radius: 24px; font-weight: 800; font-size: 15px; }} QPushButton:hover {{ background-color: #005BB5; }}")
        self.hizli_basvuru_btn.clicked.connect(self._basvuru_penceresi)
        l.addWidget(self.hizli_basvuru_btn)
        self._basvuru_durumunu_kontrol_et(); return panel

    def _basvuru_durumunu_kontrol_et(self):
        conn = db.get_connection(); k_id = self.kullanici['kullanici_id']
        basvuru = conn.execute("SELECT durum FROM antrenor_basvurulari WHERE kullanici_id=?", (k_id,)).fetchone()
        rol = conn.execute("SELECT rol FROM kullanicilar WHERE kullanici_id=?", (k_id,)).fetchone()[0]; conn.close()
        
        self.hizli_basvuru_btn.setVisible(True)
        if rol == 'admin':
            self.basvuru_durum_lbl.setText("Durum: 👑 Yönetici Hesabı")
            self.basvuru_durum_lbl.setStyleSheet("color: #E74C3C; font-weight: 800; background: transparent;")
            self.hizli_basvuru_btn.setVisible(False)
        elif rol == 'antrenor':
            self.basvuru_durum_lbl.setText("Durum: ✅ Onaylı Antrenör")
            self.basvuru_durum_lbl.setStyleSheet(f"color: {COLORS['success']}; font-weight: 800; background: transparent;")
            self.hizli_basvuru_btn.setVisible(False)
        elif basvuru:
            durum = basvuru[0]
            if durum == 'beklemede':
                self.basvuru_durum_lbl.setText("Durum: ⏳ Onay Bekleniyor...")
                self.basvuru_durum_lbl.setStyleSheet("color: #FF9500; font-weight: 800; background: transparent;")
                self.hizli_basvuru_btn.setVisible(False)
            elif durum == 'reddedildi':
                self.basvuru_durum_lbl.setText("Durum: ❌ Başvuru Reddedildi")
                self.basvuru_durum_lbl.setStyleSheet(f"color: {COLORS['danger']}; font-weight: 800; background: transparent;")
                self.hizli_basvuru_btn.setText("🔄 Tekrar Başvur")

    def _basvuru_penceresi(self):
        # ---> ÇÖZÜM İÇİN GEREKLİ İÇE AKTARMA EKLENDİ (QStyledItemDelegate) <---
        from PyQt5.QtWidgets import QDialog, QStyledItemDelegate
        from PyQt5.QtGui import QRegExpValidator
        from PyQt5.QtCore import QRegExp
        
        diyalog = QDialog(self)
        diyalog.setWindowTitle("Antrenör Başvurusu")
        diyalog.setFixedSize(420, 380)
        diyalog.setStyleSheet(APPLE_THEME)
        
        lay = QVBoxLayout(diyalog)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)
        
        lay.addWidget(QLabel("Başvuru Formu", styleSheet=f"font-size: 22px; font-weight: 900; color: {COLORS['text_main']};"))
        
        f_grid = QGridLayout()
        f_grid.setSpacing(15)
        
        tc_input_style = f"background-color: {COLORS['bg_input']}; border-radius: 12px; padding: 12px; font-weight: 600;"
        
        # TC Kutusu
        tc_in = QLineEdit()
        tc_in.setPlaceholderText("11 Haneli TC")
        tc_in.setMaxLength(11)
        tc_validator = QRegExpValidator(QRegExp("^[0-9]+$"), tc_in)
        tc_in.setValidator(tc_validator)
        tc_in.setStyleSheet(tc_input_style)
        
        # Deneyim Kutusu
        den_in = QSpinBox()
        den_in.setRange(0, 50)
        den_in.setSuffix(" Yıl")
        den_in.setStyleSheet(f"QSpinBox {{ {tc_input_style} }} QSpinBox::up-button, QSpinBox::down-button {{ width: 0px; }}")
        
        # Bölüm Kutusu (Hata Veren ComboBox)
        bol_cm = QComboBox()
        bol_cm.addItems(["Besyo", "Spor Bilimleri", "Fizyoterapi", "Antrenörlük Eğitimi", "Diğer"])
        bol_cm.setStyleSheet(tc_input_style)
        
        # =========================================================================
        # ---> ÇÖZÜM: COMBOBOX KAYMA/TİTREME SORUNUNU GİDEREN KOD BLOĞU <---
        # 1. Hatalı iç hizalama mantığını QStyledItemDelegate ile tamamen sıfırlar
        bol_cm.setItemDelegate(QStyledItemDelegate()) 
        
        # 2. Açılır menünün arka planını ve görünümünü sabitler (Apple stili)
        bol_cm.view().setStyleSheet(f"""
            QAbstractItemView {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                outline: none;
                selection-background-color: {COLORS['accent']}22;
                selection-color: {COLORS['text_main']};
            }}
            QAbstractItemView::item {{
                padding: 8px;
                min-height: 25px;
            }}
        """)
        # =========================================================================
        
        f_grid.addWidget(QLabel("TC Kimlik", styleSheet=f"color: {COLORS['text_sub']}; font-weight: 700;"), 0, 0)
        f_grid.addWidget(tc_in, 0, 1)
        f_grid.addWidget(QLabel("Deneyim", styleSheet=f"color: {COLORS['text_sub']}; font-weight: 700;"), 1, 0)
        f_grid.addWidget(den_in, 1, 1)
        f_grid.addWidget(QLabel("Bölüm", styleSheet=f"color: {COLORS['text_sub']}; font-weight: 700;"), 2, 0)
        f_grid.addWidget(bol_cm, 2, 1)
        
        lay.addLayout(f_grid)
        
        btn = QPushButton("🚀 Başvuruyu Gönder")
        btn.setFixedHeight(50)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"background-color: {COLORS['accent']}; color: white; border-radius: 25px; font-weight: 800;")
        lay.addWidget(btn)
        
        def save():
            if len(tc_in.text()) != 11: 
                AppleMesajDialog.uyari(diyalog, "Eksik Bilgi", "TC kimlik numarası tam 11 haneli olmalıdır.")
                return
            conn = db.get_connection()
            k_id = conn.execute("SELECT kullanici_id FROM sporcular WHERE sporcu_id=?", (self.sporcu_id,)).fetchone()[0]
            conn.execute("DELETE FROM antrenor_basvurulari WHERE kullanici_id=?", (k_id,))
            conn.execute("INSERT INTO antrenor_basvurulari (kullanici_id, tc_no, deneyim_yili, bolum) VALUES (?,?,?,?)", (k_id, tc_in.text(), den_in.value(), bol_cm.currentText()))
            conn.commit()
            conn.close()
            diyalog.accept()
            self._basvuru_durumunu_kontrol_et()
            AppleMesajDialog.bilgi(self, "Başarılı", "Başvurunuz yönetici onayına gönderildi.")
            
        btn.clicked.connect(save)
        diyalog.exec_()

# ==========================================
# 6.5 ADMIN PANEL EKRANI
# ==========================================
class AdminWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        from PyQt5.QtWidgets import QHeaderView 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Başlık
        baslik = QLabel("👑 Admin Kontrol Paneli")
        baslik.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {COLORS['text_main']}; letter-spacing: -0.5px;")
        layout.addWidget(baslik)

        # Apple temalı tablo stili (tüm tablolarda ortak kullanılacak)
        tablo_stili = f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                gridline-color: {COLORS['border']};
                color: {COLORS['text_main']};
                font-size: 14px;
                selection-background-color: {COLORS['accent']}22;
                selection-color: {COLORS['text_main']};
                outline: none;
            }}
            QTableWidget::item {{
                padding: 10px 14px;
                border-bottom: 1px solid {COLORS['border']};
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_main']};
            }}
            QTableWidget::item:alternate {{
                background-color: {COLORS['bg_app']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['accent']}18;
                color: {COLORS['text_main']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_app']};
                color: {COLORS['text_sub']};
                font-size: 12px;
                font-weight: 700;
                padding: 10px 14px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

        # Sekme stili
        sekme_stili = f"""
            QTabWidget::pane {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 0px 12px 12px 12px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['bg_app']};
                color: {COLORS['text_sub']};
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                border-radius: 10px 10px 0px 0px;
                padding: 10px 20px;
                min-width: 120px;
                font-size: 13px;
                font-weight: 600;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_main']};
                font-weight: 700;
                border-bottom: 2px solid {COLORS['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_main']};
            }}
        """

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(sekme_stili)
        
        # 1. SEKME: KULLANICILAR 
        self.tablo_kullanici = QTableWidget()
        self.tablo_kullanici.setColumnCount(5)
        self.tablo_kullanici.setHorizontalHeaderLabels(["ID", "Ad Soyad", "E-posta", "Kayıt Tarihi", "İşlem"])
        self.tablo_kullanici.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_kullanici.verticalHeader().setVisible(False)
        self.tablo_kullanici.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo_kullanici.setAlternatingRowColors(True)
        self.tablo_kullanici.setShowGrid(False)
        self.tablo_kullanici.setStyleSheet(tablo_stili)
        
        # 2. SEKME: BAŞVURULAR 
        self.tablo_basvuru = QTableWidget()
        self.tablo_basvuru.setColumnCount(6)
        self.tablo_basvuru.setHorizontalHeaderLabels(["ID", "Ad Soyad", "TC No", "Bölüm", "Deneyim", "İşlem"])
        self.tablo_basvuru.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_basvuru.verticalHeader().setVisible(False)
        self.tablo_basvuru.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo_basvuru.setAlternatingRowColors(True)
        self.tablo_basvuru.setShowGrid(False)
        self.tablo_basvuru.setStyleSheet(tablo_stili)

        # 3. SEKME: SİSTEM GÜNLÜĞÜ (LOGLAR)
        log_tab = QWidget()
        log_tab.setStyleSheet(f"background-color: transparent;")
        log_lay = QVBoxLayout(log_tab)
        log_lay.setContentsMargins(0, 10, 0, 0)
        self.tablo_log = QTableWidget()
        self.tablo_log.setColumnCount(4)
        self.tablo_log.setHorizontalHeaderLabels(["ID", "İşlem", "Detay", "Tarih"])
        self.tablo_log.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_log.verticalHeader().setVisible(False)
        self.tablo_log.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo_log.setAlternatingRowColors(True)
        self.tablo_log.setShowGrid(False)
        self.tablo_log.setStyleSheet(tablo_stili)
        log_lay.addWidget(self.tablo_log)

        self.tabs.addTab(self.tablo_kullanici, "  Kullanıcılar  ")
        self.tabs.addTab(self.tablo_basvuru, "  Başvurular  ")
        self.tabs.addTab(log_tab, "  Sistem Günlüğü  ")
        
        layout.addWidget(self.tabs)
        self.yenile()

    def yenile(self):
        self._kullanicilari_getir()
        self._basvurulari_getir()
        self._loglari_getir() # YENİ

    def _loglari_getir(self):
        loglar = db.loglari_getir()
        self.tablo_log.setRowCount(len(loglar))
        for i, l in enumerate(loglar):
            self.tablo_log.setItem(i, 0, QTableWidgetItem(str(l['id'])))
            self.tablo_log.setItem(i, 1, QTableWidgetItem(l['islem']))
            self.tablo_log.setItem(i, 2, QTableWidgetItem(l['detay']))
            self.tablo_log.setItem(i, 3, QTableWidgetItem(l['tarih']))

    def _kullanicilari_getir(self):
        conn = db.get_connection()
        rows = conn.execute("SELECT k.kullanici_id, k.email, k.olusturma_tarihi, s.ad, s.soyad FROM kullanicilar k LEFT JOIN sporcular s ON k.kullanici_id = s.kullanici_id WHERE k.rol != 'admin'").fetchall()
        conn.close()
        self.tablo_kullanici.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.tablo_kullanici.setItem(i, 0, QTableWidgetItem(str(r['kullanici_id'])))
            self.tablo_kullanici.setItem(i, 1, QTableWidgetItem(f"{r['ad']} {r['soyad']}"))
            self.tablo_kullanici.setItem(i, 2, QTableWidgetItem(r['email'] or "-"))
            self.tablo_kullanici.setItem(i, 3, QTableWidgetItem(str(r['olusturma_tarihi'])[:10]))
            
            btn_w = QWidget()
            btn_w.setStyleSheet("background-color: transparent; border: none;")
            lay = QHBoxLayout(btn_w)
            lay.setContentsMargins(8, 6, 8, 6)
            lay.setAlignment(Qt.AlignCenter)
            sil_btn = QPushButton("  Sil  ")
            sil_btn.setFixedHeight(32)
            sil_btn.setCursor(Qt.PointingHandCursor)
            sil_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF3B30;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 700;
                    padding: 0px 18px;
                }
                QPushButton:hover {
                    background-color: #D92B21;
                }
                QPushButton:pressed {
                    background-color: #B52218;
                }
            """)
            sil_btn.clicked.connect(lambda _, uid=r['kullanici_id']: self._kullanici_sil(uid))
            lay.addWidget(sil_btn)
            self.tablo_kullanici.setCellWidget(i, 4, btn_w)
            self.tablo_kullanici.setRowHeight(i, 52)

    def _basvurulari_getir(self):
        conn = db.get_connection()
        rows = conn.execute("SELECT b.*, s.ad, s.soyad FROM antrenor_basvurulari b JOIN kullanicilar k ON b.kullanici_id = k.kullanici_id JOIN sporcular s ON k.kullanici_id = s.kullanici_id WHERE b.durum = 'beklemede'").fetchall()
        conn.close()
        self.tablo_basvuru.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.tablo_basvuru.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.tablo_basvuru.setItem(i, 1, QTableWidgetItem(f"{r['ad']} {r['soyad']}"))
            self.tablo_basvuru.setItem(i, 2, QTableWidgetItem(r['tc_no']))
            self.tablo_basvuru.setItem(i, 3, QTableWidgetItem(r['bolum']))
            self.tablo_basvuru.setItem(i, 4, QTableWidgetItem(f"{r['deneyim_yili']} Yıl"))
            
            btn_w = QWidget()
            btn_w.setStyleSheet("background-color: transparent; border: none;")
            lay = QHBoxLayout(btn_w)
            lay.setContentsMargins(8, 6, 8, 6)
            lay.setSpacing(6)
            lay.setAlignment(Qt.AlignCenter)
            onay_btn = QPushButton(" Onayla ")
            onay_btn.setFixedHeight(32)
            onay_btn.setCursor(Qt.PointingHandCursor)
            onay_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34C759;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0px 0px;
                }
                QPushButton:hover {
                    background-color: #28A745;
                }
                QPushButton:pressed {
                    background-color: #1E8E37;
                }
            """)
            onay_btn.clicked.connect(lambda _, bid=r['id'], uid=r['kullanici_id']: self._basvuru_onayla(bid, uid))
            red_btn = QPushButton(" Reddet ")
            red_btn.setFixedHeight(32)
            red_btn.setCursor(Qt.PointingHandCursor)
            red_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF3B30;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0px 1px;
                }
                QPushButton:hover {
                    background-color: #D92B21;
                }
                QPushButton:pressed {
                    background-color: #B52218;
                }
            """)
            red_btn.clicked.connect(lambda _, bid=r['id']: self._basvuru_reddet(bid))
            lay.addWidget(onay_btn)
            lay.addWidget(red_btn)
            self.tablo_basvuru.setCellWidget(i, 5, btn_w)
            self.tablo_basvuru.setRowHeight(i, 52)

    def _basvuru_onayla(self, b_id, u_id):
        conn = db.get_connection(); conn.execute("UPDATE antrenor_basvurulari SET durum='onaylandi' WHERE id=?", (b_id,))
        conn.execute("UPDATE kullanicilar SET rol='antrenor' WHERE kullanici_id=?", (u_id,)); conn.commit(); conn.close()
        AppleMesajDialog.bilgi(self, "Başarılı", "Başvuru onaylandı. Kullanıcı artık antrenör yetkisine sahip."); self.yenile()

    def _basvuru_reddet(self, b_id):
        conn = db.get_connection(); conn.execute("UPDATE antrenor_basvurulari SET durum='reddedildi' WHERE id=?", (b_id,))
        conn.commit(); conn.close(); AppleMesajDialog.bilgi(self, "Bilgi", "Başvuru reddedildi."); self.yenile()

    def _kullanici_sil(self, uid):
        if AppleMesajDialog.soru(self, "Silme Onayı", "Bu kullanıcıyı kalıcı olarak silmek istediğinize emin misiniz?"):
            conn = db.get_connection()
            # Önce alt tablolar temizleniyor
            conn.execute("DELETE FROM antrenman_programi WHERE sporcu_id=?", (uid,))
            conn.execute("DELETE FROM sporcu_antrenor WHERE sporcu_id=?", (uid,))
            conn.execute("DELETE FROM antrenor_basvurulari WHERE kullanici_id=?", (uid,))
            
            # En son ana tablolar temizleniyor
            conn.execute("DELETE FROM sporcular WHERE kullanici_id=?", (uid,))
            conn.execute("DELETE FROM kullanicilar WHERE kullanici_id=?", (uid,))
            conn.commit()
            conn.close()
            self.yenile()

# ==========================================
# 6.6 VÜCUT KİTLE ENDEKSİ (BMI) EKRANI (APPLE KONSEPTİ)
# ==========================================
class VkiWidget(QWidget):
    def __init__(self, kullanici): 
        super().__init__()
        self.kullanici = kullanici
        from PyQt5.QtCore import QSettings
        self.ayarlar = QSettings("FitTrackPro", "BMIData")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Veritabanından mevcut sporcunun boy ve kilosunu çekiyoruz
        sporcu = db.sporcu_getir(self.kullanici['sporcu_id'])
        db_boy = sporcu.get('boy') if sporcu and sporcu.get('boy') else 170.0
        db_kilo = sporcu.get('kilo') if sporcu and sporcu.get('kilo') else 70.0

        # Apple tarzı dev siyah başlık
        baslik = QLabel("Vücut Ölçümleri")
        baslik.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {COLORS['text_main']};")
        layout.addWidget(baslik, alignment=Qt.AlignCenter)
        
        alt_baslik = QLabel("BMI (Vücut Kitle Endeksi) değerinizi anlık olarak takip edin.")
        alt_baslik.setStyleSheet(f"color: {COLORS['text_sub']}; font-size: 15px; font-weight: 600; margin-bottom: 20px;")
        layout.addWidget(alt_baslik, alignment=Qt.AlignCenter)

        # --- BEYAZ GÖLGELİ KART ---
        card = QFrame()
        card.setFixedWidth(550)
        card.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_card']}; border-radius: 24px; }}")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 12)) # %5 civarı çok yumuşak gölge
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)
        
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(40, 40, 40, 40)
        c_layout.setSpacing(25)

        input_lay = QHBoxLayout()
        input_lay.setSpacing(30)

        # Apple tarzı Input Stili (Oklar Gizlendi, Arkaplan Gri)
        input_style = f"""
            QDoubleSpinBox {{ 
                background-color: {COLORS['bg_input']}; 
                color: {COLORS['text_main']};
                border: none; 
                border-radius: 16px; 
                padding: 15px; 
                font-size: 28px; 
                font-weight: 800; 
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                width: 0px; 
                background: transparent;
            }}
        """

        # Boy Kutusu
        boy_lay = QVBoxLayout()
        boy_lay.setSpacing(10)
        boy_lbl = QLabel("Boy")
        boy_lbl.setStyleSheet(f"color: {COLORS['text_sub']}; font-size: 16px; font-weight: bold;")
        boy_lbl.setAlignment(Qt.AlignCenter)
        
        self.boy_inp = QDoubleSpinBox()
        self.boy_inp.setRange(100, 250)
        self.boy_inp.setSuffix(" cm")
        self.boy_inp.setValue(db_boy)
        self.boy_inp.setAlignment(Qt.AlignCenter)
        self.boy_inp.setStyleSheet(input_style)
        self.boy_inp.setCursor(Qt.PointingHandCursor)
        
        boy_lay.addWidget(boy_lbl)
        boy_lay.addWidget(self.boy_inp)

        # Kilo Kutusu
        kilo_lay = QVBoxLayout()
        kilo_lay.setSpacing(10)
        kilo_lbl = QLabel("Kilo")
        kilo_lbl.setStyleSheet(f"color: {COLORS['text_sub']}; font-size: 16px; font-weight: bold;")
        kilo_lbl.setAlignment(Qt.AlignCenter)
        
        self.kilo_inp = QDoubleSpinBox()
        self.kilo_inp.setRange(30, 300)
        self.kilo_inp.setSuffix(" kg")
        self.kilo_inp.setValue(db_kilo)
        self.kilo_inp.setAlignment(Qt.AlignCenter)
        self.kilo_inp.setStyleSheet(input_style)
        self.kilo_inp.setCursor(Qt.PointingHandCursor)
        
        kilo_lay.addWidget(kilo_lbl)
        kilo_lay.addWidget(self.kilo_inp)

        input_lay.addLayout(boy_lay)
        input_lay.addLayout(kilo_lay)
        c_layout.addLayout(input_lay)

        # --- CANLI HESAPLAMA BAĞLANTILARI ---
        self.boy_inp.valueChanged.connect(self._hesapla)
        self.kilo_inp.valueChanged.connect(self._hesapla)
        # ------------------------------------

        # Araya İnce Şık Bir Çizgi
        cizgi = QFrame(); cizgi.setFrameShape(QFrame.HLine)
        cizgi.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px; margin-top: 15px; margin-bottom: 15px;")
        c_layout.addWidget(cizgi)

        # Sonuç Alanları
        self.sonuc_lbl = QLabel("")
        self.sonuc_lbl.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(self.sonuc_lbl)

        self.durum_lbl = QLabel("")
        self.durum_lbl.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(self.durum_lbl)

        layout.addWidget(card)
        layout.addStretch()

        # Sayfa açıldığında ilk hesaplamayı otomatik yap
        self._hesapla()

    def _hesapla(self):
        kilo = self.kilo_inp.value()
        boy_m = self.boy_inp.value() / 100.0
        
        # Girilen değerleri hafızaya kaydet
        self.ayarlar.setValue("son_boy", self.boy_inp.value())
        self.ayarlar.setValue("son_kilo", kilo)

        # BMI Formülü
        bmi = kilo / (boy_m ** 2)

        if bmi < 18.5:
            durum, renk = "Zayıf", COLORS['info']
        elif 18.5 <= bmi < 24.9:
            durum, renk = "Normal Kilo", COLORS['success']
        elif 25 <= bmi < 29.9:
            durum, renk = "Fazla Kilolu", COLORS['warning']
        else:
            durum, renk = "Obez", COLORS['danger']

        # Kocaman modern BMI sonucu
        self.sonuc_lbl.setText(f"{bmi:.1f}")
        self.sonuc_lbl.setStyleSheet(f"font-size: 64px; font-weight: 900; color: {renk}; font-family: 'Segoe UI', sans-serif; background: transparent;")
        
        # Alt durum yazısı
        self.durum_lbl.setText(durum)
        self.durum_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {renk}; background: transparent;")

    def yenile(self):
        # Profil sayfasında değişen boy/kilo verilerini anlık olarak BMI sayfasına çeker
        sporcu = db.sporcu_getir(self.kullanici['sporcu_id'])
        if sporcu:
            db_boy = sporcu.get('boy') if sporcu.get('boy') else 170.0
            db_kilo = sporcu.get('kilo') if sporcu.get('kilo') else 70.0
            
            self.boy_inp.setValue(db_boy)
            self.kilo_inp.setValue(db_kilo)
            
        # Değerler güncellendikten sonra BMI sonucunu tekrar hesapla
        self._hesapla()

# ==========================================
# 6.2 ANTRENÖR SEÇME EKRANI
# ==========================================
class AntrenorSecWidget(QWidget):
    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici
        self.sporcu_id = kullanici['sporcu_id']
        self._setup_ui()

    def _setup_ui(self):
        # Ana dikey düzen: kenar boşlukları temayla uyumlu
        self.ana_layout = QVBoxLayout(self)
        self.ana_layout.setContentsMargins(30, 30, 30, 30)
        self.ana_layout.setSpacing(0)

        # ── Üst Başlık Bölümü ──────────────────────────────────────────────
        baslik = QLabel("Antrenörünü Seç")
        baslik.setStyleSheet(
            f"font-size: 32px; font-weight: 900; color: {COLORS['text_main']}; "
            f"letter-spacing: -0.5px;"
        )

        alt_baslik = QLabel(
            "Sana özel antrenman programı yazması için aşağıdaki uzmanlardan birini seçebilirsin."
        )
        alt_baslik.setStyleSheet(
            f"font-size: 14px; color: {COLORS['text_sub']}; font-weight: 500; margin-top: 4px;"
        )
        alt_baslik.setWordWrap(True)

        self.ana_layout.addWidget(baslik)
        self.ana_layout.addWidget(alt_baslik)
        self.ana_layout.addSpacing(24)

        # ── Aktif Antrenör Banner'ı (başlangıçta gizli) ────────────────────
        self.banner = QFrame()
        self.banner.setObjectName("activeBanner")
        self.banner.setStyleSheet(f"""
            QFrame#activeBanner {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent']}18, stop:1 {COLORS['success']}18);
                border: 1.5px solid {COLORS['success']}55;
                border-radius: 18px;
            }}
        """)
        banner_lay = QHBoxLayout(self.banner)
        banner_lay.setContentsMargins(22, 16, 22, 16)
        banner_lay.setSpacing(14)

        # Görsel: ANA_KLASOR/onay_ikon.png  (önerilen boyut: 32×32 px, PNG)
        ok_ikon = QLabel()
        ok_ikon.setFixedSize(28, 28)
        ok_ikon_yolu = f"{ANA_KLASOR}/onay_ikon.png"
        if os.path.exists(ok_ikon_yolu):
            pix = QPixmap(ok_ikon_yolu)
            if not pix.isNull():
                ok_ikon.setPixmap(
                    pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                ok_ikon.setText("✓")
                ok_ikon.setStyleSheet(f"color: {COLORS['success']}; font-size: 18px; font-weight: 900; background: transparent; border: none;")
        else:
            ok_ikon.setText("✓")
            ok_ikon.setStyleSheet(f"color: {COLORS['success']}; font-size: 18px; font-weight: 900; background: transparent; border: none;")
        ok_ikon.setAlignment(Qt.AlignCenter)
        if not ok_ikon.styleSheet():
            ok_ikon.setStyleSheet("background: transparent; border: none;")

        banner_yazi_lay = QVBoxLayout()
        banner_yazi_lay.setSpacing(2)
        self.banner_baslik = QLabel("Aktif Antrenörün")
        self.banner_baslik.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {COLORS['success']}; "
            f"background: transparent; border: none;"
        )
        self.banner_ad = QLabel("")
        self.banner_ad.setStyleSheet(
            f"font-size: 17px; font-weight: 800; color: {COLORS['text_main']}; "
            f"background: transparent; border: none;"
        )
        banner_yazi_lay.addWidget(self.banner_baslik)
        banner_yazi_lay.addWidget(self.banner_ad)

        self.bitir_btn = QPushButton("Anlaşmayı Bitir")
        self.bitir_btn.setFixedHeight(40)
        self.bitir_btn.setCursor(Qt.PointingHandCursor)
        self.bitir_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']}18;
                color: {COLORS['danger']};
                border: 1.5px solid {COLORS['danger']}55;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 700;
                padding: 0px 18px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
                border: 1.5px solid {COLORS['danger']};
            }}
        """)
        self.bitir_btn.clicked.connect(self._anlasmayi_bitir)

        banner_lay.addWidget(ok_ikon)
        banner_lay.addLayout(banner_yazi_lay)
        banner_lay.addStretch()
        banner_lay.addWidget(self.bitir_btn)

        self.banner.setVisible(False)
        self.ana_layout.addWidget(self.banner)
        self.ana_layout.addSpacing(20)

        # ── Kaydırılabilir Kart Alanı ──────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { width: 8px; background: transparent; }"
            "QScrollBar::handle:vertical { background: #D1D1D6; border-radius: 4px; }"
        )

        self.kart_container = QWidget()
        self.kart_container.setStyleSheet("background: transparent;")

        self.grid_lay = QGridLayout(self.kart_container)
        self.grid_lay.setSpacing(18)
        self.grid_lay.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll.setWidget(self.kart_container)
        self.ana_layout.addWidget(self.scroll)

        self.yenile()

    # ── Yardımcı: Tek Antrenör Kartı Oluştur ───────────────────────────────
    def _kart_olustur(self, antrenor, secili_mi):
        """Verilen antrenör verisinden Apple temalı bir kart QFrame döndürür."""

        kart = QFrame()
        kart.setFixedSize(260, 230)

        if secili_mi:
            kart.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border: 2px solid {COLORS['success']}88;
                    border-radius: 24px;
                }}
            """)
        else:
            kart.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 24px;
                }}
                QFrame:hover {{
                    border: 1.5px solid {COLORS['accent']}88;
                }}
            """)

        # Hafif gölge
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 12))
        shadow.setOffset(0, 6)
        kart.setGraphicsEffect(shadow)

        k_lay = QVBoxLayout(kart)
        k_lay.setContentsMargins(22, 22, 22, 18)
        k_lay.setSpacing(0)

        # ── Avatar / İkon alanı (Dinamik hale getirildi) ──────────────────────────
        avatar_cerceve = QFrame()
        avatar_cerceve.setFixedSize(64, 64)
        renk = COLORS['success'] if secili_mi else COLORS['accent']
        avatar_cerceve.setStyleSheet(f"""
            QFrame {{
                background-color: {renk}18;
                border-radius: 32px;
                border: 2px solid {renk}44;
            }}
        """)
        av_ic_lay = QHBoxLayout(avatar_cerceve)
        av_ic_lay.setContentsMargins(0, 0, 0, 0)

        avatar_lbl = QLabel()
        avatar_lbl.setAlignment(Qt.AlignCenter)
        avatar_lbl.setFixedSize(64, 64)
        
        # Veritabanından gelen avatarı al, yoksa varsayılanı kullan
        avatar_dosyasi = antrenor.get('avatar', 'varsayilan.png')
        if not avatar_dosyasi or avatar_dosyasi == "👤":
            avatar_dosyasi = "varsayilan.png"
            
        antrenor_ikon_yolu = f"{ANA_KLASOR}/{avatar_dosyasi}"
        
        if os.path.exists(antrenor_ikon_yolu):
            pix = QPixmap(antrenor_ikon_yolu)
            if not pix.isNull():
                # Resmi Apple tarzı daire içinde göster
                boyut = 56
                hedef = QPixmap(boyut, boyut)
                hedef.fill(Qt.transparent)
                kucuk = pix.scaled(boyut, boyut, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                cizer = QPainter(hedef)
                cizer.setRenderHint(QPainter.Antialiasing)
                yol = QPainterPath()
                yol.addEllipse(0, 0, boyut, boyut)
                cizer.setClipPath(yol)
                cizer.drawPixmap(0, 0, kucuk)
                cizer.end()
                avatar_lbl.setPixmap(hedef)
        else:
            # Resim dosyası bulunamazsa sembol göster
            avatar_lbl.setText("👤")
            avatar_lbl.setStyleSheet(f"color: {renk}; font-size: 24px; font-weight: bold;")

        av_ic_lay.addWidget(avatar_lbl)
        k_lay.addWidget(avatar_cerceve, alignment=Qt.AlignCenter)
        k_lay.addSpacing(14)
        
        # ── Ad Soyad ───────────────────────────────────────────────────────
        ad_lbl = QLabel(f"{antrenor['ad']} {antrenor['soyad']}")
        ad_lbl.setStyleSheet(
            f"font-size: 16px; font-weight: 800; color: {COLORS['text_main']}; "
            f"background: transparent; border: none;"
        )
        ad_lbl.setWordWrap(True)
        k_lay.addWidget(ad_lbl)
        k_lay.addSpacing(6)

        # ── Uzmanlık Rozeti ────────────────────────────────────────────────
        uzmanlik_cerceve = QFrame()
        uzmanlik_cerceve.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['info']}14;
                border-radius: 8px;
                border: none;
            }}
        """)
        uz_lay = QHBoxLayout(uzmanlik_cerceve)
        uz_lay.setContentsMargins(10, 5, 10, 5)

        # Görsel: ANA_KLASOR/uzmanlik_ikon.png  (önerilen boyut: 16×16 px, PNG)
        uzmanlik_ic_lay = QHBoxLayout()
        uzmanlik_ic_lay.setContentsMargins(0, 0, 0, 0)
        uzmanlik_ic_lay.setSpacing(6)

        uzmanlik_ikon_lbl = QLabel()
        uzmanlik_ikon_lbl.setFixedSize(16, 16)
        uzmanlik_ikon_lbl.setStyleSheet("background: transparent; border: none;")
        uz_ikon_yolu = f"{ANA_KLASOR}/uzmanlik_ikon.png"
        if os.path.exists(uz_ikon_yolu):
            p = QPixmap(uz_ikon_yolu)
            if not p.isNull():
                uzmanlik_ikon_lbl.setPixmap(
                    p.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

        uzmanlik_lbl = QLabel(antrenor['bolum'])
        uzmanlik_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {COLORS['info']}; "
            f"background: transparent; border: none;"
        )
        uzmanlik_ic_lay.addWidget(uzmanlik_ikon_lbl)
        uzmanlik_ic_lay.addWidget(uzmanlik_lbl)
        uz_lay.addLayout(uzmanlik_ic_lay)

        k_lay.addWidget(uzmanlik_cerceve)
        k_lay.addSpacing(6)

        # ── Deneyim Bilgisi ────────────────────────────────────────────────
        # Görsel: ANA_KLASOR/deneyim_ikon.png  (önerilen boyut: 16×16 px, PNG)
        deneyim_row = QHBoxLayout()
        deneyim_row.setContentsMargins(0, 0, 0, 0)
        deneyim_row.setSpacing(6)

        deneyim_ikon_lbl = QLabel()
        deneyim_ikon_lbl.setFixedSize(16, 16)
        deneyim_ikon_lbl.setStyleSheet("background: transparent; border: none;")
        den_ikon_yolu = f"{ANA_KLASOR}/deneyim_ikon.png"
        if os.path.exists(den_ikon_yolu):
            p2 = QPixmap(den_ikon_yolu)
            if not p2.isNull():
                deneyim_ikon_lbl.setPixmap(
                    p2.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

        deneyim_lbl = QLabel(f"{antrenor['deneyim_yili']} Yıl Deneyim")
        deneyim_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 500; color: {COLORS['text_sub']}; "
            f"background: transparent; border: none;"
        )
        deneyim_row.addWidget(deneyim_ikon_lbl)
        deneyim_row.addWidget(deneyim_lbl)
        deneyim_row.addStretch()
        k_lay.addLayout(deneyim_row)
        k_lay.addStretch()

        # ── Seç / Seçili Butonu ────────────────────────────────────────────
        if secili_mi:
            sec_btn = QPushButton("Seçili Antrenörün")
            sec_btn.setEnabled(False)
            sec_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['success']};
                    color: white;
                    border: none;
                    border-radius: 14px;
                    font-size: 13px;
                    font-weight: 700;
                    padding: 10px 0px;
                }}
            """)
        else:
            sec_btn = QPushButton("Bu Antrenörü Seç")
            sec_btn.setCursor(Qt.PointingHandCursor)
            sec_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: white;
                    border: none;
                    border-radius: 14px;
                    font-size: 13px;
                    font-weight: 700;
                    padding: 10px 0px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                }}
            """)
            sec_btn.clicked.connect(
                lambda _, aid=antrenor['kullanici_id']: self._sec(aid)
            )

        sec_btn.setFixedHeight(42)
        k_lay.addWidget(sec_btn)

        return kart

    def yenile(self):
        # Eski kartları temizle
        for i in reversed(range(self.grid_lay.count())):
            w = self.grid_lay.itemAt(i).widget()
            if w:
                w.deleteLater()

        antrenorler = db.onayli_antrenorleri_getir()
        mevcut_aid = db.mevcut_antrenor_id(self.sporcu_id)

        # ── Banner güncelle ────────────────────────────────────────────────
        if mevcut_aid is not None:
            mevcut = next(
                (a for a in antrenorler if a['kullanici_id'] == mevcut_aid), None
            )
            if mevcut:
                self.banner_ad.setText(f"{mevcut['ad']} {mevcut['soyad']}  ·  {mevcut['bolum']}")
            self.banner.setVisible(True)
        else:
            self.banner.setVisible(False)

        # ── Kartları yerleştir ─────────────────────────────────────────────
        if not antrenorler:
            bos = QLabel("Henüz onaylı antrenör bulunmuyor.")
            bos.setStyleSheet(
                f"color: {COLORS['text_sub']}; font-size: 16px; font-weight: 500;"
            )
            bos.setAlignment(Qt.AlignCenter)
            self.grid_lay.addWidget(bos, 0, 0)
            return

        SUTUN = 3
        for idx, a in enumerate(antrenorler):
            secili_mi = (a['kullanici_id'] == mevcut_aid)
            kart = self._kart_olustur(a, secili_mi)
            self.grid_lay.addWidget(kart, idx // SUTUN, idx % SUTUN)

    def _sec(self, aid):
        db.antrenor_sec(self.sporcu_id, aid)
        db.log_ekle(
            "Antrenör Seçimi",
            f"Sporcu (ID:{self.sporcu_id}), Antrenör (ID:{aid}) ile çalışmaya başladı."
        )
        AppleMesajDialog.bilgi(
            self, "Antrenör Seçildi",
            "Antrenörün başarıyla seçildi. Artık sana özel program yazabilir."
        )
        self.yenile()

    def _anlasmayi_bitir(self):
        if AppleMesajDialog.soru(
            self, "Anlaşmayı Bitir",
            "Antrenörünüzle olan anlaşmayı bitirmek istediğinize emin misiniz?"
        ):
            aid = db.mevcut_antrenor_id(self.sporcu_id)
            if aid:
                conn = db.get_connection()
                conn.execute("DELETE FROM sporcu_antrenor WHERE sporcu_id=?", (self.sporcu_id,))
                conn.commit()
                conn.close()
                db.log_ekle(
                    "Antrenör İptali",
                    f"Sporcu (ID:{self.sporcu_id}), Antrenör (ID:{aid}) ile anlaşmasını bitirdi."
                )
            AppleMesajDialog.bilgi(self, "Anlaşma Sona Erdi", "Antrenörünüzle olan anlaşmanız başarıyla sonlandırıldı.")
            self.yenile()

# ==========================================
# 6.6b SPORCU GÜNLÜK PROGRAM DETAY DİYALOĞU
# Aktivite takviminde bir güne tıklandığında açılır.
# Her hareketi görsel + set/tekrar/süre chip'leriyle gösterir.
# ==========================================
class SporcuGunlukDetayDialog(QDialog):
    def __init__(self, tarih_str, program_listesi, parent=None):
        super().__init__(parent)
        self.tarih_str = tarih_str
        self.program_listesi = program_listesi
        self.setWindowTitle(f"{tarih_str} — Günlük Program")
        self.setMinimumWidth(480)
        self.setStyleSheet(APPLE_THEME)
        self._setup_ui()

    def _setup_ui(self):
        import re as _re
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Başlık
        try:
            dt = datetime.strptime(self.tarih_str, "%Y-%m-%d")
            TURKCE_AYLAR = {1:"Ocak",2:"Şubat",3:"Mart",4:"Nisan",5:"Mayıs",
                            6:"Haziran",7:"Temmuz",8:"Ağustos",9:"Eylül",
                            10:"Ekim",11:"Kasım",12:"Aralık"}
            tarih_goster = f"{dt.day} {TURKCE_AYLAR[dt.month]} {dt.year}"
        except:
            tarih_goster = self.tarih_str

        baslik = QLabel(tarih_goster)
        baslik.setStyleSheet(f"font-size:22px;font-weight:900;color:{COLORS['text_main']};background:transparent;")
        alt = QLabel(f"{len(self.program_listesi)} hareket")
        alt.setStyleSheet(f"font-size:14px;color:{COLORS['text_sub']};background:transparent;")
        layout.addWidget(baslik)
        layout.addWidget(alt)

        cizgi = QFrame(); cizgi.setFrameShape(QFrame.HLine)
        cizgi.setStyleSheet(f"background-color:{COLORS['border']};max-height:1px;")
        layout.addWidget(cizgi)

        # Scroll alanı
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;} QScrollBar:vertical{width:6px;background:transparent;} QScrollBar::handle:vertical{background:#C7C7CC;border-radius:3px;min-height:30px;} QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}")
        ic = QWidget(); ic.setStyleSheet(f"background:transparent;")
        ic_lay = QVBoxLayout(ic); ic_lay.setContentsMargins(0,4,0,4); ic_lay.setSpacing(12)

        tum_eg = db.egzersizleri_getir()

        for program_metni in self.program_listesi:
            # Eşleşen egzersizi bul
            eslesen_eg = None
            for eg in tum_eg:
                if eg['ad'].lower() in program_metni.lower():
                    eslesen_eg = eg
                    break

            satir = QFrame()
            satir.setStyleSheet(f"""QFrame{{
                background-color:{COLORS['bg_card']};
                border:1.5px solid {COLORS['border']};
                border-left:4px solid {COLORS['accent']};
                border-radius:16px;
            }}""")
            satir_lay = QHBoxLayout(satir); satir_lay.setContentsMargins(0,0,16,0); satir_lay.setSpacing(0)

            # Görsel
            foto_lbl = QLabel()
            foto_lbl.setFixedSize(76, 76)
            foto_lbl.setAlignment(Qt.AlignCenter)
            gorsel_yuklendi = False
            if eslesen_eg:
                ad_dosya = eslesen_eg['ad'].lower().replace(' ','_').replace('/','_').replace('ş','s').replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ç','c')
                klasor = os.path.join(ANA_KLASOR, "egzersiz_gorselleri")
                foto_yol = os.path.join(klasor, f"{ad_dosya}.jpg")
                if not os.path.exists(foto_yol):
                    foto_yol = os.path.join(klasor, f"{ad_dosya}.png")
                if os.path.exists(foto_yol):
                    pix = QPixmap(foto_yol).scaled(76, 76, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    hedef = QPixmap(76, 76); hedef.fill(Qt.transparent)
                    p = QPainter(hedef); p.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath(); path.addRoundedRect(0,0,76,76,12,12)
                    p.setClipPath(path); p.drawPixmap((76-pix.width())//2,(76-pix.height())//2,pix); p.end()
                    foto_lbl.setPixmap(hedef)
                    foto_lbl.setStyleSheet("background:transparent;border:none;margin:10px 8px 10px 12px;")
                    gorsel_yuklendi = True
                    # Tıklanınca büyüt
                    _tam_pix = QPixmap(foto_yol)
                    _eg_ad = eslesen_eg['ad']
                    foto_lbl.setCursor(Qt.PointingHandCursor)
                    foto_lbl.setToolTip("Büyütmek için tıklayın")
                    foto_lbl.mousePressEvent = lambda _ev, px=_tam_pix, ad=_eg_ad: GorselZoomDialog.goster(px, ad, self)
            if not gorsel_yuklendi:
                harf = (eslesen_eg['ad'][0] if eslesen_eg else program_metni[0]).upper()
                foto_lbl.setText(harf)
                foto_lbl.setStyleSheet(f"background-color:{COLORS['accent']}18;color:{COLORS['accent']};border-radius:12px;font-size:24px;font-weight:900;margin:10px 8px 10px 12px;")
            satir_lay.addWidget(foto_lbl)

            # Metin bilgisi
            bilgi_lay = QVBoxLayout(); bilgi_lay.setSpacing(5); bilgi_lay.setContentsMargins(4,12,0,12)

            # Egzersiz adı
            ad_txt = eslesen_eg['ad'] if eslesen_eg else program_metni
            ad_lbl = QLabel(ad_txt)
            ad_lbl.setStyleSheet(f"font-size:15px;font-weight:800;color:{COLORS['text_main']};background:transparent;border:none;")
            bilgi_lay.addWidget(ad_lbl)

            # Kas grubu (varsa)
            if eslesen_eg and eslesen_eg.get('kas_grubu'):
                kas_lbl = QLabel(f"💪  {eslesen_eg['kas_grubu']}")
                kas_lbl.setStyleSheet(f"font-size:12px;font-weight:600;color:{COLORS['text_sub']};background:transparent;border:none;")
                bilgi_lay.addWidget(kas_lbl)

            # Chip'ler
            chip_row = QHBoxLayout(); chip_row.setSpacing(6); chip_row.setContentsMargins(0,0,0,0)
            chip_s = "font-size:12px;font-weight:700;padding:3px 10px;border-radius:10px;border:none;"

            set_tekrar_m = _re.search(r'(\d+)\s*[×x]\s*(\d+)', program_metni)
            sure_m       = _re.search(r'(\d+)\s*dk', program_metni, _re.IGNORECASE)
            agirlik_m    = _re.search(r'(\d+(?:\.\d+)?)\s*kg', program_metni, _re.IGNORECASE)

            if set_tekrar_m:
                c = QLabel(f"🔁  {set_tekrar_m.group(1)} set × {set_tekrar_m.group(2)} tekrar")
                c.setStyleSheet(chip_s + f"background-color:{COLORS['info']}18;color:{COLORS['info']};")
                chip_row.addWidget(c)
            if agirlik_m:
                c = QLabel(f"⚖️  {agirlik_m.group(1)} kg")
                c.setStyleSheet(chip_s + f"background-color:{COLORS['accent']}15;color:{COLORS['accent']};")
                chip_row.addWidget(c)
            if sure_m:
                c = QLabel(f"⏱  {sure_m.group(1)} dk")
                c.setStyleSheet(chip_s + f"background-color:{COLORS['success']}18;color:{COLORS['success']};")
                chip_row.addWidget(c)
            if not (set_tekrar_m or agirlik_m or sure_m):
                c = QLabel(program_metni)
                c.setStyleSheet(f"font-size:12px;color:{COLORS['text_sub']};background:transparent;border:none;")
                chip_row.addWidget(c)

            chip_row.addStretch()
            bilgi_lay.addLayout(chip_row)
            satir_lay.addLayout(bilgi_lay, stretch=1)
            ic_lay.addWidget(satir)

        ic_lay.addStretch()
        scroll.setWidget(ic)
        layout.addWidget(scroll)

        kapat_btn = QPushButton("Kapat")
        kapat_btn.setFixedHeight(46); kapat_btn.setCursor(Qt.PointingHandCursor)
        kapat_btn.clicked.connect(self.accept)
        layout.addWidget(kapat_btn)


# ==========================================
# 6.7 GOOGLE TAKVİM EKRANI (Gerçek Veri)
# ==========================================
class TakvimWidget(QWidget):
    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici
        self.sporcu_id = kullanici.get('sporcu_id')
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self.ay_label = QLabel()
        self.ay_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['accent']};")
        self.layout.addWidget(self.ay_label)
        
        self.grid = QGridLayout()
        self.grid.setSpacing(5)
        self.layout.addLayout(self.grid)
        self.layout.addStretch()
        self.yenile()

    def yenile(self):
        import random
        import calendar

        TURKCE_AYLAR = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
            5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
            9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }

        suan = datetime.now()
        ay_adi = TURKCE_AYLAR[suan.month]
        self.ay_label.setText(f"{ay_adi} {suan.year} Antrenman Takvimi")

        # Önceki takvimi temizle
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.deleteLater()

        yil_ay = suan.strftime("%Y-%m")
        programlar_sozlugu = db.takvim_programlari_getir(self.sporcu_id, yil_ay)

        gunler = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        for i, gun in enumerate(gunler):
            lbl = QLabel(gun)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; color: #888; padding: 10px;")
            self.grid.addWidget(lbl, 0, i)

        baslangic_gunu = suan.replace(day=1).weekday()
        # Ayın gerçek gün sayısını hesapla (28/29/30/31)
        ayin_gun_sayisi = calendar.monthrange(suan.year, suan.month)[1]
        gun_sayaci = 1

        renk_paleti = [
            '#6c63ff', '#27ae60', '#e74c3c', '#f39c12',
            '#3498db', '#9b59b6', '#e67e22', '#00cec9', '#d63031'
        ]

        bugun_str = suan.strftime("%Y-%m-%d")

        for row in range(1, 7):
            for col in range(7):
                if row == 1 and col < baslangic_gunu:
                    continue
                if gun_sayaci > ayin_gun_sayisi:
                    continue

                tarih_str = f"{suan.year}-{suan.month:02d}-{gun_sayaci:02d}"

                # Bugünü vurgula
                bugun_mu = (tarih_str == bugun_str)
                if bugun_mu:
                    cerceve_rengi = COLORS['accent']
                    arka_plan = f"{COLORS['accent']}10"
                else:
                    cerceve_rengi = COLORS['border']
                    arka_plan = COLORS['bg_secondary']

                gun_kutusu = QFrame()
                gun_kutusu.setMinimumSize(120, 100)
                gun_kutusu.setStyleSheet(f"""QFrame {{
                    background-color: {arka_plan};
                    border: {'2px' if bugun_mu else '1px'} solid {cerceve_rengi};
                    border-radius: 8px;
                }} QFrame:hover {{ border-color: {COLORS['accent']}; }}""")

                kutu_lay = QVBoxLayout(gun_kutusu)
                kutu_lay.setContentsMargins(5, 5, 5, 5)
                kutu_lay.setSpacing(4)

                gun_no = QLabel(str(gun_sayaci))
                gun_no_renk = COLORS['accent'] if bugun_mu else "#aaa"
                gun_no.setStyleSheet(f"color: {gun_no_renk}; font-size: 14px; font-weight: bold; border: none; background: transparent;")
                kutu_lay.addWidget(gun_no, alignment=Qt.AlignTop)

                if tarih_str in programlar_sozlugu:
                    for detay in programlar_sozlugu[tarih_str]:
                        rastgele_renk = random.choice(renk_paleti)
                        prog_etiket = QLabel(detay)
                        prog_etiket.setWordWrap(True)
                        prog_etiket.setStyleSheet(f"background-color: {rastgele_renk}; color: white; border-radius: 4px; font-size: 11px; padding: 6px; border: none;")
                        kutu_lay.addWidget(prog_etiket)

                kutu_lay.addStretch()

                # Tıklanabilir yap: program olan günlerde detay popup'ı aç
                if tarih_str in programlar_sozlugu:
                    gun_kutusu.setCursor(Qt.PointingHandCursor)
                    _t = tarih_str
                    _p = programlar_sozlugu[tarih_str]
                    gun_kutusu.mousePressEvent = lambda event, t=_t, pl=_p: self._gun_detay_ac(t, pl)

                self.grid.addWidget(gun_kutusu, row, col)
                gun_sayaci += 1

    def _gun_detay_ac(self, tarih_str, program_listesi):
        dialog = SporcuGunlukDetayDialog(tarih_str, program_listesi, self)
        dialog.exec_()


# ==========================================
# 6.7 ANTRENÖR PANELİ (Öğrencilerim ve Yaka Kartı Tasarımı)
# ==========================================

# --- 1. Tıklanabilir Özel Kutu (Takvim Günleri İçin) ---
class TiklanabilirKutu(QFrame):
    tiklandi = pyqtSignal()
    def mousePressEvent(self, event):
        self.tiklandi.emit()
        super().mousePressEvent(event)

# --- 2. Günlük Program Ekleme/Düzenleme Pop-up'ı ---
# --- 2. Günlük Program Ekleme/Düzenleme Pop-up'ı (Akıllı Kilit Sistemli) ---
class GunlukProgramDialog(QDialog):
    def __init__(self, sporcu_id, antrenor_id, tarih_str, sporcu_ad):
        super().__init__()
        self.sporcu_id   = sporcu_id
        self.antrenor_id = antrenor_id
        self.tarih_str   = tarih_str
        self.setWindowTitle(f"{sporcu_ad} — {tarih_str} Programı")
        self.setMinimumSize(560, 620)
        self.setStyleSheet(APPLE_THEME)
        bugun_str = datetime.now().strftime("%Y-%m-%d")
        self.gecmis_mi = (self.tarih_str < bugun_str)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        if self.gecmis_mi:
            baslik = QLabel(f"🔒  {self.tarih_str} — Geçmiş Program")
            baslik.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text_sub']};")
        else:
            baslik = QLabel(f"📅  {self.tarih_str} — Program Yaz")
            baslik.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text_main']};")
        layout.addWidget(baslik)

        # Mevcut program listesi
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.liste_icerik = QWidget()
        self.liste_icerik.setStyleSheet("background: transparent;")
        self.liste_lay = QVBoxLayout(self.liste_icerik)
        self.liste_lay.setAlignment(Qt.AlignTop)
        self.liste_lay.setSpacing(8)
        self.scroll.setWidget(self.liste_icerik)
        layout.addWidget(self.scroll, stretch=1)

        if not self.gecmis_mi:
            cizgi = QFrame(); cizgi.setFrameShape(QFrame.HLine)
            cizgi.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
            layout.addWidget(cizgi)

            ekle_lbl = QLabel("Hareket Ekle")
            ekle_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['text_sub']};")
            layout.addWidget(ekle_lbl)

            # --- Chip stilleri ---
            self._cks   = f"QPushButton{{background:{COLORS['bg_input']};color:{COLORS['text_sub']};border:1.5px solid transparent;border-radius:14px;font-size:11px;font-weight:600;padding:4px 12px;}} QPushButton:hover{{background:{COLORS['accent']}15;color:{COLORS['accent']};}}"
            self._cks_a = f"QPushButton{{background:{COLORS['accent']};color:white;border:1.5px solid {COLORS['accent']};border-radius:14px;font-size:11px;font-weight:700;padding:4px 12px;}}"
            self._hks   = f"QPushButton{{background:{COLORS['bg_input']};color:{COLORS['text_main']};border:1.5px solid transparent;border-radius:10px;font-size:12px;font-weight:600;padding:5px 10px;}} QPushButton:hover{{background:{COLORS['accent']}15;color:{COLORS['accent']};}}"
            self._hks_a = f"QPushButton{{background:{COLORS['accent']};color:white;border:1.5px solid {COLORS['accent']};border-radius:10px;font-size:12px;font-weight:700;padding:5px 10px;}}"
            self._aktif_kat_btn = None
            self._aktif_har_btn = None
            self._aktif_har_idx = -1
            self._egzersizler   = []

            # Kategori chip satırı
            kat_scroll = QScrollArea(); kat_scroll.setFixedHeight(38)
            kat_scroll.setWidgetResizable(True); kat_scroll.setFrameShape(QFrame.NoFrame)
            kat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            kat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            kat_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
            kat_ic = QWidget(); kat_ic.setStyleSheet("background:transparent;")
            kat_ic_lay = QHBoxLayout(kat_ic); kat_ic_lay.setContentsMargins(0,0,0,0); kat_ic_lay.setSpacing(6)
            btn_tumu = QPushButton("Tümü"); btn_tumu.setCursor(Qt.PointingHandCursor)
            btn_tumu.setStyleSheet(self._cks_a); self._aktif_kat_btn = btn_tumu
            btn_tumu.clicked.connect(lambda: self._p_kat_degisti("Tüm Kategoriler", btn_tumu))
            kat_ic_lay.addWidget(btn_tumu)
            for k in db.egzersiz_kategorileri():
                b = QPushButton(k); b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(self._cks)
                b.clicked.connect(lambda _, kat=k, xb=b: self._p_kat_degisti(kat, xb))
                kat_ic_lay.addWidget(b)
            kat_ic_lay.addStretch(); kat_scroll.setWidget(kat_ic)
            layout.addWidget(kat_scroll)

            # Hareket chip grid — sürüklenebilir + scrollbar'lı
            self.p_har_scroll = SuruklenebilirScroll()
            self.p_har_scroll.setFixedHeight(150)
            self.p_har_ic = QWidget(); self.p_har_ic.setStyleSheet("background:transparent;")
            self.p_har_lay = QGridLayout(self.p_har_ic)
            self.p_har_lay.setContentsMargins(0,0,0,0); self.p_har_lay.setSpacing(6)
            self.p_har_scroll.setWidget(self.p_har_ic)
            layout.addWidget(self.p_har_scroll)

            # Seçili hareket bilgi kartı (foto + kas + açıklama)
            self.p_bilgi = QFrame()
            self.p_bilgi.setStyleSheet(f"QFrame{{background:#4A5E2A;border-radius:12px;border:none;}}")
            self.p_bilgi.setVisible(False)
            pb_lay = QHBoxLayout(self.p_bilgi); pb_lay.setContentsMargins(12,12,12,12); pb_lay.setSpacing(14)
            self.p_foto = QLabel(); self.p_foto.setFixedSize(80, 80)
            self.p_foto.setAlignment(Qt.AlignCenter)
            self.p_foto.setStyleSheet(f"background:rgba(255,255,255,0.15);border-radius:10px;color:rgba(255,255,255,0.6);font-size:10px;")
            pb_lay.addWidget(self.p_foto)
            pb_metin = QVBoxLayout(); pb_metin.setSpacing(3)
            self.p_ad_lbl  = QLabel(); self.p_ad_lbl.setStyleSheet(f"font-size:14px;font-weight:800;color:white;background:transparent;")
            self.p_kas_lbl = QLabel(); self.p_kas_lbl.setStyleSheet(f"font-size:11px;font-weight:600;color:#FFD580;background:transparent;")
            self.p_acik_lbl = QLabel(); self.p_acik_lbl.setWordWrap(True)
            self.p_acik_lbl.setStyleSheet(f"font-size:11px;color:rgba(255,255,255,0.75);background:transparent;")
            pb_metin.addWidget(self.p_ad_lbl); pb_metin.addWidget(self.p_kas_lbl)
            pb_metin.addWidget(self.p_acik_lbl); pb_metin.addStretch()
            pb_lay.addLayout(pb_metin, stretch=1)
            layout.addWidget(self.p_bilgi)

            # Set / Tekrar / Ağırlık
            spin_style = f"""
                QSpinBox, QDoubleSpinBox {{
                    background-color: {COLORS['bg_input']}; color: {COLORS['text_main']};
                    border: 2px solid transparent; border-radius: 10px;
                    padding: 8px 10px; font-size: 14px; font-weight: 700;
                }}
                QSpinBox:focus, QDoubleSpinBox:focus {{ border: 2px solid {COLORS['accent']}55; }}
                QSpinBox::up-button, QSpinBox::down-button,
                QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; }}
            """
            lbl_s = f"color: {COLORS['text_sub']}; font-size: 12px; font-weight: 700; background: transparent;"
            form_row = QHBoxLayout(); form_row.setSpacing(10)

            def p_sarili_blok(lbl_txt, widget):
                w = QWidget(); w.setStyleSheet("background:transparent;")
                b = QVBoxLayout(w); b.setContentsMargins(0,0,0,0); b.setSpacing(4)
                b.addWidget(QLabel(lbl_txt, styleSheet=lbl_s))
                b.addWidget(widget)
                return w

            self.set_spin = QSpinBox(); self.set_spin.setRange(1, 20); self.set_spin.setValue(3); self.set_spin.setStyleSheet(spin_style)
            self.tekrar_spin = QSpinBox(); self.tekrar_spin.setRange(1, 100); self.tekrar_spin.setValue(12); self.tekrar_spin.setStyleSheet(spin_style)
            self.agirlik_spin = QDoubleSpinBox(); self.agirlik_spin.setRange(0, 500); self.agirlik_spin.setValue(0)
            self.agirlik_spin.setSuffix(" kg"); self.agirlik_spin.setStyleSheet(spin_style)
            self.p_sure_spin = QSpinBox(); self.p_sure_spin.setRange(1, 180); self.p_sure_spin.setValue(5)
            self.p_sure_spin.setSuffix(" dk"); self.p_sure_spin.setStyleSheet(spin_style)

            self._p_blok_set     = p_sarili_blok("SET",         self.set_spin)
            self._p_blok_tekrar  = p_sarili_blok("TEKRAR",      self.tekrar_spin)
            self._p_blok_agirlik = p_sarili_blok("AĞIRLIK (kg)", self.agirlik_spin)
            self._p_blok_sure    = p_sarili_blok("SÜRE",        self.p_sure_spin)

            form_row.addWidget(self._p_blok_set)
            form_row.addWidget(self._p_blok_tekrar)
            form_row.addWidget(self._p_blok_agirlik)
            form_row.addWidget(self._p_blok_sure)
            layout.addLayout(form_row)

            ekle_btn = QPushButton("＋  Programa Ekle")
            ekle_btn.setFixedHeight(48); ekle_btn.setCursor(Qt.PointingHandCursor)
            ekle_btn.setStyleSheet(f"QPushButton{{background:{COLORS['accent']};color:white;border:none;border-radius:24px;font-size:15px;font-weight:800;}} QPushButton:hover{{background:{COLORS['accent_hover']};}}")
            ekle_btn.clicked.connect(self._ekle)
            layout.addWidget(ekle_btn)

            self._p_kat_degisti("Tüm Kategoriler", btn_tumu)
        else:
            bilgi = QLabel("Bu tarih geçmişte kaldığı için değişiklik yapılamaz.")
            bilgi.setStyleSheet(f"color: {COLORS['text_sub']}; font-style: italic; font-size: 13px;")
            bilgi.setAlignment(Qt.AlignCenter)
            layout.addWidget(bilgi)

        self._yukle()

    def _p_kat_degisti(self, kat, btn=None):
        if self._aktif_kat_btn: self._aktif_kat_btn.setStyleSheet(self._cks)
        if btn: btn.setStyleSheet(self._cks_a); self._aktif_kat_btn = btn

        while self.p_har_lay.count():
            item = self.p_har_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self._egzersizler = db.egzersizleri_getir(None if kat == "Tüm Kategoriler" else kat)
        self._aktif_har_idx = -1; self._aktif_har_btn = None
        self.p_bilgi.setVisible(False)

        for i, e in enumerate(self._egzersizler):
            b = QPushButton(e['ad']); b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(self._hks)
            b.clicked.connect(lambda _, idx=i, xb=b: self._p_har_sec(idx, xb))
            self.p_har_lay.addWidget(b, i // 3, i % 3)

        if self._egzersizler:
            ilk = self.p_har_lay.itemAt(0)
            if ilk and ilk.widget(): self._p_har_sec(0, ilk.widget())

    def _p_form_alanlari_guncelle(self, tip: str):
        """Antrenör dialog form alanlarını hareket tipine göre göster/gizle."""
        try:
            self._p_blok_set.setVisible(tip in ("agirlik", "vucutagirlik", "izometrik"))
            self._p_blok_tekrar.setVisible(tip in ("agirlik", "vucutagirlik"))
            self._p_blok_agirlik.setVisible(tip == "agirlik")
            self._p_blok_sure.setVisible(tip in ("kardiyo", "izometrik"))
        except AttributeError:
            pass

    def _p_har_sec(self, idx, btn):
        if self._aktif_har_btn: self._aktif_har_btn.setStyleSheet(self._hks)
        btn.setStyleSheet(self._hks_a)
        self._aktif_har_btn = btn; self._aktif_har_idx = idx

        if 0 <= idx < len(self._egzersizler):
            e = self._egzersizler[idx]
            self.p_ad_lbl.setText(e['ad'])
            self.p_kas_lbl.setText("💪  " + (e.get('kas_grubu') or ''))
            self.p_acik_lbl.setText(e.get('aciklama') or '')

            ad_dosya = e['ad'].lower().replace(' ','_').replace('/','_').replace('ş','s').replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ç','c')
            klasor = os.path.join(ANA_KLASOR, "egzersiz_gorselleri")
            foto_yol = os.path.join(klasor, f"{ad_dosya}.jpg")
            if not os.path.exists(foto_yol):
                foto_yol = os.path.join(klasor, f"{ad_dosya}.png")

            if os.path.exists(foto_yol):
                pix = QPixmap(foto_yol).scaled(80, 80, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                hedef = QPixmap(80, 80); hedef.fill(Qt.transparent)
                p = QPainter(hedef); p.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath(); path.addRoundedRect(0, 0, 80, 80, 10, 10)
                p.setClipPath(path); p.drawPixmap((80-pix.width())//2, (80-pix.height())//2, pix); p.end()
                self.p_foto.setPixmap(hedef); self.p_foto.setText("")
                # Tıklanınca büyüt
                _tam_pix = QPixmap(foto_yol)
                _eg_ad = e['ad']
                self.p_foto.setCursor(Qt.PointingHandCursor)
                self.p_foto.setToolTip("Büyütmek için tıklayın")
                self.p_foto.mousePressEvent = lambda _ev, px=_tam_pix, ad=_eg_ad: GorselZoomDialog.goster(px, ad, self)
            else:
                self.p_foto.setPixmap(QPixmap()); self.p_foto.setText("Görsel eklenmemiş")
                self.p_foto.setCursor(Qt.ArrowCursor)
                self.p_foto.mousePressEvent = lambda _ev: None
                self.p_foto.setToolTip("")

            self.p_bilgi.setVisible(True)

            # Hareket tipine göre form alanlarını göster/gizle
            tip = hareket_tipi_al(e['ad'])
            self._p_form_alanlari_guncelle(tip)

    def _yukle(self):
        for i in reversed(range(self.liste_lay.count())):
            w = self.liste_lay.itemAt(i).widget()
            if w: w.deleteLater()

        conn = db.get_connection()
        rows = conn.execute("SELECT id, program_detay FROM antrenman_programi WHERE sporcu_id=? AND tarih=? ORDER BY id", (self.sporcu_id, self.tarih_str)).fetchall()
        conn.close()

        if not rows:
            bos = QLabel("Henüz bu güne program eklenmemiş.")
            bos.setStyleSheet(f"color: {COLORS['text_sub']}; font-size: 13px; background: transparent; padding: 16px;")
            bos.setAlignment(Qt.AlignCenter)
            self.liste_lay.addWidget(bos)
            return

        for r in rows:
            kart = QFrame()
            kart.setStyleSheet(f"""QFrame {{
                background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}""")
            k_lay = QHBoxLayout(kart)
            k_lay.setContentsMargins(16, 12, 12, 12)

            # Sol renkli şerit
            serit = QFrame(); serit.setFixedWidth(4)
            serit.setStyleSheet(f"background-color: {COLORS['accent']}; border-radius: 2px;")
            k_lay.addWidget(serit)
            k_lay.addSpacing(8)

            detay_lbl = QLabel(r['program_detay'])
            detay_lbl.setWordWrap(True)
            renk = COLORS['text_sub'] if self.gecmis_mi else COLORS['text_main']
            detay_lbl.setStyleSheet(f"border: none; color: {renk}; font-size: 14px; font-weight: 600; background: transparent;")
            k_lay.addWidget(detay_lbl, stretch=1)

            if not self.gecmis_mi:
                sil_btn = QPushButton("✕")
                sil_btn.setFixedSize(32, 32)
                sil_btn.setCursor(Qt.PointingHandCursor)
                sil_btn.setStyleSheet(f"""QPushButton {{
                    background-color: {COLORS['danger']}18; color: {COLORS['danger']};
                    border: none; border-radius: 16px; font-size: 13px; font-weight: 700;
                }} QPushButton:hover {{ background-color: {COLORS['danger']}; color: white; }}""")
                sil_btn.clicked.connect(lambda _, pid=r['id']: self._sil(pid))
                k_lay.addWidget(sil_btn)

            self.liste_lay.addWidget(kart)

    def _ekle(self):
        idx = getattr(self, '_aktif_har_idx', -1)
        if idx < 0 or not self._egzersizler:
            return
        egzersiz = self._egzersizler[idx]
        tip = hareket_tipi_al(egzersiz['ad'])

        if tip == "agirlik":
            set_s   = self.set_spin.value()
            tekrar  = self.tekrar_spin.value()
            agirlik = self.agirlik_spin.value()
            if agirlik > 0:
                detay = f"{set_s}×{tekrar}  {egzersiz['ad']}  —  {agirlik:.1f} kg"
            else:
                detay = f"{set_s}×{tekrar}  {egzersiz['ad']}"
        elif tip == "vucutagirlik":
            set_s  = self.set_spin.value()
            tekrar = self.tekrar_spin.value()
            detay  = f"{set_s}×{tekrar}  {egzersiz['ad']}"
        elif tip == "kardiyo":
            sure = self.p_sure_spin.value()
            detay = f"{egzersiz['ad']}  —  {sure} dk"
        else:  # izometrik
            set_s = self.set_spin.value()
            sure  = self.p_sure_spin.value()
            detay = f"{set_s}×{sure}dk  {egzersiz['ad']}"

        db.takvim_program_ekle(self.sporcu_id, self.antrenor_id, self.tarih_str, detay)
        self._yukle()

    def _sil(self, pid):
        conn = db.get_connection()
        conn.execute("DELETE FROM antrenman_programi WHERE id=?", (pid,))
        conn.commit(); conn.close()
        self._yukle()


# ==========================================
# EGZERSİZ KÜTÜPHANESİ + ANTRENMAN LOGU
# ==========================================
class AntrenmanLogWidget(QWidget):
    """Sporcu kendi antrenmanını loglar: hareket seç, kg/tekrar gir, kalori hesapla."""
    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici
        self.sporcu_id = kullanici['sporcu_id']
        self._egzersizler = []
        self._setup_ui()

    def _setup_ui(self):
        dis_layout = QVBoxLayout(self)
        dis_layout.setContentsMargins(0, 0, 0, 0)
        dis_layout.setSpacing(0)

        # Başlık
        baslik_w = QWidget(); baslik_w.setStyleSheet(f"background-color: {COLORS['bg_app']};")
        baslik_ic = QVBoxLayout(baslik_w)
        baslik_ic.setContentsMargins(30, 30, 30, 16); baslik_ic.setSpacing(4)
        baslik = QLabel("Antrenman Logu")
        baslik.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {COLORS['text_main']}; background: transparent;")
        alt = QLabel("Yaptığın hareketi seç, ağırlık ve tekrar sayısını gir — kalori otomatik hesaplanır.")
        alt.setStyleSheet(f"color: {COLORS['text_sub']}; font-size: 14px; background: transparent;")
        baslik_ic.addWidget(baslik); baslik_ic.addWidget(alt)
        dis_layout.addWidget(baslik_w)

        # Scroll
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;} QScrollBar:vertical{width:6px;background:transparent;} QScrollBar::handle:vertical{background:#C7C7CC;border-radius:3px;min-height:30px;} QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}")
        ic = QWidget(); ic.setStyleSheet(f"background-color: {COLORS['bg_app']};")
        ic_lay = QVBoxLayout(ic); ic_lay.setContentsMargins(30, 10, 30, 30); ic_lay.setSpacing(20)

        # -- Hareket Ekleme Kartı --
        ekle_kart = QFrame()
        ekle_kart.setStyleSheet(f"QFrame{{background-color:{COLORS['bg_card']};border-radius:24px;border:none;}}")
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(30); shadow.setColor(QColor(0,0,0,12)); shadow.setOffset(0,6)
        ekle_kart.setGraphicsEffect(shadow)
        ekle_lay = QVBoxLayout(ekle_kart); ekle_lay.setContentsMargins(28,28,28,28); ekle_lay.setSpacing(18)

        ekle_baslik = QLabel("Hareket Ekle")
        ekle_baslik.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text_main']}; background: transparent;")
        ekle_lay.addWidget(ekle_baslik)

        chip_style_kat = f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_sub']};
                border: 1.5px solid transparent;
                border-radius: 16px;
                font-size: 12px;
                font-weight: 600;
                padding: 5px 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']}15;
                color: {COLORS['accent']};
            }}
        """
        chip_style_kat_aktif = f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: 1.5px solid {COLORS['accent']};
                border-radius: 16px;
                font-size: 12px;
                font-weight: 700;
                padding: 5px 14px;
            }}
        """

        # Kategori chip satırı
        self._chip_style_kat = chip_style_kat
        self._chip_style_kat_aktif = chip_style_kat_aktif
        self._aktif_kat_btn = None

        kat_scroll = QScrollArea()
        kat_scroll.setFixedHeight(42)
        kat_scroll.setWidgetResizable(True)
        kat_scroll.setFrameShape(QFrame.NoFrame)
        kat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        kat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        kat_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")

        kat_ic = QWidget(); kat_ic.setStyleSheet("background:transparent;")
        kat_ic_lay = QHBoxLayout(kat_ic)
        kat_ic_lay.setContentsMargins(0,0,0,0); kat_ic_lay.setSpacing(6)

        btn_tumu = QPushButton("Tümü")
        btn_tumu.setCursor(Qt.PointingHandCursor)
        btn_tumu.setStyleSheet(chip_style_kat_aktif)
        btn_tumu.clicked.connect(lambda: self._kategori_degisti("Tüm Kategoriler", btn_tumu))
        self._aktif_kat_btn = btn_tumu
        kat_ic_lay.addWidget(btn_tumu)

        for k in db.egzersiz_kategorileri():
            b = QPushButton(k); b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(chip_style_kat)
            b.clicked.connect(lambda _, kat=k, btn=b: self._kategori_degisti(kat, btn))
            kat_ic_lay.addWidget(b)
        kat_ic_lay.addStretch()
        kat_scroll.setWidget(kat_ic)
        ekle_lay.addWidget(kat_scroll)

        # Hareket chip grid (scroll içinde) — sürüklenebilir + scrollbar'lı
        self.hareket_scroll = SuruklenebilirScroll()
        self.hareket_scroll.setFixedHeight(150)
        self.hareket_chip_ic = QWidget(); self.hareket_chip_ic.setStyleSheet("background:transparent;")
        self.hareket_chip_lay = QGridLayout(self.hareket_chip_ic)
        self.hareket_chip_lay.setContentsMargins(0,0,0,0); self.hareket_chip_lay.setSpacing(6)
        self.hareket_scroll.setWidget(self.hareket_chip_ic)
        ekle_lay.addWidget(self.hareket_scroll)

        self._chip_style_hareket = f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_main']};
                border: 1.5px solid transparent;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']}15;
                color: {COLORS['accent']};
            }}
        """
        self._chip_style_hareket_aktif = f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: 1.5px solid {COLORS['accent']};
                border-radius: 12px;
                font-size: 12px;
                font-weight: 700;
                padding: 6px 12px;
                text-align: left;
            }}
        """
        self._aktif_hareket_btn = None

        # Seçili hareket bilgi kartı (fotoğraf + açıklama)
        self.hareket_bilgi_kart = QFrame()
        self.hareket_bilgi_kart.setStyleSheet(f"QFrame{{background-color:#4A5E2A;border-radius:16px;border:none;}}")
        self.hareket_bilgi_kart.setVisible(False)
        hb_lay = QHBoxLayout(self.hareket_bilgi_kart)
        hb_lay.setContentsMargins(14,14,14,14); hb_lay.setSpacing(16)

        # Fotoğraf alanı
        self.hareket_foto = QLabel()
        self.hareket_foto.setFixedSize(100, 100)
        self.hareket_foto.setAlignment(Qt.AlignCenter)
        self.hareket_foto.setStyleSheet(f"background-color:rgba(255,255,255,0.15);border-radius:12px;color:rgba(255,255,255,0.6);font-size:11px;")
        hb_lay.addWidget(self.hareket_foto)

        # Metin alanı
        hb_metin = QVBoxLayout(); hb_metin.setSpacing(4)
        self.hb_ad = QLabel()
        self.hb_ad.setStyleSheet(f"font-size:15px;font-weight:800;color:white;background:transparent;")
        self.hb_kas = QLabel()
        self.hb_kas.setStyleSheet(f"font-size:12px;font-weight:600;color:#FFD580;background:transparent;")
        self.hb_acik = QLabel()
        self.hb_acik.setWordWrap(True)
        self.hb_acik.setStyleSheet(f"font-size:12px;color:rgba(255,255,255,0.75);background:transparent;")
        hb_metin.addWidget(self.hb_ad)
        hb_metin.addWidget(self.hb_kas)
        hb_metin.addWidget(self.hb_acik)
        hb_metin.addStretch()
        hb_lay.addLayout(hb_metin, stretch=1)

        ekle_lay.addWidget(self.hareket_bilgi_kart)

        spin_style = f"""
            QSpinBox,QDoubleSpinBox{{background-color:{COLORS['bg_input']};color:{COLORS['text_main']};border:2px solid transparent;
                border-radius:12px;padding:10px 14px;font-size:15px;font-weight:700;}}
            QSpinBox:focus,QDoubleSpinBox:focus{{border:2px solid {COLORS['accent']}55;background:#fff;}}
            QSpinBox::up-button,QSpinBox::down-button,QDoubleSpinBox::up-button,QDoubleSpinBox::down-button{{width:0px;}}
        """

        # Set / Tekrar / Ağırlık / Süre
        lbl_s = f"color:{COLORS['text_sub']};font-size:12px;font-weight:700;background:transparent;margin-bottom:4px;"
        form_row = QHBoxLayout(); form_row.setSpacing(12)
        def blok(lbl_txt, widget):
            b = QVBoxLayout(); b.setSpacing(4)
            b.addWidget(QLabel(lbl_txt, styleSheet=lbl_s))
            b.addWidget(widget); return b

        self.set_spin = QSpinBox(); self.set_spin.setRange(1,30); self.set_spin.setValue(3); self.set_spin.setStyleSheet(spin_style)
        self.tekrar_spin = QSpinBox(); self.tekrar_spin.setRange(1,100); self.tekrar_spin.setValue(12); self.tekrar_spin.setStyleSheet(spin_style)
        self.agirlik_spin = QDoubleSpinBox(); self.agirlik_spin.setRange(0,500); self.agirlik_spin.setValue(0); self.agirlik_spin.setSuffix(" kg"); self.agirlik_spin.setStyleSheet(spin_style)
        self.sure_spin = QSpinBox(); self.sure_spin.setRange(1,180); self.sure_spin.setValue(5); self.sure_spin.setSuffix(" dk"); self.sure_spin.setStyleSheet(spin_style)

        for sp in [self.set_spin, self.tekrar_spin, self.agirlik_spin, self.sure_spin]:
            sp.valueChanged.connect(self._kalori_guncelle)

        # Her alan için wrapper widget (show/hide için)
        def sarili_blok(lbl_txt, widget):
            w = QWidget(); w.setStyleSheet("background:transparent;")
            b = QVBoxLayout(w); b.setContentsMargins(0,0,0,0); b.setSpacing(4)
            b.addWidget(QLabel(lbl_txt, styleSheet=lbl_s))
            b.addWidget(widget)
            return w

        self._blok_set     = sarili_blok("SET",         self.set_spin)
        self._blok_tekrar  = sarili_blok("TEKRAR",      self.tekrar_spin)
        self._blok_agirlik = sarili_blok("AĞIRLIK",     self.agirlik_spin)
        self._blok_sure    = sarili_blok("SÜRE",        self.sure_spin)

        form_row.addWidget(self._blok_set)
        form_row.addWidget(self._blok_tekrar)
        form_row.addWidget(self._blok_agirlik)
        form_row.addWidget(self._blok_sure)

        # Spinbox'lar hazır, kaloriyi doğru hesapla
        self._kalori_guncelle()
        ekle_lay.addLayout(form_row)

        # Kalori önizleme
        self.kalori_preview = QLabel("≈ 0 kcal")
        self.kalori_preview.setStyleSheet(f"font-size:20px;font-weight:900;color:{COLORS['accent']};background:transparent;")
        ekle_lay.addWidget(self.kalori_preview)

        ekle_btn = QPushButton("＋  Loguuma Ekle")
        ekle_btn.setFixedHeight(50); ekle_btn.setCursor(Qt.PointingHandCursor)
        ekle_btn.setStyleSheet(f"QPushButton{{background-color:{COLORS['accent']};color:white;border:none;border-radius:25px;font-size:15px;font-weight:800;}} QPushButton:hover{{background-color:{COLORS['accent_hover']};}}")
        ekle_btn.clicked.connect(self._ekle)
        ekle_lay.addWidget(ekle_btn)
        ic_lay.addWidget(ekle_kart)

        # -- Antrenörün Bugünkü Programı --
        self.program_kart = QFrame()
        self.program_kart.setStyleSheet(f"QFrame{{background-color:{COLORS['bg_card']};border-radius:24px;border:none;}}")
        program_shadow = QGraphicsDropShadowEffect(); program_shadow.setBlurRadius(30); program_shadow.setColor(QColor(0,0,0,12)); program_shadow.setOffset(0,6)
        self.program_kart.setGraphicsEffect(program_shadow)
        self.program_kart_lay = QVBoxLayout(self.program_kart); self.program_kart_lay.setContentsMargins(28,24,28,24); self.program_kart_lay.setSpacing(12)

        program_baslik_row = QHBoxLayout(); program_baslik_row.setSpacing(10)
        # İkon (program ikonu varsa göster, yoksa emoji fallback)
        _prog_ikon_yolu = f"{ANA_KLASOR}/antrenman_logu.png"
        if os.path.exists(_prog_ikon_yolu):
            prog_ikon_lbl = QLabel()
            prog_ikon_lbl.setPixmap(QIcon(_prog_ikon_yolu).pixmap(QSize(26, 26)))
            prog_ikon_lbl.setStyleSheet("background:transparent;border:none;")
            program_baslik_row.addWidget(prog_ikon_lbl)
        program_baslik_lbl = QLabel("Antrenörünüzün Bugünkü Programı")
        program_baslik_lbl.setStyleSheet(f"font-size:18px;font-weight:800;color:{COLORS['text_main']};background:transparent;")
        program_baslik_row.addWidget(program_baslik_lbl); program_baslik_row.addStretch()
        self.program_kart_lay.addLayout(program_baslik_row)

        self.program_icerik_lay = QVBoxLayout(); self.program_icerik_lay.setSpacing(8)
        self.program_kart_lay.addLayout(self.program_icerik_lay)
        self.program_kart.setVisible(False)
        ic_lay.addWidget(self.program_kart)

        # -- Geçmiş Loglar --
        gecmis_baslik = QLabel("Geçmiş Antrenmanlar")
        gecmis_baslik.setStyleSheet(f"font-size:20px;font-weight:800;color:{COLORS['text_main']};background:transparent;")
        ic_lay.addWidget(gecmis_baslik)

        self.log_liste_lay = QVBoxLayout(); self.log_liste_lay.setSpacing(10)
        ic_lay.addLayout(self.log_liste_lay)
        ic_lay.addStretch()

        scroll.setWidget(ic); dis_layout.addWidget(scroll)

        self._kategori_degisti("Tüm Kategoriler")
        self.yenile()

    def _kategori_degisti(self, kat, btn=None):
        # Kategori chip görselini güncelle
        if self._aktif_kat_btn:
            self._aktif_kat_btn.setStyleSheet(self._chip_style_kat)
        if btn:
            btn.setStyleSheet(self._chip_style_kat_aktif)
            self._aktif_kat_btn = btn

        # Hareket chip'lerini temizle ve yeniden çiz
        while self.hareket_chip_lay.count():
            item = self.hareket_chip_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self._egzersizler = db.egzersizleri_getir(None if kat == "Tüm Kategoriler" else kat)
        self._aktif_hareket_idx = -1
        self._aktif_hareket_btn = None
        self.hareket_bilgi_kart.setVisible(False)

        for i, e in enumerate(self._egzersizler):
            b = QPushButton(e['ad'])
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(self._chip_style_hareket)
            b.clicked.connect(lambda _, idx=i, xbtn=b: self._hareket_sec(idx, xbtn))
            self.hareket_chip_lay.addWidget(b, i // 4, i % 4)

        # İlk hareketi otomatik seç
        if self._egzersizler:
            ilk = self.hareket_chip_lay.itemAt(0)
            if ilk and ilk.widget():
                self._hareket_sec(0, ilk.widget())

        self._kalori_guncelle()

    def _form_alanlari_guncelle(self, tip: str):
        """Hareket tipine göre Set/Tekrar/Ağırlık/Süre bloklarını göster veya gizle."""
        # tip: 'agirlik' | 'vucutagirlik' | 'kardiyo' | 'izometrik'
        self._blok_set.setVisible(tip in ("agirlik", "vucutagirlik", "izometrik"))
        self._blok_tekrar.setVisible(tip in ("agirlik", "vucutagirlik"))
        self._blok_agirlik.setVisible(tip == "agirlik")
        self._blok_sure.setVisible(tip in ("kardiyo", "izometrik"))
        # Kalori etiketi: sadece süre bazlı hareketlerde anlamlı
        self.kalori_preview.setVisible(tip in ("kardiyo", "izometrik"))

    def _hareket_sec(self, idx, btn):
        if self._aktif_hareket_btn:
            self._aktif_hareket_btn.setStyleSheet(self._chip_style_hareket)
        btn.setStyleSheet(self._chip_style_hareket_aktif)
        self._aktif_hareket_btn = btn
        self._aktif_hareket_idx = idx

        if 0 <= idx < len(self._egzersizler):
            e = self._egzersizler[idx]
            self.hb_ad.setText(e['ad'])
            self.hb_kas.setText("💪  " + (e.get('kas_grubu') or ''))
            self.hb_acik.setText(e.get('aciklama') or '')

            # Fotoğrafı yükle
            ad_dosya = e['ad'].lower().replace(' ', '_').replace('/', '_').replace('ş','s').replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ç','c')
            klasor = os.path.join(ANA_KLASOR, "egzersiz_gorselleri")
            foto_yol = os.path.join(klasor, f"{ad_dosya}.jpg")
            if not os.path.exists(foto_yol):
                foto_yol = os.path.join(klasor, f"{ad_dosya}.png")

            if os.path.exists(foto_yol):
                pix = QPixmap(foto_yol).scaled(100, 100, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                hedef = QPixmap(100, 100); hedef.fill(Qt.transparent)
                p = QPainter(hedef)
                p.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath(); path.addRoundedRect(0, 0, 100, 100, 12, 12)
                p.setClipPath(path)
                p.drawPixmap((100 - pix.width()) // 2, (100 - pix.height()) // 2, pix)
                p.end()
                self.hareket_foto.setPixmap(hedef)
                self.hareket_foto.setText("")
                # Tıklanınca büyüt
                _tam_pix = QPixmap(foto_yol)
                _ad = e['ad']
                self.hareket_foto.setCursor(Qt.PointingHandCursor)
                self.hareket_foto.mousePressEvent = lambda _ev, px=_tam_pix, ad=_ad: GorselZoomDialog.goster(px, ad, self)
                self.hareket_foto.setToolTip("Büyütmek için tıklayın")
            else:
                self.hareket_foto.setPixmap(QPixmap())
                self.hareket_foto.setText("Görsel\neklenmemiş")
                self.hareket_foto.setCursor(Qt.ArrowCursor)
                self.hareket_foto.mousePressEvent = lambda _ev: None
                self.hareket_foto.setToolTip("")

            self.hareket_bilgi_kart.setVisible(True)

            # Hareket tipine göre form alanlarını güncelle
            try:
                tip = hareket_tipi_al(e['ad'])
                self._form_alanlari_guncelle(tip)
            except AttributeError:
                pass  # Bloklar henüz oluşturulmamış
        self._kalori_guncelle()

    def _kalori_hesapla(self):
        idx = getattr(self, '_aktif_hareket_idx', -1)
        if idx < 0 or idx >= len(self._egzersizler): return 0
        e = self._egzersizler[idx]
        sporcu = db.sporcu_getir(self.sporcu_id)
        kilo = sporcu['kilo'] if sporcu and sporcu['kilo'] else 70
        met = e.get('met_katsayi') or 5.0
        tip = hareket_tipi_al(e['ad'])

        if tip in ("kardiyo", "izometrik"):
            # Süre bazlı: MET × kilo × süre(saat)
            sure_saat = self.sure_spin.value() / 60
        elif tip == "agirlik":
            # Ağırlık bazlı: set × tekrar × 3sn ≈ çalışma süresi tahmini
            tahmini_dk = (self.set_spin.value() * self.tekrar_spin.value() * 3) / 60
            sure_saat = tahmini_dk / 60
        else:  # vucutagirlik
            tahmini_dk = (self.set_spin.value() * self.tekrar_spin.value() * 2) / 60
            sure_saat = tahmini_dk / 60

        kalori = met * kilo * sure_saat
        return round(kalori, 1)

    def _kalori_guncelle(self):
        try:
            k = self._kalori_hesapla()
            self.kalori_preview.setText(f"≈ {k} kcal")
        except AttributeError:
            pass  # sure_spin henüz oluşturulmamış olabilir

    def _ekle(self):
        idx = getattr(self, '_aktif_hareket_idx', -1)
        if idx < 0 or not self._egzersizler: return
        e = self._egzersizler[idx]
        tip = hareket_tipi_al(e['ad'])
        kalori = self._kalori_hesapla()
        tarih = datetime.now().strftime("%Y-%m-%d")

        set_v    = self.set_spin.value()    if tip in ("agirlik", "vucutagirlik", "izometrik") else 1
        tekrar_v = self.tekrar_spin.value() if tip in ("agirlik", "vucutagirlik") else 0
        agirlik_v= self.agirlik_spin.value()if tip == "agirlik" else 0.0
        sure_v   = self.sure_spin.value()   if tip in ("kardiyo", "izometrik") else 0

        db.antrenman_logu_ekle(
            self.sporcu_id, tarih, e['id'], e['ad'],
            set_v, tekrar_v, agirlik_v, sure_v, kalori
        )
        AppleMesajDialog.bilgi(self, "Eklendi", f"{e['ad']} logunuza eklendi. ({kalori} kcal)")
        self.yenile()

    def _bugunku_programi_goster(self):
        """Antrenörün bugün için yazdığı programı kart içinde gösterir."""
        # İçeriği temizle
        while self.program_icerik_lay.count():
            item = self.program_icerik_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        bugun = datetime.now().strftime("%Y-%m-%d")
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT program_detay FROM antrenman_programi WHERE sporcu_id=? AND tarih=? ORDER BY id",
            (self.sporcu_id, bugun)
        ).fetchall()
        conn.close()

        if not rows:
            self.program_kart.setVisible(False)
            return

        self.program_kart.setVisible(True)
        for r in rows:
            # Program metnini parse ederek yapılandırılmış gösterim yap
            program_metni = r['program_detay']

            # Eşleşen egzersizi bul (görsel + kas grubu için)
            tum_eg = db.egzersizleri_getir()
            eslesen_eg = None
            for eg in tum_eg:
                if eg['ad'].lower() in program_metni.lower():
                    eslesen_eg = eg
                    break

            satir = QFrame()
            satir.setStyleSheet(f"""QFrame{{
                background-color: {COLORS['bg_card']};
                border: 1.5px solid {COLORS['border']};
                border-left: 4px solid {COLORS['accent']};
                border-radius: 14px;
            }}""")
            satir_lay = QHBoxLayout(satir); satir_lay.setContentsMargins(0, 0, 14, 0); satir_lay.setSpacing(0)

            # Sol: egzersiz görseli (varsa)
            if eslesen_eg:
                ad_dosya = eslesen_eg['ad'].lower().replace(' ','_').replace('/','_').replace('ş','s').replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ç','c')
                klasor = os.path.join(ANA_KLASOR, "egzersiz_gorselleri")
                foto_yol = os.path.join(klasor, f"{ad_dosya}.jpg")
                if not os.path.exists(foto_yol):
                    foto_yol = os.path.join(klasor, f"{ad_dosya}.png")

                foto_lbl = QLabel()
                foto_lbl.setFixedSize(72, 72)
                foto_lbl.setAlignment(Qt.AlignCenter)
                if os.path.exists(foto_yol):
                    pix = QPixmap(foto_yol).scaled(72, 72, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    hedef = QPixmap(72, 72); hedef.fill(Qt.transparent)
                    p = QPainter(hedef); p.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath(); path.addRoundedRect(0, 0, 72, 72, 12, 12)
                    p.setClipPath(path); p.drawPixmap((72-pix.width())//2, (72-pix.height())//2, pix); p.end()
                    foto_lbl.setPixmap(hedef)
                    foto_lbl.setStyleSheet("background:transparent;border:none;margin:10px 8px 10px 12px;")
                    # Tıklanınca büyüt
                    _tam_pix = QPixmap(foto_yol)
                    _eg_ad = eslesen_eg['ad']
                    foto_lbl.setCursor(Qt.PointingHandCursor)
                    foto_lbl.setToolTip("Büyütmek için tıklayın")
                    foto_lbl.mousePressEvent = lambda _ev, px=_tam_pix, ad=_eg_ad: GorselZoomDialog.goster(px, ad, self)
                else:
                    # Görsel yoksa renkli harf dairesi
                    foto_lbl.setText(eslesen_eg['ad'][0].upper())
                    foto_lbl.setStyleSheet(f"background-color:{COLORS['accent']}18;color:{COLORS['accent']};border-radius:12px;font-size:22px;font-weight:900;margin:10px 8px 10px 12px;")
                satir_lay.addWidget(foto_lbl)
            else:
                satir_lay.addSpacing(16)

            # Orta: egzersiz adı + set/tekrar/süre satırı
            bilgi_lay = QVBoxLayout(); bilgi_lay.setSpacing(3); bilgi_lay.setContentsMargins(4, 12, 4, 12)

            # Egzersiz adı
            if eslesen_eg:
                ad_lbl = QLabel(eslesen_eg['ad'])
                ad_lbl.setStyleSheet(f"font-size:15px;font-weight:800;color:{COLORS['text_main']};background:transparent;border:none;")
            else:
                ad_lbl = QLabel(program_metni)
                ad_lbl.setWordWrap(True)
                ad_lbl.setStyleSheet(f"font-size:14px;font-weight:700;color:{COLORS['text_main']};background:transparent;border:none;")
            bilgi_lay.addWidget(ad_lbl)

            # Set / Tekrar / Süre chip'leri — parse et
            import re as _re
            chip_row = QHBoxLayout(); chip_row.setSpacing(6); chip_row.setContentsMargins(0,0,0,0)
            chip_s = f"font-size:12px;font-weight:700;padding:3px 10px;border-radius:10px;border:none;"

            set_tekrar_m = _re.search(r'(\d+)\s*[×x]\s*(\d+)', program_metni)
            sure_m       = _re.search(r'(\d+)\s*dk', program_metni, _re.IGNORECASE)
            agirlik_m    = _re.search(r'(\d+(?:\.\d+)?)\s*kg', program_metni, _re.IGNORECASE)

            herhangi_chip = False
            if set_tekrar_m:
                set_chip = QLabel(f"🔁  {set_tekrar_m.group(1)} set × {set_tekrar_m.group(2)} tekrar")
                set_chip.setStyleSheet(chip_s + f"background-color:{COLORS['info']}18;color:{COLORS['info']};")
                chip_row.addWidget(set_chip); herhangi_chip = True
            if agirlik_m:
                ag_chip = QLabel(f"⚖️  {agirlik_m.group(1)} kg")
                ag_chip.setStyleSheet(chip_s + f"background-color:{COLORS['accent']}15;color:{COLORS['accent']};")
                chip_row.addWidget(ag_chip); herhangi_chip = True
            if sure_m:
                sure_chip = QLabel(f"⏱  {sure_m.group(1)} dk")
                sure_chip.setStyleSheet(chip_s + f"background-color:{COLORS['success']}18;color:{COLORS['success']};")
                chip_row.addWidget(sure_chip); herhangi_chip = True
            if not herhangi_chip:
                ham_lbl = QLabel(program_metni)
                ham_lbl.setStyleSheet(f"font-size:12px;color:{COLORS['text_sub']};background:transparent;border:none;")
                chip_row.addWidget(ham_lbl)
            chip_row.addStretch()
            bilgi_lay.addLayout(chip_row)
            satir_lay.addLayout(bilgi_lay, stretch=1)

            # Sağ: "Loğa Ekle" butonu
            ekle_btn = QPushButton("＋ Loğa Ekle")
            ekle_btn.setFixedHeight(34); ekle_btn.setCursor(Qt.PointingHandCursor)
            ekle_btn.setStyleSheet(f"""QPushButton{{
                background-color:{COLORS['accent']};color:white;border:none;
                border-radius:17px;font-size:12px;font-weight:700;padding:0px 16px;
            }} QPushButton:hover{{background-color:{COLORS['accent_hover']};}}""")
            pm = program_metni
            ekle_btn.clicked.connect(lambda _, p=pm: self._programdan_loga_ekle(p))
            satir_lay.addWidget(ekle_btn)

            self.program_icerik_lay.addWidget(satir)

    def _programdan_loga_ekle(self, program_metni: str):
        """
        Antrenörün yazdığı program metnini parse ederek antrenman_loglari'na kaydeder.
        Örnek format: '3×12  Bench Press  —  60.0 kg'  veya  'Koşu  —  20 dk'
        """
        import re
        tarih = datetime.now().strftime("%Y-%m-%d")

        # Önce egzersiz adını çıkar: metin içindeki bilinen bir egzersiz adını ara
        tum_egzersizler = db.egzersizleri_getir()
        eslesen = None
        for eg in tum_egzersizler:
            if eg['ad'].lower() in program_metni.lower():
                eslesen = eg
                break

        if eslesen is None:
            # Bilinen egzersiz bulunamadı, ham metni ad olarak kaydet
            db.antrenman_logu_ekle(self.sporcu_id, tarih, 0, program_metni, 0, 0, 0.0, 0, 0.0, "Antrenör programından")
            AppleMesajDialog.bilgi(self, "Eklendi", f"Program logunuza eklendi.")
            self.yenile()
            return

        # Değerleri regex ile parse et
        set_v = 0; tekrar_v = 0; agirlik_v = 0.0; sure_v = 0

        set_tekrar = re.search(r'(\d+)\s*[×x]\s*(\d+)', program_metni)
        if set_tekrar:
            set_v = int(set_tekrar.group(1))
            tekrar_v = int(set_tekrar.group(2))

        agirlik_m = re.search(r'(\d+(?:\.\d+)?)\s*kg', program_metni, re.IGNORECASE)
        if agirlik_m:
            agirlik_v = float(agirlik_m.group(1))

        sure_m = re.search(r'(\d+)\s*dk', program_metni, re.IGNORECASE)
        if sure_m:
            sure_v = int(sure_m.group(1))

        # Kalori hesapla
        sporcu = db.sporcu_getir(self.sporcu_id)
        kilo = sporcu['kilo'] if sporcu and sporcu['kilo'] else 70
        met = eslesen.get('met_katsayi') or 5.0
        tip = hareket_tipi_al(eslesen['ad'])

        if tip in ("kardiyo", "izometrik"):
            sure_saat = (sure_v or 10) / 60
        elif tip == "agirlik":
            sure_saat = ((set_v or 3) * (tekrar_v or 10) * 3) / 3600
        else:
            sure_saat = ((set_v or 3) * (tekrar_v or 10) * 2) / 3600

        kalori = round(met * kilo * sure_saat, 1)

        db.antrenman_logu_ekle(
            self.sporcu_id, tarih, eslesen['id'], eslesen['ad'],
            set_v, tekrar_v, agirlik_v, sure_v, kalori, "Antrenör programından"
        )
        AppleMesajDialog.bilgi(self, "Eklendi", f"{eslesen['ad']} logunuza eklendi. ({kalori} kcal)")
        self.yenile()

    def yenile(self):
        # Antrenör programını güncelle
        self._bugunku_programi_goster()
        # Eski log kartlarını temizle
        while self.log_liste_lay.count():
            item = self.log_liste_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        loglar = db.antrenman_loglari_getir(self.sporcu_id)
        if not loglar:
            bos = QLabel("Henüz antrenman logu yok. Yukarıdan ekleyebilirsin.")
            bos.setStyleSheet(f"color:{COLORS['text_sub']};font-size:14px;background:transparent;padding:20px;")
            bos.setAlignment(Qt.AlignCenter)
            self.log_liste_lay.addWidget(bos)
            return

        gun_gruplari = {}
        for log in loglar:
            gun_gruplari.setdefault(log['tarih'], []).append(log)

        TURKCE_AYLAR_KISA = {1:"Oca",2:"Şub",3:"Mar",4:"Nis",5:"May",6:"Haz",7:"Tem",8:"Ağu",9:"Eyl",10:"Eki",11:"Kas",12:"Ara"}

        for tarih, gun_loglar in list(gun_gruplari.items())[:30]:
            try:
                dt = datetime.strptime(tarih, "%Y-%m-%d")
                tarih_goster = f"{dt.day} {TURKCE_AYLAR_KISA[dt.month]} {dt.year}"
            except: tarih_goster = tarih

            toplam_kalori = sum(l['kalori'] for l in gun_loglar)

            gun_kart = QFrame()
            gun_kart.setStyleSheet(f"QFrame{{background-color:{COLORS['bg_card']};border-radius:20px;border:none;}}")
            shadow2 = QGraphicsDropShadowEffect(); shadow2.setBlurRadius(20); shadow2.setColor(QColor(0,0,0,8)); shadow2.setOffset(0,4)
            gun_kart.setGraphicsEffect(shadow2)
            gun_lay = QVBoxLayout(gun_kart); gun_lay.setContentsMargins(20,16,20,16); gun_lay.setSpacing(10)

            # Tarih + toplam kalori başlığı
            ust = QHBoxLayout()
            tarih_lbl = QLabel(tarih_goster)
            tarih_lbl.setStyleSheet(f"font-size:15px;font-weight:800;color:{COLORS['text_main']};background:transparent;")
            kcal_lbl = QLabel(f"🔥 {toplam_kalori:.0f} kcal")
            kcal_lbl.setStyleSheet(f"font-size:14px;font-weight:700;color:{COLORS['accent']};background:transparent;")
            ust.addWidget(tarih_lbl); ust.addStretch(); ust.addWidget(kcal_lbl)
            gun_lay.addLayout(ust)

            cizgi = QFrame(); cizgi.setFrameShape(QFrame.HLine)
            cizgi.setStyleSheet(f"background-color:{COLORS['border']};max-height:1px;")
            gun_lay.addWidget(cizgi)

            for log in gun_loglar:
                satir = QHBoxLayout(); satir.setSpacing(12)

                # Renkli harf dairesi
                daire = QLabel(log['egzersiz_ad'][0].upper())
                daire.setFixedSize(36, 36)
                daire.setAlignment(Qt.AlignCenter)
                daire.setStyleSheet(f"background-color:{COLORS['accent']}18;color:{COLORS['accent']};border-radius:18px;font-size:14px;font-weight:900;")

                ad_lbl = QLabel(log['egzersiz_ad'])
                ad_lbl.setStyleSheet(f"font-size:14px;font-weight:700;color:{COLORS['text_main']};background:transparent;")

                detay_lbl = QLabel(f"{log['set_sayisi']}×{log['tekrar_sayisi']}  ·  {log['agirlik_kg']:.1f} kg  ·  {log['sure_dakika']} dk")
                detay_lbl.setStyleSheet(f"font-size:12px;color:{COLORS['text_sub']};background:transparent;")

                bilgi_lay = QVBoxLayout(); bilgi_lay.setSpacing(2)
                bilgi_lay.addWidget(ad_lbl); bilgi_lay.addWidget(detay_lbl)

                kal_lbl = QLabel(f"{log['kalori']:.0f} kcal")
                kal_lbl.setStyleSheet(f"font-size:13px;font-weight:700;color:{COLORS['text_sub']};background:transparent;")

                sil_btn = QPushButton("✕")
                sil_btn.setFixedSize(28, 28); sil_btn.setCursor(Qt.PointingHandCursor)
                sil_btn.setStyleSheet(f"QPushButton{{background:{COLORS['danger']}18;color:{COLORS['danger']};border:none;border-radius:14px;font-size:11px;font-weight:700;}} QPushButton:hover{{background:{COLORS['danger']};color:white;}}")
                sil_btn.clicked.connect(lambda _, lid=log['id']: self._sil(lid))

                satir.addWidget(daire)
                satir.addLayout(bilgi_lay, stretch=1)
                satir.addWidget(kal_lbl)
                satir.addWidget(sil_btn)
                gun_lay.addLayout(satir)

            self.log_liste_lay.addWidget(gun_kart)

    def _sil(self, log_id):
        db.antrenman_logu_sil(log_id)
        self.yenile()

# --- 3. Öğrenciye Özel Takvim Pop-up'ı (Program Düzenleme Ekranı) ---
class OgrenciTakvimDialog(QDialog):
    def __init__(self, sporcu_id, sporcu_ad, antrenor_id):
        super().__init__()
        self.sporcu_id = sporcu_id
        self.sporcu_ad = sporcu_ad
        self.antrenor_id = antrenor_id
        self.suan = datetime.now()
        self.setWindowTitle(f"{sporcu_ad} - Antrenman Takvimi")
        self.setMinimumSize(950, 700)
        self.setStyleSheet(APPLE_THEME)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Üst bar: Ay değiştirme ve başlık
        ust_bar = QHBoxLayout()
        onceki_btn = QPushButton("◀ Önceki Ay")
        onceki_btn.setCursor(Qt.PointingHandCursor)
        onceki_btn.clicked.connect(lambda: self._ay_degistir(-1))
        
        self.ay_label = QLabel()
        self.ay_label.setAlignment(Qt.AlignCenter)
        self.ay_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #f39c12;")
        
        sonraki_btn = QPushButton("Sonraki Ay ▶")
        sonraki_btn.setCursor(Qt.PointingHandCursor)
        sonraki_btn.clicked.connect(lambda: self._ay_degistir(1))
        
        ust_bar.addWidget(onceki_btn); ust_bar.addWidget(self.ay_label); ust_bar.addWidget(sonraki_btn)
        layout.addLayout(ust_bar)
        layout.addSpacing(15)

        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        layout.addLayout(self.grid)
        self._takvimi_ciz()

    def _ay_degistir(self, artis):
        ay = self.suan.month + artis
        yil = self.suan.year
        if ay > 12: ay = 1; yil += 1
        elif ay < 1: ay = 12; yil -= 1
        self.suan = self.suan.replace(year=yil, month=ay, day=1)
        self._takvimi_ciz()

    def _takvimi_ciz(self):
        import calendar
        from datetime import datetime

        TURKCE_AYLAR = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
            5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
            9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }

        # 1. Eski takvimi tamamen ve güvenli bir şekilde temizle
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        ay_adi = TURKCE_AYLAR[self.suan.month]
        self.ay_label.setText(f"{ay_adi} {self.suan.year}")
        yil_ay = self.suan.strftime("%Y-%m")
        programlar = db.takvim_programlari_getir(self.sporcu_id, yil_ay)

        # 2. Gün başlıklarını (Pzt, Salı...) ekle
        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        for i, gun in enumerate(gunler):
            lbl = QLabel(gun)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; color: #888; font-size: 14px; padding: 5px;")
            self.grid.addWidget(lbl, 0, i)

        baslangic_gunu = self.suan.replace(day=1).weekday()
        _, ay_uzunlugu = calendar.monthrange(self.suan.year, self.suan.month)
        bugun_str = datetime.now().strftime("%Y-%m-%d")

        # 3. Gün kutucuklarını doğru konuma yerleştir
        # Her günün grid konumunu başlangıç gününe göre hesapla
        for gun_sayaci in range(1, ay_uzunlugu + 1):
            hucre_indeksi = baslangic_gunu + (gun_sayaci - 1)
            row = hucre_indeksi // 7 + 1
            col = hucre_indeksi % 7

            kutu = TiklanabilirKutu()
            kutu.setMinimumSize(120, 100)
            kutu.setCursor(Qt.PointingHandCursor)

            tarih_str = f"{self.suan.year}-{self.suan.month:02d}-{gun_sayaci:02d}"

            if tarih_str < bugun_str:
                kutu.setStyleSheet("""
                    TiklanabilirKutu { background-color: #12121a; border: 1px solid #1f1f2e; border-radius: 8px; }
                    TiklanabilirKutu:hover { border: 1px solid #3a3a4e; background-color: #161622; }
                """)
            else:
                kutu.setStyleSheet("""
                    TiklanabilirKutu { background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 8px; }
                    TiklanabilirKutu:hover { border: 2px solid #f39c12; background-color: #252542; }
                """)

            kutu_lay = QVBoxLayout(kutu)
            kutu_lay.setContentsMargins(8, 8, 8, 8)
            kutu_lay.setSpacing(4)

            gun_no = QLabel(str(gun_sayaci))
            if tarih_str < bugun_str:
                gun_no.setStyleSheet("color: #444; font-weight: bold; font-size: 16px; background: transparent; border: none;")
            else:
                gun_no.setStyleSheet("color: #aaa; font-weight: bold; font-size: 16px; background: transparent; border: none;")
            kutu_lay.addWidget(gun_no, alignment=Qt.AlignTop | Qt.AlignRight)

            if tarih_str in programlar:
                sayi = len(programlar[tarih_str])
                bilgi = QLabel(f"📋 {sayi} Program")
                if tarih_str < bugun_str:
                    bilgi.setStyleSheet("background-color: #2a2a3e; color: #777; border-radius: 4px; font-size: 12px; font-weight: bold; padding: 6px;")
                else:
                    bilgi.setStyleSheet("background-color: #6c63ff; color: white; border-radius: 4px; font-size: 12px; font-weight: bold; padding: 6px;")
                bilgi.setAlignment(Qt.AlignCenter)
                kutu_lay.addWidget(bilgi)

            kutu_lay.addStretch()
            kutu.tiklandi.connect(lambda t=tarih_str: self._gun_secildi(t))
            self.grid.addWidget(kutu, row, col)

    def _gun_secildi(self, tarih_str):
        dialog = GunlukProgramDialog(self.sporcu_id, self.antrenor_id, tarih_str, self.sporcu_ad)
        dialog.exec_()
        self._takvimi_ciz() # Pop-up kapanınca takvimi yenile (yeni program eklenmiş olabilir)

# --- 4. YENİ YAKA KARTI TASARIMLI ÖĞRENCİLERİM EKRANI ---
class OgrencilerimWidget(QWidget):
    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        baslik = QLabel("👥 Öğrencilerim")
        baslik.setStyleSheet("font-size: 26px; font-weight: bold; color: #f39c12;")
        layout.addWidget(baslik)
        layout.addSpacing(10)

        # Kartların yan yana dizilip alta taşınca kaydırılabilmesi için QScrollArea kullanıyoruz
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; } QScrollBar:vertical { width: 10px; }")
        
        self.kart_container = QWidget()
        self.kart_container.setStyleSheet("background-color: transparent;")
        
        # Grid layout (Kartları yan yana dizecek yapı)
        self.grid_lay = QGridLayout(self.kart_container)
        self.grid_lay.setSpacing(25) # Kartlar arası boşluk
        self.grid_lay.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll.setWidget(self.kart_container)
        layout.addWidget(self.scroll)
        
        self.yenile()

    def yenile(self):
        # Ekrandaki eski kartları temizle
        for i in reversed(range(self.grid_lay.count())):
            w = self.grid_lay.itemAt(i).widget()
            if w: w.deleteLater()

        ogrenciler = db.ogrencileri_getir(self.kullanici['kullanici_id'])
        
        if not ogrenciler:
            bos_lbl = QLabel("Henüz bir öğrenciniz bulunmuyor.")
            bos_lbl.setStyleSheet("color: #888; font-size: 16px;")
            self.grid_lay.addWidget(bos_lbl, 0, 0)
            return

        row, col = 0, 0
        maksimum_sutun = 4 # Yan yana dizilecek maksimum kart sayısı (Ekran genişliğine göre artırabilirsin)

        for og in ogrenciler:
            kart = QFrame()
            kart.setFixedSize(240, 310) 
            kart.setStyleSheet("""
                QFrame { background-color: #161625; border: 1px solid #2a2a3e; border-radius: 15px; }
                QFrame:hover { border: 2px solid #f39c12; background-color: #1a1a2e; }
            """)
            
            k_lay = QVBoxLayout(kart)
            k_lay.setContentsMargins(15, 25, 15, 20)
            k_lay.setSpacing(12)

            # 1. Profil Resmi Alanı (ARTIK GERÇEK GÖRSEL)
            avatar_dosyasi = og.get('avatar')
            if not avatar_dosyasi or avatar_dosyasi == "👤":
                avatar_dosyasi = "varsayilan.png"
                
            avatar_lbl = QLabel()
            avatar_lbl.setFixedSize(90, 90)
            
            tam_yol = f"{ANA_KLASOR}/{avatar_dosyasi}"
            if os.path.exists(tam_yol):
                hedef = QPixmap(84, 84)
                hedef.fill(Qt.transparent)
                orj = QPixmap(tam_yol)
                if not orj.isNull():
                    kucuk = orj.scaled(84, 84, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    cizer = QPainter(hedef)
                    cizer.setRenderHint(QPainter.Antialiasing)
                    yol = QPainterPath()
                    yol.addEllipse(0, 0, 84, 84)
                    cizer.setClipPath(yol)
                    cizer.drawPixmap((84 - kucuk.width()) // 2, (84 - kucuk.height()) // 2, kucuk)
                    cizer.end()

                avatar_lbl.setPixmap(hedef)
                avatar_lbl.setStyleSheet("border: 3px solid #f39c12; border-radius: 45px;")
            else:
                # Resim yoksa uyarı göster
                avatar_lbl.setText("Görsel\nYok")
                avatar_lbl.setAlignment(Qt.AlignCenter)
                avatar_lbl.setStyleSheet("background-color: #0f0f1a; color: #888; border: 3px solid #f39c12; border-radius: 45px;")
                
            k_lay.addWidget(avatar_lbl, alignment=Qt.AlignHCenter)

            # ... (Bundan sonraki kısımlar, İsim, Çizgi, Boy-Kilo vs. aynı kalsın) ...

            # 2. İsim Alanı
            isim_lbl = QLabel(f"{og['ad']} {og['soyad']}")
            isim_lbl.setAlignment(Qt.AlignCenter)
            isim_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: white; border: none; background: transparent;")
            k_lay.addWidget(isim_lbl)
            
            # Turuncu Ayıraç Çizgi
            cizgi = QFrame()
            cizgi.setFrameShape(QFrame.HLine)
            cizgi.setStyleSheet("background-color: #f39c12; max-height: 2px; border: none;")
            k_lay.addWidget(cizgi)

            # 3. İletişim / Bilgi Alanı
            mail_lbl = QLabel(f"📧 {og['email']}")
            mail_lbl.setAlignment(Qt.AlignCenter)
            mail_lbl.setStyleSheet("font-size: 12px; color: #aaa; border: none; background: transparent;")
            k_lay.addWidget(mail_lbl)
            
            # ---> YENİ: Boy ve Kilo Bilgisi <---
            boy = og.get('boy', 0)
            kilo = og.get('kilo', 0)
            fiziksel_lbl = QLabel(f"📏 {boy} cm   |   ⚖️ {kilo} kg")
            fiziksel_lbl.setAlignment(Qt.AlignCenter)
            fiziksel_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #6c63ff; background: transparent; margin-top: 5px;")
            k_lay.addWidget(fiziksel_lbl)
            
            k_lay.addStretch()

            # 4. Düzenle Butonu (Kartın Altında)
            # ... (bu kısım eski kodundakiyle aynı)
            duzenle_btn = QPushButton("📅 Programı Düzenle")
            duzenle_btn.setCursor(Qt.PointingHandCursor)
            duzenle_btn.setStyleSheet("background-color: #f39c12; color: #111; font-weight: bold; border-radius: 8px; padding: 12px; font-size: 14px;")
            duzenle_btn.clicked.connect(lambda _, s_id=og['sporcu_id'], s_ad=og['ad']: self._takvim_ac(s_id, s_ad))
            k_lay.addWidget(duzenle_btn)

            self.grid_lay.addWidget(kart, row, col)
            
            col += 1
            if col >= maksimum_sutun:
                col = 0
                row += 1

    def _takvim_ac(self, sporcu_id, sporcu_ad):
        # Butona basıldığında o öğrenciye özel takvim dialog ekranı açılır
        takvim_dialog = OgrenciTakvimDialog(sporcu_id, sporcu_ad, self.kullanici['kullanici_id'])
        takvim_dialog.exec_()


#İlk Defa Kayıt Olunca Gelen Ekran

class IlkKurulumWidget(QWidget):
    kurulum_bitti = pyqtSignal() # Kurulum bitince ana ekrana geçiş sinyali

    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici
        self.secili_avatar = "varsayilan.png"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        # Ana kart
        card = QFrame()
        card.setFixedWidth(460)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 28px;
                border: none;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50); shadow.setColor(QColor(0, 0, 0, 18)); shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(40, 40, 40, 40)
        c_lay.setSpacing(0)

        # Başlık
        baslik = QLabel("🚀 Aramıza Hoş Geldin!")
        baslik.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {COLORS['accent']}; background: transparent; border: none; letter-spacing: -0.5px;")
        baslik.setAlignment(Qt.AlignCenter)
        c_lay.addWidget(baslik)
        c_lay.addSpacing(10)

        bilgi = QLabel("Başlamadan önce birkaç bilgini alalım.")
        bilgi.setStyleSheet(f"color: {COLORS['text_sub']}; font-size: 14px; font-weight: 500; background: transparent; border: none;")
        bilgi.setAlignment(Qt.AlignCenter)
        c_lay.addWidget(bilgi)
        c_lay.addSpacing(28)

        # Avatar butonu (elleme — sadece hizalama)
        self.avatar_btn = QPushButton()
        self.avatar_btn.setFixedSize(120, 120)
        self.avatar_btn.setCursor(Qt.PointingHandCursor)
        self.avatar_btn.setIcon(QIcon(resmi_yuvarla(f"{ANA_KLASOR}/{self.secili_avatar}", 110)))
        self.avatar_btn.setIconSize(QSize(110, 110))
        self.avatar_btn.setStyleSheet("background-color: #0f0f1a; border: 3px dashed #6c63ff; border-radius: 60px;")
        self.avatar_btn.clicked.connect(self._avatar_sec)
        c_lay.addWidget(self.avatar_btn, alignment=Qt.AlignCenter)
        c_lay.addSpacing(8)

        foto_lbl = QLabel("Fotoğraf seçmek için tıkla")
        foto_lbl.setStyleSheet(f"color: {COLORS['info']}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        foto_lbl.setAlignment(Qt.AlignCenter)
        c_lay.addWidget(foto_lbl)
        c_lay.addSpacing(28)

        # Ayırıcı çizgi
        cizgi = QFrame(); cizgi.setFrameShape(QFrame.HLine)
        cizgi.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px; border: none;")
        c_lay.addWidget(cizgi)
        c_lay.addSpacing(24)

        # Input stili — tema ile uyumlu
        spinbox_style = f"""
            QDoubleSpinBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_main']};
                border: 2px solid transparent;
                border-radius: 14px;
                padding: 12px 16px;
                font-size: 16px;
                font-weight: 700;
                min-height: 20px;
            }}
            QDoubleSpinBox:focus {{
                border: 2px solid {COLORS['accent']}55;
                background-color: #FFFFFF;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; }}
        """
        lbl_style = f"color: {COLORS['text_sub']}; font-size: 13px; font-weight: 700; background: transparent; border: none; margin-bottom: 6px;"

        # Boy alanı
        boy_lbl = QLabel("BOY")
        boy_lbl.setStyleSheet(lbl_style)
        self.boy_inp = QDoubleSpinBox()
        self.boy_inp.setRange(100, 250); self.boy_inp.setSuffix(" cm")
        self.boy_inp.setValue(170.0)
        self.boy_inp.setStyleSheet(spinbox_style)

        # Kilo alanı
        kilo_lbl = QLabel("KİLO")
        kilo_lbl.setStyleSheet(lbl_style)
        self.kilo_inp = QDoubleSpinBox()
        self.kilo_inp.setRange(30, 300); self.kilo_inp.setSuffix(" kg")
        self.kilo_inp.setValue(70.0)
        self.kilo_inp.setStyleSheet(spinbox_style)

        # İki sütun yan yana
        input_row = QHBoxLayout()
        input_row.setSpacing(16)

        boy_blok = QVBoxLayout(); boy_blok.setSpacing(4)
        boy_blok.addWidget(boy_lbl); boy_blok.addWidget(self.boy_inp)

        kilo_blok = QVBoxLayout(); kilo_blok.setSpacing(4)
        kilo_blok.addWidget(kilo_lbl); kilo_blok.addWidget(self.kilo_inp)

        input_row.addLayout(boy_blok)
        input_row.addLayout(kilo_blok)
        c_lay.addLayout(input_row)
        c_lay.addSpacing(28)

        # Devam butonu (elleme rengi)
        self.bitir_btn = QPushButton("Uygulamaya Giriş Yap 🏁")
        self.bitir_btn.setFixedHeight(54)
        self.bitir_btn.setCursor(Qt.PointingHandCursor)
        self.bitir_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 15px; font-size: 16px; font-weight: bold; border-radius: 27px; border: none;")
        self.bitir_btn.clicked.connect(self._kurulumu_tamamla)
        c_lay.addWidget(self.bitir_btn)

        layout.addWidget(card)

    def _avatar_sec(self):
        dialog = AvatarSeciciDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.secili_avatar = dialog.secilen_avatar
            tam_yol = f"{ANA_KLASOR}/{self.secili_avatar}"
            self.avatar_btn.setIcon(QIcon(resmi_yuvarla(tam_yol, 110)))
            self.avatar_btn.setStyleSheet("background-color: #0f0f1a; border: 3px solid #27ae60; border-radius: 60px;")

    def _kurulumu_tamamla(self):
        if self.secili_avatar == "varsayilan.png":
            AppleMesajDialog.uyari(self, "Fotoğraf Seçilmedi", "Devam etmek için bir profil fotoğrafı seçmelisiniz.")
            return
            
        conn = db.get_connection()
        # Verileri kaydet ve kurulumu tamamla bayrağını 1 yap
        conn.execute("UPDATE sporcular SET boy=?, kilo=?, avatar=?, setup_tamamlandi=1 WHERE sporcu_id=?",
                     (self.boy_inp.value(), self.kilo_inp.value(), self.secili_avatar, self.kullanici['sporcu_id']))
        conn.commit(); conn.close()
        
        self.kurulum_bitti.emit()

# ==========================================
# 7. ANA PENCERE (APPLE HEALTH KONSEPTİ YAN MENÜ)
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici

        self.setWindowTitle("FitTrack Pro - Ana Ekran")
        self.setWindowIcon(QIcon(LOGO_YOLU))
        self.setMinimumSize(1100, 750) # Apple menüleri için biraz daha geniş alan
        self.setStyleSheet(APPLE_THEME)

        if self.kullanici.get('setup_tamamlandi') == 0:
            self._ilk_kurulumu_baslat()
        else:
            self._normal_arayuzu_yukle()

    def _ilk_kurulumu_baslat(self):
        self.kurulum_ekrani = IlkKurulumWidget(self.kullanici)
        self.kurulum_ekrani.kurulum_bitti.connect(self._normal_arayuzu_yukle)
        self.setCentralWidget(self.kurulum_ekrani)

    def _normal_arayuzu_yukle(self):
        merkez = QWidget()
        self.setCentralWidget(merkez)
        layout = QHBoxLayout(merkez)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- APPLE HEALTH TARZI YAN MENÜ (SIDEBAR) ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260) # Apple menüleri biraz daha geniştir
        # Arkaplan uygulamanın kendisiyle aynı (açık gri), sadece sağda çok ince bir çizgi
        self.sidebar.setStyleSheet(f"background-color: {COLORS['bg_app']}; border-right: 1px solid {COLORS['border']};")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 30, 15, 30)

        # LOGO VE UYGULAMA BAŞLIĞI
        baslik_lay = QHBoxLayout()
        logo_lbl = QLabel()
        pix = QPixmap(LOGO_YOLU)
        if not pix.isNull():
            logo_lbl.setPixmap(pix.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        baslik = QLabel("FitTrack")
        baslik.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text_main']}; border: none;")
        baslik_lay.addWidget(logo_lbl)
        baslik_lay.addWidget(baslik)
        baslik_lay.addStretch()
        sidebar_layout.addLayout(baslik_lay)
        sidebar_layout.addSpacing(30)

        # --- KATEGORİ BAŞLIĞI 1 ---
        kategori_lbl = QLabel("SAĞLIK KATEGORİLERİ")
        kategori_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['text_sub']}; border: none; margin-left: 10px; margin-bottom: 5px;")
        sidebar_layout.addWidget(kategori_lbl)

        self.views = []
        self.menuler = []

        # Temel Menüler (Apple Sağlık İsimleriyle)
        self.btn_dashboard = self._menu_btn("Özet", "ozet_ikon.webp", 0)
        self.btn_sporcu = self._menu_btn("Profil", "profil_ikon.png", 1)
        self.btn_vki = self._menu_btn("Vücut Ölçümleri", "vki_ikon.png", 2)
        
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_sporcu)
        sidebar_layout.addWidget(self.btn_vki)

        self.views.extend([DashboardWidget(self.kullanici), SporcuWidget(self.kullanici), VkiWidget(self.kullanici)])
        self.menuler.extend([self.btn_dashboard, self.btn_sporcu, self.btn_vki])

       # Dinamik Rol Menüleri
        if self.kullanici.get('rol') == 'antrenor':
            sidebar_layout.addSpacing(15)
            kategori2_lbl = QLabel("ANTRENÖR ARAÇLARI")
            kategori2_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['text_sub']}; border: none; margin-left: 10px; margin-bottom: 5px;")
            sidebar_layout.addWidget(kategori2_lbl)
            
            self.btn_ogrenciler = self._menu_btn("Öğrenciler", "ogrenci_ikon.png", len(self.views))
            sidebar_layout.addWidget(self.btn_ogrenciler)
            self.views.append(OgrencilerimWidget(self.kullanici))
            self.menuler.append(self.btn_ogrenciler)
            
            # "Program Yaz" butonu ve sayfası buradan tamamen kaldırıldı. 
            # İndeksleme (len(self.views)) dinamik olduğu için diğer menüler (Admin vb.) bozulmayacaktır.

        else:
            self.btn_takvim = self._menu_btn("Aktivite", "aktivite_ikon.png", len(self.views))
            sidebar_layout.addWidget(self.btn_takvim)
            self.views.append(TakvimWidget(self.kullanici))
            self.menuler.append(self.btn_takvim)
            
            if self.kullanici.get('rol') == 'sporcu':
                self.btn_antrenman_log = self._menu_btn("Antrenman Logu", "antrenman_logu.png", len(self.views))
                sidebar_layout.addWidget(self.btn_antrenman_log)
                self.views.append(AntrenmanLogWidget(self.kullanici))
                self.menuler.append(self.btn_antrenman_log)

                self.btn_antrenor_sec = self._menu_btn("Antrenör Seç", "koc_ikon.png", len(self.views))
                sidebar_layout.addWidget(self.btn_antrenor_sec)
                self.views.append(AntrenorSecWidget(self.kullanici))
                self.menuler.append(self.btn_antrenor_sec)

        # ADMIN Paneli
        if self.kullanici.get('rol') == 'admin':
            sidebar_layout.addSpacing(15)
            kategori3_lbl = QLabel("SİSTEM YÖNETİMİ")
            kategori3_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['text_sub']}; border: none; margin-left: 10px; margin-bottom: 5px;")
            sidebar_layout.addWidget(kategori3_lbl)
            
            self.btn_admin = self._menu_btn("Yönetim Paneli", "admin_ikon.png", len(self.views))
            sidebar_layout.addWidget(self.btn_admin)
            self.views.append(AdminWidget())
            self.menuler.append(self.btn_admin)

        sidebar_layout.addStretch()

        # Çıkış Butonu
        cikis_btn = self._menu_btn("Çıkış Yap", "cikis_ikon.png", -1)
        cikis_btn.clicked.disconnect() 
        cikis_btn.clicked.connect(self._cikis_yap) 
        # Çıkış butonu tehlike(kırmızı) rengi alır
        cikis_btn.setStyleSheet(f"text-align: left; padding: 12px 15px; font-size: 15px; font-weight: 600; background: transparent; color: {COLORS['danger']}; border: none;")
        sidebar_layout.addWidget(cikis_btn)

        # -- Sağ İçerik (Stack) --
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        for view in self.views:
            self.stack.addWidget(view)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)
        self._sayfa_degistir(0)

    def _cikis_yap(self):
        global login_window
        login_window.show() 
        self.close()        

    def _menu_btn(self, text, ikon_adi, index):
        # Yazıların yanına boşluk ekleyerek simgeyle arasını açıyoruz
        btn = QPushButton(f"  {text}")
        btn.setCursor(Qt.PointingHandCursor)
        
        # İkon yükleme mantığı
        ikon_yolu = f"{ANA_KLASOR}/{ikon_adi}"
        if os.path.exists(ikon_yolu):
            btn.setIcon(QIcon(ikon_yolu))
            btn.setIconSize(QSize(22, 22))
            
        btn.clicked.connect(lambda: self._sayfa_degistir(index))
        return btn

    def _sayfa_degistir(self, index):
        eski_index = self.stack.currentIndex()
        isleme_devam_et = True
        
        if eski_index == 1 and index != 1:
            profil_ekrani = self.views[1]
            if getattr(profil_ekrani, "sayfa_durumu", {}).get("degisiklik_yapildi") == True:
                sonuc = AppleMesajDialog.kaydedilmemis_degisiklikler(self)
                if sonuc == 'kaydet':
                    # Kaydedip geç
                    profil_ekrani._kaydet()
                    profil_ekrani.sayfa_durumu.update({"degisiklik_yapildi": False})
                elif sonuc == 'iptal':
                    # Değişiklikleri geri al (DB'den yeniden yükle) ve geç
                    profil_ekrani._yukle()
                    profil_ekrani.sayfa_durumu.update({"degisiklik_yapildi": False})
                elif sonuc == 'geri':
                    # Sayfada kal, hiçbir şey yapma
                    isleme_devam_et = False
                    
        if isleme_devam_et == True:
            self.stack.setCurrentIndex(index)
            self.views[index].yenile()
            
            # --- APPLE HEALTH SEÇİLİ MENÜ STİLİ ---
            for i, btn in enumerate(self.menuler):
                if i == index:
                    # Seçiliyse: Arkaplanı açık gri, yazısı kalın ve siyah
                    btn.setStyleSheet(f"""
                        text-align: left; 
                        padding: 12px 15px; 
                        font-size: 15px; 
                        font-weight: 700;
                        background-color: {COLORS['bg_tertiary']}; 
                        color: {COLORS['text_main']}; 
                        border: none; 
                        border-radius: 12px;
                    """)
                else:
                    # Seçili değilse: Şeffaf arkaplan, normal yazı
                    btn.setStyleSheet(f"""
                        text-align: left; 
                        padding: 12px 15px; 
                        font-size: 15px; 
                        font-weight: 500;
                        background: transparent; 
                        color: {COLORS['text_main']}; 
                        border: none;
                    """)


# ==========================================
# 8. UYGULAMA BAŞLATICISI
# ==========================================
if __name__ == '__main__':
    db.initialize_db()
    from PyQt5 import QtWidgets, QtCore, QtGui
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    login_window = QMainWindow()
    login_window.setWindowTitle("Sisteme Giriş")
    login_window.setWindowIcon(QIcon("logo.png"))
    login_window.setFixedSize(500, 750)
    
    # Ana ekran beyaz olacak, sadece giriş ekranına özel.
    login_window.setStyleSheet("QMainWindow { background-color: #FFFFFF; font-family: '-apple-system', 'Segoe UI', sans-serif; }")

    login_widget = LoginWidget()
    login_window.setCentralWidget(login_widget)
    
    # ---> ÇÖZÜM BURASI: GİRİŞ YAP BUTONUNU ANA PENCEREYE BAĞLAYAN EKSİK KODLAR <---
    ana_pencere = None

    def basarili_giris(kullanici_bilgisi):
        global ana_pencere
        ana_pencere = MainWindow(kullanici_bilgisi)
        ana_pencere.show()
        login_window.hide()

    login_widget.giris_basarili.connect(basarili_giris)
    # --------------------------------------------------------------------------------

    login_window.show()
    sys.exit(app.exec_())