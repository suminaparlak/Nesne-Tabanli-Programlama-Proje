#!/usr/bin/env python3
"""
VOYAGER — Seyahat Planlama Platformu v4
Yeni özellikler:
  - Kayıt/giriş: Yalnızca e-posta ve şifrede sayı/özel karakter, diğer alanlarda yalnızca harf
  - Kayıt: Hiçbir alanda boşluk bırakılamaz (e-posta ve şifre dahil)
  - Telefon: 3.3.2.2 formatı + ülke kodu seçimi (bayraklı combobox)
  - Google Maps WebEngine entegrasyonu (harita widget'ı)
  - Gelişmiş MessageBox tasarımı (özel CustomMessageBox)
  - Kaçırılmayacak Fırsatlar: Gerçekçi indirim verileri + bazı otellere ekstra indirim
"""
import sys, math, random
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QGridLayout,
    QStackedWidget, QDialog, QSpinBox, QSizePolicy, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QComboBox, QDoubleSpinBox, QDateEdit, QFormLayout, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer, QDate, pyqtSignal, QPoint, QRect, QUrl
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QLinearGradient,
    QRadialGradient, QPainterPath, QPalette, QCursor, QFontMetrics,
    QPixmap, QIcon
)
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    _HAS_WEBENGINE = True
except ImportError:
    _HAS_WEBENGINE = False

# ═══════════════════════════════════════════
#  RENK PALETİ
# ═══════════════════════════════════════════
P = {
    'bg': '#09090f', 'bg2': '#0d0d17', 'bg3': '#12121f', 'bg4': '#181828',
    'card': '#0f0f1c', 'card2': '#141425', 'border': '#1e1e34', 'brd2': '#2a2a45',
    'gold': '#c9922a', 'gold2': '#e8b84b', 'gold3': '#a07020',
    'blue': '#3a70d8', 'blue2': '#5a90f8', 'grn': '#2eb85c', 'red': '#d84040',
    'purp': '#7a5ad8', 'teal': '#2ab8b8', 'mut': '#50506a', 'mut2': '#35354a',
    'txt': '#dcdcec', 'txt2': '#9090aa', 'txt3': '#55556a',
    'nav': '#0b0b15', 'navbrd': '#1a1a2e',
    'orange': '#e07030', 'pink': '#c85080',
}
def p(k): return P.get(k, '#fff')
def qcol(k): return QColor(p(k))

# ═══════════════════════════════════════════
#  VERİ SINIFLARI
# ═══════════════════════════════════════════
class Seyahat:
    _next_id = 1
    def __init__(self, gidis_yeri, tarih, sure=7):
        self.seyahat_id = Seyahat._next_id; Seyahat._next_id += 1
        self.gidis_yeri = gidis_yeri; self.tarih = tarih; self.sure = sure

class Konaklama:
    def __init__(self, otel_adi, fiyat, yildiz=5, ozellikler=None, aciklama=''):
        self.otel_adi = otel_adi; self.fiyat = fiyat; self.yildiz = yildiz
        self.ozellikler = ozellikler or []; self.aciklama = aciklama
    
    def to_dict(self):
        return {
            'otel_adi': self.otel_adi,
            'fiyat': self.fiyat,
            'yildiz': self.yildiz,
            'ozellikler': self.ozellikler,
            'aciklama': self.aciklama
        }
    
    @staticmethod
    def from_dict(d):
        return Konaklama(d.get('otel_adi', ''), d.get('fiyat', 0), d.get('yildiz', 5), d.get('ozellikler', []), d.get('aciklama', ''))

class Plan:
    _next_id = 1
    def __init__(self, rota, aktiviteler=None):
        self.plan_id = Plan._next_id; Plan._next_id += 1
        self.rota = rota; self.aktiviteler = aktiviteler or []

# ═══════════════════════════════════════════
#  DESTİNASYON VERİTABANI (20 destinasyon)
# ═══════════════════════════════════════════
DESTS = [
    dict(id=1, name="Santorini", country="Yunanistan", flag="🇬🇷", cont="Avrupa",
         rating=4.9, price=280, color="#162a70", lat=36.4, lon=25.4,
         tags=["Romantik","Lüks","Deniz"],
         desc="Ege'nin incisi — beyaz evler, mavi kubbeler ve eşsiz gün batımı.",
         hotels=[
             Konaklama("Oia Palace",420,5,["Sonsuzluk Havuzu","Kaldera Manzarası","Butler","Spa"],"Oia'nın kalbinde kaldera manzaralı lüks suite'ler."),
             Konaklama("Fira Boutique",195,4,["Mağara Oda","Restoran","Bar","Manzara Terası"],"Fira'da geleneksel mağara oda deneyimi."),
         ],
         places=[
             dict(name="Oia Köyü", type="İkon", icon="🌅", desc="Dünyanın en meşhur gün batımı noktası."),
             dict(name="Kırmızı Plaj", type="Doğa", icon="🏖", desc="Volkanik kırmızı kayalıklar arasında siyah kum."),
             dict(name="Akrotiri Kazısı", type="Arkeoloji", icon="🏛", desc="3600 yıllık Bronz Çağı kalıntıları."),
             dict(name="Kaldera Turu", type="Aktivite", icon="⛵", desc="Tekneyle volkanik kalderayı keşfet."),
         ]),
    dict(id=2, name="Bali", country="Endonezya", flag="🇮🇩", cont="Asya",
         rating=4.8, price=155, color="#0d3d1a",
         tags=["Doğa","Kültür","Sörf"],
         desc="Tanrıların adası — pirinç tarlaları, tapınaklar, tropikal orman.",
         hotels=[
             Konaklama("Ubud Jungle Resort",380,5,["Orman Manzarası","Yoga","Organik Restoran","Sonsuzluk Havuzu"],"Ubud ormanında maymunlarla komşuluk."),
             Konaklama("Seminyak Beach",195,4,["Özel Havuz","Plaj","Bisiklet"],"Seminyak plajına sıfır butik villa."),
         ],
         places=[
             dict(name="Tanah Lot", type="Kültür", icon="🛕", desc="Okyanus ortasındaki ikonik tapınak."),
             dict(name="Tegallalang Tarlaları", type="Doğa", icon="🌾", desc="UNESCO korumalı pirinç terasları."),
             dict(name="Maymun Ormanı", type="Doğa", icon="🐒", desc="600+ Macaque maymununun kutsal evi."),
             dict(name="Seminyak Sahili", type="Plaj", icon="🌊", desc="Sörf ve gün batımı bar kültürü."),
         ]),
    dict(id=3, name="Maldivler", country="Maldivler", flag="🇲🇻", cont="Asya",
         rating=5.0, price=680, color="#003880",
         tags=["Lüks","Dalış","Balayı"],
         desc="Dünyanın en sığ ve en mavi sularında su bungalov cenneti.",
         hotels=[
             Konaklama("Amari Havoosdhoo",850,5,["Su Bungalov","Dalış","All-Inclusive","Sualtı Restoran"],"Mercan resifleri üzerinde yüzen cennet."),
             Konaklama("Coco Palm Dhuni",580,5,["Özel Plaj","Snorkeling","Biyosfer Rezervi"],"Ekolojik lüks ve mavi lagün."),
         ],
         places=[
             dict(name="Vaadhoo Işıklı Plaj", type="Doğa", icon="✨", desc="Biyolüminesan planktonların mavi ışıltısı."),
             dict(name="Hanifaru Körfezi", type="Dalış", icon="🦈", desc="Manta vatozlarıyla yüzme deneyimi."),
             dict(name="Malé Şehri", type="Kültür", icon="🕌", desc="Dünyanın en küçük başkenti."),
             dict(name="Mercan Bahçeleri", type="Sualtı", icon="🐠", desc="Kristal sularda tropik balıklar."),
         ]),
    dict(id=4, name="Paris", country="Fransa", flag="🇫🇷", cont="Avrupa",
         rating=4.7, price=340, color="#4a2808",
         tags=["Romantik","Sanat","Gastronomi"],
         desc="Işık şehri — moda, sanat, aşk ve Fransız mutfağının kalbi.",
         hotels=[
             Konaklama("Le Marais Boutique",480,5,["Tarihi Bina","Michelin Restoran","Concierge","Spa"],"Le Marais'de 17. yüzyıl binasında modern lüks."),
             Konaklama("Montmartre Garni",280,4,["Sacré-Cœur Manzarası","Kahvaltı","WiFi"],"Sanatçılar semtinde şirin Parisien deneyimi."),
         ],
         places=[
             dict(name="Eyfel Kulesi", type="İkon", icon="🗼", desc="1889'dan beri Paris'in simgesi."),
             dict(name="Louvre Müzesi", type="Sanat", icon="🖼", desc="Mona Lisa ve dünyanın en büyük koleksiyonu."),
             dict(name="Montmartre", type="Kültür", icon="🎨", desc="Kaldırım kafeleri ve Sacré-Cœur."),
             dict(name="Seine Kruvaziyer", type="Aktivite", icon="🚢", desc="Gece nehir turu, köprü manzaraları."),
         ]),
    dict(id=5, name="Tokyo", country="Japonya", flag="🇯🇵", cont="Asya",
         rating=4.9, price=300, color="#800020",
         tags=["Kültür","Teknoloji","Anime"],
         desc="Gelecek ve gelenek iç içe — neon, sakura, suşi ve robot restoranlar.",
         hotels=[
             Konaklama("Shinjuku Granbell",280,4,["Tasarım Otel","Şehir Manzarası","Rooftop Bar"],"Avant-garde tasarım ve Fuji manzarası."),
             Konaklama("Ryokan Asakusa",220,4,["Tatami","Onsen","Kimono","Akşam Yemeği"],"Geleneksel Japon konağında otantik deneyim."),
         ],
         places=[
             dict(name="Shibuya Geçidi", type="İkon", icon="🚦", desc="Dünyanın en kalabalık yaya geçidi."),
             dict(name="Senso-ji", type="Tarihi", icon="⛩", desc="628'den kalma Tokyo'nun en eski tapınağı."),
             dict(name="Akihabara", type="Eğlence", icon="🎮", desc="Elektronik ve anime cenneti."),
             dict(name="Fuji Dağı", type="Doğa", icon="🗻", desc="Japonya'nın kutsal dağı."),
         ]),
    dict(id=6, name="New York", country="ABD", flag="🇺🇸", cont="Amerika",
         rating=4.6, price=420, color="#1a2840",
         tags=["Metropol","Kültür","Broadway"],
         desc="Uyumayan şehir — Broadway, Central Park ve ikonik skyline.",
         hotels=[
             Konaklama("The Plaza",650,5,["Central Park Manzarası","Butler","Spa","Michelin"],"1907'den beri New York'un en prestijli adresi."),
             Konaklama("Brooklyn Heights",320,4,["Manhattan Manzarası","Rooftop Bar","Kahvaltı"],"Köprü manzaralı butik Brooklyn oteli."),
         ],
         places=[
             dict(name="Central Park", type="Doğa", icon="🌳", desc="843 dönümlük şehrin akciğeri."),
             dict(name="MET Müzesi", type="Sanat", icon="🏛", desc="5000 yıl, 2 milyon eser."),
             dict(name="Times Square", type="İkon", icon="🎭", desc="LED'li kalabalık kavşak ve Broadway."),
             dict(name="Özgürlük Anıtı", type="Tarihi", icon="🗽", desc="1886'dan bu yana özgürlüğün simgesi."),
         ]),
    dict(id=7, name="Dubai", country="BAE", flag="🇦🇪", cont="Orta Doğu",
         rating=4.8, price=380, color="#7a5500",
         tags=["Lüks","Alışveriş","Mimari"],
         desc="Çöl ortasında mega lüks — Burj Khalifa, altın ve yapay adalar.",
         hotels=[
             Konaklama("Atlantis The Palm",580,5,["Aquapark","Özel Plaj","Akvaryum","Michelin"],"Palm Jumeirah'da efsanevi tatil kompleksi."),
             Konaklama("Burj Al Arab",1800,5,["7 Yıldız","Helikopter","Butler 24/7","9 Restoran"],"Dünyanın en prestijli oteli."),
         ],
         places=[
             dict(name="Burj Khalifa", type="Mimari", icon="🏗", desc="828 metreyle dünyanın en yüksek binası."),
             dict(name="Altın Çarşısı", type="Alışveriş", icon="🛍", desc="Geleneksel altın ve baharat pazarı."),
             dict(name="Çöl Safarisi", type="Aktivite", icon="🐪", desc="Kum tepelerinde 4x4 ve deve gezisi."),
             dict(name="Dubai Mall", type="Alışveriş", icon="🏬", desc="Buz pateni ve akvaryumlu dev AVM."),
         ]),
    dict(id=8, name="İstanbul", country="Türkiye", flag="🇹🇷", cont="Avrupa/Asya",
         rating=4.9, price=190, color="#7a1010",
         tags=["Tarih","Kültür","Gastronomi"],
         desc="İki kıtanın buluştuğu şehir — Boğaz, Osmanlı mirası, dünya mutfağı.",
         hotels=[
             Konaklama("Çırağan Palace",450,5,["Boğaz Manzarası","Osmanlı Sarayı","Spa","Özel Plaj"],"Sultanların sarayında Boğaz kenarı lüks."),
             Konaklama("Sultanahmet Butik",180,4,["Tarihi Yarımada","Ayasofya Manzarası","Hamam"],"Tarihi yarımadanın kalbinde."),
         ],
         places=[
             dict(name="Ayasofya", type="Tarihi", icon="🕌", desc="537'den beri ayakta, Bizans-Osmanlı mucizesi."),
             dict(name="Topkapı Sarayı", type="Tarihi", icon="🏰", desc="Osmanlı'nın 400 yıllık iktidar merkezi."),
             dict(name="Boğaz Turu", type="Aktivite", icon="⛵", desc="Avrupa'dan Asya'ya vapur keyfi."),
             dict(name="Kapalıçarşı", type="Kültür", icon="🛒", desc="4000 dükkanla dünyanın en büyük çarşısı."),
         ]),
    dict(id=9, name="Roma", country="İtalya", flag="🇮🇹", cont="Avrupa",
         rating=4.8, price=270, color="#6a3808",
         tags=["Tarih","Sanat","Gastronomi"],
         desc="Sonsuz şehir — Kolezyum, Vatikan ve İtalyan mutfağının beşiği.",
         hotels=[
             Konaklama("Hotel de Russie",480,5,["Bahçe","Spa","Fine Dining","Butler"],"Via del Babuino'da efsanevi hotel."),
             Konaklama("Trastevere Inn",130,3,["Tarihi Semt","Kahvaltı","Çatı Terası"],"Romantik Trastevere'de gerçek Roma."),
         ],
         places=[
             dict(name="Kolezyum", type="Tarihi", icon="🏟", desc="MS 72'den kalma 80.000 kişilik amfitiyatro."),
             dict(name="Vatikan", type="Sanat", icon="🎨", desc="Michelangelo'nun Sistina Şapeli."),
             dict(name="Trevi Çeşmesi", type="İkon", icon="⛲", desc="Baroque devri su başyapıtı."),
             dict(name="Pantheon", type="Mimari", icon="🏛", desc="MS 125'ten, insanlığın en mükemmel binası."),
         ]),
    dict(id=10, name="Barselona", country="İspanya", flag="🇪🇸", cont="Avrupa",
         rating=4.7, price=260, color="#701008",
         tags=["Mimari","Plaj","Gece Hayatı"],
         desc="Gaudí'nin şehri — La Rambla, Sagrada Familia ve Akdeniz kıyıları.",
         hotels=[
             Konaklama("W Barcelona",420,5,["Plaj","Rooftop Bar","Spa","Design Hotel"],"Barceloneta plajında yelken biçimli futurizm."),
             Konaklama("Gothic Quarter",140,3,["Tarihi Merkez","Rambla Yakını","Kahvaltı"],"Gotik mahallede 15. yüzyıl taş bina."),
         ],
         places=[
             dict(name="Sagrada Familia", type="Mimari", icon="⛪", desc="1882'den beri inşaatta Gaudí'nin başyapıtı."),
             dict(name="Park Güell", type="Sanat", icon="🎨", desc="Renkli mozaiklerle fantezi parkı."),
             dict(name="La Boqueria", type="Gastronomi", icon="🍅", desc="1840'tan beri Akdeniz lezzetlerinin pazarı."),
             dict(name="Camp Nou", type="Spor", icon="⚽", desc="FC Barcelona'nın efsanevi yuvası."),
         ]),
    dict(id=11, name="Sidney", country="Avustralya", flag="🇦🇺", cont="Okyanusya",
         rating=4.7, price=480, color="#083888",
         tags=["Plaj","Kültür","Sörf"],
         desc="Harbour Bridge, Opera Binası ve dünya sınıfı plajlarıyla ışıklı şehir.",
         hotels=[
             Konaklama("Park Hyatt Sydney",600,5,["Opera Manzarası","Rooftop Havuz","Butler","Fine Dining"],"Opera Binası karşısında eşsiz Harbour manzarası."),
             Konaklama("Bondi Retreat",280,4,["Plaj Manzarası","Sörf Dersi","Kahvaltı"],"Bondi plajında sağlıklı yaşam oteli."),
         ],
         places=[
             dict(name="Opera Binası", type="Kültür", icon="🎭", desc="UNESCO Mirası, mimarinin mucizesi."),
             dict(name="Bondi Plajı", type="Plaj", icon="🏄", desc="Dünyanın en ünlü plajlarından."),
             dict(name="Harbour Köprüsü", type="İkon", icon="🌉", desc="1932'den beri dünyanın en büyük çelik kemeri."),
             dict(name="Blue Mountains", type="Doğa", icon="🏔", desc="UNESCO'nun uçurumları ve şelaleleri."),
         ]),
    dict(id=12, name="Antalya", country="Türkiye", flag="🇹🇷", cont="Avrupa",
         rating=4.8, price=150, color="#004a7a",
         tags=["Tatil","Plaj","All-Inclusive"],
         desc="Türkiye'nin turizm cenneti — Akdeniz mavisi, antik kentler, ultra AI.",
         hotels=[
             Konaklama("Rixos Belek",280,5,["Ultra AI","Golf","Aquapark","Özel Plaj"],"Akdeniz'in en prestijli resort kompleksi."),
             Konaklama("Kaleiçi Butik",120,4,["Tarihi Kaleiçi","Konak","Liman Manzarası"],"Roma surları içinde Osmanlı konağı."),
         ],
         places=[
             dict(name="Kaleiçi", type="Tarihi", icon="🏛", desc="Roma-Bizans-Osmanlı izleri taşıyan liman."),
             dict(name="Aspendos", type="Arkeoloji", icon="🏺", desc="MS 155, dünyanın en iyi korunan antik tiyatrosu."),
             dict(name="Düden Şelalesi", type="Doğa", icon="💧", desc="Akdeniz'e dökülen şelale ve mağaralar."),
             dict(name="Belek Plajları", type="Plaj", icon="⛱", desc="Mavi bayraklı bembeyaz kumsallar."),
         ]),
    dict(id=13, name="Prag", country="Çek Cumhuriyeti", flag="🇨🇿", cont="Avrupa",
         rating=4.8, price=180, color="#2a1a5a",
         tags=["Tarih","Romantik","Mimari"],
         desc="Yüz Kuleli Şehir — Gotik kaleler, peri masalı sokaklar ve Bohemian ruh.",
         hotels=[
             Konaklama("Augustine Prague",390,5,["13. yy Manastır","Kafedrale Manzara","Spa","Bar"],"Augustinyan manastırından dönüştürülmüş 5 yıldızlı."),
             Konaklama("Old Town Inn",140,3,["Eski Şehir","Kahvaltı","Tarihi Bina"],"Astroloji saatine 2 dakika yürüme mesafesi."),
         ],
         places=[
             dict(name="Praha Kalesi", type="Tarihi", icon="🏰", desc="Dünyanın en büyük antik kale kompleksi."),
             dict(name="Charles Köprüsü", type="İkon", icon="🌉", desc="14. yüzyıldan 30 aziz heykeli taşıyan köprü."),
             dict(name="Astronomik Saat", type="Kültür", icon="🕐", desc="1410 yapımı, saatte bir dans eden figürler."),
             dict(name="Vinohrady Semti", type="Gece Hayatı", icon="🍺", desc="Çek birasının kalbi, ev sörfü bölgesi."),
         ]),
    dict(id=14, name="Kyoto", country="Japonya", flag="🇯🇵", cont="Asya",
         rating=4.9, price=250, color="#3a1a5a",
         tags=["Tarih","Zen","Sakura"],
         desc="Japonya'nın eski başkenti — 1600 tapınak, geisha kültürü ve bambu ormanları.",
         hotels=[
             Konaklama("Tawaraya Ryokan",680,5,["300 Yıllık","Kaiseki","Bahçe","Onsen"],"Japonya'nın en prestijli geleneksel misafirhanesi."),
             Konaklama("The Celestine Kyoto",280,4,["Modern","Zen Tasarım","Arashiyama Yakını"],"Doğa ile buluşan çağdaş konfor."),
         ],
         places=[
             dict(name="Fushimi Inari", type="Tarihi", icon="⛩", desc="Binlerce turuncu torii kapısı tüneli."),
             dict(name="Arashiyama Bambu", type="Doğa", icon="🎋", desc="Yüksek bambu gölgesinde meditasyon yürüyüşü."),
             dict(name="Gion Hanamikoji", type="Kültür", icon="🌸", desc="Geisha mahallesinin taş döşeli sokakları."),
             dict(name="Kinkaku-ji", type="Tarihi", icon="🏯", desc="Altın Köşk — göl kenarında yaldızlı Zen tapınağı."),
         ]),
    dict(id=15, name="Cape Town", country="Güney Afrika", flag="🇿🇦", cont="Afrika",
         rating=4.7, price=220, color="#1a4a2a",
         tags=["Doğa","Plaj","Safari"],
         desc="Tablo Dağı'nın gölgesinde — şarap ülkesi, penguen kolonisi ve Cape vaadi.",
         hotels=[
             Konaklama("One&Only Cape Town",520,5,["Marina","Spa","Robben Ada Manzarası","Fine Dining"],"Waterfront Marina'da spektaküler konum."),
             Konaklama("The Silo Hotel",650,5,["Grain Silo","Havuz","Tablo Dağı Manzarası"],"Tarihi tahıl deposundan ikonik butik otel."),
         ],
         places=[
             dict(name="Tablo Dağı", type="Doğa", icon="🏔", desc="Cape Town'un taçı, teleferikle çıkılır."),
             dict(name="Boulders Plajı", type="Doğa", icon="🐧", desc="Yürüyerek ulaşılan Afrika penguenleri kolonisi."),
             dict(name="Cape of Good Hope", type="İkon", icon="🌊", desc="Afrika'nın güneybatı ucu, efsanevi burun."),
             dict(name="Stellenbosch Şarap", type="Gastronomi", icon="🍷", desc="Dünyanın en iyi şarap bölgelerinden biri."),
         ]),
    dict(id=16, name="Venedik", country="İtalya", flag="🇮🇹", cont="Avrupa",
         rating=4.9, price=380, color="#0a2a60",
         tags=["Romantik","Tarih","Gondol"],
         desc="Su üzerinde şehir — 118 ada, 400 köprü ve gondolların büyüsü.",
         hotels=[
             Konaklama("Gritti Palace",750,5,["Grand Canal","15. yy Saray","Butler","Spa"],"Doçlar sarayından dönüştürülmüş efsanevi otel."),
             Konaklama("Al Ponte Antico",320,4,["Rialto Köprüsü","Kanal Manzarası","Tarihi Bina"],"Rialto Köprüsü karşısında Gotik palazzo."),
         ],
         places=[
             dict(name="San Marco Meydanı", type="İkon", icon="🕊", desc="Venedik'in kalbi, Doge Sarayı ve bazilika."),
             dict(name="Gondol Turu", type="Aktivite", icon="🚣", desc="Dar kanallardan gondolla romantik yolculuk."),
             dict(name="Murano Adası", type="Kültür", icon="🏺", desc="800 yıllık cam ustalarının adası."),
             dict(name="Rialto Köprüsü", type="Tarihi", icon="🌉", desc="1591 yapımı, ticaretin kalbi."),
         ]),
    dict(id=17, name="Marakeş", country="Fas", flag="🇲🇦", cont="Afrika",
         rating=4.6, price=160, color="#6a2a10",
         tags=["Kültür","Egzotik","Pazar"],
         desc="Kırmızı şehir — labirent medina, Berberi kültürü ve Sahara kapısı.",
         hotels=[
             Konaklama("La Mamounia",550,5,["Bahçe","Spa","Churchill'in Favori","Atlas Manzarası"],"Fas kraliçesinin 1923'ten beri en prestijli oteli."),
             Konaklama("Riad Farnatchi",280,5,["Geleneksel Riad","Havuz","Kişisel Şef","Medina Merkezi"],"El dokuması kumaşlar ve turunç bahçeli riad."),
         ],
         places=[
             dict(name="Djemaa el-Fna", type="Kültür", icon="🎪", desc="UNESCO, günde iki kez değişen açık hava tiyatrosu."),
             dict(name="Bahia Sarayı", type="Tarihi", icon="🏰", desc="19. yy vezirinin 8 hektarlık sarayı."),
             dict(name="Majorelle Bahçesi", type="Doğa", icon="🌵", desc="Yves Saint Laurent'in kobalt mavi vahası."),
             dict(name="Medina Souks", type="Alışveriş", icon="🛍", desc="El işi deri, baharat ve kilimler."),
         ]),
    dict(id=18, name="Singapur", country="Singapur", flag="🇸🇬", cont="Asya",
         rating=4.8, price=320, color="#003344",
         tags=["Teknoloji","Yemek","Mimari"],
         desc="Aslan şehir — fütürist bahçeler, Michelin street food ve ikonik skyline.",
         hotels=[
             Konaklama("Marina Bay Sands",480,5,["SkyPark Havuzu","Casino","Sonsuz Manzara","ArtScience"],"Dünyanın en çok fotoğraflanan otel çatısı."),
             Konaklama("Capella Sentosa",620,5,["Özel Ada","Plaj","Spa","Butler"],"Sentosa Adası'nda sığınak gibi lüks resort."),
         ],
         places=[
             dict(name="Gardens by the Bay", type="Doğa", icon="🌿", desc="Süper ağaçlar ve futuristik biodome seraları."),
             dict(name="Hawker Centre", type="Gastronomi", icon="🍜", desc="Michelin yıldızlı sokak yemeği kültürü."),
             dict(name="Marina Bay", type="İkon", icon="🌃", desc="Lazer şov ve ışık sanatı gösteri alanı."),
             dict(name="Chinatown & Little India", type="Kültür", icon="🏮", desc="Çok kültürlü sokak yaşamının renkleri."),
         ]),
    dict(id=19, name="Amsterdam", country="Hollanda", flag="🇳🇱", cont="Avrupa",
         rating=4.6, price=290, color="#0a3a20",
         tags=["Bisiklet","Kültür","Kanal"],
         desc="Kanallar şehri — bisiklet, Rembrandt ve 1001 köprünün Venedik'i.",
         hotels=[
             Konaklama("Conservatorium Hotel",480,5,["Tarihi Bina","Müze Yakını","Spa","Fine Dining"],"Konservatuardan dönüştürülmüş Grand Café."),
             Konaklama("The Hoxton Amsterdam",220,4,["Kanal Manzarası","Lounge Bar","Kahvaltı","Tasarım"],"Hip ve uygun fiyatlı kanal kenarı butiği."),
         ],
         places=[
             dict(name="Rijksmuseum", type="Sanat", icon="🖼", desc="Rembrandt ve Vermeer'in dünyadaki en büyük koleksiyonu."),
             dict(name="Anne Frank Evi", type="Tarihi", icon="🏠", desc="Tarihin en dokunulan gizli sığınağı."),
             dict(name="Kanal Turu", type="Aktivite", icon="⛵", desc="17. yy'dan kalma halka açık su yollarında tekne."),
             dict(name="Vondelpark", type="Doğa", icon="🌷", desc="Lalelerin ve bisikletçilerin buluşma noktası."),
         ]),
    dict(id=20, name="Rio de Janeiro", country="Brezilya", flag="🇧🇷", cont="Amerika",
         rating=4.7, price=230, color="#1a4a10",
         tags=["Karneval","Plaj","Doğa"],
         desc="Mucizeli şehir — Kurtarıcı Mesih, Copacabana ve samba ritmi.",
         hotels=[
             Konaklama("Belmond Copacabana Palace",580,5,["Okyanus Manzarası","Havuz","Fine Dining","Tarihi"],"1923'ten beri Copacabana'nın kraliçesi."),
             Konaklama("Santa Teresa Hotel",320,4,["Manzaralı Tepe","Pool","Brezilya Kültürü"],"Tarihi Santa Teresa semtinde sanat oteli."),
         ],
         places=[
             dict(name="Kurtarıcı Mesih", type="İkon", icon="✝", desc="Dünyanın 7. harikasından biri, 38 m heykel."),
             dict(name="Copacabana Plajı", type="Plaj", icon="🏖", desc="4km'lik efsanevi kumsal, dünya müziğinin kalbi."),
             dict(name="Sugarloaf Dağı", type="Doğa", icon="🚡", desc="Teleferikle Guanabara Körfezi'ne panoramik bakış."),
             dict(name="Lapa Arches", type="Gece Hayatı", icon="🎵", desc="Samba barları ve Rio'nun en canlı geceleri."),
         ]),
]

MAP_PTS = [
    ("Paris",0.36,0.22),("Roma",0.40,0.28),("Barselona",0.32,0.26),
    ("Venedik",0.39,0.24),("İstanbul",0.46,0.25),("Antalya",0.47,0.30),
    ("Prag",0.41,0.20),("Amsterdam",0.37,0.19),
    ("Tokyo",0.80,0.22),("Kyoto",0.79,0.24),
    ("Dubai",0.55,0.32),("Maldivler",0.58,0.42),("Singapur",0.72,0.42),("Bali",0.75,0.44),
    ("Santorini",0.44,0.26),("New York",0.17,0.23),("Rio de Janeiro",0.23,0.52),
    ("Sidney",0.81,0.58),("Cape Town",0.45,0.64),("Marakeş",0.36,0.32),
]

# ═══════════════════════════════════════════
#  FİYATLANDIRMA MANTIĞI
#  Kişi sayısı artınca birim fiyat artar (grup indirimi yok, tersine kalabalık primi)
# ═══════════════════════════════════════════
ADMIN_INDIRIM = 0.15  # Admin rezervasyonlarına %15 ekstra indirim

def hesapla_fiyat(baz_fiyat, n_gece, n_yetiskin, n_cocuk, is_admin=False):
    """
    1 kişi: baz fiyat
    2 kişi: +%15
    3-4 kişi: +%25 her kişi için
    5+ kişi: +%35 her kişi için
    Çocuk: baz fiyatın %50'si
    Admin: toplama %15 ekstra indirim
    """
    if n_yetiskin == 1:
        carpan = 1.0
    elif n_yetiskin == 2:
        carpan = 1.15
    elif n_yetiskin <= 4:
        carpan = 1.25
    else:
        carpan = 1.35
    oda_fiyat = baz_fiyat * carpan
    cocuk_fiyat = baz_fiyat * 0.5
    gece_toplam = oda_fiyat * n_yetiskin + cocuk_fiyat * n_cocuk
    toplam = gece_toplam * n_gece
    if is_admin:
        toplam = toplam * (1 - ADMIN_INDIRIM)
    return round(toplam)

def fiyat_aciklamasi(n_yetiskin, is_admin=False):
    if n_yetiskin == 1: base = "Standart fiyat"
    elif n_yetiskin == 2: base = "+%15 çift primi"
    elif n_yetiskin <= 4: base = "+%25 aile primi"
    else: base = "+%35 sülale primi"
    if is_admin:
        return base + " · 🛡 Admin indirimi -%15"
    return base

# ═══════════════════════════════════════════
#  UYGULAMA DURUMU
# ═══════════════════════════════════════════
class State:
    def __init__(self):
        self.user = None; self.role = 'guest'; self.page = 'home'
        self.filt_cont = 'Tümü'; self.search = ''
        self.sort_key = 'puan'   # 'puan' | 'fiyat_asc' | 'fiyat_desc' | 'isim'
        self.bookings = []   # Uygulama boyunca kalıcı — logout'ta silinmez
        self.favs = set(); self.bk_id = 1
        self.users = [
            {"id":1,"name":"Ahmet Yılmaz","email":"ahmet@mail.com","pwd":"123456","role":"user","joined":"2026-01-15","phone":"","city":"İstanbul"},
            {"id":2,"name":"Fatma Kaya","email":"fatma@mail.com","pwd":"123456","role":"user","joined":"2026-03-10","phone":"","city":"Ankara"},
            {"id":3,"name":"Admin","email":"admin@mail.com","pwd":"admin","role":"admin","joined":"2026-01-01","phone":"","city":""},
        ]
        self.nxt_uid = 4
        self._reserv_filter = 'tumu'
        # Ticket sistemi
        self.tickets = []  # {id, user_id, user_name, konu, mesaj, tarih, durum, cevaplar:[]}
        self.nxt_tid = 1

S = State()

# ═══════════════════════════════════════════
#  YARDIMCI STİLLER
# ═══════════════════════════════════════════
def Btn(bg, fg='#fff', hov=None, r=10, pad='9px 18px', fs=13, bold=True):
    hov = hov or bg; fw = '700' if bold else '500'
    return (f"QPushButton{{background:{bg};color:{fg};border:none;border-radius:{r}px;"
            f"padding:{pad};font-size:{fs}px;font-weight:{fw};}}"
            f"QPushButton:hover{{background:{hov};}}"
            f"QPushButton:pressed{{background:{bg};}}")

def Inp():
    return (f"QLineEdit{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};"
            f"border-radius:9px;padding:9px 13px;font-size:13px;}}"
            f"QLineEdit:focus{{border-color:{p('gold')};}}")

def Card():
    return (f"QFrame{{background:{p('card')};border:1.5px solid {p('border')};border-radius:14px;}}"
            f"QFrame:hover{{border-color:{p('brd2')};}}")

# ═══════════════════════════════════════════
#  ÖZEL MESSAGE BOX
# ═══════════════════════════════════════════
class CustomMsgBox(QDialog):
    """Stillendirilmiş özel mesaj kutusu — QMessageBox yerine kullanılır."""
    def __init__(self, parent=None, title="Bilgi", msg="", kind="info"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background:{p('bg')};color:{p('txt')};")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build(title, msg, kind)

    def _build(self, title, msg, kind):
        icons = {'info':'✈', 'warning':'⚠', 'error':'✗', 'success':'✅', 'confirm':'❓'}
        icon_cols = {'info': p('blue2'), 'warning': p('orange'), 'error': p('red'),
                     'success': p('grn'), 'confirm': p('gold')}
        ico = icons.get(kind, '✈')
        col = icon_cols.get(kind, p('gold'))

        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        # Header şeridi
        hdr = QFrame(); hdr.setFixedHeight(6)
        hdr.setStyleSheet(f"background:{col};border-radius:0;")
        outer.addWidget(hdr)

        body = QFrame()
        body.setStyleSheet(f"background:{p('bg2')};border:1px solid {p('border')};border-radius:0 0 14px 14px;")
        bv = QVBoxLayout(body); bv.setContentsMargins(28, 22, 28, 22); bv.setSpacing(14)

        # İkon + başlık
        row = QHBoxLayout(); row.setSpacing(14)
        ic_lbl = QLabel(ico); ic_lbl.setFixedSize(48, 48); ic_lbl.setAlignment(Qt.AlignCenter)
        ic_lbl.setStyleSheet(f"background:{col}22;border:2px solid {col}55;border-radius:24px;"
                             f"font-size:22px;color:{col};")
        tt = QLabel(title)
        tt.setStyleSheet(f"color:{p('txt')};font-size:16px;font-weight:700;background:transparent;border:none;")
        row.addWidget(ic_lbl); row.addWidget(tt); row.addStretch()
        bv.addLayout(row)

        # Mesaj
        ml = QLabel(msg); ml.setWordWrap(True)
        ml.setStyleSheet(f"color:{p('txt2')};font-size:13px;background:transparent;border:none;line-height:1.5;")
        bv.addWidget(ml)

        # Ayırıcı
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{p('border')};border:none;")
        bv.addWidget(sep)

        # Buton(lar)
        btn_row = QHBoxLayout(); btn_row.addStretch()
        ok_btn = QPushButton("  Tamam  "); ok_btn.setFixedHeight(38)
        ok_btn.setStyleSheet(Btn(col, '#fff' if kind != 'info' else '#09090f',
                                 col, 9, '7px 24px', 13))
        ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        bv.addLayout(btn_row)

        outer.addWidget(body)

    @staticmethod
    def info(parent, title, msg):
        d = CustomMsgBox(parent, title, msg, 'info'); d.exec_()

    @staticmethod
    def warning(parent, title, msg):
        d = CustomMsgBox(parent, title, msg, 'warning'); d.exec_()

    @staticmethod
    def error(parent, title, msg):
        d = CustomMsgBox(parent, title, msg, 'error'); d.exec_()

    @staticmethod
    def success(parent, title, msg):
        d = CustomMsgBox(parent, title, msg, 'success'); d.exec_()


# ═══════════════════════════════════════════
#  DÜNYA HARİTASI — Google Maps (WebEngine)
# ═══════════════════════════════════════════
def _build_leaflet_maps_html():
    """Canvas tabanlı interaktif dünya haritası — CDN/internet gerektirmez."""
    # Koordinatlardan SVG pin data üret
    pins_data = []
    hotel_pins_data = []
    import random as _rnd2; _rnd2.seed(42)
    for d in DESTS:
        lat, lon = _APPROX_COORDS.get(d['name'], (d.get('lat',0), d.get('lon',0)))
        pins_data.append({
            'name': d['name'], 'lat': lat, 'lon': lon,
            'flag': d['flag'], 'country': d['country'],
            'rating': d['rating'], 'price': d['price'],
            'tags': ', '.join(d['tags']),
            'hotels_info': [{'name': h.otel_adi, 'price': h.fiyat, 'stars': h.yildiz} for h in d['hotels']]
        })
        for h in d['hotels']:
            olat = lat + _rnd2.uniform(0.05, 0.15) * _rnd2.choice([-1,1])
            olon = lon + _rnd2.uniform(0.05, 0.15) * _rnd2.choice([-1,1])
            hotel_pins_data.append({'name': h.otel_adi, 'dest': d['name'], 'flag': d['flag'],
                                     'lat': olat, 'lon': olon, 'price': h.fiyat, 'stars': h.yildiz})

    import json as _json
    pins_json = _json.dumps(pins_data, ensure_ascii=False)
    hotel_pins_json = _json.dumps(hotel_pins_data, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:100%; height:100%; background:#09090f; overflow:hidden; font-family:Arial,sans-serif; }}
#wrap {{ position:relative; width:100%; height:100%; }}
canvas {{ position:absolute; top:0; left:0; display:block; }}
#tooltip {{
  position:absolute; display:none; z-index:100;
  background:#141425; border:1.5px solid #2a2a45; border-radius:12px;
  padding:10px 14px; min-width:180px; max-width:240px;
  box-shadow:0 4px 24px rgba(0,0,0,.8); color:#dcdcec; font-size:12px; line-height:1.6; pointer-events:none;
}}
#tooltip .tt-title {{ color:#e8b84b; font-size:13px; font-weight:700; }}
#tooltip .tt-sub {{ color:#9090aa; font-size:10px; }}
#tooltip .tt-price {{ color:#e8b84b; font-weight:700; }}
#tooltip .tt-hotels {{ margin-top:7px; border-top:1px solid #2a2a45; padding-top:6px; }}
#tooltip .tt-hotrow {{ background:#1e1e3a; border-radius:6px; padding:4px 7px; margin-top:4px; font-size:10px; }}
#btn-visit {{
  display:none; position:absolute; z-index:101;
  background:#c9922a; color:#000; border:none; border-radius:7px;
  padding:5px 13px; font-size:10px; font-weight:700; cursor:pointer;
  box-shadow:0 2px 8px #c9922a66;
}}
#btn-visit:hover {{ background:#e8b84b; }}
#legend {{
  position:absolute; bottom:14px; left:12px; z-index:50;
  background:#141425cc; border:1px solid #2a2a45; border-radius:8px;
  padding:7px 12px; font-size:10px; color:#9090aa;
}}
#legend span {{ display:inline-block; border-radius:50%; margin-right:5px; vertical-align:middle; }}
#legend .lh {{ border-radius:3px !important; }}
#zoom-btns {{
  position:absolute; top:14px; right:14px; z-index:50; display:flex; flex-direction:column; gap:4px;
}}
#zoom-btns button {{
  width:28px; height:28px; background:#141425; color:#e8b84b;
  border:1px solid #2a2a45; border-radius:6px; font-size:16px; font-weight:700;
  cursor:pointer; line-height:1;
}}
#zoom-btns button:hover {{ background:#1e1e3a; }}
#attrib {{ position:absolute; bottom:6px; right:8px; font-size:9px; color:#35354a; z-index:50; }}
</style>
</head>
<body>
<div id="wrap">
  <canvas id="bg"></canvas>
  <canvas id="map"></canvas>
  <div id="tooltip"></div>
  <button id="btn-visit" onclick="visitDest()">✈ İncele &amp; Rezerve Et</button>
  <div id="legend">
    <div><span style="width:12px;height:12px;background:#c9922a;box-shadow:0 0 5px #c9922a88;"></span> Destinasyon</div>
    <div style="margin-top:4px"><span class="lh" style="width:10px;height:10px;background:#3a70d8;border-radius:3px;display:inline-block;margin-right:5px;vertical-align:middle;"></span> Otel</div>
  </div>
  <div id="zoom-btns">
    <button onclick="zoom(1.25)">+</button>
    <button onclick="zoom(0.8)">−</button>
  </div>
  <div id="attrib">© Voyager · OpenStreetMap katkıcıları</div>
</div>
<script>
var PINS = {pins_json};
var HOTEL_PINS = {hotel_pins_json};

var bgCanvas = document.getElementById('bg');
var canvas = document.getElementById('map');
var tooltip = document.getElementById('tooltip');
var btnVisit = document.getElementById('btn-visit');
var wrap = document.getElementById('wrap');

var scale = 1.0, offX = 0, offY = 0;
var isDrag = false, dragStart = null, dragOff = null;
var hovPin = null, selPin = null;

function _notify(name) {{
  try {{
    if (window.pybridge && window.pybridge.mapClicked) window.pybridge.mapClicked(name);
  }} catch(e) {{}}
}}
function visitDest() {{
  if (selPin) _notify(selPin.name);
  hideTip();
}}

// Lon/lat → canvas pixels (Mercator)
function geoToCanvas(lat, lon, W, H) {{
  var x = ((lon + 180) / 360) * W * scale + offX;
  var sinLat = Math.sin(lat * Math.PI / 180);
  var y = (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * H * scale + offY;
  return [x, y];
}}

function resize() {{
  var W = wrap.clientWidth, H = wrap.clientHeight;
  bgCanvas.width = W; bgCanvas.height = H;
  canvas.width = W; canvas.height = H;
  drawBg(); drawPins();
}}

// — Kıta kara şekilleri (basitleştirilmiş poligonlar) —
// [lon, lat] nokta listeleri
var LAND = [
  // Avrupa + Batı Asya
  [[-10,35],[40,35],[60,45],[60,70],[-10,70],[-10,35]],
  // Afrika
  [[-18,35],[52,35],[52,-35],[-18,-35],[-18,35]],
  // Asya (kaba)
  [[40,10],[145,10],[145,75],[40,75],[40,10]],
  // Kuzey Amerika
  [[-170,15],[-50,15],[-50,75],[-170,75],[-170,15]],
  // Güney Amerika
  [[-82,-55],[-34,-55],[-34,15],[-82,15],[-82,-55]],
  // Avustralya
  [[112,-44],[154,-44],[154,-10],[112,-10],[112,-44]],
  // Grönland
  [[-72,58],[-10,58],[-10,84],[-72,84],[-72,58]],
];

var CONT_LABELS = [
  [20,52,"AVRUPA"],[20,5,"AFRİKA"],[90,45,"ASYA"],
  [-100,45,"K.AMERİKA"],[-55,-15,"G.AMERİKA"],[135,-25,"OKYANUSYA"],
];

function drawBg() {{
  var c = bgCanvas, ctx = c.getContext('2d');
  var W = c.width, H = c.height;
  // Arka plan
  var grd = ctx.createLinearGradient(0,0,0,H);
  grd.addColorStop(0,'#05050f'); grd.addColorStop(1,'#080818');
  ctx.fillStyle = grd; ctx.fillRect(0,0,W,H);

  // Izgara (meridyen/paralel çizgileri)
  ctx.strokeStyle = '#0f0f25'; ctx.lineWidth = 0.5;
  for (var lon2 = -180; lon2 <= 180; lon2 += 30) {{
    var x1 = geoToCanvas(0, lon2, W, H)[0];
    ctx.beginPath(); ctx.moveTo(x1, 0); ctx.lineTo(x1, H); ctx.stroke();
  }}
  for (var lat2 = -90; lat2 <= 90; lat2 += 30) {{
    var y1 = geoToCanvas(lat2, 0, W, H)[1];
    ctx.beginPath(); ctx.moveTo(0, y1); ctx.lineTo(W, y1); ctx.stroke();
  }}

  // Ekvator
  ctx.strokeStyle = '#1a1a3a'; ctx.lineWidth = 1; ctx.setLineDash([4,6]);
  var eqY = geoToCanvas(0, 0, W, H)[1];
  ctx.beginPath(); ctx.moveTo(0, eqY); ctx.lineTo(W, eqY); ctx.stroke();
  ctx.setLineDash([]);

  // Kara kütlesi
  ctx.fillStyle = '#1a1a38';
  LAND.forEach(function(poly) {{
    ctx.beginPath();
    poly.forEach(function(pt, i) {{
      var xy = geoToCanvas(pt[1], pt[0], W, H);
      if (i===0) ctx.moveTo(xy[0], xy[1]); else ctx.lineTo(xy[0], xy[1]);
    }});
    ctx.closePath(); ctx.fill();
  }});

  // Kara sınır çizgisi
  ctx.strokeStyle = '#252550'; ctx.lineWidth = 1;
  LAND.forEach(function(poly) {{
    ctx.beginPath();
    poly.forEach(function(pt, i) {{
      var xy = geoToCanvas(pt[1], pt[0], W, H);
      if (i===0) ctx.moveTo(xy[0], xy[1]); else ctx.lineTo(xy[0], xy[1]);
    }});
    ctx.closePath(); ctx.stroke();
  }});

  // Kıta etiketleri
  ctx.fillStyle = '#2a2a55'; ctx.font = 'bold 9px Arial'; ctx.textAlign = 'center';
  CONT_LABELS.forEach(function(lbl) {{
    var xy = geoToCanvas(lbl[1], lbl[0], W, H);
    ctx.fillText(lbl[2], xy[0], xy[1]);
  }});
}}

function drawPins() {{
  var c = canvas, ctx = c.getContext('2d');
  var W = c.width, H = c.height;
  ctx.clearRect(0,0,W,H);

  // Otel pinleri (mavi kare)
  HOTEL_PINS.forEach(function(h) {{
    var xy = geoToCanvas(h.lat, h.lon, W, H);
    var x = xy[0], y = xy[1];
    if (x < -10 || x > W+10 || y < -10 || y > H+10) return;
    ctx.fillStyle = '#3a70d8';
    ctx.strokeStyle = '#5a90f8'; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(x-5,y-5,10,10,2) : ctx.rect(x-5,y-5,10,10);
    ctx.fill(); ctx.stroke();
  }});

  // Destinasyon pinleri (altın daire)
  PINS.forEach(function(pin) {{
    var xy = geoToCanvas(pin.lat, pin.lon, W, H);
    var x = xy[0], y = xy[1];
    if (x < -10 || x > W+10 || y < -10 || y > H+10) return;
    var isHov = hovPin && hovPin.name === pin.name;
    var r = isHov ? 10 : 7;

    // Halo
    var halo = ctx.createRadialGradient(x,y,r,x,y,r+10);
    halo.addColorStop(0,'rgba(201,146,42,0.3)'); halo.addColorStop(1,'rgba(201,146,42,0)');
    ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(x,y,r+10,0,Math.PI*2); ctx.fill();

    // Dış halka
    ctx.strokeStyle = isHov ? '#e8b84b' : '#c9922a'; ctx.lineWidth = isHov ? 2.5 : 1.5;
    ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); ctx.stroke();

    // İç dolu
    var grd2 = ctx.createRadialGradient(x,y,0,x,y,r);
    grd2.addColorStop(0, isHov ? '#fff8e0' : '#e8b84b');
    grd2.addColorStop(1, isHov ? '#e8b84b' : '#c9922a');
    ctx.fillStyle = grd2; ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); ctx.fill();
  }});
}}

function getPin(mx, my, W, H) {{
  for (var i = PINS.length-1; i >= 0; i--) {{
    var pin = PINS[i];
    var xy = geoToCanvas(pin.lat, pin.lon, W, H);
    var dx = mx - xy[0], dy = my - xy[1];
    if (dx*dx + dy*dy < 144) return pin; // r=12
  }}
  return null;
}}

function showTip(pin, x, y) {{
  var hotelsHtml = '<div class="tt-hotels"><small style="color:#c9922a;font-weight:700;">🏨 OTELLER</small>';
  pin.hotels_info.forEach(function(h) {{
    var stars = '⭐'.repeat(h.stars);
    hotelsHtml += '<div class="tt-hotrow"><span style="color:#e8b84b;font-weight:700;">' + h.name + '</span> ' + stars +
      '<br><span style="color:#e8b84b;font-weight:700;">$' + h.price + '</span><span style="color:#7a7a99">/gece</span></div>';
  }});
  hotelsHtml += '</div>';
  tooltip.innerHTML =
    '<div class="tt-title">' + pin.flag + ' ' + pin.name + '</div>' +
    '<div class="tt-sub">' + pin.country + '</div>' +
    '<div>⭐ ' + pin.rating + ' &nbsp;|&nbsp; <span class="tt-price">$' + pin.price + '/gece</span></div>' +
    '<div style="color:#7a7a99;font-size:9px">' + pin.tags + '</div>' +
    hotelsHtml;
  var W = wrap.clientWidth, H = wrap.clientHeight;
  var tx = Math.min(x+12, W-255), ty = Math.max(y-40, 4);
  tooltip.style.left = tx+'px'; tooltip.style.top = ty+'px'; tooltip.style.display='block';
  btnVisit.style.left = tx+'px'; btnVisit.style.top = (ty + tooltip.offsetHeight + 4)+'px';
  btnVisit.style.display = 'block';
  selPin = pin;
}}

function hideTip() {{
  tooltip.style.display='none'; btnVisit.style.display='none'; selPin=null;
}}

canvas.addEventListener('mousemove', function(e) {{
  var W = canvas.width, H = canvas.height;
  var pin = getPin(e.offsetX, e.offsetY, W, H);
  if (pin) {{
    canvas.style.cursor = 'pointer';
    if (!hovPin || hovPin.name !== pin.name) {{
      hovPin = pin; drawPins();
    }}
  }} else {{
    if (hovPin) {{ hovPin = null; drawPins(); canvas.style.cursor = 'grab'; }}
    if (!isDrag) canvas.style.cursor = 'grab';
  }}
  if (isDrag && dragStart) {{
    offX = dragOff[0] + (e.clientX - dragStart[0]);
    offY = dragOff[1] + (e.clientY - dragStart[1]);
    drawBg(); drawPins(); hideTip();
  }}
}});

canvas.addEventListener('mousedown', function(e) {{
  isDrag = true; dragStart = [e.clientX, e.clientY]; dragOff = [offX, offY];
  canvas.style.cursor = 'grabbing';
}});

canvas.addEventListener('mouseup', function(e) {{
  var moved = dragStart && (Math.abs(e.clientX-dragStart[0])+Math.abs(e.clientY-dragStart[1])) < 5;
  isDrag = false; dragStart = null; canvas.style.cursor = 'grab';
  if (moved) {{
    var W = canvas.width, H = canvas.height;
    var pin = getPin(e.offsetX, e.offsetY, W, H);
    if (pin) {{ showTip(pin, e.offsetX, e.offsetY); }}
    else hideTip();
  }}
}});

canvas.addEventListener('mouseleave', function() {{ isDrag=false; hovPin=null; drawPins(); }});

canvas.addEventListener('wheel', function(e) {{
  e.preventDefault();
  var factor = e.deltaY < 0 ? 1.15 : 0.87;
  var W = canvas.width, H = canvas.height;
  var mx = e.offsetX, my = e.offsetY;
  offX = mx - (mx - offX) * factor;
  offY = my - (my - offY) * factor;
  scale *= factor;
  scale = Math.max(0.5, Math.min(12, scale));
  drawBg(); drawPins();
}}, {{passive:false}});

function zoom(f) {{
  var W = canvas.width, H = canvas.height;
  var cx = W/2, cy = H/2;
  offX = cx - (cx - offX) * f; offY = cy - (cy - offY) * f;
  scale *= f; scale = Math.max(0.5, Math.min(12, scale));
  drawBg(); drawPins();
}}

// İlk çizim
window.addEventListener('resize', resize);
resize();
</script>
</body>
</html>"""


def _build_leaflet_maps_html_webchannel():
    """QWebChannel destekli versiyon — qwebchannel.js köprüsü ile."""
    base = _build_leaflet_maps_html()
    # QWebChannel köprüsünü head'e ekle, _notify'ı override et
    webchannel_script = """
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
// QWebChannel hazır olunca _notify'ı override et
document.addEventListener('DOMContentLoaded', function() {
  if (typeof QWebChannel !== 'undefined') {
    new QWebChannel(qt.webChannelTransport, function(channel) {
      var bridge = channel.objects.pybridge;
      window._notify = function(destName) {
        if (bridge) bridge.mapClicked(destName);
      };
    });
  }
});
</script>"""
    base = base.replace("</head>", webchannel_script + "\n</head>")
    return base


class _MapBridge(QWidget):
    """JS → Python köprüsü: popup butonundan destinasyon adı alır."""
    map_clicked = pyqtSignal(str)

    from PyQt5.QtCore import pyqtSlot as _slot

    @_slot(str)
    def mapClicked(self, name):   # JS/QWebChannel tarafından çağrılır
        self.map_clicked.emit(name)


class GoogleMapWidget(QWidget):
    """Leaflet.js (OpenStreetMap) WebEngine widget. WebEngine yoksa eski çizim haritasına döner."""
    clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(460)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._web = None
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0)

        if _HAS_WEBENGINE:
            self._web = QWebEngineView()
            self._web.setStyleSheet("background:#09090f;")
            self._web.page().setBackgroundColor(QColor('#09090f'))
            # JS → Python köprüsü kur
            self._bridge = _MapBridge()
            self._bridge.map_clicked.connect(self.clicked)
            try:
                from PyQt5.QtWebChannel import QWebChannel
                self._channel = QWebChannel()
                self._channel.registerObject("pybridge", self._bridge)
                self._web.page().setWebChannel(self._channel)
                html = _build_leaflet_maps_html_webchannel()
            except ImportError:
                html = _build_leaflet_maps_html()
            self._web.setHtml(html, QUrl("about:blank"))
            lay.addWidget(self._web)
        else:
            # Fallback: mevcut QPainter haritası
            self._fallback = MapWidgetFallback()
            self._fallback.clicked.connect(self.clicked)
            lay.addWidget(self._fallback)

    def refresh(self):
        """Destinasyon/otel listesi değişince haritayı yenile."""
        if self._web is not None:
            try:
                from PyQt5.QtWebChannel import QWebChannel
                html = _build_leaflet_maps_html_webchannel()
            except ImportError:
                html = _build_leaflet_maps_html()
            self._web.setHtml(html, QUrl("about:blank"))
        elif hasattr(self, '_fallback'):
            self._fallback.update()

    # ---- eski imza ile uyum ----
    def paintEvent(self, ev):
        if self._web is None:
            super().paintEvent(ev)


# ═══════════════════════════════════════════
#  DÜNYA HARİTASI — Orijinal QPainter (Fallback)
# ═══════════════════════════════════════════
class MapWidgetFallback(QWidget):
    clicked = pyqtSignal(str)
    def __init__(self):
        super().__init__(); self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._hov = None; self.setMouseTracking(True)
        self.setStyleSheet(f"background:{p('bg3')};border-radius:14px;")

    def _xy(self, rx, ry): return int(rx*self.width()), int(ry*self.height())

    def mouseMoveEvent(self, e):
        self._hov = None
        for nm, rx, ry in MAP_PTS:
            x, y = self._xy(rx, ry)
            if abs(e.x()-x)<13 and abs(e.y()-y)<13:
                self._hov = nm; self.setCursor(QCursor(Qt.PointingHandCursor)); break
        else: self.setCursor(QCursor(Qt.ArrowCursor))
        self.update()

    def mousePressEvent(self, e):
        for nm, rx, ry in MAP_PTS:
            x, y = self._xy(rx, ry)
            if abs(e.x()-x)<13 and abs(e.y()-y)<13: self.clicked.emit(nm); return

    def paintEvent(self, ev):
        qp = QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        # ── Arka plan ──
        bg_grad = QLinearGradient(0, 0, 0, H)
        bg_grad.setColorAt(0, QColor('#05050f'))
        bg_grad.setColorAt(1, QColor('#080815'))
        qp.fillRect(0, 0, W, H, QBrush(bg_grad))

        # ── Noktalı kara tanımlama (yaklaşık bbox'lar) ──
        LAND_ZONES = [
            (0.31,0.11, 0.54,0.35),   # Avrupa
            (0.35,0.30, 0.55,0.73),   # Afrika
            (0.47,0.08, 0.92,0.53),   # Asya
            (0.04,0.06, 0.30,0.43),   # Kuzey Amerika
            (0.15,0.36, 0.33,0.75),   # Güney Amerika
            (0.68,0.49, 0.91,0.71),   # Avustralya
        ]
        def is_land(rx, ry):
            for x0,y0,x1,y1 in LAND_ZONES:
                if x0<=rx<=x1 and y0<=ry<=y1: return True
            return False

        dot_ocean = QColor('#131326')
        dot_land  = QColor('#1f1f42')
        dot_r = 2
        cols, rows = 80, 36
        dx = W / cols; dy = H / rows
        qp.setPen(Qt.NoPen)
        for row in range(rows + 1):
            for col in range(cols + 1):
                cx = col * dx + (dx * 0.5 if row % 2 else 0)
                cy = row * dy
                c = dot_land if is_land(cx/W, cy/H) else dot_ocean
                qp.setBrush(QBrush(c))
                qp.drawEllipse(int(cx-dot_r), int(cy-dot_r), dot_r*2, dot_r*2)

        # ── Ekvator & meridyen ──
        qp.setPen(QPen(QColor('#1e1e45'), 1, Qt.DashLine))
        qp.drawLine(0, int(H*.47), W, int(H*.47))
        qp.drawLine(int(W*.50), 0, int(W*.50), H)

        # ── Kıta etiketleri ──
        cont_labels = [
            (0.38,0.20,"AVRUPA"),(0.44,0.53,"AFRİKA"),(0.68,0.22,"ASYA"),
            (0.13,0.18,"K.AMERİKA"),(0.23,0.57,"G.AMERİKA"),(0.78,0.59,"OKYANUSYA"),
        ]
        fnt_cont = QFont("Arial", 7, QFont.Bold)
        qp.setFont(fnt_cont)
        for rx,ry,lbl in cont_labels:
            x,y = int(rx*W), int(ry*H)
            fm = QFontMetrics(fnt_cont); tw = fm.horizontalAdvance(lbl)
            qp.setPen(QPen(QColor('#2a2a55')))
            qp.drawText(x-tw//2, y, lbl)

        # ── Destinasyon noktaları ──
        for nm, rx, ry in MAP_PTS:
            x, y = self._xy(rx, ry); hov = self._hov == nm

            if hov:
                for ring in range(3):
                    rr = 20 + ring*10; alpha = 55 - ring*15
                    gr = QRadialGradient(x,y,rr)
                    gr.setColorAt(0, QColor(201,146,42,alpha))
                    gr.setColorAt(1, QColor(201,146,42,0))
                    qp.setPen(Qt.NoPen); qp.setBrush(QBrush(gr))
                    qp.drawEllipse(x-rr,y-rr,rr*2,rr*2)
            else:
                gr = QRadialGradient(x,y,9)
                gr.setColorAt(0, QColor(201,146,42,50)); gr.setColorAt(1, QColor(201,146,42,0))
                qp.setPen(Qt.NoPen); qp.setBrush(QBrush(gr))
                qp.drawEllipse(x-9,y-9,18,18)

            ring_r = 7 if hov else 5
            qp.setPen(QPen(QColor(p('gold') if hov else p('gold3')), 1))
            qp.setBrush(Qt.NoBrush)
            qp.drawEllipse(x-ring_r,y-ring_r,ring_r*2,ring_r*2)

            r_dot = 4 if hov else 2
            qp.setBrush(QBrush(QColor(p('gold') if hov else p('gold3'))))
            qp.setPen(Qt.NoPen)
            qp.drawEllipse(x-r_dot,y-r_dot,r_dot*2,r_dot*2)

            if hov:
                dest = next((d for d in DESTS if d['name']==nm), None)
                if dest:
                    line1 = f"{dest['flag']}  {nm}"
                    line2 = f"⭐ {dest['rating']}   ${dest['price']}/gece"
                    fnt1 = QFont("Arial",10,QFont.Bold); fnt2 = QFont("Arial",8)
                    fm1 = QFontMetrics(fnt1); fm2 = QFontMetrics(fnt2)
                    tw = max(fm1.horizontalAdvance(line1), fm2.horizontalAdvance(line2)) + 24
                    th = 48
                    tx = min(max(x-tw//2,4), W-tw-4); ty = y-th-12

                    shadow = QPainterPath(); shadow.addRoundedRect(tx+2,ty+2,tw,th,9,9)
                    qp.setBrush(QBrush(QColor(0,0,0,90))); qp.setPen(Qt.NoPen); qp.drawPath(shadow)

                    card_path = QPainterPath(); card_path.addRoundedRect(tx,ty,tw,th,9,9)
                    card_bg = QLinearGradient(tx,ty,tx,ty+th)
                    card_bg.setColorAt(0, QColor('#1e1e3e')); card_bg.setColorAt(1, QColor('#13132a'))
                    qp.setBrush(QBrush(card_bg))
                    qp.setPen(QPen(QColor(p('gold')),1)); qp.drawPath(card_path)

                    qp.setFont(fnt1); qp.setPen(QPen(QColor(p('txt'))))
                    qp.drawText(tx+12,ty+18,line1)
                    qp.setFont(fnt2); qp.setPen(QPen(QColor(p('gold2'))))
                    qp.drawText(tx+12,ty+36,line2)

                    tri = QPainterPath()
                    tri.moveTo(x-5,ty+th); tri.lineTo(x+5,ty+th); tri.lineTo(x,ty+th+7); tri.closeSubpath()
                    qp.setBrush(QBrush(QColor('#13132a'))); qp.setPen(Qt.NoPen); qp.drawPath(tri)

        qp.setPen(QPen(QColor('#28285a')))
        qp.setFont(QFont("Arial",7))
        qp.drawText(8,H-7,"© Voyager · Destinasyona tıkla ve keşfet"); qp.end()

# ═══════════════════════════════════════════
#  PLAN HARİTASI — Seçili destinasyonlar
# ═══════════════════════════════════════════
_APPROX_COORDS = {
    "Santorini":(36.4,25.4),"Bali":(-8.3,115.1),"Maldivler":(4.2,73.5),
    "Paris":(48.85,2.35),"Tokyo":(35.68,139.69),"New York":(40.71,-74.01),
    "Dubai":(25.2,55.27),"İstanbul":(41.01,28.96),"Roma":(41.9,12.5),
    "Barselona":(41.38,2.17),"Sidney":(-33.87,151.21),"Antalya":(36.9,30.7),
    "Prag":(50.08,14.43),"Kyoto":(35.01,135.77),"Cape Town":(-33.9,18.42),
    "Venedik":(45.44,12.33),"Marakeş":(31.63,-7.99),"Singapur":(1.35,103.82),
    "Amsterdam":(52.37,4.9),"Rio de Janeiro":(-22.91,-43.17),
}

def _build_plan_map_html(dests):
    """Canvas tabanlı plan haritası — sadece önerilen destinasyonları gösterir, CDN gerektirmez."""
    import json as _json
    colors = ["#e8b84b","#5a90f8","#2eb85c","#c85080","#2ab8b8"]
    pins = []
    for idx, d in enumerate(dests):
        lat, lon = _APPROX_COORDS.get(d['name'], (d.get('lat',0), d.get('lon',0)))
        pins.append({
            'name': d['name'], 'lat': lat, 'lon': lon,
            'flag': d['flag'], 'country': d['country'],
            'rating': d['rating'], 'price': d['price'],
            'tags': ', '.join(d['tags']),
            'color': colors[idx % len(colors)],
            'rank': idx+1,
            'is_best': idx == 0
        })
    pins_json = _json.dumps(pins, ensure_ascii=False)
    legend_html = "".join(
        f'<div style="margin-top:3px"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{colors[i%len(colors)]};margin-right:5px;vertical-align:middle;"></span>#{i+1} {d["name"]}</div>'
        for i, d in enumerate(dests)
    )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin:0;padding:0;box-sizing:border-box; }}
html,body {{ width:100%;height:100%;background:#09090f;overflow:hidden;font-family:Arial,sans-serif; }}
#wrap {{ position:relative;width:100%;height:100%; }}
canvas {{ position:absolute;top:0;left:0;display:block; }}
#tooltip {{
  position:absolute;display:none;z-index:100;
  background:#141425;border:1.5px solid #2a2a45;border-radius:12px;
  padding:10px 14px;min-width:175px;max-width:230px;
  box-shadow:0 4px 24px rgba(0,0,0,.8);color:#dcdcec;font-size:12px;line-height:1.6;pointer-events:none;
}}
#btn-visit {{
  display:none;position:absolute;z-index:101;
  color:#000;border:none;border-radius:7px;
  padding:5px 13px;font-size:10px;font-weight:700;cursor:pointer;
}}
#btn-visit:hover {{ filter:brightness(1.15); }}
#legend {{
  position:absolute;bottom:12px;left:12px;z-index:50;
  background:#141425cc;border:1px solid #2a2a45;border-radius:8px;
  padding:7px 12px;font-size:10px;color:#9090aa;
}}
#zoom-btns {{
  position:absolute;top:12px;right:12px;z-index:50;display:flex;flex-direction:column;gap:4px;
}}
#zoom-btns button {{
  width:26px;height:26px;background:#141425;color:#e8b84b;
  border:1px solid #2a2a45;border-radius:6px;font-size:15px;font-weight:700;cursor:pointer;line-height:1;
}}
#zoom-btns button:hover {{ background:#1e1e3a; }}
</style>
</head>
<body>
<div id="wrap">
  <canvas id="bg"></canvas>
  <canvas id="map"></canvas>
  <div id="tooltip"></div>
  <button id="btn-visit" onclick="visitDest()">✈ İncele &amp; Rezerve Et</button>
  <div id="legend">
    <div style="font-weight:700;color:#e8b84b;margin-bottom:4px;">📍 Önerilen Destinasyonlar</div>
    {legend_html}
  </div>
  <div id="zoom-btns">
    <button onclick="zm(1.2)">+</button>
    <button onclick="zm(0.83)">−</button>
  </div>
</div>
<script>
var PINS = {pins_json};
var bgC = document.getElementById('bg'), mapC = document.getElementById('map');
var tip = document.getElementById('tooltip'), btnV = document.getElementById('btn-visit');
var wrap = document.getElementById('wrap');
var sc=1, ox=0, oy=0, drag=false, ds=null, do_=null, hov=null, sel=null;

function _notify(n){{try{{if(window.pybridge&&window.pybridge.mapClicked)window.pybridge.mapClicked(n);}}catch(e){{}}}}
function visitDest(){{if(sel)_notify(sel.name);hideTip();}}

function geo(lat,lon,W,H){{
  var x=((lon+180)/360)*W*sc+ox;
  var s=Math.sin(lat*Math.PI/180);
  var y=(0.5-Math.log((1+s)/(1-s))/(4*Math.PI))*H*sc+oy;
  return[x,y];
}}

var LAND=[
  [[-10,35],[40,35],[60,45],[60,70],[-10,70]],
  [[-18,35],[52,35],[52,-35],[-18,-35]],
  [[40,10],[145,10],[145,75],[40,75]],
  [[-170,15],[-50,15],[-50,75],[-170,75]],
  [[-82,-55],[-34,-55],[-34,15],[-82,15]],
  [[112,-44],[154,-44],[154,-10],[112,-10]],
  [[-72,58],[-10,58],[-10,84],[-72,84]],
];
var CLBLS=[[20,52,"AVRUPA"],[22,5,"AFRİKA"],[90,45,"ASYA"],[-100,45,"K.AMERİKA"],[-55,-15,"G.AMERİKA"],[134,-25,"OKYANUSYA"]];

function drawBg(){{
  var c=bgC,ctx=c.getContext('2d'),W=c.width,H=c.height;
  var g=ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,'#05050f');g.addColorStop(1,'#080818');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  ctx.strokeStyle='#0e0e22';ctx.lineWidth=0.5;
  for(var ln=-180;ln<=180;ln+=30){{var x=geo(0,ln,W,H)[0];ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}}
  for(var lt=-60;lt<=60;lt+=30){{var y=geo(lt,0,W,H)[1];ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}}
  ctx.strokeStyle='#1a1a38';ctx.lineWidth=1;ctx.setLineDash([3,5]);
  var ey=geo(0,0,W,H)[1];ctx.beginPath();ctx.moveTo(0,ey);ctx.lineTo(W,ey);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle='#1c1c3a';
  LAND.forEach(function(poly){{
    ctx.beginPath();poly.forEach(function(pt,i){{var xy=geo(pt[1],pt[0],W,H);if(i===0)ctx.moveTo(xy[0],xy[1]);else ctx.lineTo(xy[0],xy[1]);}});
    ctx.closePath();ctx.fill();
  }});
  ctx.strokeStyle='#262655';ctx.lineWidth=1;
  LAND.forEach(function(poly){{
    ctx.beginPath();poly.forEach(function(pt,i){{var xy=geo(pt[1],pt[0],W,H);if(i===0)ctx.moveTo(xy[0],xy[1]);else ctx.lineTo(xy[0],xy[1]);}});
    ctx.closePath();ctx.stroke();
  }});
  ctx.fillStyle='#2a2a55';ctx.font='bold 9px Arial';ctx.textAlign='center';
  CLBLS.forEach(function(l){{var xy=geo(l[1],l[0],W,H);ctx.fillText(l[2],xy[0],xy[1]);}});

  // Destinasyonlar arası bağlantı çizgisi
  if(PINS.length>1){{
    ctx.strokeStyle='rgba(232,184,75,0.25)';ctx.lineWidth=1.5;ctx.setLineDash([4,6]);
    ctx.beginPath();
    PINS.forEach(function(p,i){{var xy=geo(p.lat,p.lon,W,H);if(i===0)ctx.moveTo(xy[0],xy[1]);else ctx.lineTo(xy[0],xy[1]);}});
    ctx.stroke();ctx.setLineDash([]);
  }}
}}

function drawPins(){{
  var c=mapC,ctx=c.getContext('2d'),W=c.width,H=c.height;
  ctx.clearRect(0,0,W,H);
  PINS.forEach(function(pin){{
    var xy=geo(pin.lat,pin.lon,W,H),x=xy[0],y=xy[1];
    if(x<-20||x>W+20||y<-20||y>H+20)return;
    var isH=(hov&&hov.name===pin.name),r=isH?14:10;
    var halo=ctx.createRadialGradient(x,y,r,x,y,r+12);
    var rgb=hexRGB(pin.color);
    halo.addColorStop(0,'rgba('+rgb+',0.35)');halo.addColorStop(1,'rgba('+rgb+',0)');
    ctx.fillStyle=halo;ctx.beginPath();ctx.arc(x,y,r+12,0,Math.PI*2);ctx.fill();
    // Daire
    ctx.strokeStyle=pin.color;ctx.lineWidth=isH?2.5:2;
    ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.stroke();
    var gr=ctx.createRadialGradient(x,y,0,x,y,r);
    gr.addColorStop(0,isH?'#fff':pin.color);gr.addColorStop(1,pin.color);
    ctx.fillStyle=gr;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();
    // Numara
    ctx.fillStyle='#000';ctx.font='bold '+(isH?10:8)+'px Arial';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(pin.rank,x,y);
  }});
}}

function hexRGB(h){{
  var r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16);
  return r+','+g+','+b;
}}

function getPin(mx,my,W,H){{
  for(var i=PINS.length-1;i>=0;i--){{
    var p=PINS[i],xy=geo(p.lat,p.lon,W,H),dx=mx-xy[0],dy=my-xy[1];
    if(dx*dx+dy*dy<196)return p;
  }}return null;
}}

function showTip(p,x,y){{
  tip.innerHTML='<div style="color:'+p.color+';font-size:13px;font-weight:700">'+p.flag+' '+p.name+'</div>'+
    '<div style="color:#9090aa;font-size:10px">'+p.country+(p.is_best?' · 👑 EN İYİ EŞLEŞİM':'')+'</div>'+
    '<div>⭐ '+p.rating+' &nbsp;|&nbsp; <span style="color:#e8b84b;font-weight:700">$'+p.price+'/gece</span></div>'+
    '<div style="color:#7a7a99;font-size:9px">'+p.tags+'</div>';
  var W=wrap.clientWidth,H=wrap.clientHeight;
  var tx=Math.min(x+14,W-245),ty=Math.max(y-36,4);
  tip.style.left=tx+'px';tip.style.top=ty+'px';tip.style.display='block';
  btnV.style.left=tx+'px';btnV.style.top=(ty+tip.offsetHeight+4)+'px';
  btnV.style.background=p.color;btnV.style.display='block';
  sel=p;
}}
function hideTip(){{tip.style.display='none';btnV.style.display='none';sel=null;}}

function resize(){{
  var W=wrap.clientWidth,H=wrap.clientHeight;
  bgC.width=W;bgC.height=H;mapC.width=W;mapC.height=H;
  drawBg();drawPins();
}}

mapC.addEventListener('mousemove',function(e){{
  var W=mapC.width,H=mapC.height,p=getPin(e.offsetX,e.offsetY,W,H);
  if(p){{mapC.style.cursor='pointer';if(!hov||hov.name!==p.name){{hov=p;drawPins();}};}}
  else{{if(hov){{hov=null;drawPins();}}mapC.style.cursor=drag?'grabbing':'grab';}}
  if(drag&&ds){{ox=do_[0]+(e.clientX-ds[0]);oy=do_[1]+(e.clientY-ds[1]);drawBg();drawPins();hideTip();}}
}});
mapC.addEventListener('mousedown',function(e){{drag=true;ds=[e.clientX,e.clientY];do_=[ox,oy];mapC.style.cursor='grabbing';}});
mapC.addEventListener('mouseup',function(e){{
  var mv=ds&&(Math.abs(e.clientX-ds[0])+Math.abs(e.clientY-ds[1]))<5;
  drag=false;ds=null;mapC.style.cursor='grab';
  if(mv){{var p=getPin(e.offsetX,e.offsetY,mapC.width,mapC.height);if(p)showTip(p,e.offsetX,e.offsetY);else hideTip();}}
}});
mapC.addEventListener('mouseleave',function(){{drag=false;hov=null;drawPins();}});
mapC.addEventListener('wheel',function(e){{
  e.preventDefault();var f=e.deltaY<0?1.15:0.87;
  var W=mapC.width,H=mapC.height;
  ox=e.offsetX-(e.offsetX-ox)*f;oy=e.offsetY-(e.offsetY-oy)*f;
  sc*=f;sc=Math.max(0.5,Math.min(12,sc));drawBg();drawPins();
}},{{passive:false}});
function zm(f){{
  var W=mapC.width,H=mapC.height;
  ox=W/2-(W/2-ox)*f;oy=H/2-(H/2-oy)*f;
  sc*=f;sc=Math.max(0.5,Math.min(12,sc));drawBg();drawPins();
}}
window.addEventListener('resize',resize);
resize();
</script>
</body>
</html>"""


class PlanMapWidget(QWidget):
    """Tatil planı sonuçlarını gösteren mini harita widget'ı."""
    clicked = pyqtSignal(dict)

    def __init__(self, plan_dests):
        super().__init__()
        self._dests = plan_dests
        self.setMinimumHeight(360)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)

        if _HAS_WEBENGINE and plan_dests:
            self._web = QWebEngineView()
            self._web.setStyleSheet("background:#09090f;")
            self._web.page().setBackgroundColor(QColor('#09090f'))
            self._bridge = _MapBridge()
            self._bridge.map_clicked.connect(self._on_map_click)
            try:
                from PyQt5.QtWebChannel import QWebChannel
                ch = QWebChannel()
                ch.registerObject("pybridge", self._bridge)
                self._web.page().setWebChannel(ch)
                html = _build_plan_map_html(plan_dests)
                # webchannel köprüsünü HTML'e ekle
                wc_script = """<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>document.addEventListener('DOMContentLoaded',function(){
  if(typeof QWebChannel!=='undefined')
    new QWebChannel(qt.webChannelTransport,function(ch){
      window.pybridge=ch.objects.pybridge;
    });
});</script>"""
                html = html.replace("</head>", wc_script + "\n</head>")
            except ImportError:
                html = _build_plan_map_html(plan_dests)
            self._web.setHtml(html, QUrl("about:blank"))
            lay.addWidget(self._web)
        else:
            # Fallback: geliştirilmiş QPainter plan haritası
            self._fallback = PlanMapFallback(plan_dests)
            self._fallback.name_clicked.connect(self._on_map_click)
            lay.addWidget(self._fallback)

    def _on_map_click(self, name):
        dest = next((d for d in self._dests if d['name'] == name), None)
        if dest:
            self.clicked.emit(dest)


class PlanMapFallback(QWidget):
    """WebEngine yoksa QPainter ile plan haritası — seçili destinasyonlar renkli numaralı."""
    name_clicked = pyqtSignal(str)

    _APPROX = _APPROX_COORDS
    _COLORS = ["#e8b84b","#5a90f8","#2eb85c","#c85080","#2ab8b8"]

    def __init__(self, plan_dests):
        super().__init__()
        self._dests = plan_dests
        self._hov = None
        self.setMinimumHeight(320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMouseTracking(True)
        self.setStyleSheet(f"background:{p('bg3')};border-radius:14px;")

    def _geo_to_xy(self, lat, lon, W, H):
        """Enlem/boylamı basit Mercator ile piksel koordinatına çevirir."""
        import math
        x = (lon + 180) / 360 * W
        lat_r = math.radians(max(min(lat, 85), -85))
        mercN = math.log(math.tan(math.pi/4 + lat_r/2))
        y = H/2 - W * mercN / (2 * math.pi)
        return int(x), int(y)

    def mouseMoveEvent(self, e):
        W, H = self.width(), self.height()
        self._hov = None
        for idx, d in enumerate(self._dests):
            lat, lon = self._APPROX.get(d['name'], (d.get('lat',0), d.get('lon',0)))
            x, y = self._geo_to_xy(lat, lon, W, H)
            if abs(e.x()-x) < 16 and abs(e.y()-y) < 16:
                self._hov = idx; self.setCursor(QCursor(Qt.PointingHandCursor)); break
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
        self.update()

    def mousePressEvent(self, e):
        W, H = self.width(), self.height()
        for idx, d in enumerate(self._dests):
            lat, lon = self._APPROX.get(d['name'], (d.get('lat',0), d.get('lon',0)))
            x, y = self._geo_to_xy(lat, lon, W, H)
            if abs(e.x()-x) < 16 and abs(e.y()-y) < 16:
                self.name_clicked.emit(d['name']); return

    def paintEvent(self, ev):
        qp = QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        # Arka plan gradient
        bg = QLinearGradient(0,0,0,H)
        bg.setColorAt(0, QColor('#05050f')); bg.setColorAt(1, QColor('#080818'))
        qp.fillRect(0,0,W,H,QBrush(bg))

        # Kıta bölgeleri
        LAND_ZONES = [
            (0.31,0.10,0.54,0.38),(0.35,0.32,0.55,0.76),(0.47,0.07,0.92,0.56),
            (0.04,0.05,0.30,0.45),(0.15,0.37,0.33,0.78),(0.68,0.50,0.91,0.73),
        ]
        def is_land(rx,ry):
            for x0,y0,x1,y1 in LAND_ZONES:
                if x0<=rx<=x1 and y0<=ry<=y1: return True
            return False

        qp.setPen(Qt.NoPen)
        cols2,rows2 = 80,40; dx=W/cols2; dy=H/rows2
        for row in range(rows2+1):
            for col in range(cols2+1):
                cx2=col*dx+(dx*.5 if row%2 else 0); cy2=row*dy
                c2 = QColor('#1c1c40') if is_land(cx2/W,cy2/H) else QColor('#0e0e25')
                qp.setBrush(QBrush(c2)); qp.drawEllipse(int(cx2-1.5),int(cy2-1.5),3,3)

        # Ekvator + meridyen
        qp.setPen(QPen(QColor('#1e1e45'),1,Qt.DashLine))
        qp.drawLine(0,int(H*.5),W,int(H*.5)); qp.drawLine(int(W*.5),0,int(W*.5),H)

        # Bağlantı çizgileri (önerilen destinasyonlar arası)
        if len(self._dests) > 1:
            pts = []
            for d in self._dests:
                lat,lon = self._APPROX.get(d['name'],(d.get('lat',0),d.get('lon',0)))
                pts.append(self._geo_to_xy(lat,lon,W,H))
            pen_line = QPen(QColor('#e8b84b44'),1,Qt.DotLine)
            qp.setPen(pen_line)
            for i in range(len(pts)-1):
                qp.drawLine(pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1])

        # Destinasyon noktaları
        for idx, d in enumerate(self._dests):
            lat,lon = self._APPROX.get(d['name'],(d.get('lat',0),d.get('lon',0)))
            x,y = self._geo_to_xy(lat,lon,W,H)
            color = QColor(self._COLORS[idx % len(self._COLORS)])
            hov = self._hov == idx
            r_dot = 14 if hov else 11

            # Halo
            halo = QRadialGradient(x,y,r_dot+8)
            halo.setColorAt(0,QColor(color.red(),color.green(),color.blue(),60))
            halo.setColorAt(1,QColor(color.red(),color.green(),color.blue(),0))
            qp.setPen(Qt.NoPen); qp.setBrush(QBrush(halo))
            qp.drawEllipse(x-r_dot-8,y-r_dot-8,(r_dot+8)*2,(r_dot+8)*2)

            # Dolgu
            qp.setBrush(QBrush(color)); qp.setPen(Qt.NoPen)
            qp.drawEllipse(x-r_dot,y-r_dot,r_dot*2,r_dot*2)

            # Numara
            fnt_n = QFont("Arial", 9 if hov else 7, QFont.Bold)
            qp.setFont(fnt_n); qp.setPen(QPen(QColor('#000000')))
            fm = QFontMetrics(fnt_n); rank_txt = str(idx+1)
            tw = fm.horizontalAdvance(rank_txt); th2 = fm.height()
            qp.drawText(x-tw//2, y+th2//3, rank_txt)

            # Tooltip (hover)
            if hov:
                line1 = f"{d['flag']} {d['name']}, {d['country']}"
                line2 = f"⭐ {d['rating']}  ${d['price']}/gece"
                fnt1 = QFont("Arial",10,QFont.Bold); fnt2 = QFont("Arial",8)
                fm1 = QFontMetrics(fnt1); fm2 = QFontMetrics(fnt2)
                tw2 = max(fm1.horizontalAdvance(line1),fm2.horizontalAdvance(line2))+24
                th3 = 50
                tx2 = min(max(x-tw2//2,4),W-tw2-4); ty2 = y-th3-16

                shadow = QPainterPath(); shadow.addRoundedRect(tx2+2,ty2+2,tw2,th3,9,9)
                qp.setBrush(QBrush(QColor(0,0,0,100))); qp.setPen(Qt.NoPen); qp.drawPath(shadow)

                card = QPainterPath(); card.addRoundedRect(tx2,ty2,tw2,th3,9,9)
                cbg = QLinearGradient(tx2,ty2,tx2,ty2+th3)
                cbg.setColorAt(0,QColor('#1e1e3e')); cbg.setColorAt(1,QColor('#13132a'))
                qp.setBrush(QBrush(cbg)); qp.setPen(QPen(color,1.5)); qp.drawPath(card)
                qp.setFont(fnt1); qp.setPen(QPen(QColor(p('txt'))))
                qp.drawText(tx2+12,ty2+18,line1)
                qp.setFont(fnt2); qp.setPen(QPen(color))
                qp.drawText(tx2+12,ty2+36,line2)

                tri = QPainterPath()
                tri.moveTo(x-5,ty2+th3); tri.lineTo(x+5,ty2+th3); tri.lineTo(x,ty2+th3+8); tri.closeSubpath()
                qp.setBrush(QBrush(QColor('#13132a'))); qp.setPen(Qt.NoPen); qp.drawPath(tri)

        # Lejant
        leg_x, leg_y = 10, H-10-len(self._dests)*16-26
        qp.setPen(Qt.NoPen); qp.setBrush(QBrush(QColor('#141425cc')))
        qp.drawRoundedRect(leg_x,leg_y,170,len(self._dests)*16+28,8,8)
        qp.setFont(QFont("Arial",8,QFont.Bold)); qp.setPen(QPen(QColor(p('gold'))))
        qp.drawText(leg_x+8,leg_y+14,"📍 Önerilen Destinasyonlar")
        for i,d in enumerate(self._dests):
            color2 = QColor(self._COLORS[i%len(self._COLORS)])
            qp.setPen(Qt.NoPen); qp.setBrush(QBrush(color2))
            qp.drawEllipse(leg_x+8,leg_y+20+i*16,8,8)
            qp.setFont(QFont("Arial",8)); qp.setPen(QPen(QColor(p('txt2'))))
            qp.drawText(leg_x+22,leg_y+28+i*16,f"#{i+1} {d['name']}")

        qp.setPen(QPen(QColor('#28285a'))); qp.setFont(QFont("Arial",7))
        qp.drawText(8,H-5,"© Voyager · Tatil Planı Haritası"); qp.end()


# ═══════════════════════════════════════════
#  DESTİNASYON KARTI
# ═══════════════════════════════════════════
class DestCard(QFrame):
    clicked = pyqtSignal(dict); fav_click = pyqtSignal(dict)
    def __init__(self, dest):
        super().__init__(); self.dest = dest
        self.setFixedSize(222,255); self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(Card()); self._build()

    def _build(self):
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); v.setSpacing(0)
        hdr = QFrame(); hdr.setFixedHeight(115)
        hdr.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                          f"stop:0 {self.dest['color']}dd,stop:1 {self.dest['color']}44);"
                          f"border-radius:14px 14px 0 0;border:none;}}")
        gl = QGridLayout(hdr); gl.setContentsMargins(11,9,11,9)
        flag = QLabel(self.dest['flag']); flag.setStyleSheet("font-size:26px;background:transparent;border:none;")
        gl.addWidget(flag,0,0,Qt.AlignTop|Qt.AlignLeft)
        is_fav = self.dest['id'] in S.favs
        self.fav_btn = QPushButton("♥" if is_fav else "♡"); self.fav_btn.setFixedSize(26,26)
        fc = p('gold') if is_fav else '#ffffff88'
        self.fav_btn.setStyleSheet(f"QPushButton{{background:#00000055;color:{fc};border:none;border-radius:13px;font-size:13px;}}"
                                   f"QPushButton:hover{{background:#00000099;}}")
        self.fav_btn.clicked.connect(self._fav); gl.addWidget(self.fav_btn,0,1,Qt.AlignTop|Qt.AlignRight)
        rat = QLabel(f"⭐ {self.dest['rating']}")
        rat.setStyleSheet(f"background:#000000aa;color:{p('gold')};border:none;border-radius:9px;padding:2px 7px;font-size:10px;font-weight:700;")
        gl.addWidget(rat,1,0,1,2,Qt.AlignBottom|Qt.AlignRight)
        nm = QLabel(self.dest['name']); nm.setStyleSheet("color:#fff;font-size:15px;font-weight:700;background:transparent;border:none;")
        gl.addWidget(nm,2,0,1,2,Qt.AlignBottom|Qt.AlignLeft); v.addWidget(hdr)
        body = QFrame(); body.setStyleSheet("background:transparent;border:none;")
        bl = QVBoxLayout(body); bl.setContentsMargins(11,9,11,10); bl.setSpacing(4)
        loc = QLabel(f"{self.dest['country']} · {self.dest['cont']}")
        loc.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
        bl.addWidget(loc)
        trow = QHBoxLayout(); trow.setSpacing(4)
        for tg in self.dest['tags'][:2]:
            t = QLabel(tg)
            t.setStyleSheet(f"background:{p('gold')}22;color:{p('gold')};border:none;border-radius:7px;padding:1px 7px;font-size:9px;font-weight:700;")
            trow.addWidget(t)
        trow.addStretch(); bl.addLayout(trow); bl.addStretch()
        prow = QHBoxLayout()
        pr = QLabel(f"${self.dest['price']}")
        pr.setStyleSheet(f"color:{p('gold2')};font-size:16px;font-weight:700;background:transparent;border:none;")
        pn = QLabel("/gece"); pn.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
        ob = QPushButton("İncele →"); ob.setFixedHeight(26); ob.setCursor(QCursor(Qt.PointingHandCursor))
        ob.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),7,'0 9px',11))
        ob.clicked.connect(lambda: self.clicked.emit(self.dest))
        prow.addWidget(pr); prow.addWidget(pn); prow.addStretch(); prow.addWidget(ob)
        bl.addLayout(prow); v.addWidget(body)

    def _fav(self):
        did = self.dest['id']
        if did in S.favs: S.favs.discard(did); sym,col = "♡","#ffffff88"
        else: S.favs.add(did); sym,col = "♥",p('gold')
        self.fav_btn.setText(sym)
        self.fav_btn.setStyleSheet(f"QPushButton{{background:#00000055;color:{col};border:none;border-radius:13px;font-size:13px;}}"
                                   f"QPushButton:hover{{background:#00000099;}}")
        self.fav_click.emit(self.dest)

    def mousePressEvent(self, e):
        if e.button()==Qt.LeftButton: self.clicked.emit(self.dest)

# ═══════════════════════════════════════════
#  DETAY DİYALOĞU — Otel detay düzenleme eklendi
# ═══════════════════════════════════════════
class DetailDlg(QDialog):
    booked = pyqtSignal(dict)
    def __init__(self, dest, parent=None):
        super().__init__(parent); self.dest = dest
        self.sel_hotel = dest['hotels'][0] if dest['hotels'] else None
        self.setWindowTitle(f"{dest['name']} — Detay"); self.setMinimumSize(820,700)
        self.setStyleSheet(f"background:{p('bg')};color:{p('txt')};"); self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        hdr = QFrame(); hdr.setFixedHeight(130)
        hdr.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                          f"stop:0 {self.dest['color']}ff,stop:1 {self.dest['color']}33);"
                          f"border-bottom:1px solid {p('border')};}}")
        hl = QVBoxLayout(hdr); hl.setContentsMargins(26,18,26,18); hl.setSpacing(4)
        t1 = QLabel(f"{self.dest['flag']}  {self.dest['name']}")
        t1.setStyleSheet("color:#fff;font-size:26px;font-weight:700;background:transparent;border:none;")
        t2 = QLabel(f"📍 {self.dest['country']} · {self.dest['cont']}")
        t2.setStyleSheet(f"color:#ffffffbb;font-size:13px;background:transparent;border:none;")
        t3 = QLabel(self.dest['desc'])
        t3.setStyleSheet(f"color:#ffffff99;font-size:11px;background:transparent;border:none;"); t3.setWordWrap(True)
        hl.addWidget(t1); hl.addWidget(t2); hl.addWidget(t3); lay.addWidget(hdr)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            f"QTabWidget::pane{{background:{p('bg2')};border:none;}}"
            f"QTabBar::tab{{background:{p('bg3')};color:{p('mut')};padding:9px 18px;font-size:12px;font-weight:600;border:none;}}"
            f"QTabBar::tab:selected{{background:{p('card')};color:{p('gold')};border-bottom:2px solid {p('gold')};}}"
            f"QTabBar::tab:hover{{color:{p('txt2')};}}")

        # Tab1 — Oteller
        hw = QWidget(); hw.setStyleSheet(f"background:{p('bg2')};")
        self._hotel_scroll_lay = QVBoxLayout(hw); self._hotel_scroll_lay.setContentsMargins(18,14,18,14); self._hotel_scroll_lay.setSpacing(10)
        self._build_hotel_list()
        tabs.addTab(hw, "🏨 Oteller")

        # Tab2 — Gezilecek Yerler
        pw = QWidget(); pw.setStyleSheet(f"background:{p('bg2')};")
        pv = QVBoxLayout(pw); pv.setContentsMargins(18,14,18,14); pv.setSpacing(9)
        for pl in self.dest['places']:
            pf = QFrame(); pf.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:12px;}}")
            pfl = QHBoxLayout(pf); pfl.setContentsMargins(14,11,14,11); pfl.setSpacing(11)
            ic = QLabel(pl['icon']); ic.setFixedSize(42,42); ic.setAlignment(Qt.AlignCenter)
            ic.setStyleSheet(f"background:{p('bg3')};border-radius:10px;font-size:19px;border:1px solid {p('border')};")
            info = QVBoxLayout(); info.setSpacing(2)
            nm = QLabel(pl['name']); nm.setStyleSheet(f"color:{p('txt')};font-size:13px;font-weight:700;background:transparent;border:none;")
            tp = QLabel(pl['type']); tp.setStyleSheet(f"color:{p('gold')};background:{p('gold')}22;border:none;border-radius:6px;padding:1px 7px;font-size:9px;font-weight:700;")
            dc = QLabel(pl['desc']); dc.setStyleSheet(f"color:{p('txt3')};font-size:10px;background:transparent;border:none;"); dc.setWordWrap(True)
            info.addWidget(nm); info.addWidget(tp); info.addWidget(dc)
            pfl.addWidget(ic); pfl.addLayout(info); pv.addWidget(pf)
        pv.addStretch(); tabs.addTab(pw,"📍 Gezilecek Yerler")

        # Tab3 — Rezervasyon
        bw = QWidget(); bw.setStyleSheet(f"background:{p('bg2')};")
        bv = QVBoxLayout(bw); bv.setContentsMargins(22,18,22,18); bv.setSpacing(11)
        bt = QLabel("Rezervasyon Yap"); bt.setStyleSheet(f"color:{p('txt')};font-size:17px;font-weight:700;background:transparent;border:none;")
        bv.addWidget(bt)
        is_s = Inp()
        dsp = (f"QDateEdit{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};"
               f"border-radius:9px;padding:8px 12px;font-size:13px;}}"
               f"QDateEdit:focus{{border-color:{p('gold')};}}")
        ssp = (f"QSpinBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};"
               f"border-radius:9px;padding:8px 12px;font-size:13px;}}"
               f"QSpinBox::up-button,QSpinBox::down-button{{width:22px;}}")
        g = QGridLayout(); g.setSpacing(10)
        fl = QLabel("Giriş"); fl.setStyleSheet(f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;")
        self.d_in = QDateEdit(); self.d_in.setCalendarPopup(True); self.d_in.setDate(QDate.currentDate().addDays(14))
        self.d_in.setFixedHeight(38); self.d_in.setStyleSheet(dsp); self.d_in.dateChanged.connect(self._calc)
        tl = QLabel("Çıkış"); tl.setStyleSheet(fl.styleSheet())
        self.d_out = QDateEdit(); self.d_out.setCalendarPopup(True); self.d_out.setDate(QDate.currentDate().addDays(21))
        self.d_out.setFixedHeight(38); self.d_out.setStyleSheet(dsp); self.d_out.dateChanged.connect(self._calc)
        al = QLabel("Yetişkin"); al.setStyleSheet(fl.styleSheet())
        self.sp_ad = QSpinBox(); self.sp_ad.setRange(1,12); self.sp_ad.setValue(2)
        self.sp_ad.setFixedHeight(38); self.sp_ad.setStyleSheet(ssp); self.sp_ad.valueChanged.connect(self._calc)
        cl = QLabel("Çocuk"); cl.setStyleSheet(fl.styleSheet())
        self.sp_ch = QSpinBox(); self.sp_ch.setRange(0,8); self.sp_ch.setValue(0)
        self.sp_ch.setFixedHeight(38); self.sp_ch.setStyleSheet(ssp); self.sp_ch.valueChanged.connect(self._calc)
        g.addWidget(fl,0,0); g.addWidget(self.d_in,1,0)
        g.addWidget(tl,0,1); g.addWidget(self.d_out,1,1)
        g.addWidget(al,2,0); g.addWidget(self.sp_ad,3,0)
        g.addWidget(cl,2,1); g.addWidget(self.sp_ch,3,1)
        bv.addLayout(g)

        # Fiyat detay kutusu
        tot_f = QFrame(); tot_f.setStyleSheet(f"QFrame{{background:{p('bg3')};border:1px solid {p('border')};border-radius:11px;}}")
        tfl = QVBoxLayout(tot_f); tfl.setContentsMargins(14,11,14,11); tfl.setSpacing(4)
        self.tot_lbl = QLabel(""); self.tot_lbl.setStyleSheet(f"color:{p('txt2')};font-size:12px;background:transparent;border:none;")
        self.tot_fiyat_detay = QLabel(""); self.tot_fiyat_detay.setStyleSheet(f"color:{p('orange')};font-size:10px;background:transparent;border:none;")
        self.tot_amt = QLabel(""); self.tot_amt.setStyleSheet(f"color:{p('gold2')};font-size:22px;font-weight:700;background:transparent;border:none;")
        tfl.addWidget(self.tot_lbl); tfl.addWidget(self.tot_fiyat_detay); tfl.addWidget(self.tot_amt)
        bv.addWidget(tot_f); self._calc()
        cfm = QPushButton("✈  Rezervasyonu Onayla"); cfm.setFixedHeight(44); cfm.setCursor(QCursor(Qt.PointingHandCursor))
        cfm.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),11))
        cfm.clicked.connect(self._confirm)
        bv.addWidget(cfm); bv.addStretch(); tabs.addTab(bw,"📋 Rezervasyon")
        lay.addWidget(tabs)
        foot = QFrame(); foot.setFixedHeight(48); foot.setStyleSheet(f"QFrame{{background:{p('bg2')};border-top:1px solid {p('border')};}}")
        fl2 = QHBoxLayout(foot); fl2.setContentsMargins(18,0,18,0)
        cb = QPushButton("Kapat"); cb.setFixedHeight(34)
        cb.setStyleSheet(Btn(p('bg3'),p('txt2'),p('bg4'),8,'6px 18px',12,False))
        cb.clicked.connect(self.close); fl2.addStretch(); fl2.addWidget(cb); lay.addWidget(foot)

    def _build_hotel_list(self):
        lay = self._hotel_scroll_lay
        while lay.count():
            it = lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for hotel in self.dest['hotels']:
            sel = self.sel_hotel and self.sel_hotel.otel_adi == hotel.otel_adi
            hf = QFrame()
            hf.setStyleSheet(f"QFrame{{background:{p('card')};border:2px solid "
                             f"{p('gold') if sel else p('border')};border-radius:13px;}}")
            hfl = QVBoxLayout(hf); hfl.setContentsMargins(14,12,14,12); hfl.setSpacing(5)
            r1 = QHBoxLayout()
            n = QLabel(hotel.otel_adi); n.setStyleSheet(f"color:{p('txt')};font-size:14px;font-weight:700;background:transparent;border:none;")
            s = QLabel("⭐"*hotel.yildiz); s.setStyleSheet("font-size:11px;background:transparent;border:none;")
            pr = QLabel(f"${hotel.fiyat}/gece"); pr.setStyleSheet(f"color:{p('gold')};font-size:15px;font-weight:700;background:transparent;border:none;")
            r1.addWidget(n); r1.addWidget(s); r1.addStretch(); r1.addWidget(pr)
            hfl.addLayout(r1)
            d = QLabel(hotel.aciklama); d.setStyleSheet(f"color:{p('txt3')};font-size:11px;background:transparent;border:none;"); d.setWordWrap(True); hfl.addWidget(d)
            r2 = QHBoxLayout(); r2.setSpacing(5)
            for oz in hotel.ozellikler[:4]:
                ot = QLabel(oz); ot.setStyleSheet(f"background:{p('bg3')};color:{p('txt2')};border:1px solid {p('brd2')};border-radius:6px;padding:2px 7px;font-size:9px;")
                r2.addWidget(ot)
            r2.addStretch()
            # Düzenle butonu — sadece admin görebilir
            if S.role == 'admin':
                edit_btn = QPushButton("✏"); edit_btn.setFixedSize(28,28)
                edit_btn.setStyleSheet(f"QPushButton{{background:{p('bg3')};color:{p('txt2')};border:1px solid {p('border')};border-radius:7px;font-size:11px;}}"
                                       f"QPushButton:hover{{border-color:{p('gold')};color:{p('gold')};}}")
                edit_btn.setCursor(QCursor(Qt.PointingHandCursor)); edit_btn.setToolTip("Otel detaylarını düzenle")
                edit_btn.clicked.connect(lambda _, h=hotel: self._edit_hotel_detail(h))
                r2.addWidget(edit_btn); hfl.addLayout(r2)
            sb = QPushButton("✓ Seçildi" if sel else "Bu Oteli Seç"); sb.setFixedHeight(30)
            sb.setStyleSheet(Btn(p('gold') if sel else p('bg3'), '#09090f' if sel else p('txt2'),
                                 p('gold2') if sel else p('bg4'), 8,'0 12px',11))
            sb.clicked.connect(lambda _, h=hotel: self._sel(h))
            hfl.addWidget(sb); lay.addWidget(hf)
        lay.addStretch()

    def _edit_hotel_detail(self, hotel):
        dlg = HotelDetailEditDlg(hotel, self)
        if dlg.exec_() == QDialog.Accepted:
            dlg.apply(hotel)
            self._build_hotel_list()
            if self.sel_hotel and self.sel_hotel.otel_adi == hotel.otel_adi:
                self._calc()

    def _sel(self, hotel):
        self.sel_hotel = hotel; self._build_hotel_list(); self._calc()

    def _calc(self):
        if not self.sel_hotel: return
        n = self.d_in.date().daysTo(self.d_out.date())
        if n <= 0:
            self.tot_lbl.setText("⚠ Çıkış, girişten sonra olmalı"); self.tot_amt.setText(""); return
        n_yet = self.sp_ad.value(); n_coc = self.sp_ch.value()
        is_admin = (S.role == 'admin')
        toplam = hesapla_fiyat(self.sel_hotel.fiyat, n, n_yet, n_coc, is_admin)
        detay = fiyat_aciklamasi(n_yet, is_admin)
        self.tot_lbl.setText(f"🏨 {self.sel_hotel.otel_adi} · {n} gece · {n_yet} yetişkin {n_coc} çocuk")
        self.tot_fiyat_detay.setText(f"💡 {detay} — Çocuk indirimli (%50)")
        if is_admin:
            normal = hesapla_fiyat(self.sel_hotel.fiyat, n, n_yet, n_coc, False)
            kazanc = normal - toplam
            self.tot_amt.setText(f"${toplam:,}")
        else:
            self.tot_amt.setText(f"${toplam:,}")

    def _confirm(self):
        if not self.sel_hotel:
            CustomMsgBox.warning(self,"⚠ Uyarı","Lütfen önce bir otel seçin."); return
        n = self.d_in.date().daysTo(self.d_out.date())
        if n <= 0:
            CustomMsgBox.warning(self,"⚠ Tarih Hatası","Çıkış tarihi, giriş tarihinden sonra olmalıdır."); return
        if n > 365:
            CustomMsgBox.warning(self,"⚠ Süre Hatası","Konaklama süresi 365 geceden fazla olamaz."); return
        if self.d_in.date() < QDate.currentDate():
            CustomMsgBox.warning(self,"⚠ Tarih Hatası","Giriş tarihi geçmişte olamaz."); return
        n_yet = self.sp_ad.value(); n_coc = self.sp_ch.value()
        if n_yet + n_coc == 0:
            CustomMsgBox.warning(self,"⚠ Kişi Sayısı","En az 1 kişi olmalıdır."); return
        # Aynı destinasyon + tarih çakışma kontrolü
        giris_str = self.d_in.date().toString("dd.MM.yyyy")
        cikis_str = self.d_out.date().toString("dd.MM.yyyy")
        for bk in S.bookings:
            if bk['durum'] == 'cancelled': continue
            if bk['seyahat'].gidis_yeri == self.dest['name'] and bk['konaklama'].otel_adi == self.sel_hotel.otel_adi:
                if bk['giris'] == giris_str:
                    CustomMsgBox.warning(self,"⚠ Tarih Çakışması",f"{self.dest['name']} – {self.sel_hotel.otel_adi} için bu tarihte zaten bir rezervasyonunuz var."); return
        is_admin = (S.role == 'admin')
        toplam = hesapla_fiyat(self.sel_hotel.fiyat, n, n_yet, n_coc, is_admin)
        sey = Seyahat(self.dest['name'], giris_str, n)
        kon = self.sel_hotel
        pln = Plan(f"{self.dest['name']} → {'→'.join(pl['name'] for pl in self.dest['places'][:2])}",
                   [pl['name'] for pl in self.dest['places']])
        bk = {
            "id": S.bk_id, "seyahat": sey, "konaklama": kon, "plan": pln,
            "giris": giris_str, "cikis": cikis_str,
            "kisi": n_yet, "cocuk": n_coc, "toplam": toplam,
            "durum": "confirmed", "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user_id": S.user['id'] if S.user else 0,
            "user_name": S.user['name'] if S.user else 'Misafir',
            "is_admin_booking": is_admin,
        }
        indirim_msg = ""
        if is_admin:
            normal = hesapla_fiyat(self.sel_hotel.fiyat, n, n_yet, n_coc, False)
            kazanc = normal - toplam
            indirim_msg = f"\n🛡 Admin indirimi (%15): -${kazanc:,} tasarruf!"
        S.bk_id += 1; S.bookings.append(bk); self.booked.emit(bk)
        CustomMsgBox.success(self,"✅ Rezervasyon Onaylandı",
            f"{sey.gidis_yeri} — {kon.otel_adi}\n{bk['giris']} → {bk['cikis']}\n"
            f"👥 {n_yet} yetişkin, {n_coc} çocuk\nToplam: ${toplam:,}{indirim_msg}")
        self.close()

# ═══════════════════════════════════════════
#  KULLANICI OTEL EKLEME DİYALOĞU
# ═══════════════════════════════════════════
class UserHotelAddDlg(QDialog):
    def __init__(self, dest, parent=None):
        super().__init__(parent); self.dest = dest
        self.setWindowTitle(f"Yeni Otel Öner — {dest['name']}")
        self.setMinimumSize(500, 520)
        self.setStyleSheet(f"background:{p('bg')};color:{p('txt')};"); self._build()

    def _build(self):
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); v.setSpacing(0)

        # Header
        hdr = QFrame(); hdr.setFixedHeight(72)
        hdr.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                          f"stop:0 {p('teal')}33,stop:1 transparent);"
                          f"border-bottom:1px solid {p('border')};}}")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(22,0,22,0); hl.setSpacing(12)
        ic = QLabel("🏨"); ic.setStyleSheet("font-size:28px;background:transparent;border:none;")
        info_v = QVBoxLayout(); info_v.setSpacing(1)
        t1 = QLabel("Yeni Otel Öner"); t1.setStyleSheet(f"color:{p('txt')};font-size:16px;font-weight:700;background:transparent;border:none;")
        t2 = QLabel(f"Bu öneri {self.dest['name']} destinasyonuna eklenecek")
        t2.setStyleSheet(f"color:{p('teal')};font-size:10px;background:transparent;border:none;")
        info_v.addWidget(t1); info_v.addWidget(t2)
        hl.addWidget(ic); hl.addLayout(info_v); hl.addStretch()
        v.addWidget(hdr)

        # Form alanı
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:{p('bg')};border:none;}}"
                             f"QScrollBar:vertical{{background:{p('bg2')};width:6px;border-radius:3px;}}"
                             f"QScrollBar::handle:vertical{{background:{p('border')};border-radius:3px;}}")
        form_w = QWidget(); form_w.setStyleSheet(f"background:{p('bg')};")
        fv = QVBoxLayout(form_w); fv.setContentsMargins(22,18,22,10); fv.setSpacing(11)

        is_s = Inp()
        lbl_s = f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;"

        # Otel adı
        lbl_ad = QLabel("Otel Adı *"); lbl_ad.setStyleSheet(lbl_s)
        self.inp_ad = QLineEdit(); self.inp_ad.setPlaceholderText("Örn: Grand Hilton Resort")
        self.inp_ad.setFixedHeight(40); self.inp_ad.setStyleSheet(is_s)
        fv.addWidget(lbl_ad); fv.addWidget(self.inp_ad)

        # Açıklama
        lbl_ac = QLabel("Açıklama *"); lbl_ac.setStyleSheet(lbl_s)
        self.inp_ac = QLineEdit(); self.inp_ac.setPlaceholderText("Oteli kısaca tanımlayın...")
        self.inp_ac.setFixedHeight(40); self.inp_ac.setStyleSheet(is_s)
        fv.addWidget(lbl_ac); fv.addWidget(self.inp_ac)

        # Yıldız + Fiyat yan yana
        row = QHBoxLayout(); row.setSpacing(14)
        ssp = (f"QSpinBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};"
               f"border-radius:9px;padding:8px 11px;font-size:12px;}}")
        for lbl_txt, attr, mn, mx, dv, sfx in [
            ("⭐ Yıldız","yildiz",1,5,4,""),
            ("💰 Fiyat ($/gece)","fiyat",30,9999,200,"")
        ]:
            col = QVBoxLayout(); col.setSpacing(4)
            lbl_sp = QLabel(lbl_txt); lbl_sp.setStyleSheet(lbl_s)
            sp = QSpinBox(); sp.setRange(mn, mx); sp.setValue(dv)
            if sfx: sp.setSuffix(sfx)
            sp.setFixedHeight(40); sp.setStyleSheet(ssp)
            setattr(self, f'sp_{attr}', sp)
            col.addWidget(lbl_sp); col.addWidget(sp); row.addLayout(col)
        fv.addLayout(row)

        # Özellikler — çoklu seçim
        lbl_oz = QLabel("Özellikler (isteğe bağlı)"); lbl_oz.setStyleSheet(lbl_s)
        fv.addWidget(lbl_oz)

        oz_row = QHBoxLayout(); oz_row.setSpacing(6)
        self._oz_combo = QComboBox(); self._oz_combo.setFixedHeight(36)
        self._oz_combo.setStyleSheet(
            f"QComboBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:5px 11px;font-size:11px;}}"
            f"QComboBox::drop-down{{border:none;width:20px;}}"
            f"QComboBox QAbstractItemView{{background:{p('bg3')};color:{p('txt')};selection-background-color:{p('teal')}44;border:1px solid {p('border')};}}")
        for oz_item in ["Havuz","Sonsuzluk Havuzu","Özel Havuz","Spa","Hamam","Fitness","Restoran",
                        "Kahvaltı","All-Inclusive","Bar","Rooftop Bar","Butler","Concierge","WiFi",
                        "Otopark","Transfer","Plaj","Özel Plaj","Dalış","Snorkeling","Bahçe",
                        "Teras","Manzara Terası","Şehir Manzarası","Deniz Manzarası","Aile Dostu","Bisiklet"]:
            self._oz_combo.addItem(oz_item)
        oz_add_btn = QPushButton("+ Ekle"); oz_add_btn.setFixedHeight(36)
        oz_add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        oz_add_btn.setStyleSheet(Btn(p('teal'),'#09090f','#1aaa88',8,'5px 12px',11))
        oz_row.addWidget(self._oz_combo); oz_row.addWidget(oz_add_btn)
        fv.addLayout(oz_row)

        self._selected_oz = []
        self._oz_tags_frame = QFrame(); self._oz_tags_frame.setStyleSheet("background:transparent;border:none;")
        self._oz_tags_lay = QHBoxLayout(self._oz_tags_frame)
        self._oz_tags_lay.setContentsMargins(0,0,0,0); self._oz_tags_lay.setSpacing(4)
        self._oz_tags_lay.addStretch(); fv.addWidget(self._oz_tags_frame)

        def _refresh_oz():
            while self._oz_tags_lay.count():
                it = self._oz_tags_lay.takeAt(0)
                if it.widget(): it.widget().deleteLater()
            for oz_i in self._selected_oz:
                tf = QFrame(); tf.setStyleSheet(f"background:{p('teal')}1a;border:1px solid {p('teal')}55;border-radius:7px;")
                tl = QHBoxLayout(tf); tl.setContentsMargins(6,2,3,2); tl.setSpacing(3)
                tlbl = QLabel(oz_i); tlbl.setStyleSheet(f"color:{p('teal')};font-size:9px;font-weight:700;background:transparent;border:none;")
                rb = QPushButton("✕"); rb.setFixedSize(14,14); rb.setCursor(QCursor(Qt.PointingHandCursor))
                rb.setStyleSheet(f"QPushButton{{background:transparent;color:{p('mut')};border:none;font-size:9px;}}QPushButton:hover{{color:{p('red')};}}")
                rb.clicked.connect(lambda _checked=False,o=oz_i: _rm(oz_i=o))
                tl.addWidget(tlbl); tl.addWidget(rb); self._oz_tags_lay.insertWidget(self._oz_tags_lay.count()-1, tf)

        def _rm(_checked=False, oz_i=None):
            if oz_i and oz_i in self._selected_oz: self._selected_oz.remove(oz_i)
            _refresh_oz()

        def _add_oz(_checked=False):
            oz_i = self._oz_combo.currentText()
            if oz_i and oz_i not in self._selected_oz:
                self._selected_oz.append(oz_i); _refresh_oz()

        oz_add_btn.clicked.connect(_add_oz)
        self._refresh_oz = _refresh_oz

        # Hata etiketi
        self._err = QLabel(""); self._err.setStyleSheet(f"color:{p('red')};font-size:10px;font-weight:600;background:transparent;border:none;")
        fv.addWidget(self._err)
        fv.addStretch()

        scroll.setWidget(form_w); v.addWidget(scroll)

        # Footer butonlar
        foot = QFrame(); foot.setFixedHeight(56)
        foot.setStyleSheet(f"background:{p('bg2')};border-top:1px solid {p('border')};")
        fl = QHBoxLayout(foot); fl.setContentsMargins(18,0,18,0); fl.setSpacing(8); fl.addStretch()
        cancel_btn = QPushButton("İptal"); cancel_btn.setFixedHeight(38)
        cancel_btn.setStyleSheet(Btn(p('bg3'),p('txt2'),p('bg4'),9,'7px 18px',12,False))
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("✓  Oteli Ekle"); save_btn.setFixedHeight(38)
        save_btn.setStyleSheet(Btn(p('teal'),'#09090f','#1aaa88',9,'7px 22px',12))
        save_btn.clicked.connect(self._validate)
        fl.addWidget(cancel_btn); fl.addWidget(save_btn); v.addWidget(foot)

    def _validate(self):
        import re
        harf_re = re.compile(r'[a-zA-Z\u00c7\u00e7\u011e\u011f\u0130\u0131\u00d6\u00f6\u015e\u015f\u00dc\u00fc]')
        ad = self.inp_ad.text().strip()
        ac = self.inp_ac.text().strip()
        if not ad or not harf_re.search(ad):
            self._err.setText("❌ Otel adı boş olamaz ve en az bir harf içermelidir."); return
        if not ac or not harf_re.search(ac):
            self._err.setText("❌ Açıklama boş olamaz ve en az bir harf içermelidir."); return
        # Aynı adda otel var mı?
        for h in self.dest['hotels']:
            if h.otel_adi.lower() == ad.lower():
                self._err.setText("❌ Bu isimde bir otel zaten mevcut."); return
        self._err.setText("")
        self.accept()

    def get_hotel(self):
        return Konaklama(
            self.inp_ad.text().strip(),
            self.sp_fiyat.value(),
            self.sp_yildiz.value(),
            list(self._selected_oz),
            self.inp_ac.text().strip()
        )

# ═══════════════════════════════════════════
#  OTEL DETAY DÜZENLEME DİYALOĞU (kullanıcı arayüzünden)
# ═══════════════════════════════════════════
class HotelDetailEditDlg(QDialog):
    def __init__(self, hotel, parent=None):
        super().__init__(parent); self.hotel = hotel
        self.setWindowTitle(f"Otel Düzenle — {hotel.otel_adi}")
        self.setMinimumSize(480,420); self.setStyleSheet(f"background:{p('bg')};color:{p('txt')};"); self._build()

    def _build(self):
        v = QVBoxLayout(self); v.setContentsMargins(22,18,22,18); v.setSpacing(10)
        is_s = Inp()
        lbl_s = f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;"

        v.addWidget(self._lbl("🏨 Otel Detaylarını Düzenle", 15, True))
        v.addSpacing(4)

        v.addWidget(self._lbl("Otel Adı")); self.inp_ad = QLineEdit(self.hotel.otel_adi)
        self.inp_ad.setFixedHeight(38); self.inp_ad.setStyleSheet(is_s); v.addWidget(self.inp_ad)

        v.addWidget(self._lbl("Açıklama")); self.inp_ac = QTextEdit(self.hotel.aciklama)
        self.inp_ac.setFixedHeight(70)
        self.inp_ac.setStyleSheet(f"QTextEdit{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:7px;font-size:11px;}}")
        v.addWidget(self.inp_ac)

        v.addWidget(self._lbl("Özellikler (virgülle ayırın)")); self.inp_oz = QLineEdit(', '.join(self.hotel.ozellikler))
        self.inp_oz.setFixedHeight(38); self.inp_oz.setStyleSheet(is_s); v.addWidget(self.inp_oz)

        g = QGridLayout(); g.setSpacing(10)
        yl = self._lbl("Yıldız"); self.sp_yil = QSpinBox(); self.sp_yil.setRange(1,5); self.sp_yil.setValue(self.hotel.yildiz)
        self.sp_yil.setFixedHeight(38); self.sp_yil.setStyleSheet(f"QSpinBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:7px 11px;font-size:12px;}}")
        fl = self._lbl("Fiyat ($/gece)"); self.sp_fi = QSpinBox(); self.sp_fi.setRange(10,9999); self.sp_fi.setValue(int(self.hotel.fiyat))
        self.sp_fi.setFixedHeight(38); self.sp_fi.setStyleSheet(self.sp_yil.styleSheet())
        g.addWidget(yl,0,0); g.addWidget(self.sp_yil,1,0)
        g.addWidget(fl,0,1); g.addWidget(self.sp_fi,1,1)
        v.addLayout(g); v.addStretch()

        br = QHBoxLayout(); br.addStretch()
        cb = QPushButton("İptal"); cb.setFixedHeight(36)
        cb.setStyleSheet(Btn(p('bg3'),p('txt2'),p('bg4'),9,'7px 18px',12,False)); cb.clicked.connect(self.reject)
        sb = QPushButton("💾 Kaydet"); sb.setFixedHeight(36)
        sb.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),9,'7px 18px',12)); sb.clicked.connect(self.accept)
        br.addWidget(cb); br.addWidget(sb); v.addLayout(br)

    def _lbl(self, txt, fs=11, bold=False):
        l = QLabel(txt); fw = '700' if bold else '600'
        l.setStyleSheet(f"color:{p('txt2')};font-size:{fs}px;font-weight:{fw};background:transparent;border:none;")
        return l

    def apply(self, hotel):
        hotel.otel_adi = self.inp_ad.text().strip() or hotel.otel_adi
        hotel.aciklama = self.inp_ac.toPlainText().strip()
        hotel.yildiz = self.sp_yil.value(); hotel.fiyat = self.sp_fi.value()
        hotel.ozellikler = [x.strip() for x in self.inp_oz.text().split(',') if x.strip()]

# ═══════════════════════════════════════════
#  TOAST
# ═══════════════════════════════════════════
class Toast(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setFixedSize(320,48)
        self._t = QTimer(); self._t.setSingleShot(True); self._t.timeout.connect(self.hide)
        lay = QHBoxLayout(self); lay.setContentsMargins(14,0,14,0)
        self._dot = QLabel(); self._dot.setFixedSize(8,8)
        self._lbl = QLabel(); self._lbl.setStyleSheet(f"color:{p('txt')};font-size:12px;background:transparent;border:none;")
        lay.addWidget(self._dot); lay.addSpacing(6); lay.addWidget(self._lbl)
        self.setStyleSheet(f"QWidget{{background:{p('card2')};border:1px solid {p('brd2')};border-radius:11px;}}")

    def show_msg(self, msg, ok=True):
        self._lbl.setText(msg); col = p('grn') if ok else p('red')
        self._dot.setStyleSheet(f"background:{col};border-radius:4px;")
        if self.parent():
            r = self.parent().rect(); gp = self.parent().mapToGlobal(QPoint(0,0))
            self.move(gp.x()+r.width()-335, gp.y()+r.height()-60)
        self.show(); self.raise_(); self._t.start(2800)

# ═══════════════════════════════════════════
#  GİRİŞ EKRANI
# ═══════════════════════════════════════════
class LoginScreen(QWidget):
    ok = pyqtSignal(str)
    def __init__(self):
        super().__init__(); self._mode = 'select'
        self.setStyleSheet(f"background:{p('bg')};"); self._build()

    def _build(self):
        self._main_lay = QHBoxLayout(self); self._main_lay.setContentsMargins(0,0,0,0)
        left = QFrame(); left.setMinimumWidth(420)
        left.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                           f"stop:0 #0d0d1a,stop:0.5 #0a0a15,stop:1 #080810);"
                           f"border-right:1px solid {p('border')};}}")
        lv = QVBoxLayout(left); lv.setContentsMargins(40,50,40,30); lv.setSpacing(0)
        lg = QLabel("✈"); lg.setAlignment(Qt.AlignCenter)
        lg.setStyleSheet(f"color:{p('gold')};font-size:48px;background:transparent;border:none;")
        t1 = QLabel("VOYAGER"); t1.setAlignment(Qt.AlignCenter)
        t1.setStyleSheet(f"color:{p('gold')};font-size:28px;font-weight:700;letter-spacing:8px;background:transparent;border:none;")
        t2 = QLabel("Seyahat Planlama Platformu"); t2.setAlignment(Qt.AlignCenter)
        t2.setStyleSheet(f"color:{p('mut')};font-size:11px;letter-spacing:3px;background:transparent;border:none;")
        lv.addStretch(); lv.addWidget(lg); lv.addSpacing(8); lv.addWidget(t1); lv.addSpacing(4); lv.addWidget(t2); lv.addStretch()
        for val,lbl,col in [(str(len(DESTS)),"Destinasyon",p('gold')),(str(sum(len(d['hotels']) for d in DESTS)),"Otel",p('blue2'))]:
            sf = QFrame(); sf.setStyleSheet(f"background:{p('card')};border:1px solid {p('border')};border-radius:10px;margin:3px;")
            sl = QHBoxLayout(sf); sl.setContentsMargins(14,10,14,10)
            vl = QLabel(val); vl.setStyleSheet(f"color:{col};font-size:18px;font-weight:700;background:transparent;border:none;")
            nl = QLabel(f"  {lbl}"); nl.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
            sl.addWidget(vl); sl.addWidget(nl); sl.addStretch(); lv.addWidget(sf)
        lv.addStretch()
        self._main_lay.addWidget(left)
        right = QFrame(); right.setStyleSheet(f"background:{p('bg2')};")
        rv = QVBoxLayout(right); rv.setContentsMargins(50,0,50,0)
        self.form_cont = QWidget(); self.form_cont.setStyleSheet("background:transparent;")
        self.form_lay = QVBoxLayout(self.form_cont); self.form_lay.setContentsMargins(0,0,0,0); self.form_lay.setSpacing(5)
        rv.addStretch(); rv.addWidget(self.form_cont); rv.addStretch()
        self._main_lay.addWidget(right)
        self._show_select()

    def _lbl(self, txt, fs=12, bold=True, col=None):
        l = QLabel(txt); fw = '700' if bold else '400'
        l.setStyleSheet(f"color:{col or p('txt')};font-size:{fs}px;font-weight:{fw};background:transparent;border:none;")
        return l

    def _clr(self):
        while self.form_lay.count():
            it = self.form_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()

    def _show_select(self):
        self._mode = 'select'; self._clr()
        self.form_lay.addWidget(self._lbl("Hoş Geldiniz",22,True))
        self.form_lay.addSpacing(4)
        self.form_lay.addWidget(self._lbl("Lütfen giriş türünü seçin",12,False,p('mut')))
        self.form_lay.addSpacing(22)
        for txt,fn,col in [("🧳  Kullanıcı Girişi",self._show_user_login,p('gold')),
                           ("⚙  Admin Paneli",self._show_admin_login,p('blue2')),
                           ("📝  Yeni Hesap Oluştur",self._show_register,p('grn'))]:
            b = QPushButton(txt); b.setFixedHeight(46); b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setStyleSheet(f"QPushButton{{background:{col}22;color:{col};border:1.5px solid {col}44;"
                            f"border-radius:11px;font-size:13px;font-weight:700;text-align:left;padding-left:18px;}}"
                            f"QPushButton:hover{{background:{col}44;border-color:{col};}}")
            b.clicked.connect(fn); self.form_lay.addWidget(b); self.form_lay.addSpacing(6)

    def _show_user_login(self):
        self._mode = 'user'; self._clr()
        self.form_lay.addWidget(self._lbl("🧳  Kullanıcı Girişi",20,True)); self.form_lay.addSpacing(4)
        self.form_lay.addWidget(self._lbl("Hesabınıza giriş yapın",12,False,p('mut'))); self.form_lay.addSpacing(22)
        is_s = Inp()
        self.form_lay.addWidget(self._lbl("E-Posta")); self.form_lay.addSpacing(4)
        self.u_email = QLineEdit(); self.u_email.setPlaceholderText("Mail Giriniz"); self.u_email.setFixedHeight(42); self.u_email.setStyleSheet(is_s)
        def _u_em_filter(t, w=self.u_email):
            f=t.replace(' ','');
            if f!=t: c=w.cursorPosition(); w.blockSignals(True); w.setText(f); w.blockSignals(False); w.setCursorPosition(max(0,c-1))
        self.u_email.textChanged.connect(_u_em_filter)
        self.form_lay.addWidget(self.u_email); self.form_lay.addSpacing(12)
        self.form_lay.addWidget(self._lbl("Parola")); self.form_lay.addSpacing(4)
        self.u_pwd = QLineEdit(); self.u_pwd.setPlaceholderText("Parolanız"); self.u_pwd.setEchoMode(QLineEdit.Password)
        self.u_pwd.setFixedHeight(42); self.u_pwd.setStyleSheet(is_s); self.u_pwd.returnPressed.connect(self._do_user_login)
        def _u_pw_filter(t, w=self.u_pwd):
            f=t.replace(' ','');
            if f!=t: c=w.cursorPosition(); w.blockSignals(True); w.setText(f); w.blockSignals(False); w.setCursorPosition(max(0,c-1))
        self.u_pwd.textChanged.connect(_u_pw_filter)
        self.form_lay.addWidget(self.u_pwd); self.form_lay.addSpacing(6)
        self.u_err = self._lbl("",11,False,p('red')); self.form_lay.addWidget(self.u_err); self.form_lay.addSpacing(14)
        lb = QPushButton("Giriş Yap"); lb.setFixedHeight(44); lb.setCursor(QCursor(Qt.PointingHandCursor))
        lb.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),11)); lb.clicked.connect(self._do_user_login); self.form_lay.addWidget(lb)
        self.form_lay.addSpacing(14)
        bk = QPushButton("← Geri"); bk.setCursor(QCursor(Qt.PointingHandCursor))
        bk.setStyleSheet(f"QPushButton{{background:transparent;color:{p('mut')};border:none;font-size:12px;}}QPushButton:hover{{color:{p('txt2')};}}")
        bk.clicked.connect(self._show_select); self.form_lay.addWidget(bk,alignment=Qt.AlignCenter)
        self.form_lay.addSpacing(10)
        dm = self._lbl("",9,False,p('mut2')); dm.setAlignment(Qt.AlignCenter); self.form_lay.addWidget(dm)

    def _show_admin_login(self):
        self._mode = 'admin'; self._clr()
        self.form_lay.addWidget(self._lbl("⚙  Admin Girişi",20,True)); self.form_lay.addSpacing(4)
        self.form_lay.addWidget(self._lbl("Yönetici hesabınızla giriş yapın",12,False,p('mut'))); self.form_lay.addSpacing(22)
        is_s = Inp()
        self.form_lay.addWidget(self._lbl("Admin E-Posta")); self.form_lay.addSpacing(4)
        self.a_email = QLineEdit(); self.a_email.setPlaceholderText("Mailinizi girin"); self.a_email.setFixedHeight(42); self.a_email.setStyleSheet(is_s)
        def _a_em_filter(t, w=self.a_email):
            f=t.replace(' ','');
            if f!=t: c=w.cursorPosition(); w.blockSignals(True); w.setText(f); w.blockSignals(False); w.setCursorPosition(max(0,c-1))
        self.a_email.textChanged.connect(_a_em_filter)
        self.form_lay.addWidget(self.a_email); self.form_lay.addSpacing(12)
        self.form_lay.addWidget(self._lbl("Parola")); self.form_lay.addSpacing(4)
        self.a_pwd = QLineEdit(); self.a_pwd.setPlaceholderText("Admin parolası"); self.a_pwd.setEchoMode(QLineEdit.Password)
        self.a_pwd.setFixedHeight(42); self.a_pwd.setStyleSheet(is_s); self.a_pwd.returnPressed.connect(self._do_admin_login)
        def _a_pw_filter(t, w=self.a_pwd):
            f=t.replace(' ','');
            if f!=t: c=w.cursorPosition(); w.blockSignals(True); w.setText(f); w.blockSignals(False); w.setCursorPosition(max(0,c-1))
        self.a_pwd.textChanged.connect(_a_pw_filter)
        self.form_lay.addWidget(self.a_pwd); self.form_lay.addSpacing(6)
        self.a_err = self._lbl("",11,False,p('red')); self.form_lay.addWidget(self.a_err); self.form_lay.addSpacing(14)
        lb = QPushButton("Admin Girişi"); lb.setFixedHeight(44); lb.setCursor(QCursor(Qt.PointingHandCursor))
        lb.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),11)); lb.clicked.connect(self._do_admin_login); self.form_lay.addWidget(lb)
        self.form_lay.addSpacing(14)
        bk = QPushButton("← Geri"); bk.setCursor(QCursor(Qt.PointingHandCursor))
        bk.setStyleSheet(f"QPushButton{{background:transparent;color:{p('mut')};border:none;font-size:12px;}}QPushButton:hover{{color:{p('txt2')};}}")
        bk.clicked.connect(self._show_select); self.form_lay.addWidget(bk,alignment=Qt.AlignCenter)
        self.form_lay.addSpacing(10)
        dm = self._lbl("",9,False,p('mut2')); dm.setAlignment(Qt.AlignCenter); self.form_lay.addWidget(dm)

    # ── Ülke kodları listesi ──
    COUNTRY_CODES = [
        ("🇹🇷 Türkiye", "+90", "3.3.2.2"),
        ("🇺🇸 ABD", "+1", "3.3.4"),
        ("🇬🇧 İngiltere", "+44", "4.3.4"),
        ("🇩🇪 Almanya", "+49", "3.4.4"),
        ("🇫🇷 Fransa", "+33", "1.2.2.2"),
        ("🇮🇹 İtalya", "+39", "3.3.4"),
        ("🇪🇸 İspanya", "+34", "3.3.3"),
        ("🇳🇱 Hollanda", "+31", "2.4.4"),
        ("🇷🇺 Rusya", "+7", "3.3.2.2"),
        ("🇸🇦 S. Arabistan", "+966", "2.3.4"),
        ("🇦🇪 BAE", "+971", "2.3.4"),
        ("🇯🇵 Japonya", "+81", "2.4.4"),
        ("🇨🇳 Çin", "+86", "3.4.4"),
        ("🇮🇳 Hindistan", "+91", "5.5"),
        ("🇧🇷 Brezilya", "+55", "2.5.4"),
        ("🇦🇺 Avustralya", "+61", "1.4.4"),
        ("🇿🇦 G. Afrika", "+27", "2.3.4"),
        ("🇬🇷 Yunanistan", "+30", "3.3.4"),
    ]

    def _show_register(self):
        self._mode = 'register'; self._clr()
        import re as _re2

        tl = self._lbl("✈  Hesap Oluştur", 20, True); self.form_lay.addWidget(tl)
        self.form_lay.addSpacing(2)
        sub = self._lbl("Voyager'a ücretsiz katılın ve hayalinizdeki seyahati planlayın", 11, False, p('mut'))
        sub.setWordWrap(True); self.form_lay.addWidget(sub)
        self.form_lay.addSpacing(16)

        is_s = Inp(); self.r_fields = {}
        cb_s = (f"QComboBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};"
                f"border-radius:9px;padding:5px 10px;font-size:12px;}}"
                f"QComboBox::drop-down{{border:none;width:22px;}}"
                f"QComboBox QAbstractItemView{{background:{p('bg3')};color:{p('txt')};"
                f"selection-background-color:{p('gold')}44;border:1px solid {p('border')};}}")

        # ── Helper: sadece harf ve boşluk validasyonu için filter ──
        def _only_letters_validator(inp_widget):
            """Ad, Soyad, Şehir: rakam, özel karakter ve boşluk yasak."""
            def _check(txt):
                # Boşluk ve rakam ve özel karakter filtrele
                filtered = _re2.sub(r'[^a-zA-ZçÇğĞıİöÖşŞüÜÀ-ɏ ]', '', txt)
                # Boşluk da yasak
                filtered = filtered.replace(' ', '')
                if filtered != txt:
                    c = inp_widget.cursorPosition()
                    inp_widget.blockSignals(True); inp_widget.setText(filtered)
                    inp_widget.blockSignals(False)
                    inp_widget.setCursorPosition(max(0, c - (len(txt) - len(filtered))))
            inp_widget.textChanged.connect(_check)

        # Ad Soyad + Şehir yan yana — sadece harf, boşluk yasak
        row1 = QHBoxLayout(); row1.setSpacing(10)
        for lbl_txt, key, ph in [("👤  Ad Soyad","name","Adınız ve soyadınız"),
                                  ("🌆  Şehir (İsteğe bağlı)","city","Şehiriniz")]:
            col_v = QVBoxLayout(); col_v.setSpacing(3)
            col_v.addWidget(self._lbl(lbl_txt, 10, True))
            inp = QLineEdit(); inp.setPlaceholderText(ph); inp.setFixedHeight(40); inp.setStyleSheet(is_s)
            _only_letters_validator(inp)
            self.r_fields[key] = inp; col_v.addWidget(inp); row1.addLayout(col_v)
        row1_w = QWidget(); row1_w.setStyleSheet("background:transparent;"); row1_w.setLayout(row1)
        self.form_lay.addWidget(row1_w); self.form_lay.addSpacing(6)

        # E-posta — boşluk yasak (ama sayı/özel karakter serbest)
        self.form_lay.addWidget(self._lbl("✉  E-Posta Adresi", 10, True)); self.form_lay.addSpacing(3)
        em_inp = QLineEdit(); em_inp.setPlaceholderText("ornek@email.com"); em_inp.setFixedHeight(40); em_inp.setStyleSheet(is_s)
        def _email_filter(txt):
            f2 = txt.replace(' ', '')
            if f2 != txt: c = em_inp.cursorPosition(); em_inp.blockSignals(True); em_inp.setText(f2); em_inp.blockSignals(False); em_inp.setCursorPosition(max(0,c-1))
        em_inp.textChanged.connect(_email_filter)
        self.r_fields['email'] = em_inp; self.form_lay.addWidget(em_inp); self.form_lay.addSpacing(6)

        # Telefon — ülke kodu + 3.3.2.2 formatı
        self.form_lay.addWidget(self._lbl("📱  Telefon (İsteğe bağlı)", 10, True)); self.form_lay.addSpacing(3)
        ph_row = QHBoxLayout(); ph_row.setSpacing(8)
        self._ph_country_cb = QComboBox(); self._ph_country_cb.setFixedHeight(40); self._ph_country_cb.setFixedWidth(180)
        self._ph_country_cb.setStyleSheet(cb_s)
        for label, code, fmt in self.COUNTRY_CODES:
            self._ph_country_cb.addItem(label, (code, fmt))
        ph_inp = QLineEdit(); ph_inp.setFixedHeight(40); ph_inp.setStyleSheet(is_s)
        ph_inp.setMaxLength(13)

        def _update_ph_placeholder():
            code, fmt = self._ph_country_cb.currentData()
            # fmt gibi "3.3.2.2" → örnek "532 456 78 90"
            parts = [int(x) for x in fmt.split('.')]
            example = ' '.join('x'*n for n in parts)
            ph_inp.setPlaceholderText(f"{code} {example}")
            ph_inp.clear()
        self._ph_country_cb.currentIndexChanged.connect(_update_ph_placeholder)
        _update_ph_placeholder()

        def _phone_auto_format(txt):
            code, fmt = self._ph_country_cb.currentData()
            parts = [int(x) for x in fmt.split('.')]
            digits = _re2.sub(r'\D', '', txt)
            total = sum(parts)
            digits = digits[:total]
            result = ''; pos = 0
            for i, sz in enumerate(parts):
                chunk = digits[pos:pos+sz]; pos += sz
                if chunk: result += chunk + (' ' if i < len(parts)-1 else '')
            result = result.rstrip()
            if result != txt:
                c = ph_inp.cursorPosition(); ph_inp.blockSignals(True); ph_inp.setText(result)
                ph_inp.blockSignals(False); ph_inp.setCursorPosition(min(c, len(result)))
        ph_inp.textChanged.connect(_phone_auto_format)
        self.r_fields['phone_widget'] = ph_inp
        self.r_fields['phone_cb'] = self._ph_country_cb
        ph_row.addWidget(self._ph_country_cb); ph_row.addWidget(ph_inp, 1)
        ph_row_w = QWidget(); ph_row_w.setStyleSheet("background:transparent;"); ph_row_w.setLayout(ph_row)
        self.form_lay.addWidget(ph_row_w); self.form_lay.addSpacing(6)

        # Parola + tekrar — boşluk yasak (sayı/özel karakter serbest)
        row2 = QHBoxLayout(); row2.setSpacing(10)
        for lbl_txt, key, ph in [("🔒  Parola","pwd","En az 6 karakter"),
                                  ("🔒  Parola (Tekrar)","pwd2","Parolanızı tekrarlayın")]:
            col2 = QVBoxLayout(); col2.setSpacing(3)
            col2.addWidget(self._lbl(lbl_txt, 10, True))
            inp2 = QLineEdit(); inp2.setPlaceholderText(ph); inp2.setFixedHeight(40)
            inp2.setEchoMode(QLineEdit.Password); inp2.setStyleSheet(is_s)
            def _pwd_filter(txt, w=inp2):
                f3 = txt.replace(' ', '')
                if f3 != txt: c = w.cursorPosition(); w.blockSignals(True); w.setText(f3); w.blockSignals(False); w.setCursorPosition(max(0,c-1))
            inp2.textChanged.connect(_pwd_filter)
            self.r_fields[key] = inp2; col2.addWidget(inp2); row2.addLayout(col2)
        row2_w = QWidget(); row2_w.setStyleSheet("background:transparent;"); row2_w.setLayout(row2)
        self.form_lay.addWidget(row2_w); self.form_lay.addSpacing(4)

        self._pwd_strength_bar = QFrame(); self._pwd_strength_bar.setFixedHeight(4)
        self._pwd_strength_bar.setStyleSheet(f"background:{p('border')};border-radius:2px;")
        self._pwd_strength_lbl = self._lbl("", 9, False, p('mut'))
        self.form_lay.addWidget(self._pwd_strength_bar); self.form_lay.addWidget(self._pwd_strength_lbl)
        self.r_fields['pwd'].textChanged.connect(self._update_pwd_strength)
        self.form_lay.addSpacing(6)

        self.r_err = self._lbl("", 11, False, p('red')); self.form_lay.addWidget(self.r_err); self.form_lay.addSpacing(8)

        # ── Bot Doğrulama (Matematik CAPTCHA) ──
        import random as _rnd
        self._cap_a = _rnd.randint(1, 12)
        self._cap_b = _rnd.randint(1, 12)
        self._cap_ans = self._cap_a + self._cap_b
        cap_f = QFrame()
        cap_f.setStyleSheet(f"QFrame{{background:{p('card')};border:1.5px solid {p('border')};border-radius:10px;}}")
        cap_lay = QHBoxLayout(cap_f); cap_lay.setContentsMargins(14,10,14,10); cap_lay.setSpacing(10)
        cap_icon = QLabel("🤖"); cap_icon.setStyleSheet("font-size:18px;background:transparent;border:none;")
        cap_q = QLabel(f"Bot değil miyim? → {self._cap_a} + {self._cap_b} = ?")
        cap_q.setStyleSheet(f"color:{p('txt2')};font-size:12px;font-weight:600;background:transparent;border:none;")
        self._cap_inp = QLineEdit(); self._cap_inp.setFixedWidth(70); self._cap_inp.setFixedHeight(36)
        self._cap_inp.setPlaceholderText("Cevap"); self._cap_inp.setStyleSheet(Inp())
        def _cap_filter(txt, w=self._cap_inp):
            f_txt = ''.join(c for c in txt if c.isdigit())
            if f_txt != txt:
                c = w.cursorPosition(); w.blockSignals(True); w.setText(f_txt)
                w.blockSignals(False); w.setCursorPosition(max(0, c-1))
        self._cap_inp.textChanged.connect(_cap_filter)
        cap_lay.addWidget(cap_icon); cap_lay.addWidget(cap_q); cap_lay.addStretch(); cap_lay.addWidget(self._cap_inp)
        self.form_lay.addWidget(cap_f); self.form_lay.addSpacing(6)

        rb = QPushButton("🚀  Hesap Oluştur"); rb.setFixedHeight(44); rb.setCursor(QCursor(Qt.PointingHandCursor))
        rb.setStyleSheet(Btn(p('grn'), '#fff', '#25a050', 11)); rb.clicked.connect(self._do_register)
        self.form_lay.addWidget(rb); self.form_lay.addSpacing(10)

        bk = QPushButton("← Zaten hesabınız var mı? Giriş yapın"); bk.setCursor(QCursor(Qt.PointingHandCursor))
        bk.setStyleSheet(f"QPushButton{{background:transparent;color:{p('gold')};border:none;font-size:11px;font-weight:600;}}QPushButton:hover{{color:{p('gold2')};}}")
        bk.clicked.connect(self._show_user_login); self.form_lay.addWidget(bk, alignment=Qt.AlignCenter)

    def _update_pwd_strength(self, text):
        import re
        score = 0
        if len(text) >= 6: score += 1
        if len(text) >= 10: score += 1
        if re.search(r'[A-Z]', text): score += 1
        if re.search(r'\d', text): score += 1
        if re.search(r'[^a-zA-Z0-9]', text): score += 1
        colors = ['#d84040','#e07030','#e8b84b','#2eb85c','#2ab8b8']
        labels = ['Çok Zayıf','Zayıf','Orta','Güçlü','Çok Güçlü']
        pcts   = [20, 40, 60, 80, 100]
        idx = min(score, 4)
        col = colors[idx] if text else p('border')
        lbl_txt = f"Şifre Gücü: {labels[idx]}" if text else ""
        pct = pcts[idx] if text else 0
        self._pwd_strength_bar.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {col},stop:{pct/100:.2f} {col},"
            f"stop:{min(pct/100+0.001,1):.3f} {p('border')},stop:1 {p('border')});"
            f"border-radius:2px;")
        self._pwd_strength_lbl.setText(lbl_txt)
        self._pwd_strength_lbl.setStyleSheet(f"color:{col};font-size:9px;background:transparent;border:none;")

    def _do_user_login(self):
        em = self.u_email.text().strip(); pw = self.u_pwd.text()
        u = next((x for x in S.users if x['email']==em and x['pwd']==pw and x['role']=='user'),None)
        if u: S.user=u; S.role='user'; self.ok.emit('user')
        else: self.u_err.setText("❌ E-posta veya parola hatalı.")

    def _do_admin_login(self):
        em = self.a_email.text().strip(); pw = self.a_pwd.text()
        u = next((x for x in S.users if x['email']==em and x['pwd']==pw and x['role']=='admin'),None)
        if u: S.user=u; S.role='admin'; self.ok.emit('admin')
        else: self.a_err.setText("❌ Admin bilgileri hatalı.")

    def _do_register(self):
        import re as _re3
        f = self.r_fields; nm=f['name'].text().strip(); em=f['email'].text().strip()
        pw=f['pwd'].text(); pw2=f['pwd2'].text()
        city=f.get('city',QLineEdit()).text().strip()
        # Yeni telefon alanı
        ph_widget = f.get('phone_widget'); ph_cb = f.get('phone_cb')
        if ph_widget and ph_cb:
            code, fmt = ph_cb.currentData()
            ph_digits = ph_widget.text().strip()
            phone = f"{code} {ph_digits}".strip() if ph_digits else ""
        else:
            phone = f.get('phone', QLineEdit()).text().strip() if 'phone' in f else ""
        # Boşluk yasak — hepsinde
        for field_nm, val in [("Ad",nm)]:
            if ' ' in val: self.r_err.setText(f"❌ {field_nm} alanında boşluk bırakılamaz."); return
        if ' ' in em: self.r_err.setText("❌ E-posta adresi boşluk içeremez."); return
        if ' ' in pw: self.r_err.setText("❌ Parola boşluk içeremez."); return
        # Zorunlu alan kontrolü
        if not all([nm,em,pw]): self.r_err.setText("❌ Ad, e-posta ve parola zorunludur."); return
        if '@' not in em or '.' not in em.split('@')[-1]:
            self.r_err.setText("❌ Geçerli bir e-posta adresi girin."); return
        if pw!=pw2: self.r_err.setText("❌ Parolalar eşleşmiyor."); return
        if len(pw)<6: self.r_err.setText("❌ Parola en az 6 karakter."); return
        if len(nm) < 2: self.r_err.setText("❌ Ad en az 2 karakter olmalıdır."); return
        # Ad/Şehir'de sayı/özel karakter yasak
        if _re3.search(r'[0-9!@#$%^&*()_+={}\[\]|\\:;"\'<>,.?/~`]', nm):
            self.r_err.setText("❌ Ad alanında sayı veya özel karakter kullanılamaz."); return
        if city and _re3.search(r'[0-9!@#$%^&*()_+={}\[\]|\\:;"\'<>,.?/~`]', city):
            self.r_err.setText("❌ Şehir alanında sayı veya özel karakter kullanılamaz."); return
        if any(u['email']==em for u in S.users): self.r_err.setText("❌ E-posta zaten kayıtlı."); return
        # Bot doğrulama kontrolü
        cap_val = self._cap_inp.text().strip() if hasattr(self, '_cap_inp') else ''
        if not cap_val: self.r_err.setText("❌ Lütfen bot doğrulama sorusunu cevaplayın."); return
        try:
            if int(cap_val) != self._cap_ans:
                self.r_err.setText("❌ Bot doğrulama cevabı yanlış. Tekrar deneyin."); return
        except ValueError:
            self.r_err.setText("❌ Geçersiz doğrulama cevabı."); return
        nu={"id":S.nxt_uid,"name":nm,"email":em,"pwd":pw,"role":"user",
            "joined":datetime.now().strftime("%Y-%m-%d"),"phone":phone,"city":city}
        S.nxt_uid+=1; S.users.append(nu)
        self._clr()
        self.form_lay.addSpacing(30)
        ok_lbl = self._lbl("✅ Hesabınız oluşturuldu!", 18, True, p('grn'))
        ok_lbl.setAlignment(Qt.AlignCenter); self.form_lay.addWidget(ok_lbl)
        self.form_lay.addSpacing(8)
        sub_lbl = self._lbl(f"Hoş geldiniz, {nm}!\nArtık e-posta ve parolanızla giriş yapabilirsiniz.", 12, False, p('mut'))
        sub_lbl.setAlignment(Qt.AlignCenter); sub_lbl.setWordWrap(True); self.form_lay.addWidget(sub_lbl)
        self.form_lay.addSpacing(24)
        login_btn = QPushButton("🧳  Giriş Yap"); login_btn.setFixedHeight(46); login_btn.setCursor(QCursor(Qt.PointingHandCursor))
        login_btn.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),11))
        login_btn.clicked.connect(self._show_user_login); self.form_lay.addWidget(login_btn)
        self.form_lay.addStretch()

# ═══════════════════════════════════════════
#  BİLDİRİM ÇAN BUTONU (TopBar için)
# ═══════════════════════════════════════════
class BellButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("🔔", parent)
        self.setFixedSize(38,38)
        self._count = 0
        self.setStyleSheet(f"QPushButton{{background:{p('bg3')};color:{p('txt2')};border:1px solid {p('border')};border-radius:9px;font-size:14px;}}"
                           f"QPushButton:hover{{border-color:{p('gold')};color:{p('gold')};}}")
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def set_count(self, n):
        self._count = n
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._count > 0:
            qp = QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
            qp.setBrush(QBrush(QColor(p('red')))); qp.setPen(Qt.NoPen)
            qp.drawEllipse(22, 2, 14, 14)
            qp.setPen(QPen(QColor('#fff'))); qp.setFont(QFont("Arial",7,QFont.Bold))
            qp.drawText(22,2,14,14,Qt.AlignCenter,str(min(self._count,99))); qp.end()

# ═══════════════════════════════════════════
#  BİLDİRİM POPUP (açılan kutu)
# ═══════════════════════════════════════════
class NotifPopup(QFrame):
    go_ticket = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup|Qt.FramelessWindowHint)
        self.setFixedWidth(340)
        self.setStyleSheet(f"QFrame{{background:{p('bg3')};border:1.5px solid {p('brd2')};border-radius:12px;}}")
        self._build()

    def _build(self):
        self._lay = QVBoxLayout(self); self._lay.setContentsMargins(0,0,0,0); self._lay.setSpacing(0)
        hdr = QFrame(); hdr.setFixedHeight(44)
        hdr.setStyleSheet(f"background:{p('bg4')};border-radius:12px 12px 0 0;border-bottom:1px solid {p('border')};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(14,0,14,0)
        tl = QLabel("🔔  Bildirimler")
        tl.setStyleSheet(f"color:{p('txt')};font-size:13px;font-weight:700;background:transparent;border:none;")
        hl.addWidget(tl); hl.addStretch()
        self._lay.addWidget(hdr)
        self._body = QWidget(); self._body.setStyleSheet("background:transparent;")
        self._body_lay = QVBoxLayout(self._body); self._body_lay.setContentsMargins(0,0,0,0); self._body_lay.setSpacing(0)
        self._lay.addWidget(self._body)
        foot = QFrame(); foot.setFixedHeight(40)
        foot.setStyleSheet(f"background:{p('bg4')};border-top:1px solid {p('border')};border-radius:0 0 12px 12px;")
        fl = QHBoxLayout(foot); fl.setContentsMargins(14,0,14,0)
        gb = QPushButton("Tüm ticketları gör →"); gb.setCursor(QCursor(Qt.PointingHandCursor))
        gb.setStyleSheet(f"QPushButton{{background:transparent;color:{p('gold')};border:none;font-size:11px;font-weight:600;}}QPushButton:hover{{color:{p('gold2')};}}")
        gb.clicked.connect(self._go); fl.addStretch(); fl.addWidget(gb)
        self._lay.addWidget(foot)

    def _go(self):
        self.hide(); self.go_ticket.emit()

    def refresh(self):
        while self._body_lay.count():
            it = self._body_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        pending = [t for t in S.tickets if t['durum'] == 'bekliyor']
        if not pending:
            lbl = QLabel("✅  Bekleyen ticket yok"); lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color:{p('mut')};font-size:12px;padding:20px;background:transparent;border:none;")
            self._body_lay.addWidget(lbl)
        else:
            for t in pending[-5:][::-1]:
                row = QFrame()
                row.setStyleSheet(f"QFrame{{background:transparent;border-bottom:1px solid {p('border')};}}")
                rl = QHBoxLayout(row); rl.setContentsMargins(14,10,14,10); rl.setSpacing(8)
                dot = QLabel("●"); dot.setFixedSize(10,10)
                dot.setStyleSheet(f"color:{p('orange')};font-size:9px;background:transparent;border:none;")
                info = QVBoxLayout(); info.setSpacing(1)
                t1 = QLabel(f"{t['konu'][:30]}...") if len(t['konu'])>30 else QLabel(t['konu'])
                t1.setStyleSheet(f"color:{p('txt')};font-size:11px;font-weight:600;background:transparent;border:none;")
                t2 = QLabel(f"{t['user_name']} · {t['tarih'][:10]}")
                t2.setStyleSheet(f"color:{p('mut')};font-size:9px;background:transparent;border:none;")
                info.addWidget(t1); info.addWidget(t2)
                rl.addWidget(dot); rl.addLayout(info); rl.addStretch()
                self._body_lay.addWidget(row)
        self.adjustSize()

# ═══════════════════════════════════════════
#  ANA UYGULAMA
# ═══════════════════════════════════════════
class MainApp(QWidget):
    logout_req = pyqtSignal()
    def __init__(self, start_page='home'):
        super().__init__(); self.setStyleSheet(f"background:{p('bg')};")
        self.toast = Toast(self); self._notif_popup = None
        self._setup_layout(); self._build_all_pages(); self._nav(start_page)
        if S.role == 'admin':
            self._bell_timer = QTimer(); self._bell_timer.timeout.connect(self._update_bell); self._bell_timer.start(3000)

    def _setup_layout(self):
        out = QHBoxLayout(self); out.setContentsMargins(0,0,0,0); out.setSpacing(0)
        self.sb = self._make_sidebar(); out.addWidget(self.sb)
        rw = QWidget(); rw.setStyleSheet(f"background:{p('bg')};")
        rv = QVBoxLayout(rw); rv.setContentsMargins(0,0,0,0); rv.setSpacing(0)
        self.topbar = self._make_topbar(); rv.addWidget(self.topbar)
        self.stack = QStackedWidget(); self.stack.setStyleSheet(f"background:{p('bg')};")
        rv.addWidget(self.stack); out.addWidget(rw)

    def _make_sidebar(self):
        sb = QFrame(); sb.setFixedWidth(210)
        sb.setStyleSheet(f"QFrame{{background:{p('nav')};border-right:1px solid {p('navbrd')};}}")
        sv = QVBoxLayout(sb); sv.setContentsMargins(0,0,0,0); sv.setSpacing(0)
        lf = QFrame(); lf.setFixedHeight(64)
        lf.setStyleSheet(f"background:transparent;border-bottom:1px solid {p('navbrd')};")
        ll = QVBoxLayout(lf); ll.setContentsMargins(16,10,16,10)
        lt = QLabel("✈  VOYAGER"); lt.setStyleSheet(f"color:{p('gold')};font-size:17px;font-weight:700;letter-spacing:4px;background:transparent;border:none;")
        ls = QLabel("Seyahat Platformu"); ls.setStyleSheet(f"color:{p('mut')};font-size:9px;letter-spacing:2px;background:transparent;border:none;")
        ll.addWidget(lt); ll.addWidget(ls); sv.addWidget(lf)
        ns = QScrollArea(); ns.setWidgetResizable(True); ns.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self.nav_cont = QWidget(); self.nav_cont.setStyleSheet("background:transparent;")
        self.nav_v = QVBoxLayout(self.nav_cont); self.nav_v.setContentsMargins(8,12,8,12); self.nav_v.setSpacing(2)
        ns.setWidget(self.nav_cont); sv.addWidget(ns)
        ff = QFrame(); ff.setFixedHeight(60)
        ff.setStyleSheet(f"background:transparent;border-top:1px solid {p('navbrd')};")
        fl = QHBoxLayout(ff); fl.setContentsMargins(12,8,12,8); fl.setSpacing(8)
        nm = S.user['name'] if S.user else ''
        av = QLabel(nm[0].upper() if nm else '?'); av.setFixedSize(32,32); av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet(f"background:{p('gold')}22;border:1.5px solid {p('gold')};border-radius:16px;color:{p('gold')};font-size:12px;font-weight:700;")
        ic = QVBoxLayout(); ic.setSpacing(0)
        in1 = QLabel(nm); in1.setStyleSheet(f"color:{p('txt')};font-size:11px;font-weight:600;background:transparent;border:none;")
        in2 = QLabel("Yönetici" if S.role=='admin' else "Üye")
        in2.setStyleSheet(f"color:{p('mut')};font-size:9px;background:transparent;border:none;")
        ic.addWidget(in1); ic.addWidget(in2)
        lg = QPushButton("Çık"); lg.setStyleSheet(f"QPushButton{{background:transparent;color:{p('mut')};border:none;font-size:10px;}}QPushButton:hover{{color:{p('red')};}}")
        lg.setCursor(QCursor(Qt.PointingHandCursor)); lg.clicked.connect(self.logout_req.emit)
        fl.addWidget(av); fl.addLayout(ic); fl.addStretch(); fl.addWidget(lg); sv.addWidget(ff)
        return sb

    def _build_nav(self):
        while self.nav_v.count():
            it = self.nav_v.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        def sec(txt):
            l = QLabel(txt); l.setStyleSheet(f"color:{p('mut2')};font-size:9px;letter-spacing:2px;padding:10px 8px 3px;background:transparent;border:none;")
            self.nav_v.addWidget(l)
        def nbtn(pid,ico,lbl):
            b = QPushButton(f"  {ico}  {lbl}"); b.setFixedHeight(36); active = S.page==pid
            b.setStyleSheet(f"QPushButton{{background:{p('gold')+'22' if active else 'transparent'};"
                            f"color:{p('gold') if active else p('txt3')};border:none;border-radius:9px;"
                            f"font-size:12px;font-weight:{'700' if active else '400'};text-align:left;padding-left:10px;}}"
                            f"QPushButton:hover{{background:{p('bg3')};color:{p('txt2')};}}")
            b.setCursor(QCursor(Qt.PointingHandCursor)); b.clicked.connect(lambda _,pg=pid: self._nav(pg)); self.nav_v.addWidget(b)
        sec("MENÜ")
        if S.role == 'admin':
            sec("YÖNETİM"); nbtn('admin','⚙','Admin Paneli')
            sec("HESAP"); nbtn('profile','👤','Profilim'); self.nav_v.addStretch()
        else:
            nbtn('home','🏠','Ana Sayfa'); nbtn('explore','🌍','Destinasyonlar')
            nbtn('plan','🗺','Tatil Planı')
            nbtn('bookings','📋','Rezervasyonlarım'); nbtn('favorites','⭐','Favorilerim')
            nbtn('support','🎫','Teknik Destek')
            sec("HESAP"); nbtn('profile','👤','Profilim'); self.nav_v.addStretch()

    def _make_topbar(self):
        tb = QFrame(); tb.setFixedHeight(52)
        tb.setStyleSheet(f"QFrame{{background:{p('nav')};border-bottom:1px solid {p('navbrd')};}}")
        tl = QHBoxLayout(tb); tl.setContentsMargins(20,0,20,0); tl.setSpacing(12)
        self.tb_title = QLabel("Ana Sayfa")
        self.tb_title.setStyleSheet(f"color:{p('txt')};font-size:15px;font-weight:700;background:transparent;border:none;")
        sf = QFrame(); sf.setStyleSheet(f"QFrame{{background:{p('bg3')};border:1px solid {p('border')};border-radius:9px;}}")
        sfl = QHBoxLayout(sf); sfl.setContentsMargins(9,0,9,0); sfl.setSpacing(5)
        si = QLabel("🔍"); si.setStyleSheet("background:transparent;border:none;font-size:11px;")
        self.s_inp = QLineEdit(); self.s_inp.setPlaceholderText("Destinasyon, otel ara...")
        self.s_inp.setFixedHeight(34); self.s_inp.setMinimumWidth(220)
        self.s_inp.setStyleSheet(f"QLineEdit{{background:transparent;border:none;color:{p('txt')};font-size:12px;}}")
        self.s_inp.textChanged.connect(self._on_search)
        sfl.addWidget(si); sfl.addWidget(self.s_inp)
        tl.addWidget(self.tb_title); tl.addStretch(); tl.addWidget(sf)
        # Admin bildirim çanı
        if S.role == 'admin':
            self.bell_btn = BellButton()
            pending = len([t for t in S.tickets if t['durum']=='bekliyor'])
            self.bell_btn.set_count(pending)
            self.bell_btn.clicked.connect(self._toggle_notif)
            tl.addWidget(self.bell_btn)
        return tb

    def _update_bell(self):
        if hasattr(self,'bell_btn'):
            pending = len([t for t in S.tickets if t['durum']=='bekliyor'])
            self.bell_btn.set_count(pending)

    def _toggle_notif(self):
        if self._notif_popup and self._notif_popup.isVisible():
            self._notif_popup.hide(); return
        if not self._notif_popup:
            self._notif_popup = NotifPopup(self)
            self._notif_popup.go_ticket.connect(lambda: self._nav_admin_ticket())
        self._notif_popup.refresh()
        btn_pos = self.bell_btn.mapToGlobal(QPoint(0,0))
        popup_x = btn_pos.x() - 340 + self.bell_btn.width()
        popup_y = btn_pos.y() + self.bell_btn.height() + 4
        self._notif_popup.move(popup_x, popup_y)
        self._notif_popup.show(); self._notif_popup.raise_()

    def _nav_admin_ticket(self):
        self._atab = 'tickets'; self._nav('admin')

    def _on_search(self, txt):
        S.search = txt.strip().lower()
        if S.page in ('home','explore'): self._nav('explore')

    def _nav(self, page):
        S.page = page
        titles = {'home':'Ana Sayfa','explore':'Destinasyonlar','bookings':'Rezervasyonlarım',
                  'favorites':'Favorilerim','profile':'Profilim','admin':'Admin Paneli',
                  'support':'Teknik Destek','plan':'🗺 Tatil Planı'}
        self.tb_title.setText(titles.get(page,''))
        self._build_nav()
        if page in self._pages: self.stack.setCurrentWidget(self._pages[page])
        getattr(self,f'_refresh_{page}',lambda:None)()

    def _page(self, pid):
        pg = QWidget(); pg.setStyleSheet(f"background:{p('bg')};")
        v = QVBoxLayout(pg); v.setContentsMargins(0,0,0,0)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        inn = QWidget(); inn.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(inn); lay.setContentsMargins(22,22,22,22); lay.setSpacing(16)
        sc.setWidget(inn); v.addWidget(sc)
        self.stack.addWidget(pg); self._pages[pid] = pg
        if not hasattr(self, '_scrolls'): self._scrolls = {}
        self._scrolls[pid] = sc
        return lay

    def _build_all_pages(self):
        self._pages = {}
        self.home_v = self._page('home'); self.explore_v = self._page('explore')
        self.booking_v = self._page('bookings'); self.fav_v = self._page('favorites')
        self.profile_v = self._page('profile'); self.support_v = self._page('support')
        self.plan_v = self._page('plan')
        if S.role == 'admin': self.admin_v = self._page('admin')

    def _clr_lay(self, lay):
        while lay.count():
            it = lay.takeAt(0)
            if it.widget():
                w = it.widget()
                w.setParent(None)
                w.deleteLater()
            elif it.layout():
                self._clr_lay(it.layout())
            elif it.spacerItem():
                pass  # spacer otomatik silinir

    def _lbl2(self, txt, fs=11, bold=False, col=None):
        l = QLabel(txt); fw = '700' if bold else '400'
        l.setStyleSheet(f"color:{col or p('txt2')};font-size:{fs}px;font-weight:{fw};background:transparent;border:none;")
        return l

    # ══════════════════════════════
    #  ANA SAYFA
    # ══════════════════════════════
    def _refresh_home(self):
        v = self.home_v; self._clr_lay(v)
        nm = S.user['name'] if S.user else 'Yolcu'
        hero = QFrame()
        hero.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                           f"stop:0 #09091a,stop:0.5 #0c0e20,stop:1 #080812);"
                           f"border:1px solid {p('border')};border-radius:14px;}}")
        hv = QVBoxLayout(hero); hv.setContentsMargins(30,22,30,22); hv.setSpacing(7)
        ht = QLabel("DÜNYANIN EN İYİ DESTİNASYONLARI")
        ht.setStyleSheet(f"color:{p('gold3')};font-size:9px;font-weight:700;letter-spacing:3px;background:transparent;border:none;")
        h1 = QLabel(f"Hayalinizdeki Seyahati\nPlanlayın")
        h1.setStyleSheet(f"color:{p('txt')};font-size:26px;font-weight:700;background:transparent;border:none;")
        h2 = QLabel(f"Merhaba {nm}! {len(DESTS)} destinasyon, {sum(len(d['hotels']) for d in DESTS)} otel ile size özel rotalar oluşturun.")
        h2.setStyleSheet(f"color:{p('txt3')};font-size:12px;background:transparent;border:none;"); h2.setWordWrap(True)
        hv.addWidget(ht); hv.addWidget(h1); hv.addWidget(h2); hv.addSpacing(10)
        sr = QHBoxLayout(); sr.setSpacing(10)
        for val,lbl,col in [(str(len(DESTS)),"Destinasyon",p('gold')),(str(sum(len(d['hotels']) for d in DESTS)),"Otel",p('blue2')),
                            (str(sum(len(d['places']) for d in DESTS)),"Gezilecek Yer",p('grn')),(str(len(S.bookings)),"Rezervasyonunuz",p('purp'))]:
            sf = QFrame(); sf.setStyleSheet(f"background:{p('card')};border:1px solid {p('border')};border-radius:9px;")
            sl = QHBoxLayout(sf); sl.setContentsMargins(13,9,13,9)
            vl = QLabel(val); vl.setStyleSheet(f"color:{col};font-size:18px;font-weight:700;background:transparent;border:none;")
            nl = QLabel(f"  {lbl}"); nl.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
            sl.addWidget(vl); sl.addWidget(nl); sl.addStretch(); sr.addWidget(sf)
        sw = QWidget(); sw.setStyleSheet("background:transparent;"); sw.setLayout(sr)
        hv.addWidget(sw); v.addWidget(hero)

        # ══ FIRSATLAR BÖLÜMÜ ══
        # Her açılışta rastgele indirim uygula
        _ALL_DEALS = [
            ("Antalya",   "Rixos Belek",         (30,50), "🔥 FLASH İNDİRİM",    "red",    True),
            ("Bali",      "Seminyak Beach",       (20,45), "⚡ SON 5 YER!",       "orange", False),
            ("Istanbul",  "Sultanahmet Butik",    (15,35), "🏆 EN ÇOK SATAN",    "gold",   False),
            ("Prag",      "Old Town Inn",         (20,40), "🕐 ERKEN REZERV",     "blue2",  False),
            ("Marakes",   "Riad Farnatchi",       (25,45), "✨ VIP FIRSATI",      "purp",   True),
            ("Barselona", "Gothic Quarter",       (15,30), "🌟 YENİ LİSTELENDİ", "grn",    False),
            ("Kyoto",     "The Celestine Kyoto",  (20,40), "🎌 ÖZEL TATİL",      "teal",   False),
            ("Rio",       "Santa Teresa Hotel",   (25,50), "🎉 HAFİF SEZON",     "red",    True),
            ("Dubai",     "Atlantis The Palm",    (10,25), "💎 LÜKS İNDİRİM",    "gold",   False),
            ("Maldivler", "Coco Palm Dhuni",      (15,30), "🌊 BALIK SEZONU",    "blue2",  True),
        ]
        _KALAN_OPTIONS = ["3sa 20dk","11sa 50dk","18sa 30dk","1g 4sa","1g 12sa","2g 0sa","2g 17sa","3g 8sa","23sa 14dk","6sa 45dk"]
        random.shuffle(_ALL_DEALS)
        DEALS_DATA = []
        for (d_key, otel_adi, disc_range, badge_txt, badge_col_key, is_extra_flag) in _ALL_DEALS[:8]:
            disc = random.randint(*disc_range)
            kalan = random.choice(_KALAN_OPTIONS)
            DEALS_DATA.append((d_key, otel_adi, disc, badge_txt, badge_col_key, kalan, is_extra_flag))

        DEST_KEYS = {
            "Antalya": "Antalya", "Bali": "Bali", "Istanbul": "İstanbul",
            "Prag": "Prag", "Marakes": "Marakeş", "Barselona": "Barselona",
            "Kyoto": "Kyoto", "Rio": "Rio de Janeiro",
            "Dubai": "Dubai", "Maldivler": "Maldivler",
        }

        deals_hdr = QHBoxLayout()
        deals_icon = QLabel("🔥"); deals_icon.setStyleSheet("font-size:20px;background:transparent;border:none;")
        deals_title = QLabel("KAÇIRILMAYACAK FIRSATLAR")
        deals_title.setStyleSheet(f"color:{p('gold')};font-size:12px;font-weight:700;letter-spacing:3px;background:transparent;border:none;")
        deals_sub = QLabel("Sınırlı süre · Erken rezerv indirimleri")
        deals_sub.setStyleSheet(f"color:{p('red')};font-size:10px;font-weight:600;background:transparent;border:none;")
        deals_hdr.addWidget(deals_icon); deals_hdr.addSpacing(6); deals_hdr.addWidget(deals_title)
        deals_hdr.addSpacing(14); deals_hdr.addWidget(deals_sub); deals_hdr.addStretch()
        dhw = QWidget(); dhw.setStyleSheet("background:transparent;"); dhw.setLayout(deals_hdr)
        v.addWidget(dhw)

        deals_scroll = QScrollArea(); deals_scroll.setFixedHeight(182)
        deals_scroll.setWidgetResizable(True)
        deals_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        deals_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        deals_scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            f"QScrollBar:horizontal{{background:{p('bg2')};height:5px;border-radius:2px;}}"
            f"QScrollBar::handle:horizontal{{background:{p('border')};border-radius:2px;}}"
        )
        deals_inner = QWidget(); deals_inner.setStyleSheet("background:transparent;")
        deals_lay = QHBoxLayout(deals_inner); deals_lay.setContentsMargins(2,4,2,4); deals_lay.setSpacing(12)

        for deal_item in DEALS_DATA:
            d_key, otel_adi, disc, badge_txt, badge_col_key, kalan, is_extra = deal_item
            real_name = DEST_KEYS.get(d_key, d_key)
            dest = next((d for d in DESTS if d['name'] == real_name), None)
            if not dest: continue
            badge_col = p(badge_col_key)
            otel = next((h for h in dest['hotels'] if h.otel_adi == otel_adi), None)
            base_price = otel.fiyat if otel else dest['price']
            orig_price = int(base_price * 100 / (100 - disc))
            disc_price = base_price

            df = QFrame(); df.setFixedSize(232, 172); df.setCursor(QCursor(Qt.PointingHandCursor))
            df.setStyleSheet(
                f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                f"stop:0 {dest['color']}dd,stop:1 {dest['color']}66);"
                f"border:1.5px solid {p('brd2')};border-radius:16px;}}"
                f"QFrame:hover{{border-color:{badge_col};border-width:2.5px;background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {dest['color']}ff,stop:1 {dest['color']}88);}}"
            )
            dl = QVBoxLayout(df); dl.setContentsMargins(13,10,13,10); dl.setSpacing(3)

            badge_row = QHBoxLayout(); badge_row.setSpacing(0)
            badge_lbl = QLabel(badge_txt)
            badge_lbl.setStyleSheet(f"background:{badge_col};color:#fff;border:none;border-radius:6px;padding:2px 7px;font-size:8px;font-weight:700;")
            flag_lbl = QLabel(dest['flag']); flag_lbl.setStyleSheet("font-size:20px;background:transparent;border:none;")
            badge_row.addWidget(badge_lbl); badge_row.addStretch(); badge_row.addWidget(flag_lbl)
            dl.addLayout(badge_row)

            nm_l = QLabel(dest['name']); nm_l.setStyleSheet("color:#fff;font-size:13px;font-weight:700;background:transparent;border:none;")
            otel_l = QLabel(otel_adi); otel_l.setStyleSheet(f"color:#ffffffaa;font-size:9px;background:transparent;border:none;")
            dl.addWidget(nm_l); dl.addWidget(otel_l); dl.addStretch()

            price_row = QHBoxLayout(); price_row.setSpacing(6)
            orig_l = QLabel(f"${orig_price}"); orig_l.setStyleSheet(f"color:#ffffff55;font-size:10px;text-decoration:line-through;background:transparent;border:none;")
            new_l = QLabel(f"${disc_price}"); new_l.setStyleSheet(f"color:{p('gold2')};font-size:16px;font-weight:700;background:transparent;border:none;")
            disc_lbl_txt = f"-%{disc}" + (" ⭐" if is_extra else "")
            disc_col2 = p('purp') if is_extra else p('red')
            disc_l = QLabel(disc_lbl_txt); disc_l.setStyleSheet(f"background:{disc_col2};color:#fff;border:none;border-radius:5px;padding:1px 6px;font-size:8px;font-weight:700;")
            per_l = QLabel("/gece"); per_l.setStyleSheet(f"color:#ffffff66;font-size:9px;background:transparent;border:none;")
            price_row.addWidget(orig_l); price_row.addWidget(new_l); price_row.addWidget(per_l); price_row.addStretch(); price_row.addWidget(disc_l)
            dl.addLayout(price_row)

            time_row = QHBoxLayout()
            t_lbl = QLabel(f"⏱  Son {kalan}"); t_lbl.setStyleSheet(f"color:{p('orange')};font-size:9px;font-weight:600;background:transparent;border:none;")
            book_btn = QPushButton("Rezerve Et →"); book_btn.setFixedHeight(22); book_btn.setCursor(QCursor(Qt.PointingHandCursor))
            book_btn.setStyleSheet(f"QPushButton{{background:{badge_col}33;color:{badge_col};border:1px solid {badge_col}66;border-radius:5px;font-size:8px;font-weight:700;padding:0 7px;}}"
                                   f"QPushButton:hover{{background:{badge_col}66;color:#fff;}}")
            time_row.addWidget(t_lbl); time_row.addStretch(); time_row.addWidget(book_btn)
            dl.addLayout(time_row)

            # Tüm karta ve butona tıklama bağla
            def _open_deal_dest(checked=False, d=dest): self._open_detail(d)
            book_btn.clicked.connect(_open_deal_dest)
            df.mousePressEvent = (lambda e, d=dest: self._open_detail(d))
            deals_lay.addWidget(df)

        deals_lay.addStretch()
        deals_scroll.setWidget(deals_inner)
        v.addWidget(deals_scroll)
        mf = QFrame(); mf.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:14px;}}")
        mf.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        mf.setMinimumHeight(510)
        mv = QVBoxLayout(mf); mv.setContentsMargins(0,0,0,0); mv.setSpacing(0)
        mhdr = QFrame(); mhdr.setFixedHeight(44)
        mhdr.setStyleSheet(f"background:transparent;border-bottom:1px solid {p('border')};")
        mhl = QHBoxLayout(mhdr); mhl.setContentsMargins(16,0,16,0)
        mt = QLabel("🌍  Dünya Haritası"); mt.setStyleSheet(f"color:{p('txt')};font-size:13px;font-weight:700;background:transparent;border:none;")
        ms = QLabel("Destinasyona tıklayın"); ms.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
        mhl.addWidget(mt); mhl.addSpacing(10); mhl.addWidget(ms); mhl.addStretch()
        self.world_map = GoogleMapWidget(); self.world_map.clicked.connect(self._map_click)
        mv.addWidget(mhdr); mv.addWidget(self.world_map); v.addWidget(mf)
        fl = QLabel("ÖNE ÇIKAN DESTİNASYONLAR")
        fl.setStyleSheet(f"color:{p('mut')};font-size:10px;font-weight:700;letter-spacing:3px;background:transparent;border:none;")
        v.addWidget(fl)
        featured = sorted(DESTS,key=lambda d:d['rating'],reverse=True)[:8]
        gw = QWidget(); gw.setStyleSheet("background:transparent;")
        g = QGridLayout(gw); g.setSpacing(12); g.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        for i,dest in enumerate(featured):
            c = DestCard(dest); c.clicked.connect(self._open_detail); c.fav_click.connect(lambda _:None)
            g.addWidget(c,i//4,i%4)
        v.addWidget(gw)
        ab = QPushButton("Tüm Destinasyonları Gör  →"); ab.setFixedHeight(38); ab.setCursor(QCursor(Qt.PointingHandCursor))
        ab.setStyleSheet(f"QPushButton{{background:{p('bg3')};color:{p('txt2')};border:1px solid {p('border')};border-radius:9px;font-size:12px;font-weight:600;}}"
                         f"QPushButton:hover{{border-color:{p('gold')};color:{p('gold')};}}")
        ab.clicked.connect(lambda: self._nav('explore')); v.addWidget(ab,alignment=Qt.AlignHCenter); v.addStretch()

    def _map_click(self, name):
        dest = next((d for d in DESTS if d['name']==name),None)
        if dest: self._open_detail(dest)

    # ══════════════════════════════
    #  DESTİNASYONLAR
    # ══════════════════════════════
    def _refresh_explore(self):
        v = self.explore_v; self._clr_lay(v)
        # ── Filtre + Sıralama satırı ──
        ff = QFrame(); ff.setStyleSheet(f"QFrame{{background:{p('bg2')};border:1px solid {p('border')};border-radius:11px;}}")
        fl = QHBoxLayout(ff); fl.setContentsMargins(12,8,12,8); fl.setSpacing(7)
        ql = QLabel("Kıta:"); ql.setStyleSheet(f"color:{p('mut')};font-size:11px;background:transparent;border:none;")
        fl.addWidget(ql)
        conts = ['Tümü'] + sorted(set(d['cont'] for d in DESTS))
        for ct in conts:
            b = QPushButton(ct); b.setFixedHeight(26); active = S.filt_cont==ct
            b.setStyleSheet(f"QPushButton{{padding:0 10px;border-radius:7px;font-size:10px;font-weight:600;"
                            f"border:1px solid {p('gold') if active else p('border')};"
                            f"background:{p('gold')+'22' if active else p('bg3')};"
                            f"color:{p('gold') if active else p('txt3')};}}"
                            f"QPushButton:hover{{border-color:{p('gold')};color:{p('gold')};}}")
            b.setCursor(QCursor(Qt.PointingHandCursor)); b.clicked.connect(lambda _,c=ct: self._filt(c)); fl.addWidget(b)
        fl.addStretch()
        # Sıralama combobox
        sort_lbl = QLabel("Sırala:"); sort_lbl.setStyleSheet(f"color:{p('mut')};font-size:11px;background:transparent;border:none;")
        self.sort_cb = QComboBox(); self.sort_cb.setFixedHeight(28); self.sort_cb.setFixedWidth(160)
        self.sort_cb.setStyleSheet(
            f"QComboBox{{background:{p('bg3')};color:{p('txt')};border:1px solid {p('border')};border-radius:7px;"
            f"padding:2px 10px;font-size:11px;font-weight:600;}}"
            f"QComboBox::drop-down{{border:none;width:18px;}}"
            f"QComboBox QAbstractItemView{{background:{p('bg3')};color:{p('txt')};selection-background-color:{p('gold')}44;"
            f"border:1px solid {p('border')};}}")
        sort_opts = [("⭐ Puana Göre","puan"),("💰 Fiyat (Düşük→Yüksek)","fiyat_asc"),
                     ("💎 Fiyat (Yüksek→Düşük)","fiyat_desc"),("🔤 İsme Göre","isim")]
        for lbl2,key in sort_opts: self.sort_cb.addItem(lbl2,key)
        cur_keys = [k for _,k in sort_opts]
        if S.sort_key in cur_keys: self.sort_cb.setCurrentIndex(cur_keys.index(S.sort_key))
        self.sort_cb.currentIndexChanged.connect(self._on_sort_change)
        fl.addWidget(sort_lbl); fl.addWidget(self.sort_cb)
        self.cnt_lbl = QLabel(); self.cnt_lbl.setStyleSheet(f"color:{p('mut')};font-size:11px;background:transparent;border:none;")
        fl.addSpacing(6); fl.addWidget(self.cnt_lbl); v.addWidget(ff)
        # ── Filtreleme ──
        filt = list(DESTS)
        if S.filt_cont != 'Tümü': filt = [d for d in filt if d['cont']==S.filt_cont]
        if S.search: filt = [d for d in filt if S.search in d['name'].lower() or S.search in d['country'].lower()
                             or any(S.search in tg.lower() for tg in d['tags'])]
        # ── Sıralama ──
        if S.sort_key == 'puan': filt.sort(key=lambda d: d['rating'], reverse=True)
        elif S.sort_key == 'fiyat_asc': filt.sort(key=lambda d: d['price'])
        elif S.sort_key == 'fiyat_desc': filt.sort(key=lambda d: d['price'], reverse=True)
        elif S.sort_key == 'isim': filt.sort(key=lambda d: d['name'])
        self.cnt_lbl.setText(f"{len(filt)} destinasyon")
        if not filt:
            e = QLabel("🔍 Sonuç bulunamadı"); e.setAlignment(Qt.AlignCenter)
            e.setStyleSheet(f"color:{p('mut')};font-size:15px;padding:50px;background:transparent;border:none;")
            v.addWidget(e); return
        gw = QWidget(); gw.setStyleSheet("background:transparent;")
        g = QGridLayout(gw); g.setSpacing(12); g.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        for i,dest in enumerate(filt):
            c = DestCard(dest); c.clicked.connect(self._open_detail); c.fav_click.connect(lambda _:None)
            g.addWidget(c,i//4,i%4)
        v.addWidget(gw); v.addStretch()

    def _filt(self, ct): S.filt_cont=ct; self._refresh_explore()

    def _on_sort_change(self, idx):
        S.sort_key = self.sort_cb.itemData(idx); self._refresh_explore()

    # ══════════════════════════════
    #  REZERVASYONLAR
    # ══════════════════════════════
    def _refresh_bookings(self):
        v = self.booking_v; self._clr_lay(v)
        t = QLabel("Rezervasyonlarım"); t.setStyleSheet(f"color:{p('txt')};font-size:19px;font-weight:700;background:transparent;border:none;"); v.addWidget(t)
        if not S.bookings:
            e = QFrame(); e.setStyleSheet("background:transparent;border:none;")
            ev = QVBoxLayout(e); ev.setAlignment(Qt.AlignCenter)
            ei = QLabel("📋"); ei.setAlignment(Qt.AlignCenter); ei.setStyleSheet("font-size:48px;background:transparent;border:none;")
            em = QLabel("Henüz rezervasyonunuz yok"); em.setAlignment(Qt.AlignCenter)
            em.setStyleSheet(f"color:{p('mut')};font-size:13px;background:transparent;border:none;")
            gb = QPushButton("Destinasyonları Keşfet →"); gb.setFixedSize(210,40); gb.setCursor(QCursor(Qt.PointingHandCursor))
            gb.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),10)); gb.clicked.connect(lambda: self._nav('explore'))
            ev.addWidget(ei); ev.addSpacing(8); ev.addWidget(em); ev.addSpacing(16)
            ev.addWidget(gb,alignment=Qt.AlignCenter)
            v.addStretch(); v.addWidget(e); v.addStretch(); return
        sr = QHBoxLayout(); sr.setSpacing(10)
        for val,lbl,col in [(str(len(S.bookings)),"Toplam",p('gold')),
                            (str(sum(1 for b in S.bookings if b['durum']=='confirmed')),"Onaylı",p('grn')),
                            (f"${sum(b['toplam'] for b in S.bookings):,}","Harcama",p('blue2')),
                            (str(len(set(b['seyahat'].gidis_yeri for b in S.bookings))),"Farklı Yer",p('purp'))]:
            sf = QFrame(); sf.setStyleSheet(f"background:{p('card')};border:1px solid {p('border')};border-radius:11px;")
            sl = QVBoxLayout(sf); sl.setContentsMargins(14,12,14,12)
            vl = QLabel(val); vl.setStyleSheet(f"color:{col};font-size:20px;font-weight:700;background:transparent;border:none;")
            nl = QLabel(lbl); nl.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
            sl.addWidget(vl); sl.addWidget(nl); sr.addWidget(sf)
        sw = QWidget(); sw.setStyleSheet("background:transparent;"); sw.setLayout(sr); v.addWidget(sw)
        for bk in reversed(S.bookings):
            sey = bk['seyahat']; kon = bk['konaklama']; pln = bk['plan']
            dest = next((d for d in DESTS if d['name']==sey.gidis_yeri),None); flag = dest['flag'] if dest else '✈'
            bf = QFrame(); bf.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:13px;}}QFrame:hover{{border-color:{p('brd2')};}}")
            bl = QHBoxLayout(bf); bl.setContentsMargins(16,12,16,12); bl.setSpacing(14)
            ic = QVBoxLayout(); ic.setSpacing(3)
            d1 = QLabel(f"{flag}  {sey.gidis_yeri}"); d1.setStyleSheet(f"color:{p('txt')};font-size:15px;font-weight:700;background:transparent;border:none;")
            d2 = QLabel(f"🏨 {kon.otel_adi}  ·  {'⭐'*kon.yildiz}"); d2.setStyleSheet(f"color:{p('txt2')};font-size:11px;background:transparent;border:none;")
            d3 = QLabel(f"📅 {bk['giris']} → {bk['cikis']} ({sey.sure} gece)"); d3.setStyleSheet(f"color:{p('txt3')};font-size:10px;background:transparent;border:none;")
            d5 = QLabel(f"👥 {bk['kisi']} yetişkin, {bk['cocuk']} çocuk"); d5.setStyleSheet(f"color:{p('txt3')};font-size:10px;background:transparent;border:none;")
            ic.addWidget(d1); ic.addWidget(d2); ic.addWidget(d3); ic.addWidget(d5)
            bl.addLayout(ic); bl.addStretch()
            rc = QVBoxLayout(); rc.setAlignment(Qt.AlignRight)
            ta = QLabel(f"${bk['toplam']:,}"); ta.setAlignment(Qt.AlignRight)
            ta.setStyleSheet(f"color:{p('gold')};font-size:20px;font-weight:700;background:transparent;border:none;")
            sc2 = p('grn') if bk['durum']=='confirmed' else p('red')
            st = QLabel("✓ Onaylı" if bk['durum']=='confirmed' else "✗ İptal"); st.setAlignment(Qt.AlignRight)
            st.setStyleSheet(f"color:{sc2};font-size:11px;font-weight:600;background:transparent;border:none;")
            cb2 = QPushButton("İptal Et"); cb2.setFixedSize(76,26)
            cb2.setStyleSheet(f"QPushButton{{background:transparent;color:{p('red')};border:1px solid {p('red')}44;border-radius:7px;font-size:10px;}}QPushButton:hover{{background:{p('red')}22;}}")
            cb2.clicked.connect(lambda _,bid=bk['id']: self._cancel(bid))
            rc.addWidget(ta); rc.addWidget(st); rc.addWidget(cb2)
            bl.addLayout(rc); v.addWidget(bf)
        v.addStretch()

    def _cancel(self, bid):
        for b in S.bookings:
            if b['id']==bid:
                # Geçmişe ait rezervasyonu iptal etmeyi engelle
                try:
                    giris_parts = b['giris'].split('.')
                    giris_qdate = QDate(int(giris_parts[2]), int(giris_parts[1]), int(giris_parts[0]))
                    if giris_qdate < QDate.currentDate():
                        self.toast.show_msg("Başlamış/geçmiş rezervasyon iptal edilemez!",False); return
                except Exception: pass
                b['durum']='cancelled'; break
        self._refresh_bookings(); self.toast.show_msg("Rezervasyon iptal edildi",False)

    # ══════════════════════════════
    #  FAVORİLER
    # ══════════════════════════════
    def _refresh_favorites(self):
        v = self.fav_v; self._clr_lay(v)
        t = QLabel("Favorilerim"); t.setStyleSheet(f"color:{p('txt')};font-size:19px;font-weight:700;background:transparent;border:none;"); v.addWidget(t)
        favs = [d for d in DESTS if d['id'] in S.favs]
        if not favs:
            ef = QFrame(); ef.setStyleSheet("background:transparent;border:none;")
            ev = QVBoxLayout(ef); ev.setAlignment(Qt.AlignCenter)
            ei = QLabel("⭐"); ei.setAlignment(Qt.AlignCenter); ei.setStyleSheet("font-size:48px;background:transparent;border:none;")
            em = QLabel("Henüz favori eklemediniz"); em.setAlignment(Qt.AlignCenter)
            em.setStyleSheet(f"color:{p('mut')};font-size:13px;background:transparent;border:none;")
            em2 = QLabel("Kartlardaki ♡ ikonuna tıklayın"); em2.setAlignment(Qt.AlignCenter)
            em2.setStyleSheet(f"color:{p('txt3')};font-size:11px;background:transparent;border:none;")
            ev.addWidget(ei); ev.addSpacing(8); ev.addWidget(em); ev.addSpacing(4); ev.addWidget(em2)
            v.addStretch(); v.addWidget(ef); v.addStretch(); return
        gw = QWidget(); gw.setStyleSheet("background:transparent;")
        g = QGridLayout(gw); g.setSpacing(12); g.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        for i,dest in enumerate(favs):
            c = DestCard(dest); c.clicked.connect(self._open_detail)
            c.fav_click.connect(lambda _: self._refresh_favorites()); g.addWidget(c,i//4,i%4)
        v.addWidget(gw); v.addStretch()

    # ══════════════════════════════
    #  PROFİL
    # ══════════════════════════════
    def _refresh_profile(self):
        v = self.profile_v; self._clr_lay(v)
        u = S.user
        if not u: return
        pf = QFrame(); pf.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:14px;}}")
        pl = QHBoxLayout(pf); pl.setContentsMargins(22,18,22,18); pl.setSpacing(14)
        av = QLabel(u['name'][0].upper()); av.setFixedSize(58,58); av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet(f"background:{p('gold')}22;border:2px solid {p('gold')};border-radius:29px;color:{p('gold')};font-size:24px;font-weight:700;")
        ic = QVBoxLayout(); ic.setSpacing(3)
        for lbl,sty in [(u['name'],f"color:{p('txt')};font-size:17px;font-weight:700;background:transparent;border:none;"),
                        (u['email'],f"color:{p('mut')};font-size:12px;background:transparent;border:none;"),
                        ("👑 Yönetici" if S.role=='admin' else "✈ Üye",f"color:{p('gold')};font-size:11px;background:transparent;border:none;"),
                        (f"Katılım: {u.get('joined','—')}",f"color:{p('txt3')};font-size:10px;background:transparent;border:none;")]:
            l = QLabel(lbl); l.setStyleSheet(sty); ic.addWidget(l)
        pl.addWidget(av); pl.addLayout(ic); pl.addStretch(); v.addWidget(pf)
        sr = QHBoxLayout(); sr.setSpacing(10)
        for val,lbl,col in [(str(len(S.bookings)),"Rezervasyon",p('gold')),(f"${sum(b['toplam'] for b in S.bookings):,}","Harcama",p('grn')),(str(len(S.favs)),"Favori",p('purp'))]:
            sf=QFrame(); sf.setStyleSheet(f"background:{p('card')};border:1px solid {p('border')};border-radius:11px;")
            sl=QVBoxLayout(sf); sl.setContentsMargins(16,13,16,13)
            vl=QLabel(val); vl.setStyleSheet(f"color:{col};font-size:20px;font-weight:700;background:transparent;border:none;")
            nl=QLabel(lbl); nl.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
            sl.addWidget(vl); sl.addWidget(nl); sr.addWidget(sf)
        sw=QWidget(); sw.setStyleSheet("background:transparent;"); sw.setLayout(sr); v.addWidget(sw)
        cpf = QFrame(); cpf.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:13px;}}")
        cpv = QVBoxLayout(cpf); cpv.setContentsMargins(18,14,18,14); cpv.setSpacing(8)
        ptl = QLabel("Parola Değiştir"); ptl.setStyleSheet(f"color:{p('txt')};font-size:13px;font-weight:700;background:transparent;border:none;")
        cpv.addWidget(ptl); is_s = Inp()
        self.pw_old = QLineEdit(); self.pw_old.setPlaceholderText("Mevcut parola"); self.pw_old.setEchoMode(QLineEdit.Password)
        self.pw_old.setFixedHeight(38); self.pw_old.setStyleSheet(is_s)
        self.pw_new = QLineEdit(); self.pw_new.setPlaceholderText("Yeni parola"); self.pw_new.setEchoMode(QLineEdit.Password)
        self.pw_new.setFixedHeight(38); self.pw_new.setStyleSheet(is_s)
        pb = QPushButton("Güncelle"); pb.setFixedHeight(36)
        pb.setStyleSheet(Btn(p('bg3'),p('txt2'),p('bg4'),9,'7px 18px',12,False)); pb.clicked.connect(self._chg_pwd)
        cpv.addWidget(self.pw_old); cpv.addWidget(self.pw_new); cpv.addWidget(pb)
        v.addWidget(cpf); v.addStretch()

    def _chg_pwd(self):
        old=self.pw_old.text(); new=self.pw_new.text()
        if old!=S.user['pwd']: self.toast.show_msg("Mevcut parola hatalı!",False); return
        if len(new)<6: self.toast.show_msg("Parola en az 6 karakter!",False); return
        for u in S.users:
            if u['id']==S.user['id']: u['pwd']=new; S.user['pwd']=new; break
        self.pw_old.clear(); self.pw_new.clear(); self.toast.show_msg("Parola güncellendi!")

    # ══════════════════════════════
    #  TEKNİK DESTEK (Kullanıcı)
    # ══════════════════════════════
    def _refresh_support(self):
        v = self.support_v; self._clr_lay(v)
        t = QLabel("🎫  Teknik Destek"); t.setStyleSheet(f"color:{p('txt')};font-size:19px;font-weight:700;background:transparent;border:none;"); v.addWidget(t)
        sub = QLabel("Sorunlarınızı bildirin, ekibimiz en kısa sürede yanıtlasın.")
        sub.setStyleSheet(f"color:{p('mut')};font-size:12px;background:transparent;border:none;"); v.addWidget(sub)

        # Yeni ticket formu
        nf = QFrame(); nf.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:13px;}}")
        nfl = QVBoxLayout(nf); nfl.setContentsMargins(18,14,18,14); nfl.setSpacing(9)
        ntl = QLabel("📝  Yeni Ticket Oluştur"); ntl.setStyleSheet(f"color:{p('gold')};font-size:13px;font-weight:700;background:transparent;border:none;"); nfl.addWidget(ntl)
        is_s = Inp()
        kl = QLabel("Konu"); kl.setStyleSheet(f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;"); nfl.addWidget(kl)
        self.tick_konu = QLineEdit(); self.tick_konu.setPlaceholderText("Sorunuzu kısaca özetleyin"); self.tick_konu.setFixedHeight(38); self.tick_konu.setStyleSheet(is_s); nfl.addWidget(self.tick_konu)
        ml = QLabel("Mesaj"); ml.setStyleSheet(kl.styleSheet()); nfl.addWidget(ml)
        self.tick_msg = QTextEdit(); self.tick_msg.setPlaceholderText("Sorununuzu detaylı olarak açıklayın...")
        self.tick_msg.setFixedHeight(90)
        self.tick_msg.setStyleSheet(f"QTextEdit{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:8px;font-size:12px;}}QTextEdit:focus{{border-color:{p('gold')};}}")
        nfl.addWidget(self.tick_msg)
        sb2 = QPushButton("🎫  Ticket Gönder"); sb2.setFixedHeight(38); sb2.setCursor(QCursor(Qt.PointingHandCursor))
        sb2.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),10)); sb2.clicked.connect(self._send_ticket); nfl.addWidget(sb2)
        v.addWidget(nf)

        # Mevcut ticketlar
        my_tickets = [t for t in S.tickets if t.get('user_id')==(S.user['id'] if S.user else -1)]
        if my_tickets:
            tl2 = QLabel("📋  Önceki Ticketlarım"); tl2.setStyleSheet(f"color:{p('txt')};font-size:14px;font-weight:700;background:transparent;border:none;"); v.addWidget(tl2)
            for tk in reversed(my_tickets):
                tf = QFrame(); tf.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:11px;}}")
                tfl2 = QVBoxLayout(tf); tfl2.setContentsMargins(14,11,14,11); tfl2.setSpacing(5)
                hr = QHBoxLayout()
                did = p('grn') if tk['durum']=='cevaplandi' else p('orange') if tk['durum']=='bekliyor' else p('mut')
                ds = QLabel("✅ Cevaplandı" if tk['durum']=='cevaplandi' else "⏳ Bekliyor")
                ds.setStyleSheet(f"background:{did}22;color:{did};border:none;border-radius:6px;padding:2px 9px;font-size:9px;font-weight:700;")
                hr.addWidget(QLabel(f"#{tk['id']}"))
                hr.itemAt(0).widget().setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
                hr.addWidget(ds); hr.addStretch()
                dt = QLabel(tk['tarih'][:16]); dt.setStyleSheet(f"color:{p('mut')};font-size:9px;background:transparent;border:none;"); hr.addWidget(dt)
                tfl2.addLayout(hr)
                kn = QLabel(tk['konu']); kn.setStyleSheet(f"color:{p('txt')};font-size:12px;font-weight:600;background:transparent;border:none;"); tfl2.addWidget(kn)
                mn = QLabel(tk['mesaj'][:120]+"..." if len(tk['mesaj'])>120 else tk['mesaj'])
                mn.setStyleSheet(f"color:{p('txt3')};font-size:10px;background:transparent;border:none;"); mn.setWordWrap(True); tfl2.addWidget(mn)
                if tk.get('cevaplar'):
                    for cv in tk['cevaplar']:
                        cf = QFrame(); cf.setStyleSheet(f"background:{p('gold')}11;border-left:3px solid {p('gold')};border-radius:0 6px 6px 0;padding:4px;")
                        cfl = QVBoxLayout(cf); cfl.setContentsMargins(10,5,10,5); cfl.setSpacing(2)
                        ca = QLabel(f"👑 Admin cevabı · {cv['tarih'][:16]}")
                        ca.setStyleSheet(f"color:{p('gold')};font-size:9px;font-weight:700;background:transparent;border:none;"); cfl.addWidget(ca)
                        cm = QLabel(cv['mesaj']); cm.setStyleSheet(f"color:{p('txt2')};font-size:11px;background:transparent;border:none;"); cm.setWordWrap(True); cfl.addWidget(cm)
                        tfl2.addWidget(cf)
                v.addWidget(tf)
        v.addStretch()

    def _send_ticket(self):
        konu = self.tick_konu.text().strip(); msg = self.tick_msg.toPlainText().strip()
        if not konu:
            self.toast.show_msg("Lütfen bir konu girin!",False); return
        if not msg:
            self.toast.show_msg("Lütfen mesajınızı yazın!",False); return
        if len(konu) < 5:
            self.toast.show_msg("Konu en az 5 karakter olmalıdır!",False); return
        if len(msg) < 10:
            self.toast.show_msg("Mesaj en az 10 karakter olmalıdır!",False); return
        # Aynı konuda açık ticket kontrolü
        uid = S.user['id'] if S.user else 0
        acik = [t for t in S.tickets if t.get('user_id')==uid and t['durum']=='bekliyor' and t['konu'].lower()==konu.lower()]
        if acik:
            self.toast.show_msg("Bu konuda zaten bekleyen bir ticketınız var!",False); return
        tk = {"id": S.nxt_tid, "user_id": uid,
              "user_name": S.user['name'] if S.user else 'Misafir',
              "konu": konu, "mesaj": msg, "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
              "durum": "bekliyor", "cevaplar": []}
        S.nxt_tid += 1; S.tickets.append(tk)
        self.tick_konu.clear(); self.tick_msg.clear()
        self.toast.show_msg("✅ Ticket gönderildi! En kısa sürede yanıtlanacak.")
        if hasattr(self,'bell_btn'): self._update_bell()
        self._refresh_support()

    # ══════════════════════════════
    #  TATİL PLANI (Akıllı Öneri)
    # ══════════════════════════════
    def _refresh_plan(self):
        v = self.plan_v; self._clr_lay(v)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                          f"stop:0 #0a0a1e,stop:1 #101030);"
                          f"border:1px solid {p('border')};border-radius:14px;}}")
        hv = QVBoxLayout(hdr); hv.setContentsMargins(26,20,26,20); hv.setSpacing(6)
        ht = QLabel("AKILLI TATİL PLANLAYICI")
        ht.setStyleSheet(f"color:{p('gold3')};font-size:9px;font-weight:700;letter-spacing:3px;background:transparent;border:none;")
        h1 = QLabel("Size Özel Tatil Planı Oluşturun")
        h1.setStyleSheet(f"color:{p('txt')};font-size:22px;font-weight:700;background:transparent;border:none;")
        h2 = QLabel("Bütçenizi ve aktivite tercihlerinizi girin — size en uygun otelleri bulalım.")
        h2.setStyleSheet(f"color:{p('txt3')};font-size:12px;background:transparent;border:none;")
        hv.addWidget(ht); hv.addWidget(h1); hv.addWidget(h2); v.addWidget(hdr)

        # Form kartı
        form_f = QFrame()
        form_f.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:14px;}}")
        form_lay = QVBoxLayout(form_f); form_lay.setContentsMargins(22,18,22,18); form_lay.setSpacing(14)
        form_tl = QLabel("🔍  Tatil Kriterlerinizi Girin")
        form_tl.setStyleSheet(f"color:{p('gold')};font-size:14px;font-weight:700;background:transparent;border:none;")
        form_lay.addWidget(form_tl)

        is_s = Inp()
        lbl_s = f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;"
        g = QGridLayout(); g.setSpacing(12)

        # Bütçe
        bl = QLabel("💰 Kişi Başı Maks. Bütçe ($/gece)"); bl.setStyleSheet(lbl_s)
        self.plan_budget = QSpinBox(); self.plan_budget.setRange(50,5000); self.plan_budget.setValue(300)
        self.plan_budget.setSuffix(" $/gece"); self.plan_budget.setFixedHeight(38)
        self.plan_budget.setStyleSheet(f"QSpinBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:7px 11px;font-size:12px;}}"
                                       f"QSpinBox::up-button,QSpinBox::down-button{{width:20px;}}")

        # Gece sayısı
        nl = QLabel("📅 Kaç Gece?"); nl.setStyleSheet(lbl_s)
        self.plan_nights = QSpinBox(); self.plan_nights.setRange(1,30); self.plan_nights.setValue(7)
        self.plan_nights.setSuffix(" gece"); self.plan_nights.setFixedHeight(38)
        self.plan_nights.setStyleSheet(self.plan_budget.styleSheet())

        # Kişi sayısı
        kl = QLabel("👥 Yetişkin Sayısı"); kl.setStyleSheet(lbl_s)
        self.plan_pax = QSpinBox(); self.plan_pax.setRange(1,10); self.plan_pax.setValue(2)
        self.plan_pax.setSuffix(" kişi"); self.plan_pax.setFixedHeight(38)
        self.plan_pax.setStyleSheet(self.plan_budget.styleSheet())

        # Kıta
        contl = QLabel("🌍 Tercih Edilen Kıta"); contl.setStyleSheet(lbl_s)
        self.plan_cont = QComboBox(); self.plan_cont.setFixedHeight(38)
        self.plan_cont.setStyleSheet(f"QComboBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:7px 11px;font-size:12px;}}")
        self.plan_cont.addItem("🌐 Fark Etmez", "Tümü")
        for cont in sorted(set(d['cont'] for d in DESTS)):
            self.plan_cont.addItem(cont, cont)

        g.addWidget(bl,0,0); g.addWidget(self.plan_budget,1,0)
        g.addWidget(nl,0,1); g.addWidget(self.plan_nights,1,1)
        g.addWidget(kl,0,2); g.addWidget(self.plan_pax,1,2)
        g.addWidget(contl,0,3); g.addWidget(self.plan_cont,1,3)
        form_lay.addLayout(g)

        # Aktivite tercihleri — çoklu seçim checkbox benzeri butonlar
        al = QLabel("🎯 Yapmak İstediğiniz Aktiviteler (birden fazla seçebilirsiniz)")
        al.setStyleSheet(lbl_s); form_lay.addWidget(al)
        aktiv_frame = QFrame(); aktiv_frame.setStyleSheet("background:transparent;border:none;")
        aktiv_lay = QHBoxLayout(aktiv_frame); aktiv_lay.setContentsMargins(0,0,0,0); aktiv_lay.setSpacing(8)
        self._plan_tags = {}
        tag_options = [("🏖 Plaj & Deniz","Plaj"), ("🏔 Doğa & Dağ","Doğa"), ("🎭 Kültür & Tarih","Kültür"),
                       ("🍽 Gastronomi","Gastronomi"), ("🛕 Tapınak & Din","Din"), ("🎮 Eğlence","Eğlence"),
                       ("💆 Spa & Romantik","Romantik"), ("🤿 Dalış & Su Sporları","Dalış"), ("🛍 Alışveriş","Alışveriş")]
        for lbl_txt, key in tag_options:
            btn = QPushButton(lbl_txt); btn.setCheckable(True); btn.setFixedHeight(30)
            btn.setStyleSheet(
                f"QPushButton{{background:{p('bg3')};color:{p('txt3')};border:1px solid {p('border')};border-radius:8px;padding:0 10px;font-size:10px;font-weight:600;}}"
                f"QPushButton:checked{{background:{p('gold')}22;color:{p('gold')};border-color:{p('gold')};}}"
                f"QPushButton:hover{{border-color:{p('brd2')};color:{p('txt2')};}}"); btn.setCursor(QCursor(Qt.PointingHandCursor))
            self._plan_tags[key] = btn; aktiv_lay.addWidget(btn)
        aktiv_lay.addStretch(); form_lay.addWidget(aktiv_frame)

        # Ara butonu
        sb = QPushButton("🗺  Tatil Planı Oluştur"); sb.setFixedHeight(44)
        sb.setCursor(QCursor(Qt.PointingHandCursor))
        sb.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),11)); sb.clicked.connect(self._do_plan)
        form_lay.addWidget(sb); v.addWidget(form_f)

        # Sonuç alanı
        self._plan_result_v = v

    def _do_plan(self):
        budget = self.plan_budget.value()
        nights = self.plan_nights.value()
        pax = self.plan_pax.value()
        cont_pref = self.plan_cont.currentData()  # 'Tümü' veya kıta adı
        selected_tags = [key for key, btn in self._plan_tags.items() if btn.isChecked()]

        # Skor hesapla
        scored = []
        for dest in DESTS:
            # Bütçe uyumu — otel fiyatına bak
            eligible_hotels = [h for h in dest['hotels'] if h.fiyat <= budget]
            if not eligible_hotels: continue
            if cont_pref and cont_pref != 'Tümü' and dest['cont'] != cont_pref: continue

            score = 0
            score += dest['rating'] * 10  # rating puanı
            # Tag eşleşmesi
            dest_tags_lower = [t.lower() for t in dest['tags']]
            dest_places_types = [pl['type'].lower() for pl in dest.get('places',[])]
            all_dest_keywords = dest_tags_lower + dest_places_types + [dest['cont'].lower()]
            tag_map = {'Plaj':['plaj','deniz','sörf'],'Doğa':['doğa','orman','dağ'],'Kültür':['kültür','tarihi','tarih','sanat'],
                       'Gastronomi':['gastronomi','yemek'],'Din':['tapınak','camii'],'Eğlence':['eğlence','anime','gece'],
                       'Romantik':['romantik','balayı','lüks'],'Dalış':['dalış','sualtı','snorkel'],'Alışveriş':['alışveriş']}
            for sel_tag in selected_tags:
                keywords = tag_map.get(sel_tag, [sel_tag.lower()])
                for kw in keywords:
                    if any(kw in k for k in all_dest_keywords):
                        score += 15; break
            # Fiyat uyumu bonusu
            best_hotel = min(eligible_hotels, key=lambda h: abs(h.fiyat - budget*0.7))
            price_ratio = best_hotel.fiyat / budget
            if 0.5 <= price_ratio <= 0.85: score += 10
            total_cost = hesapla_fiyat(best_hotel.fiyat, nights, pax, 0)
            scored.append((score, dest, best_hotel, total_cost))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:5]

        # Önceki sonuçları temizle (form'dan sonraki widgetları sil)
        v = self._plan_result_v
        # Formdan sonra eklenen widgetları temizle (index 2+)
        while v.count() > 2:
            it = v.takeAt(v.count()-1)
            if it.widget(): it.widget().deleteLater()

        if not top:
            nf = QLabel("😔 Belirttiğiniz kriterlere uygun destinasyon bulunamadı.\nBütçeyi artırın veya farklı kıta seçin.")
            nf.setAlignment(Qt.AlignCenter); nf.setWordWrap(True)
            nf.setStyleSheet(f"color:{p('mut')};font-size:13px;padding:30px;background:transparent;border:none;")
            v.addWidget(nf); return

        rl = QLabel(f"✨  {len(top)} Öneri Bulundu")
        rl.setStyleSheet(f"color:{p('txt')};font-size:16px;font-weight:700;background:transparent;border:none;")
        v.addWidget(rl)

        tag_labels = ', '.join(selected_tags) if selected_tags else 'Genel'
        info_l = QLabel(f"📊 Kriter: {budget}$/gece bütçe · {nights} gece · {pax} kişi · {tag_labels}")
        info_l.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
        v.addWidget(info_l)

        for rank, (score, dest, hotel, total_cost) in enumerate(top):
            rf = QFrame()
            border = p('gold') if rank == 0 else p('border')
            rf.setStyleSheet(f"QFrame{{background:{p('card')};border:2px solid {border};border-radius:14px;}}")
            rl2 = QVBoxLayout(rf); rl2.setContentsMargins(18,14,18,14); rl2.setSpacing(8)

            # Başlık satırı
            h_row = QHBoxLayout()
            if rank == 0:
                crown = QLabel("👑 #1 EN İYİ EŞLEŞİM")
                crown.setStyleSheet(f"background:{p('gold')}22;color:{p('gold')};border:none;border-radius:8px;padding:3px 10px;font-size:10px;font-weight:700;")
                h_row.addWidget(crown)
            else:
                rank_l = QLabel(f"#{rank+1}")
                rank_l.setStyleSheet(f"background:{p('bg3')};color:{p('txt2')};border:none;border-radius:8px;padding:3px 10px;font-size:10px;font-weight:700;")
                h_row.addWidget(rank_l)
            h_row.addStretch()
            score_l = QLabel(f"Uyum: {min(int(score),99)}/99")
            score_l.setStyleSheet(f"color:{p('teal')};font-size:10px;background:transparent;border:none;")
            h_row.addWidget(score_l); rl2.addLayout(h_row)

            # Dest ve otel bilgisi
            r2 = QHBoxLayout(); r2.setSpacing(14)
            icon_lbl = QLabel(dest['flag']); icon_lbl.setFixedSize(52,52); icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet(f"background:{dest['color']}44;border:1px solid {p('border')};border-radius:12px;font-size:26px;")
            r2.addWidget(icon_lbl)
            info_col = QVBoxLayout(); info_col.setSpacing(3)
            dest_nm = QLabel(f"{dest['name']}, {dest['country']}")
            dest_nm.setStyleSheet(f"color:{p('txt')};font-size:16px;font-weight:700;background:transparent;border:none;")
            hotel_nm = QLabel(f"🏨 {hotel.otel_adi}  {'⭐'*hotel.yildiz}")
            hotel_nm.setStyleSheet(f"color:{p('txt2')};font-size:12px;background:transparent;border:none;")
            desc_l = QLabel(dest['desc']); desc_l.setWordWrap(True)
            desc_l.setStyleSheet(f"color:{p('txt3')};font-size:10px;background:transparent;border:none;")
            info_col.addWidget(dest_nm); info_col.addWidget(hotel_nm); info_col.addWidget(desc_l)

            # Hotel özellikleri
            oz_row = QHBoxLayout(); oz_row.setSpacing(5)
            for oz in hotel.ozellikler[:4]:
                ot = QLabel(oz); ot.setStyleSheet(f"background:{p('bg3')};color:{p('txt2')};border:1px solid {p('brd2')};border-radius:6px;padding:2px 7px;font-size:9px;")
                oz_row.addWidget(ot)
            oz_row.addStretch(); info_col.addLayout(oz_row)
            r2.addLayout(info_col); r2.addStretch()

            # Fiyat ve buton
            price_col = QVBoxLayout(); price_col.setAlignment(Qt.AlignRight|Qt.AlignVCenter); price_col.setSpacing(4)
            pn = QLabel(f"${hotel.fiyat}/gece")
            pn.setStyleSheet(f"color:{p('gold2')};font-size:18px;font-weight:700;background:transparent;border:none;"); pn.setAlignment(Qt.AlignRight)
            tot_l = QLabel(f"Toplam ≈ ${total_cost:,}")
            tot_l.setStyleSheet(f"color:{p('orange')};font-size:11px;font-weight:600;background:transparent;border:none;"); tot_l.setAlignment(Qt.AlignRight)
            nights_l = QLabel(f"{nights} gece · {pax} kişi")
            nights_l.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;"); nights_l.setAlignment(Qt.AlignRight)
            book_btn = QPushButton("✈ İncele & Rezervasyon"); book_btn.setFixedHeight(32)
            book_btn.setCursor(QCursor(Qt.PointingHandCursor))
            book_btn.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),8,'0 12px',11))
            book_btn.clicked.connect(lambda _, d=dest: self._open_detail(d))
            price_col.addWidget(pn); price_col.addWidget(tot_l); price_col.addWidget(nights_l); price_col.addSpacing(6); price_col.addWidget(book_btn)
            r2.addLayout(price_col); rl2.addLayout(r2)

            # Eşleşen aktiviteler
            matching_places = [pl for pl in dest.get('places',[])
                               if any(tag.lower() in pl['type'].lower() or tag.lower() in pl['name'].lower() for tag in selected_tags)] if selected_tags else dest.get('places',[])[:2]
            if matching_places:
                act_row = QHBoxLayout(); act_row.setSpacing(8)
                act_lbl = QLabel("📍 Aktiviteler:"); act_lbl.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
                act_row.addWidget(act_lbl)
                for pl in matching_places[:3]:
                    at = QLabel(f"{pl['icon']} {pl['name']}")
                    at.setStyleSheet(f"background:{p('bg3')};color:{p('txt2')};border:1px solid {p('border')};border-radius:7px;padding:2px 8px;font-size:9px;")
                    act_row.addWidget(at)
                act_row.addStretch(); rl2.addLayout(act_row)

            v.addWidget(rf)

        # ── Plan Haritası: Önerilen destinasyonları haritada göster ──
        plan_dests = [dest for _, dest, _, _ in top]
        map_frame = QFrame()
        map_frame.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:14px;}}")
        map_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        map_frame.setMinimumHeight(420)
        mfv = QVBoxLayout(map_frame); mfv.setContentsMargins(0,0,0,0); mfv.setSpacing(0)
        mhdr2 = QFrame(); mhdr2.setFixedHeight(42)
        mhdr2.setStyleSheet(f"background:transparent;border-bottom:1px solid {p('border')};")
        mhl2 = QHBoxLayout(mhdr2); mhl2.setContentsMargins(16,0,16,0)
        mt2 = QLabel("🗺  Önerilen Destinasyonlar — Harita")
        mt2.setStyleSheet(f"color:{p('txt')};font-size:13px;font-weight:700;background:transparent;border:none;")
        ms2 = QLabel(f"{len(plan_dests)} konum gösteriliyor")
        ms2.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
        mhl2.addWidget(mt2); mhl2.addSpacing(10); mhl2.addWidget(ms2); mhl2.addStretch()
        mfv.addWidget(mhdr2)
        plan_map = PlanMapWidget(plan_dests)
        plan_map.clicked.connect(self._open_detail)
        mfv.addWidget(plan_map)
        v.addWidget(map_frame)
        v.addStretch()

    # ══════════════════════════════
    #  ADMİN PANELİ
    # ══════════════════════════════
    def _refresh_admin(self):
        if not hasattr(self,'admin_v'): return
        v = self.admin_v; self._clr_lay(v)
        t = QLabel("Admin Paneli"); t.setStyleSheet(f"color:{p('txt')};font-size:19px;font-weight:700;background:transparent;border:none;"); v.addWidget(t)
        if not hasattr(self,'_atab'): self._atab = 'genel'
        tf = QFrame(); tf.setFixedHeight(40)
        tf.setStyleSheet(f"QFrame{{background:{p('bg3')};border:1px solid {p('border')};border-radius:9px;}}")
        tfl = QHBoxLayout(tf); tfl.setContentsMargins(3,3,3,3); tfl.setSpacing(2)
        pending_cnt = len([t2 for t2 in S.tickets if t2['durum']=='bekliyor'])
        tab_items = [('genel','📊 Genel'),('dests','🌍 Destinasyonlar'),('hotels','🏨 Oteller'),
                     ('users','👥 Kullanıcılar'),('reserv','📋 Rezervasyonlar'),
                     ('tickets',f"🎫 Ticketlar{f' ({pending_cnt})' if pending_cnt else ''}")]
        for tid,tlbl in tab_items:
            b = QPushButton(tlbl); b.setFixedHeight(32); act = self._atab==tid
            badge_col = p('orange') if tid=='tickets' and pending_cnt and not act else (p('gold') if act else p('mut'))
            b.setStyleSheet(f"QPushButton{{background:{'#0f0f1c' if act else 'transparent'};"
                            f"color:{badge_col};border:none;border-radius:6px;font-size:11px;font-weight:600;}}"
                            f"QPushButton:hover{{color:{p('txt2')};}}")
            b.setCursor(QCursor(Qt.PointingHandCursor)); b.clicked.connect(lambda _,t=tid: self._set_atab(t)); tfl.addWidget(b)
        v.addWidget(tf)
        if self._atab=='genel': self._admin_genel(v)
        elif self._atab=='dests': self._admin_dests(v)
        elif self._atab=='hotels': self._admin_hotels(v)
        elif self._atab=='users': self._admin_users(v)
        elif self._atab=='reserv': self._admin_reserv(v)
        elif self._atab=='tickets': self._admin_tickets(v)
        v.addStretch()

    def _set_atab(self, t): self._atab=t; self._refresh_admin()

    def _admin_genel(self, v):
        confirmed_bks = [b for b in S.bookings if b['durum']=='confirmed']
        toplam_gelir = sum(b['toplam'] for b in confirmed_bks)
        sr = QHBoxLayout(); sr.setSpacing(10)
        for val,lbl,col in [(str(len(S.users)),"Kullanıcı",p('blue2')),(str(len(DESTS)),"Destinasyon",p('gold')),
                            (str(sum(len(d['hotels']) for d in DESTS)),"Otel",p('grn')),(str(len(S.bookings)),"Rezervasyon",p('purp')),
                            (f"${toplam_gelir:,}","Onaylı Gelir",p('teal')),
                            (str(len([t for t in S.tickets if t['durum']=='bekliyor'])),"Bekleyen Ticket",p('orange'))]:
            sf=QFrame(); sf.setStyleSheet(f"background:{p('card')};border:1px solid {p('border')};border-radius:12px;")
            sl=QVBoxLayout(sf); sl.setContentsMargins(14,12,14,12)
            vl=QLabel(val); vl.setStyleSheet(f"color:{col};font-size:20px;font-weight:700;background:transparent;border:none;")
            nl=QLabel(lbl); nl.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
            sl.addWidget(vl); sl.addWidget(nl); sr.addWidget(sf)
        sw=QWidget(); sw.setStyleSheet("background:transparent;"); sw.setLayout(sr); v.addWidget(sw)
        if S.bookings:
            rf=QFrame(); rf.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:13px;}}")
            rl=QVBoxLayout(rf); rl.setContentsMargins(16,13,16,13); rl.setSpacing(7)
            rl.addWidget(self._lbl2("Son Rezervasyonlar",13,True))
            for bk in reversed(S.bookings[-8:]):
                row=QHBoxLayout()
                user=next((u for u in S.users if u['id']==bk.get('user_id',0)),None)
                user_nm=user['name'] if user else '—'
                u_lbl=QLabel(f"👤 {user_nm}"); u_lbl.setStyleSheet(f"color:{p('gold2')};font-size:10px;background:transparent;border:none;")
                d=QLabel(f"✈ {bk['seyahat'].gidis_yeri}"); d.setStyleSheet(f"color:{p('txt2')};font-size:11px;background:transparent;border:none;")
                h=QLabel(bk['konaklama'].otel_adi); h.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
                t2=QLabel(f"${bk['toplam']:,}"); t2.setStyleSheet(f"color:{p('teal') if bk['durum']=='confirmed' else p('red')};font-size:11px;font-weight:700;background:transparent;border:none;")
                s=QLabel("✓" if bk['durum']=='confirmed' else "✗"); sc2=p('grn') if bk['durum']=='confirmed' else p('red')
                s.setStyleSheet(f"color:{sc2};font-size:11px;background:transparent;border:none;")
                row.addWidget(u_lbl); row.addSpacing(6); row.addWidget(d); row.addWidget(h); row.addStretch(); row.addWidget(t2); row.addSpacing(8); row.addWidget(s)
                rl.addLayout(row)
            v.addWidget(rf)

    def _admin_dests(self, v):
        # ── Başlık + Ekle butonu ──
        hdr_f = QFrame(); hdr_f.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:12px;}}")
        hdr_l = QHBoxLayout(hdr_f); hdr_l.setContentsMargins(16,12,16,12)
        icon_l = QLabel("🌍"); icon_l.setStyleSheet("font-size:22px;background:transparent;border:none;")
        info_l = QVBoxLayout(); info_l.setSpacing(1)
        info_l.addWidget(self._lbl2("Destinasyon Yönetimi",14,True,p('txt')))
        info_l.addWidget(self._lbl2(f"Toplam {len(DESTS)} destinasyon · {sum(len(d['hotels']) for d in DESTS)} otel",10,False,p('mut')))
        ab = QPushButton("  ＋  Yeni Destinasyon Ekle"); ab.setFixedHeight(38); ab.setCursor(QCursor(Qt.PointingHandCursor))
        ab.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),9,'7px 18px',12))
        ab.clicked.connect(self._add_dest)
        hdr_l.addWidget(icon_l); hdr_l.addSpacing(8); hdr_l.addLayout(info_l); hdr_l.addStretch(); hdr_l.addWidget(ab)
        v.addWidget(hdr_f)
        # ── Kart ızgarası ──
        grid_w = QWidget(); grid_w.setStyleSheet("background:transparent;")
        grid = QGridLayout(grid_w); grid.setSpacing(10); grid.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        for i, dest in enumerate(DESTS):
            df = QFrame()
            df.setStyleSheet(f"QFrame{{background:{p('card')};border:1.5px solid {p('border')};border-radius:13px;}}"
                             f"QFrame:hover{{border-color:{p('brd2')};}}")
            dv = QVBoxLayout(df); dv.setContentsMargins(0,0,0,0); dv.setSpacing(0)
            # Renkli başlık bandı
            top_f = QFrame(); top_f.setFixedHeight(52)
            top_f.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                                f"stop:0 {dest['color']}cc,stop:1 {dest['color']}44);"
                                f"border-radius:13px 13px 0 0;border:none;}}")
            top_l = QHBoxLayout(top_f); top_l.setContentsMargins(11,6,11,6)
            flag_l = QLabel(dest['flag']); flag_l.setStyleSheet("font-size:22px;background:transparent;border:none;")
            nm_l = QLabel(dest['name']); nm_l.setStyleSheet("color:#fff;font-size:13px;font-weight:700;background:transparent;border:none;")
            rat_l = QLabel(f"⭐ {dest['rating']}")
            rat_l.setStyleSheet(f"background:#00000066;color:{p('gold')};border:none;border-radius:8px;padding:2px 7px;font-size:9px;font-weight:700;")
            top_l.addWidget(flag_l); top_l.addSpacing(5); top_l.addWidget(nm_l); top_l.addStretch(); top_l.addWidget(rat_l)
            dv.addWidget(top_f)
            # Bilgi alanı
            body_f = QFrame(); body_f.setStyleSheet("background:transparent;border:none;")
            body_l = QVBoxLayout(body_f); body_l.setContentsMargins(11,8,11,8); body_l.setSpacing(4)
            body_l.addWidget(self._lbl2(f"📍 {dest['country']} · {dest['cont']}",10,False,p('mut')))
            # Metrikler satırı
            met_row = QHBoxLayout(); met_row.setSpacing(5)
            for mv, mk, mc in [(f"${dest['price']}","gece",p('gold2')),(f"{len(dest['hotels'])}","otel",p('blue2')),(f"{len(dest.get('places',[]))}","yer",p('teal'))]:
                mf = QFrame(); mf.setStyleSheet(f"background:{p('bg3')};border:1px solid {p('border')};border-radius:7px;")
                ml2 = QHBoxLayout(mf); ml2.setContentsMargins(6,3,6,3); ml2.setSpacing(3)
                ml2.addWidget(self._lbl2(mv,10,True,mc)); ml2.addWidget(self._lbl2(mk,8,False,p('mut')))
                met_row.addWidget(mf)
            met_row.addStretch(); body_l.addLayout(met_row)
            # Etiketler
            tag_row = QHBoxLayout(); tag_row.setSpacing(4)
            for tg in dest['tags'][:2]:
                tl2 = QLabel(tg); tl2.setStyleSheet(f"background:{p('gold')}18;color:{p('gold')};border:none;border-radius:6px;padding:1px 7px;font-size:8px;font-weight:700;")
                tag_row.addWidget(tl2)
            tag_row.addStretch(); body_l.addLayout(tag_row)
            dv.addWidget(body_f)
            # Aksiyon butonları
            act_f = QFrame(); act_f.setStyleSheet(f"background:transparent;border-top:1px solid {p('border')};border-radius:0 0 13px 13px;")
            act_l = QHBoxLayout(act_f); act_l.setContentsMargins(10,7,10,7); act_l.setSpacing(6)
            eb = QPushButton("✏ Düzenle"); eb.setFixedHeight(28)
            eb.setStyleSheet(f"QPushButton{{background:{p('bg3')};color:{p('txt2')};border:1px solid {p('border')};border-radius:7px;font-size:10px;font-weight:600;padding:0 10px;}}QPushButton:hover{{border-color:{p('gold')};color:{p('gold')};}}")
            eb.setCursor(QCursor(Qt.PointingHandCursor)); eb.clicked.connect(lambda _,d=dest: self._edit_dest(d))
            db = QPushButton("🗑 Sil"); db.setFixedHeight(28)
            db.setStyleSheet(f"QPushButton{{background:{p('bg3')};color:{p('red')};border:1px solid {p('border')};border-radius:7px;font-size:10px;font-weight:600;padding:0 10px;}}QPushButton:hover{{background:{p('red')}22;border-color:{p('red')};}}")
            db.setCursor(QCursor(Qt.PointingHandCursor)); db.clicked.connect(lambda _,did=dest['id']: self._del_dest(did))
            act_l.addStretch(); act_l.addWidget(eb); act_l.addWidget(db)
            dv.addWidget(act_f)
            grid.addWidget(df, i//3, i%3)
        v.addWidget(grid_w)

    def _admin_hotels(self, v):
        tb=QHBoxLayout()
        cnt=sum(len(d['hotels']) for d in DESTS)
        tl=self._lbl2(f"{cnt} otel",11,False,p('mut')); tb.addWidget(tl); tb.addStretch()
        ab=QPushButton("+ Yeni Otel"); ab.setFixedHeight(32); ab.setCursor(QCursor(Qt.PointingHandCursor))
        ab.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),8,'5px 14px',11))
        ab.clicked.connect(self._add_hotel); tb.addWidget(ab)
        tbw=QWidget(); tbw.setStyleSheet("background:transparent;"); tbw.setLayout(tb); v.addWidget(tbw)
        # Yeni eklenen oteli üstte göstermek için ters sıra
        all_hotels = []
        for dest in DESTS:
            for hotel in dest['hotels']:
                all_hotels.append((dest, hotel))
        for dest, hotel in reversed(all_hotels):
                hf=QFrame(); hf.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:10px;}}")
                hl=QHBoxLayout(hf); hl.setContentsMargins(13,9,13,9); hl.setSpacing(10)
                st=QLabel("⭐"*hotel.yildiz); st.setStyleSheet("font-size:10px;background:transparent;border:none;")
                inf=QVBoxLayout()
                inf.addWidget(self._lbl2(f"{dest['flag']} {dest['name']} — {hotel.otel_adi}",12,True))
                inf.addWidget(self._lbl2(f"${hotel.fiyat}/gece · {', '.join(hotel.ozellikler[:3])}",10))
                hl.addWidget(st); hl.addLayout(inf); hl.addStretch()
                eb=QPushButton("✏ Düzenle"); eb.setFixedHeight(28)
                eb.setStyleSheet(f"QPushButton{{background:{p('bg3')};color:{p('txt2')};border:1px solid {p('border')};border-radius:7px;font-size:10px;padding:0 9px;}}QPushButton:hover{{border-color:{p('gold')};color:{p('gold')};}}")
                eb.setCursor(QCursor(Qt.PointingHandCursor))
                eb.clicked.connect(lambda _,d=dest,h=hotel: self._edit_hotel(d,h)); hl.addWidget(eb); v.addWidget(hf)

    def _admin_users(self, v):
        v.addWidget(self._lbl2(f"{len(S.users)} kullanıcı",11,False,p('mut')))
        tbl=QTableWidget(len(S.users),5)
        tbl.setHorizontalHeaderLabels(["Ad Soyad","E-Posta","Rol","Katılım","İşlem"])
        tbl.setStyleSheet(f"QTableWidget{{background:{p('card')};border:1px solid {p('border')};border-radius:13px;color:{p('txt2')};font-size:11px;gridline-color:{p('border')};}}QTableWidget::item{{padding:9px 11px;border:none;}}QTableWidget::item:selected{{background:{p('bg4')};}}QHeaderView::section{{background:{p('bg3')};color:{p('mut')};border:none;border-bottom:1px solid {p('border')};padding:9px 11px;font-size:9px;font-weight:700;}}")
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); tbl.verticalHeader().setVisible(False); tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        for i,u in enumerate(S.users):
            for j,tx in enumerate([u['name'],u['email'],u['role'].upper(),u.get('joined','—')]):
                it=QTableWidgetItem(tx); it.setForeground(QColor(p('gold') if j==2 else p('txt2'))); tbl.setItem(i,j,it)
            db=QPushButton("Kaldır"); db.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{p('red')};font-size:10px;}}")
            db.clicked.connect(lambda _,uid=u['id']: self._del_user(uid)); tbl.setCellWidget(i,4,db)
        v.addWidget(tbl)

    def _admin_reserv(self, v):
        confirmed = [b for b in S.bookings if b['durum']=='confirmed']
        cancelled = [b for b in S.bookings if b['durum']=='cancelled']
        admin_bks = [b for b in S.bookings if b.get('is_admin_booking')]
        toplam_gelir = sum(b['toplam'] for b in confirmed)
        admin_tasarruf = sum(
            hesapla_fiyat(b['konaklama'].fiyat, b['seyahat'].sure, b['kisi'], b['cocuk'], False) - b['toplam']
            for b in admin_bks if b['durum']=='confirmed'
        )
        # Özet kartlar
        sr=QHBoxLayout(); sr.setSpacing(10)
        for val,lbl,col in [(str(len(S.bookings)),"Toplam Rezervasyon",p('gold')),
                            (str(len(confirmed)),"Onaylı",p('grn')),
                            (str(len(cancelled)),"İptal",p('red')),
                            (f"${toplam_gelir:,}","Toplam Gelir",p('teal')),
                            (str(len(admin_bks)),"Admin Rezervasyonu",p('purp')),
                            (f"${admin_tasarruf:,}","Admin Tasarrufu",p('blue2'))]:
            sf=QFrame(); sf.setStyleSheet(f"background:{p('card')};border:1px solid {p('border')};border-radius:12px;")
            sl=QVBoxLayout(sf); sl.setContentsMargins(14,11,14,11)
            vl=QLabel(val); vl.setStyleSheet(f"color:{col};font-size:18px;font-weight:700;background:transparent;border:none;")
            nl=QLabel(lbl); nl.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
            sl.addWidget(vl); sl.addWidget(nl); sr.addWidget(sf)
        sw=QWidget(); sw.setStyleSheet("background:transparent;"); sw.setLayout(sr); v.addWidget(sw)
        if not S.bookings: v.addWidget(self._lbl2("Henüz rezervasyon yok",13)); return

        # Filtre satırı
        filt_row = QHBoxLayout(); filt_row.setSpacing(6)
        filt_lbl = self._lbl2("Filtre:", 10, False, p('mut')); filt_row.addWidget(filt_lbl)
        if not hasattr(self,'_reserv_filter'): self._reserv_filter = 'tumu'  # noqa – intentional guard
        for fkey, ftxt, fcol in [('tumu','Tümü',p('txt2')),('confirmed','Onaylı',p('grn')),
                                   ('cancelled','İptal',p('red')),('admin','🛡 Admin',p('purp'))]:
            act = self._reserv_filter == fkey
            fb = QPushButton(ftxt); fb.setFixedHeight(26)
            fb.setStyleSheet(f"QPushButton{{background:{p('card') if act else p('bg3')};color:{fcol if act else p('mut')};border:1.5px solid {fcol if act else p('border')};border-radius:6px;font-size:10px;font-weight:{'700' if act else '500'};padding:0 10px;}}QPushButton:hover{{border-color:{fcol};}}")
            fb.setCursor(QCursor(Qt.PointingHandCursor))
            fb.clicked.connect(lambda _, k=fkey: self._set_reserv_filter(k))
            filt_row.addWidget(fb)
        filt_row.addStretch()
        fw=QWidget(); fw.setStyleSheet("background:transparent;"); fw.setLayout(filt_row); v.addWidget(fw)

        # Tablo
        filt = self._reserv_filter
        if filt == 'admin': show_bks = [b for b in S.bookings if b.get('is_admin_booking')]
        elif filt == 'confirmed': show_bks = confirmed
        elif filt == 'cancelled': show_bks = cancelled
        else: show_bks = S.bookings

        tbl=QTableWidget(len(show_bks),9)
        tbl.setHorizontalHeaderLabels(["#","Kullanıcı","Tür","Destinasyon","Otel","Tarih","Kişi","Toplam","İşlem"])
        tbl.setStyleSheet(f"QTableWidget{{background:{p('card')};border:1px solid {p('border')};border-radius:13px;color:{p('txt2')};font-size:11px;gridline-color:{p('border')};}}QTableWidget::item{{padding:8px 10px;border:none;}}QTableWidget::item:selected{{background:{p('bg4')};}}QHeaderView::section{{background:{p('bg3')};color:{p('mut')};border:none;border-bottom:1px solid {p('border')};padding:8px 10px;font-size:9px;font-weight:700;}}")
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        tbl.verticalHeader().setVisible(False); tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setRowHeight(0, 36)
        for i,bk in enumerate(reversed(show_bks)):
            tbl.setRowHeight(i, 36)
            is_adm = bk.get('is_admin_booking', False)
            # Kullanıcı adını güvenli şekilde al
            user_name = bk.get('user_name','')
            if not user_name or user_name == 'Misafir':
                uid = bk.get('user_id', 0)
                user = next((u for u in S.users if u['id']==uid), None)
                user_name = user['name'] if user else ('👑 Admin' if is_adm else 'Misafir')
            tur_txt = "🛡 Admin" if is_adm else "👤 Kullanıcı"
            data=[str(bk['id']), user_name, tur_txt, bk['seyahat'].gidis_yeri, bk['konaklama'].otel_adi,
                  f"{bk['giris']}→{bk['cikis']}", f"{bk['kisi']}Y {bk['cocuk']}Ç",
                  f"${bk['toplam']:,}"]
            col_map = [p('txt2'), p('gold2'), p('purp') if is_adm else p('blue2'), p('txt2'),
                       p('txt2'), p('txt3'), p('txt3'),
                       p('grn') if bk['durum']=='confirmed' else p('red')]
            for j,tx in enumerate(data):
                it=QTableWidgetItem(tx); it.setForeground(QColor(col_map[j])); tbl.setItem(i,j,it)
            # İşlem butonu
            if bk['durum'] == 'confirmed':
                iptal_btn = QPushButton("✗ İptal")
                iptal_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{p('red')};font-size:10px;font-weight:600;}}QPushButton:hover{{color:#ff6060;}}")
                iptal_btn.clicked.connect(lambda _, bid=bk['id']: self._cancel_booking(bid))
                tbl.setCellWidget(i, 8, iptal_btn)
            else:
                it2 = QTableWidgetItem("✗ İptal"); it2.setForeground(QColor(p('mut'))); tbl.setItem(i,8,it2)
        v.addWidget(tbl)

    def _set_reserv_filter(self, k):
        self._reserv_filter = k; self._refresh_admin()

    def _cancel_booking(self, bid):
        bk = next((b for b in S.bookings if b['id']==bid), None)
        if not bk: return
        dest_name = bk['seyahat'].gidis_yeri; otel = bk['konaklama'].otel_adi
        if QMessageBox.question(self,"Rezervasyonu İptal Et",
                f"#{bid} nolu rezervasyon iptal edilsin mi?\n{dest_name} — {otel}",
                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            bk['durum'] = 'cancelled'
            self.toast.show_msg(f"#{bid} nolu rezervasyon iptal edildi.", False)
            self._refresh_admin()

    # ══════════════════════════════
    #  ADMİN — TİCKET YÖNETİMİ
    # ══════════════════════════════
    def _admin_tickets(self, v):
        pending = [t for t in S.tickets if t['durum']=='bekliyor']
        answered = [t for t in S.tickets if t['durum']=='cevaplandi']
        sr = QHBoxLayout(); sr.setSpacing(10)
        for val,lbl,col in [(str(len(S.tickets)),"Toplam Ticket",p('gold')),(str(len(pending)),"Bekleyen",p('orange')),(str(len(answered)),"Cevaplanan",p('grn'))]:
            sf=QFrame(); sf.setStyleSheet(f"background:{p('card')};border:1px solid {p('border')};border-radius:11px;")
            sl=QVBoxLayout(sf); sl.setContentsMargins(14,10,14,10)
            vl=QLabel(val); vl.setStyleSheet(f"color:{col};font-size:20px;font-weight:700;background:transparent;border:none;")
            nl=QLabel(lbl); nl.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
            sl.addWidget(vl); sl.addWidget(nl); sr.addWidget(sf)
        sw=QWidget(); sw.setStyleSheet("background:transparent;"); sw.setLayout(sr); v.addWidget(sw)
        if not S.tickets:
            v.addWidget(self._lbl2("Henüz ticket bulunmuyor.",13)); return
        for tk in reversed(S.tickets):
            tf=QFrame()
            border_col = p('orange') if tk['durum']=='bekliyor' else p('border')
            tf.setStyleSheet(f"QFrame{{background:{p('card')};border:1.5px solid {border_col};border-radius:12px;}}")
            tfl=QVBoxLayout(tf); tfl.setContentsMargins(14,12,14,12); tfl.setSpacing(6)
            hr=QHBoxLayout()
            did = p('orange') if tk['durum']=='bekliyor' else p('grn')
            ds=QLabel("⏳ Bekliyor" if tk['durum']=='bekliyor' else "✅ Cevaplandı")
            ds.setStyleSheet(f"background:{did}22;color:{did};border:none;border-radius:6px;padding:2px 9px;font-size:9px;font-weight:700;")
            idl=QLabel(f"#T{tk['id']:03d}"); idl.setStyleSheet(f"color:{p('mut')};font-size:10px;font-weight:600;background:transparent;border:none;")
            unl=QLabel(f"👤 {tk['user_name']}"); unl.setStyleSheet(f"color:{p('txt2')};font-size:11px;background:transparent;border:none;")
            dtl=QLabel(tk['tarih'][:16]); dtl.setStyleSheet(f"color:{p('mut')};font-size:9px;background:transparent;border:none;")
            hr.addWidget(idl); hr.addWidget(ds); hr.addSpacing(8); hr.addWidget(unl); hr.addStretch(); hr.addWidget(dtl)
            tfl.addLayout(hr)
            kn=QLabel(tk['konu']); kn.setStyleSheet(f"color:{p('txt')};font-size:13px;font-weight:700;background:transparent;border:none;"); tfl.addWidget(kn)
            mn=QLabel(tk['mesaj']); mn.setStyleSheet(f"color:{p('txt3')};font-size:11px;background:transparent;border:none;"); mn.setWordWrap(True); tfl.addWidget(mn)
            # Cevaplar
            for cv in tk.get('cevaplar',[]):
                cf=QFrame(); cf.setStyleSheet(f"background:{p('gold')}11;border-left:3px solid {p('gold')};border-radius:0 6px 6px 0;")
                cfl=QVBoxLayout(cf); cfl.setContentsMargins(10,5,10,5); cfl.setSpacing(2)
                ca=QLabel(f"👑 Admin · {cv['tarih'][:16]}"); ca.setStyleSheet(f"color:{p('gold')};font-size:9px;font-weight:700;background:transparent;border:none;"); cfl.addWidget(ca)
                cm=QLabel(cv['mesaj']); cm.setStyleSheet(f"color:{p('txt2')};font-size:11px;background:transparent;border:none;"); cm.setWordWrap(True); cfl.addWidget(cm)
                tfl.addWidget(cf)
            # Cevap formu
            if tk['durum']=='bekliyor':
                rf=QFrame(); rf.setStyleSheet(f"background:{p('bg3')};border-radius:8px;")
                rfl=QHBoxLayout(rf); rfl.setContentsMargins(8,6,8,6); rfl.setSpacing(8)
                ri=QLineEdit(); ri.setPlaceholderText("Cevabınızı yazın..."); ri.setFixedHeight(34)
                ri.setStyleSheet(f"QLineEdit{{background:{p('bg4')};color:{p('txt')};border:1px solid {p('border')};border-radius:7px;padding:5px 10px;font-size:11px;}}QLineEdit:focus{{border-color:{p('gold')};}}")
                rb=QPushButton("Cevapla ✓"); rb.setFixedHeight(34); rb.setCursor(QCursor(Qt.PointingHandCursor))
                rb.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),7,'5px 12px',11))
                rb.clicked.connect(lambda _,tid=tk['id'],inp=ri: self._reply_ticket(tid,inp))
                rfl.addWidget(ri); rfl.addWidget(rb); tfl.addWidget(rf)
            v.addWidget(tf)

    def _reply_ticket(self, tid, inp):
        msg = inp.text().strip()
        if not msg: self.toast.show_msg("Cevap boş olamaz!",False); return
        for tk in S.tickets:
            if tk['id']==tid:
                tk['durum']='cevaplandi'
                tk['cevaplar'].append({"mesaj":msg,"tarih":datetime.now().strftime("%Y-%m-%d %H:%M")})
                break
        self._update_bell(); self.toast.show_msg("Ticket cevaplandı!"); self._refresh_admin()

    # ── Admin CRUD ──
    def _refresh_map(self):
        """Haritayı DESTS değişince yenile."""
        if hasattr(self, 'world_map') and self.world_map:
            self.world_map.refresh()

    def _add_dest(self):
        d=DestEditDlg(parent=self)
        if d.exec_()==QDialog.Accepted:
            nd=d.get(); nd['id']=max(x['id'] for x in DESTS)+1; nd.setdefault('places',[])
            DESTS.append(nd)
            self._atab='dests'
            self._refresh_admin()
            self._refresh_explore()
            self._refresh_home()
            self._refresh_map()
            self.toast.show_msg(f"{nd['name']} eklendi!")

    def _edit_dest(self, dest):
        d=DestEditDlg(dest,parent=self)
        if d.exec_()==QDialog.Accepted:
            nd=d.get(); nd['id']=dest['id']; nd['hotels']=dest['hotels']; nd['places']=dest.get('places',[])
            idx=next(i for i,x in enumerate(DESTS) if x['id']==dest['id'])
            DESTS[idx]=nd
            self._atab='dests'
            self._refresh_admin()
            self._refresh_explore()
            self._refresh_home()
            self._refresh_map()
            self.toast.show_msg(f"{nd['name']} güncellendi!")

    def _del_dest(self, did):
        dest=next((d for d in DESTS if d['id']==did),None)
        if not dest: return
        if QMessageBox.question(self,"Onayla",f"'{dest['name']}' silinsin mi?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            DESTS.remove(dest)
            self._refresh_admin()
            self._refresh_explore()
            self._refresh_home()
            self._refresh_map()
            self.toast.show_msg(f"{dest['name']} silindi",False)

    def _add_hotel(self):
        d=HotelEditDlg(DESTS,parent=self)
        if d.exec_()==QDialog.Accepted:
            dest,hotel=d.get()
            dest['hotels'].append(hotel)
            self._atab='hotels'
            self._refresh_admin()
            self._refresh_explore()
            self._refresh_home()
            self._refresh_map()
            QApplication.processEvents()
            if hasattr(self, '_scrolls') and 'admin' in self._scrolls:
                self._scrolls['admin'].verticalScrollBar().setValue(0)
            self.toast.show_msg(f"{hotel.otel_adi} eklendi!")

    def _edit_hotel(self, dest, hotel):
        d=HotelEditDlg(DESTS,dest,hotel,parent=self)
        if d.exec_()==QDialog.Accepted:
            _,nh=d.get()
            idx=next(i for i,h in enumerate(dest['hotels']) if h.otel_adi==hotel.otel_adi)
            dest['hotels'][idx]=nh
            self._atab='hotels'
            self._refresh_admin()
            self._refresh_explore()
            self._refresh_home()
            self._refresh_map()
            self.toast.show_msg(f"{nh.otel_adi} güncellendi!")

    def _del_user(self, uid):
        if uid==(S.user['id'] if S.user else -1): self.toast.show_msg("Kendinizi silemezsiniz!",False); return
        S.users=[u for u in S.users if u['id']!=uid]; self._refresh_admin(); self.toast.show_msg("Kullanıcı kaldırıldı")

    def _open_detail(self, dest):
        dlg=DetailDlg(dest,parent=self)
        def _on_booked(bk):
            self.toast.show_msg(f"✈ {bk['seyahat'].gidis_yeri} rezervasyonu onaylandı! ${bk['toplam']:,}")
            # Admin paneli açıksa yenile
            if S.role=='admin' and hasattr(self,'admin_v'):
                self._refresh_admin()
        dlg.booked.connect(_on_booked)
        dlg.exec_()

# ═══════════════════════════════════════════
#  ADMİN DÜZENLEME DİYALOGLARI
# ═══════════════════════════════════════════
class DestEditDlg(QDialog):
    """Destinasyon ekleme/düzenleme diyaloğu — çok adımlı, tam doğrulamalı"""
    # Popüler bayrak emojileri
    FLAG_EMOJIS = [
        ("🇹🇷","Türkiye"),("🇬🇷","Yunanistan"),("🇮🇹","İtalya"),("🇫🇷","Fransa"),
        ("🇪🇸","İspanya"),("🇵🇹","Portekiz"),("🇩🇪","Almanya"),("🇬🇧","İngiltere"),
        ("🇺🇸","ABD"),("🇯🇵","Japonya"),("🇨🇳","Çin"),("🇰🇷","Güney Kore"),
        ("🇮🇩","Endonezya"),("🇹🇭","Tayland"),("🇻🇳","Vietnam"),("🇮🇳","Hindistan"),
        ("🇦🇪","BAE"),("🇸🇦","Suudi Arabistan"),("🇲🇻","Maldivler"),("🇱🇰","Sri Lanka"),
        ("🇲🇦","Fas"),("🇪🇬","Mısır"),("🇿🇦","Güney Afrika"),("🇰🇪","Kenya"),
        ("🇦🇺","Avustralya"),("🇳🇿","Yeni Zelanda"),("🇧🇷","Brezilya"),("🇦🇷","Arjantin"),
        ("🇲🇽","Meksika"),("🇨🇦","Kanada"),("🇨🇿","Çek Cum."),("🇦🇹","Avusturya"),
        ("🇭🇷","Hırvatistan"),("🇨🇭","İsviçre"),("🇳🇴","Norveç"),("🇮🇸","İzlanda"),
        ("🇵🇱","Polonya"),("🇸🇪","İsveç"),("🇩🇰","Danimarka"),("🇳🇱","Hollanda"),
    ]
    ALL_TAGS = ["Romantik","Lüks","Deniz","Plaj","Tarih","Kültür","Gastronomi","Doğa",
                "Sörf","Dalış","Snorkeling","Eğlence","Teknoloji","Anime","Gece Hayatı",
                "Alışveriş","Mimari","Spor","Zen","Sakura","Metropol","Broadway","Tatil",
                "All-Inclusive","Balayı","Aile","Kış","Kayak","Safari","Trek","Yoga"]
    COLOR_PRESETS = [
        ("#162a70","Mavi"),("#0d3d1a","Yeşil"),("#003880","Lacivert"),("#4a2808","Kahve"),
        ("#800020","Bordo"),("#1a2840","Lacivert2"),("#7a5500","Altın"),("#7a1010","Kırmızı"),
        ("#6a3808","Turuncu"),("#701008","Koyu Kırmızı"),("#083888","Koyu Mavi"),("#004a7a","Teal"),
        ("#2a1a5a","Mor"),("#3a1a5a","Mor2"),("#083840","Koyu Teal"),("#401808","Koyu Turuncu"),
    ]

    def __init__(self, dest=None, parent=None):
        super().__init__(parent); self.dest=dest
        self.setWindowTitle("✏ Destinasyon Düzenle" if dest else "＋ Yeni Destinasyon Ekle")
        self.setMinimumSize(620,640); self.setStyleSheet(f"background:{p('bg')};color:{p('txt')};")
        self._selected_flag = dest.get('flag','🌍') if dest else '🌍'
        self._selected_tags = list(dest.get('tags',[])) if dest else []
        self._pending_hotels = []  # Yeni eklenen oteller (sadece yeni dest için)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        # ── Başlık bandı ──
        hdr = QFrame(); hdr.setFixedHeight(56)
        hdr.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                          f"stop:0 {p('bg3')},stop:1 {p('bg2')});"
                          f"border-bottom:1px solid {p('border')};}}")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(22,0,22,0)
        icon_l = QLabel("🌍" if not self.dest else self.dest.get('flag','🌍'))
        icon_l.setStyleSheet("font-size:22px;background:transparent;border:none;")
        title_l = QLabel("Yeni Destinasyon Ekle" if not self.dest else f"Düzenle: {self.dest['name']}")
        title_l.setStyleSheet(f"color:{p('txt')};font-size:15px;font-weight:700;background:transparent;border:none;")
        hl.addWidget(icon_l); hl.addSpacing(8); hl.addWidget(title_l); hl.addStretch()
        outer.addWidget(hdr)

        # ── Scroll area ──
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        body = QWidget(); body.setStyleSheet("background:transparent;")
        v = QVBoxLayout(body); v.setContentsMargins(22,18,22,6); v.setSpacing(14)
        sc.setWidget(body); outer.addWidget(sc)

        is_s = Inp(); cb_s = (
            f"QComboBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};"
            f"border-radius:9px;padding:7px 11px;font-size:12px;}}"
            f"QComboBox::drop-down{{border:none;width:20px;}}"
            f"QComboBox QAbstractItemView{{background:{p('bg3')};color:{p('txt')};"
            f"selection-background-color:{p('gold')}44;border:1px solid {p('border')};}}")
        self.inputs = {}

        def sec_lbl(txt):
            l = QLabel(txt)
            l.setStyleSheet(f"color:{p('gold3')};font-size:9px;font-weight:700;letter-spacing:2px;background:transparent;border:none;")
            return l

        def field_lbl(txt, req=True):
            suffix = " *" if req else ""
            l = QLabel(txt+suffix)
            l.setStyleSheet(f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;")
            return l

        # ══ BÖLÜM 1: TEMEL BİLGİLER ══
        v.addWidget(sec_lbl("TEMEL BİLGİLER"))

        # Bayrak seçici
        v.addWidget(field_lbl("Bayrak / Ülke Simgesi"))
        flag_frame = QFrame(); flag_frame.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:11px;}}")
        flag_lay = QVBoxLayout(flag_frame); flag_lay.setContentsMargins(12,10,12,10); flag_lay.setSpacing(8)

        # Seçili bayrak göstergesi
        sel_row = QHBoxLayout()
        self._flag_preview = QLabel(self._selected_flag)
        self._flag_preview.setFixedSize(44,44); self._flag_preview.setAlignment(Qt.AlignCenter)
        self._flag_preview.setStyleSheet(f"font-size:28px;background:{p('bg3')};border:2px solid {p('gold')};border-radius:11px;")
        sel_txt = QLabel("Seçili bayrak")
        sel_txt.setStyleSheet(f"color:{p('mut')};font-size:10px;background:transparent;border:none;")
        sel_row.addWidget(self._flag_preview); sel_row.addSpacing(8); sel_row.addWidget(sel_txt); sel_row.addStretch()
        flag_lay.addLayout(sel_row)

        # Emoji grid
        eg_lbl = QLabel("Ülke bayrağını seçin:")
        eg_lbl.setStyleSheet(f"color:{p('txt2')};font-size:10px;background:transparent;border:none;")
        flag_lay.addWidget(eg_lbl)
        eg_scroll = QScrollArea(); eg_scroll.setFixedHeight(120); eg_scroll.setWidgetResizable(True)
        eg_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        eg_w = QWidget(); eg_w.setStyleSheet("background:transparent;")
        eg_grid = QGridLayout(eg_w); eg_grid.setSpacing(4); eg_grid.setContentsMargins(0,0,0,0)
        cols = 10
        for idx,(emoji,country_name) in enumerate(self.FLAG_EMOJIS):
            btn = QPushButton(emoji); btn.setFixedSize(34,34)
            btn.setToolTip(country_name); btn.setCursor(QCursor(Qt.PointingHandCursor))
            is_sel = (emoji == self._selected_flag)
            btn.setStyleSheet(
                f"QPushButton{{background:{p('gold')+'33' if is_sel else p('bg3')};border:{('2px solid '+p('gold')) if is_sel else ('1px solid '+p('border'))};border-radius:8px;font-size:16px;}}"
                f"QPushButton:hover{{background:{p('gold')}22;border-color:{p('gold')};}}"
            )
            def _pick(_checked=False, e=emoji, b=btn):
                self._selected_flag = e; self._flag_preview.setText(e)
                for i2 in range(eg_grid.count()):
                    it = eg_grid.itemAt(i2)
                    if it and it.widget():
                        w = it.widget()
                        is_active = (w.text() == e)
                        w.setStyleSheet(
                            f"QPushButton{{background:{p('gold')+'33' if is_active else p('bg3')};border:{('2px solid '+p('gold')) if is_active else ('1px solid '+p('border'))};border-radius:8px;font-size:16px;}}"
                            f"QPushButton:hover{{background:{p('gold')}22;border-color:{p('gold')};}}"
                        )
            btn.clicked.connect(_pick)
            eg_grid.addWidget(btn, idx//cols, idx%cols)
        eg_scroll.setWidget(eg_w); flag_lay.addWidget(eg_scroll)

        # Manuel bayrak girişi
        man_lbl = QLabel("veya emoji kodunu yazın:")
        man_lbl.setStyleSheet(f"color:{p('txt3')};font-size:9px;background:transparent;border:none;")
        self._flag_manual = QLineEdit(); self._flag_manual.setPlaceholderText("Bayrak emojisi yapıştırın (ör: 🇹🇷)")
        self._flag_manual.setFixedHeight(34); self._flag_manual.setStyleSheet(is_s)
        if self.dest: self._flag_manual.setText(self._selected_flag)
        def _manual_flag_changed(txt):
            if txt.strip():
                self._selected_flag = txt.strip()
                self._flag_preview.setText(self._selected_flag)
        self._flag_manual.textChanged.connect(_manual_flag_changed)
        flag_lay.addWidget(man_lbl); flag_lay.addWidget(self._flag_manual)
        v.addWidget(flag_frame)

        # Ad + Ülke yan yana
        row1 = QHBoxLayout(); row1.setSpacing(10)
        for lbl_txt,key,ph in [("Destinasyon Adı *","name","ör: Kapadokya"),("Ülke *","country","ör: Türkiye")]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(field_lbl(lbl_txt, False))
            inp = QLineEdit(); inp.setPlaceholderText(ph); inp.setFixedHeight(38); inp.setStyleSheet(is_s)
            if self.dest: inp.setText(str(self.dest.get(key,'')))
            self.inputs[key] = inp; col.addWidget(inp); row1.addLayout(col)
        rw1 = QWidget(); rw1.setStyleSheet("background:transparent;"); rw1.setLayout(row1); v.addWidget(rw1)

        # Kıta
        v.addWidget(field_lbl("Kıta"))
        self.cont_cb = QComboBox(); self.cont_cb.setFixedHeight(38); self.cont_cb.setStyleSheet(cb_s)
        cont_opts = [("🌍 Avrupa","Avrupa"),("🌏 Asya","Asya"),("🌎 Amerika","Amerika"),
                     ("🌍 Afrika","Afrika"),("🌏 Okyanusya","Okyanusya"),
                     ("🌍 Orta Doğu","Orta Doğu"),("🌏 Avrupa/Asya","Avrupa/Asya")]
        for lbl_c,val_c in cont_opts: self.cont_cb.addItem(lbl_c, val_c)
        cur_cont = self.dest.get('cont','Avrupa') if self.dest else 'Avrupa'
        idx2 = next((i for i,(l,val) in enumerate(cont_opts) if val==cur_cont), 0)
        self.cont_cb.setCurrentIndex(idx2); v.addWidget(self.cont_cb)

        # Açıklama
        v.addWidget(field_lbl("Açıklama"))
        self.inputs['desc'] = QTextEdit(); self.inputs['desc'].setFixedHeight(70)
        self.inputs['desc'].setPlaceholderText("Destinasyonu kısaca tanıtın...")
        self.inputs['desc'].setStyleSheet(f"QTextEdit{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:7px;font-size:11px;}}QTextEdit:focus{{border-color:{p('gold')};}}")
        if self.dest: self.inputs['desc'].setPlainText(self.dest.get('desc',''))
        v.addWidget(self.inputs['desc'])

        # ══ BÖLÜM 2: FİYATLANDIRMA ══
        v.addWidget(sec_lbl("FİYATLANDIRMA VE PUAN"))
        g = QGridLayout(); g.setSpacing(10)
        ssp = f"QSpinBox,QDoubleSpinBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:7px 11px;font-size:13px;font-weight:600;}}"
        for i,(lb,key,mn,mx,dv,isfloat,suf,hint) in enumerate([
            ("Başlangıç Fiyatı ($/gece) *","price",50,9999,200,False," $","Gecelik minimum fiyat"),
            ("Puan (1.0–5.0) *","rating",1.0,5.0,4.5,True,"","Destinasyon puanı"),
        ]):
            col2 = QVBoxLayout(); col2.setSpacing(4)
            lbl_w = QLabel(lb); lbl_w.setStyleSheet(f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;")
            if isfloat:
                sp = QDoubleSpinBox(); sp.setRange(mn,mx); sp.setSingleStep(0.1)
                sp.setValue(float(self.dest.get(key,dv)) if self.dest else dv)
            else:
                sp = QSpinBox(); sp.setRange(mn,mx)
                sp.setValue(int(self.dest.get(key,dv)) if self.dest else dv)
            if suf: sp.setSuffix(suf)
            sp.setFixedHeight(42); sp.setStyleSheet(ssp)
            hint_l = QLabel(hint); hint_l.setStyleSheet(f"color:{p('txt3')};font-size:9px;background:transparent;border:none;")
            col2.addWidget(lbl_w); col2.addWidget(sp); col2.addWidget(hint_l)
            self.inputs[key] = sp; g.addLayout(col2,0,i)
        v.addLayout(g)

        # ══ BÖLÜM 3: ETİKETLER ══
        v.addWidget(sec_lbl("ETİKETLER"))
        tag_frame = QFrame(); tag_frame.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:11px;}}")
        tag_lay = QVBoxLayout(tag_frame); tag_lay.setContentsMargins(12,10,12,10); tag_lay.setSpacing(8)
        tag_lay.addWidget(field_lbl("Kategori etiketleri seçin (en az 1)", False))

        self._tag_btns = {}
        tg_grid = QGridLayout(); tg_grid.setSpacing(5)
        tg_cols = 5
        for idx,tag in enumerate(self.ALL_TAGS):
            is_sel = tag in self._selected_tags
            tb = QPushButton(tag); tb.setFixedHeight(26); tb.setCursor(QCursor(Qt.PointingHandCursor))
            tb.setCheckable(True); tb.setChecked(is_sel)
            tb.setStyleSheet(
                f"QPushButton{{padding:0 9px;border-radius:7px;font-size:9px;font-weight:600;"
                f"border:1px solid {p('gold') if is_sel else p('border')};"
                f"background:{p('gold')+'22' if is_sel else p('bg3')};"
                f"color:{p('gold') if is_sel else p('txt3')};}}"
                f"QPushButton:hover{{border-color:{p('gold')};color:{p('gold')};}}"
                f"QPushButton:checked{{background:{p('gold')}22;border:1px solid {p('gold')};color:{p('gold')};}}"
            )
            def _tog_tag(chk, t=tag, b=tb):
                if chk:
                    if t not in self._selected_tags: self._selected_tags.append(t)
                    b.setStyleSheet(f"QPushButton{{padding:0 9px;border-radius:7px;font-size:9px;font-weight:600;border:1px solid {p('gold')};background:{p('gold')}22;color:{p('gold')};}}QPushButton:hover{{border-color:{p('gold')};color:{p('gold')};}}QPushButton:checked{{background:{p('gold')}22;border:1px solid {p('gold')};color:{p('gold')};}}")
                else:
                    if t in self._selected_tags: self._selected_tags.remove(t)
                    b.setStyleSheet(f"QPushButton{{padding:0 9px;border-radius:7px;font-size:9px;font-weight:600;border:1px solid {p('border')};background:{p('bg3')};color:{p('txt3')};}}QPushButton:hover{{border-color:{p('gold')};color:{p('gold')};}}QPushButton:checked{{background:{p('gold')}22;border:1px solid {p('gold')};color:{p('gold')};}}")
            tb.toggled.connect(_tog_tag)
            self._tag_btns[tag] = tb; tg_grid.addWidget(tb, idx//tg_cols, idx%tg_cols)
        tag_lay.addLayout(tg_grid); v.addWidget(tag_frame)

        # ══ BÖLÜM 4: RENK ══
        v.addWidget(sec_lbl("KART RENK TEMASI"))
        col_frame = QFrame(); col_frame.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:11px;}}")
        col_lay = QVBoxLayout(col_frame); col_lay.setContentsMargins(12,10,12,10); col_lay.setSpacing(8)
        col_lay.addWidget(field_lbl("Destinasyon kart rengi", False))

        self._sel_color = self.dest.get('color','#162a70') if self.dest else '#162a70'
        self._color_preview = QFrame(); self._color_preview.setFixedSize(44,44)
        self._color_preview.setStyleSheet(f"background:{self._sel_color};border:2px solid {p('gold')};border-radius:11px;")
        col_hex_inp = QLineEdit(self._sel_color); col_hex_inp.setPlaceholderText("#1a3a8a")
        col_hex_inp.setFixedHeight(34); col_hex_inp.setStyleSheet(is_s); col_hex_inp.setMaximumWidth(120)
        def _hex_changed(txt):
            if len(txt)==7 and txt.startswith('#'):
                self._sel_color = txt
                self._color_preview.setStyleSheet(f"background:{txt};border:2px solid {p('gold')};border-radius:11px;")
        col_hex_inp.textChanged.connect(_hex_changed)
        self._col_hex_inp = col_hex_inp
        prev_row = QHBoxLayout(); prev_row.setSpacing(10)
        prev_row.addWidget(self._color_preview); prev_row.addWidget(col_hex_inp); prev_row.addStretch()
        col_lay.addLayout(prev_row)

        # Hazır renkler
        preset_lbl = QLabel("Hazır tema renkleri:")
        preset_lbl.setStyleSheet(f"color:{p('txt3')};font-size:9px;background:transparent;border:none;")
        col_lay.addWidget(preset_lbl)
        preset_grid = QGridLayout(); preset_grid.setSpacing(5)
        for idx,(hex_c,name_c) in enumerate(self.COLOR_PRESETS):
            pb = QPushButton(); pb.setFixedSize(32,32)
            pb.setStyleSheet(f"QPushButton{{background:{hex_c};border-radius:8px;border:1px solid {p('border')};}}QPushButton:hover{{border:2px solid {p('gold')};}}")
            pb.setToolTip(name_c); pb.setCursor(QCursor(Qt.PointingHandCursor))
            def _pick_color(checked=False, hc=hex_c):
                self._sel_color = hc
                self._color_preview.setStyleSheet(f"background:{hc};border:2px solid {p('gold')};border-radius:11px;")
                self._col_hex_inp.blockSignals(True); self._col_hex_inp.setText(hc); self._col_hex_inp.blockSignals(False)
            pb.clicked.connect(_pick_color)
            preset_grid.addWidget(pb, idx//8, idx%8)
        col_lay.addLayout(preset_grid)

        # Otomatik renk — hasattr koruması ile
        def _auto_color(txt):
            if not self.dest and txt and hasattr(self,'_color_preview') and hasattr(self,'_col_hex_inp'):
                import hashlib
                h = hashlib.md5(txt.lower().encode()).hexdigest()
                r = int(h[0:2],16)//3; g2 = int(h[2:4],16)//3; b2 = int(h[4:6],16)//3
                auto_hex = f"#{r:02x}{g2:02x}{b2:02x}"
                self._sel_color = auto_hex
                self._color_preview.setStyleSheet(f"background:{auto_hex};border:2px solid {p('gold')};border-radius:11px;")
                self._col_hex_inp.blockSignals(True); self._col_hex_inp.setText(auto_hex); self._col_hex_inp.blockSignals(False)
        self._auto_color_fn = _auto_color
        self.inputs['name'].textChanged.connect(_auto_color)
        v.addWidget(col_frame)

        # ══ BÖLÜM 5: OTEL EKLEME (sadece yeni destinasyon) ══
        if not self.dest:
            v.addWidget(sec_lbl("OTEL FİYAT BİLGİSİ (İSTEĞE BAĞLI)"))
            hotel_frame = QFrame()
            hotel_frame.setStyleSheet(f"QFrame{{background:{p('card')};border:1px solid {p('border')};border-radius:11px;}}")
            hotel_lay = QVBoxLayout(hotel_frame); hotel_lay.setContentsMargins(14,12,14,12); hotel_lay.setSpacing(10)
            hotel_lay.addWidget(field_lbl("Destinasyona otel ekleyin (fiyatlarla birlikte)", False))

            # Mini otel form
            h_form = QFrame(); h_form.setStyleSheet(f"QFrame{{background:{p('bg3')};border:1px solid {p('brd2')};border-radius:9px;}}")
            hfl = QVBoxLayout(h_form); hfl.setContentsMargins(12,10,12,10); hfl.setSpacing(8)

            h_row1 = QHBoxLayout(); h_row1.setSpacing(8)
            self._h_name = QLineEdit(); self._h_name.setPlaceholderText("Otel adı  ör: Grand Palace Hotel")
            self._h_name.setFixedHeight(36); self._h_name.setStyleSheet(is_s)

            self._h_price = QSpinBox(); self._h_price.setRange(50,9999); self._h_price.setValue(200)
            self._h_price.setSuffix(" $/gece"); self._h_price.setFixedHeight(36)
            self._h_price.setStyleSheet(ssp)

            self._h_stars = QSpinBox(); self._h_stars.setRange(1,5); self._h_stars.setValue(4)
            self._h_stars.setPrefix("⭐ "); self._h_stars.setFixedHeight(36)
            self._h_stars.setStyleSheet(ssp); self._h_stars.setFixedWidth(90)

            h_row1.addWidget(self._h_name,3); h_row1.addWidget(self._h_price,1); h_row1.addWidget(self._h_stars)
            hfl.addLayout(h_row1)

            self._h_desc = QLineEdit(); self._h_desc.setPlaceholderText("Kısa açıklama  ör: Şehir merkezinde lüks otel")
            self._h_desc.setFixedHeight(34); self._h_desc.setStyleSheet(is_s)
            hfl.addWidget(self._h_desc)

            h_add_btn = QPushButton("＋  Oteli Listeye Ekle"); h_add_btn.setFixedHeight(34)
            h_add_btn.setCursor(QCursor(Qt.PointingHandCursor))
            h_add_btn.setStyleSheet(Btn(p('grn'),'#fff','#1ea040',9,'5px 14px',11))
            hfl.addWidget(h_add_btn)
            hotel_lay.addWidget(h_form)

            # Eklenen oteller listesi
            h_list_lbl = QLabel("Eklenen oteller:")
            h_list_lbl.setStyleSheet(f"color:{p('txt3')};font-size:10px;font-weight:600;background:transparent;border:none;")
            hotel_lay.addWidget(h_list_lbl)
            self._hotel_list_lay = QVBoxLayout(); self._hotel_list_lay.setSpacing(5)
            hotel_lay.addLayout(self._hotel_list_lay)

            def _add_hotel_to_list(_checked=False):
                nm = self._h_name.text().strip()
                if not nm: return
                desc = self._h_desc.text().strip() or f"{nm} — konforlu konaklama seçeneği."
                h = Konaklama(nm, self._h_price.value(), self._h_stars.value(), [], desc)
                self._pending_hotels.append(h)
                self._refresh_hotel_list()
                self._h_name.clear(); self._h_desc.clear()

            def _refresh_hotel_list():
                while self._hotel_list_lay.count():
                    it = self._hotel_list_lay.takeAt(0)
                    if it.widget(): it.widget().deleteLater()
                for hh in self._pending_hotels:
                    hf = QFrame(); hf.setStyleSheet(f"QFrame{{background:{p('bg4')};border:1px solid {p('brd2')};border-radius:8px;}}")
                    hhl = QHBoxLayout(hf); hhl.setContentsMargins(10,6,10,6); hhl.setSpacing(8)
                    star_l = QLabel("⭐"*hh.yildiz); star_l.setStyleSheet("font-size:9px;background:transparent;border:none;")
                    name_l = QLabel(hh.otel_adi); name_l.setStyleSheet(f"color:{p('txt')};font-size:11px;font-weight:600;background:transparent;border:none;")
                    price_l = QLabel(f"${hh.fiyat}/gece"); price_l.setStyleSheet(f"color:{p('gold')};font-size:11px;font-weight:700;background:transparent;border:none;")
                    del_btn = QPushButton("✕"); del_btn.setFixedSize(22,22); del_btn.setCursor(QCursor(Qt.PointingHandCursor))
                    del_btn.setStyleSheet(f"QPushButton{{background:transparent;color:{p('mut')};border:none;font-size:10px;}}QPushButton:hover{{color:{p('red')};}}")
                    def _rm(_checked=False, h2=hh):
                        if h2 in self._pending_hotels: self._pending_hotels.remove(h2)
                        _refresh_hotel_list()
                    del_btn.clicked.connect(_rm)
                    hhl.addWidget(star_l); hhl.addWidget(name_l); hhl.addStretch(); hhl.addWidget(price_l); hhl.addWidget(del_btn)
                    self._hotel_list_lay.addWidget(hf)
                if not self._pending_hotels:
                    no_lbl = QLabel("Henüz otel eklenmedi — otel olmadan da devam edebilirsiniz.")
                    no_lbl.setStyleSheet(f"color:{p('txt3')};font-size:9px;background:transparent;border:none;")
                    self._hotel_list_lay.addWidget(no_lbl)

            self._refresh_hotel_list = _refresh_hotel_list
            h_add_btn.clicked.connect(_add_hotel_to_list)
            _refresh_hotel_list()
            v.addWidget(hotel_frame)

        v.addStretch()

        # ── Footer butonlar ──
        footer = QFrame(); footer.setFixedHeight(60)
        footer.setStyleSheet(f"QFrame{{background:{p('bg2')};border-top:1px solid {p('border')};}}")
        fl2 = QHBoxLayout(footer); fl2.setContentsMargins(22,0,22,0); fl2.setSpacing(10)
        self._err_lbl = QLabel(""); self._err_lbl.setStyleSheet(f"color:{p('red')};font-size:10px;font-weight:600;background:transparent;border:none;")
        fl2.addWidget(self._err_lbl); fl2.addStretch()
        cancel_btn = QPushButton("İptal"); cancel_btn.setFixedSize(90,38)
        cancel_btn.setStyleSheet(Btn(p('bg3'),p('txt2'),p('bg4'),9,'7px 18px',12,False))
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("✓  Kaydet"); save_btn.setFixedSize(120,38)
        save_btn.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),9,'7px 18px',12))
        save_btn.clicked.connect(self._validate_and_accept)
        fl2.addWidget(cancel_btn); fl2.addWidget(save_btn)
        outer.addWidget(footer)

    def _validate_and_accept(self):
        import re
        harf_re = re.compile(r'[a-zA-ZÇçĞğİıÖöŞşÜü]')
        errors = []
        name_val = self.inputs['name'].text().strip()
        country_val = self.inputs['country'].text().strip()
        desc_val = self.inputs['desc'].toPlainText().strip()
        if not name_val: errors.append("Destinasyon adı zorunlu.")
        elif not harf_re.search(name_val): errors.append("Destinasyon adı harf içermeli.")
        if not country_val: errors.append("Ülke adı zorunlu.")
        elif not harf_re.search(country_val): errors.append("Ülke adı harf içermeli.")
        if not desc_val: errors.append("Açıklama zorunlu.")
        elif not harf_re.search(desc_val): errors.append("Açıklama harf içermeli.")
        if not self._selected_tags: errors.append("En az 1 etiket seçin.")
        flag_val = self._flag_manual.text().strip() if self._flag_manual.text().strip() else self._selected_flag
        if not flag_val: errors.append("Bayrak seçin veya girin.")
        if errors:
            self._err_lbl.setText("❌ " + "  |  ".join(errors)); return
        self._err_lbl.setText(""); self.accept()

    def get(self):
        d = {}
        for key, inp in self.inputs.items():
            if isinstance(inp, QTextEdit): d[key] = inp.toPlainText()
            elif isinstance(inp, (QSpinBox, QDoubleSpinBox)): d[key] = inp.value()
            else: d[key] = inp.text()
        flag_val = self._flag_manual.text().strip()
        d['flag'] = flag_val if flag_val else self._selected_flag
        cont_opts = ["Avrupa","Asya","Amerika","Afrika","Okyanusya","Orta Doğu","Avrupa/Asya"]
        cont_idx = self.cont_cb.currentIndex()
        d['cont'] = cont_opts[cont_idx] if 0 <= cont_idx < len(cont_opts) else "Avrupa"
        d['color'] = self._sel_color or '#1a3a8a'
        d['tags'] = self._selected_tags or []
        d['hotels'] = list(self.dest.get('hotels',[])) if self.dest else list(self._pending_hotels)
        d['places'] = list(self.dest.get('places',[])) if self.dest else []
        return d

class HotelEditDlg(QDialog):
    def __init__(self, dests, dest=None, hotel=None, parent=None):
        super().__init__(parent); self.dests=dests; self.sel_dest=dest; self.hotel=hotel
        self.setWindowTitle("Otel Düzenle" if hotel else "Yeni Otel")
        self.setMinimumSize(460,440); self.setStyleSheet(f"background:{p('bg')};color:{p('txt')};"); self._build()

    def _build(self):
        v=QVBoxLayout(self); v.setContentsMargins(22,18,22,18); v.setSpacing(9); is_s=Inp()
        if not self.sel_dest:
            dl=QLabel("Destinasyon"); dl.setStyleSheet(f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;")
            self.dest_cb=QComboBox(); self.dest_cb.setFixedHeight(38)
            self.dest_cb.setStyleSheet(f"QComboBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:7px 11px;font-size:12px;}}")
            for d in self.dests: self.dest_cb.addItem(f"{d['flag']} {d['name']}",d)
            v.addWidget(dl); v.addWidget(self.dest_cb)
        for lb,attr,ph in [("Otel Adı","otel_adi","Otel adı"),("Açıklama","aciklama","Kısa açıklama")]:
            ll=QLabel(lb); ll.setStyleSheet(f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;")
            inp=QLineEdit(); inp.setPlaceholderText(ph); inp.setFixedHeight(38); inp.setStyleSheet(is_s)
            if self.hotel:
                inp.setText(str(getattr(self.hotel,attr,'')))
            v.addWidget(ll); v.addWidget(inp); setattr(self,f'inp_{attr}',inp)
        # Özellikler — combobox ile çoklu seçim
        oz_lbl=QLabel("Özellikler (seçip ekleyin)"); oz_lbl.setStyleSheet(f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;"); v.addWidget(oz_lbl)
        oz_row=QHBoxLayout(); oz_row.setSpacing(6)
        self._oz_combo=QComboBox(); self._oz_combo.setFixedHeight(36)
        self._oz_combo.setStyleSheet(f"QComboBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:5px 11px;font-size:11px;}}"
                                     f"QComboBox::drop-down{{border:none;width:20px;}}"
                                     f"QComboBox QAbstractItemView{{background:{p('bg3')};color:{p('txt')};selection-background-color:{p('gold')}44;border:1px solid {p('border')};}}")
        oz_secenekler=["Havuz","Sonsuzluk Havuzu","Özel Havuz","Spa","Hamam","Sauna","Fitness",
                       "Restoran","Fine Dining","Kahvaltı","All-Inclusive","Bar","Rooftop Bar",
                       "Butler","Butler 24/7","Concierge","WiFi","Otopark","Transfer",
                       "Plaj","Özel Plaj","Dalış","Snorkeling","Su Sporları",
                       "Bahçe","Teras","Manzara Terası","Şehir Manzarası","Deniz Manzarası",
                       "Aile Dostu","Evcil Hayvan Kabul","Bisiklet","Golf",
                       "Onsen","Tatami","Kimono","Akşam Yemeği","Yoga","Organik Restoran"]
        for oz in oz_secenekler: self._oz_combo.addItem(oz)
        oz_add_btn=QPushButton("+ Ekle"); oz_add_btn.setFixedHeight(36); oz_add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        oz_add_btn.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),8,'5px 12px',11))
        oz_row.addWidget(self._oz_combo); oz_row.addWidget(oz_add_btn); v.addLayout(oz_row)
        # Seçilen özellikler listesi
        oz_sel_lbl=QLabel("Seçilen özellikler:"); oz_sel_lbl.setStyleSheet(f"color:{p('txt3')};font-size:10px;background:transparent;border:none;"); v.addWidget(oz_sel_lbl)
        self._oz_tags_frame=QFrame(); self._oz_tags_frame.setStyleSheet("background:transparent;border:none;")
        self._oz_tags_lay=QHBoxLayout(self._oz_tags_frame); self._oz_tags_lay.setContentsMargins(0,0,0,0); self._oz_tags_lay.setSpacing(4)
        self._oz_tags_lay.addStretch(); v.addWidget(self._oz_tags_frame)
        self._selected_oz = []
        if self.hotel: self._selected_oz = list(self.hotel.ozellikler)
        def _refresh_oz_tags():
            while self._oz_tags_lay.count():
                it=self._oz_tags_lay.takeAt(0)
                if it.widget(): it.widget().deleteLater()
            for oz_item in self._selected_oz:
                tag_f=QFrame(); tag_f.setStyleSheet(f"background:{p('gold')}22;border:1px solid {p('gold')}55;border-radius:7px;")
                tag_l=QHBoxLayout(tag_f); tag_l.setContentsMargins(6,2,3,2); tag_l.setSpacing(3)
                tag_lbl=QLabel(oz_item); tag_lbl.setStyleSheet(f"color:{p('gold')};font-size:9px;font-weight:700;background:transparent;border:none;")
                rem_btn=QPushButton("✕"); rem_btn.setFixedSize(14,14); rem_btn.setCursor(QCursor(Qt.PointingHandCursor))
                rem_btn.setStyleSheet(f"QPushButton{{background:transparent;color:{p('mut')};border:none;font-size:9px;}}QPushButton:hover{{color:{p('red')};}}")
                rem_btn.clicked.connect(lambda _checked=False,o=oz_item: _remove_oz(o))
                tag_l.addWidget(tag_lbl); tag_l.addWidget(rem_btn); self._oz_tags_lay.insertWidget(self._oz_tags_lay.count()-1,tag_f)
        def _remove_oz(oz_item):
            if oz_item in self._selected_oz: self._selected_oz.remove(oz_item)
            _refresh_oz_tags()
        def _add_oz(_checked=False):
            oz_item=self._oz_combo.currentText()
            if oz_item and oz_item not in self._selected_oz:
                self._selected_oz.append(oz_item); _refresh_oz_tags()
        oz_add_btn.clicked.connect(_add_oz)
        self._refresh_oz_tags = _refresh_oz_tags
        _refresh_oz_tags()
        g=QGridLayout(); g.setSpacing(9)
        ssp=(f"QSpinBox{{background:{p('bg3')};color:{p('txt')};border:1.5px solid {p('border')};border-radius:9px;padding:7px 11px;font-size:12px;}}")
        for i,(lb,attr,mn,mx,dv) in enumerate([("Yıldız","yildiz",1,5,5),("Fiyat ($)","fiyat",150,9999,200)]):
            ll=QLabel(lb); ll.setStyleSheet(f"color:{p('txt2')};font-size:11px;font-weight:600;background:transparent;border:none;")
            sp=QSpinBox(); sp.setRange(mn,mx); sp.setFixedHeight(38); sp.setStyleSheet(ssp)
            sp.setValue(int(getattr(self.hotel,attr,dv)) if self.hotel else dv)
            setattr(self,f'sp_{attr}',sp); g.addWidget(ll,0,i); g.addWidget(sp,1,i)
        v.addLayout(g); v.addStretch()
        br=QHBoxLayout(); br.addStretch()
        cb=QPushButton("İptal"); cb.setFixedHeight(36); cb.setStyleSheet(Btn(p('bg3'),p('txt2'),p('bg4'),9,'7px 18px',12,False)); cb.clicked.connect(self.reject)
        sb=QPushButton("Kaydet"); sb.setFixedHeight(36); sb.setStyleSheet(Btn(p('gold'),'#09090f',p('gold2'),9,'7px 18px',12)); sb.clicked.connect(self._validate_and_accept)
        br.addWidget(cb); br.addWidget(sb); v.addLayout(br)
        self._err_lbl = QLabel(""); self._err_lbl.setStyleSheet(f"color:{p('red')};font-size:10px;font-weight:600;background:transparent;border:none;")
        v.addWidget(self._err_lbl)

    def _validate_and_accept(self):
        import re
        harf_re = re.compile(r'[a-zA-Z\u00c7\u00e7\u011e\u011f\u0130\u0131\u00d6\u00f6\u015e\u015f\u00dc\u00fc]')
        ad_val = self.inp_otel_adi.text().strip()
        ac_val = self.inp_aciklama.text().strip()
        errors = []
        if not ad_val:
            errors.append("Otel adı boş bırakılamaz.")
        elif not harf_re.search(ad_val):
            errors.append("Otel adı en az bir harf içermelidir.")
        if not ac_val:
            errors.append("Açıklama boş bırakılamaz.")
        elif not harf_re.search(ac_val):
            errors.append("Açıklama en az bir harf içermelidir.")
        if errors:
            self._err_lbl.setText("❌ " + "  ".join(errors))
            return
        self._err_lbl.setText("")
        self.accept()

    def get(self):
        if self.sel_dest:
            dest = self.sel_dest
        else:
            idx = self.dest_cb.currentIndex()
            dest = self.dests[idx] if 0 <= idx < len(self.dests) else self.dests[0]
        oz=self._selected_oz
        h=Konaklama(self.inp_otel_adi.text(),self.sp_fiyat.value(),self.sp_yildiz.value(),oz,self.inp_aciklama.text())
        return dest,h

def _make_voyager_icon(size=64):
    """Uçak + altın halka — uygulama ikonu (pencere başlık çubuğu + görev çubuğu)."""
    px = QPixmap(size, size); px.fill(Qt.transparent)
    qp = QPainter(px); qp.setRenderHint(QPainter.Antialiasing)
    cx = cy = size // 2; r = size // 2 - 2

    # Arka plan: koyu daire
    bg_g = QRadialGradient(cx, cy, r)
    bg_g.setColorAt(0, QColor('#1a1a2e'))
    bg_g.setColorAt(1, QColor('#09090f'))
    qp.setBrush(QBrush(bg_g)); qp.setPen(Qt.NoPen)
    qp.drawEllipse(cx - r, cy - r, r * 2, r * 2)

    # Altın dış halka
    pen_outer = QPen(QColor('#c9922a'), max(2, size // 20))
    pen_outer.setCapStyle(Qt.RoundCap)
    qp.setPen(pen_outer); qp.setBrush(Qt.NoBrush)
    inset = max(2, size // 18)
    qp.drawEllipse(cx - r + inset, cy - r + inset, (r - inset) * 2, (r - inset) * 2)

    # İç parlak halka (ince)
    pen_inner = QPen(QColor('#e8b84b'), max(1, size // 32))
    qp.setPen(pen_inner)
    inset2 = inset + max(3, size // 14)
    qp.drawEllipse(cx - r + inset2, cy - r + inset2, (r - inset2) * 2, (r - inset2) * 2)

    # Uçak sembolü — QPainterPath ile
    sc = size / 64.0
    plane = QPainterPath()
    # Gövde (yatay)
    plane.moveTo(cx - 20*sc, cy)
    plane.cubicTo(cx - 10*sc, cy - 5*sc, cx + 10*sc, cy - 5*sc, cx + 22*sc, cy)
    plane.cubicTo(cx + 10*sc, cy + 5*sc, cx - 10*sc, cy + 5*sc, cx - 20*sc, cy)
    # Sol kanat
    plane.moveTo(cx - 4*sc, cy)
    plane.lineTo(cx - 10*sc, cy + 14*sc)
    plane.lineTo(cx + 8*sc, cy)
    # Sağ küçük kanat (kuyruk)
    plane.moveTo(cx + 14*sc, cy)
    plane.lineTo(cx + 10*sc, cy + 8*sc)
    plane.lineTo(cx + 22*sc, cy)

    gold_g = QLinearGradient(cx - 22*sc, cy, cx + 22*sc, cy)
    gold_g.setColorAt(0, QColor('#e8b84b'))
    gold_g.setColorAt(1, QColor('#c9922a'))
    qp.setPen(QPen(QBrush(gold_g), max(2, size // 16), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    qp.setBrush(Qt.NoBrush)
    qp.drawPath(plane)

    # "V" harfi — küçük, sağ üst köşede
    fnt = QFont("Arial", max(7, int(size * 0.18)), QFont.Bold)
    qp.setFont(fnt)
    qp.setPen(QPen(QColor('#e8b84b')))
    qp.drawText(cx + int(r * 0.38), cy - int(r * 0.42), "v4")

    qp.end()
    return QIcon(px)


# ═══════════════════════════════════════════
#  ANA PENCERE
# ═══════════════════════════════════════════
class VoyagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("✈  Voyager — Seyahat Planlama Platformu v4")
        self.setWindowIcon(_make_voyager_icon(64))
        self.setMinimumSize(1150,720); self.resize(1400,860)
        self.stack = QStackedWidget(); self.setCentralWidget(self.stack)
        self.login = LoginScreen(); self.login.ok.connect(self._on_login)
        self.stack.addWidget(self.login); self.stack.setCurrentWidget(self.login)
        self.app_w = None

    def _on_login(self, role):
        if self.app_w:
            self.stack.removeWidget(self.app_w); self.app_w.deleteLater()
        self.app_w = MainApp(start_page='admin' if role=='admin' else 'home')
        self.app_w.logout_req.connect(self._on_logout)
        self.stack.addWidget(self.app_w); self.stack.setCurrentWidget(self.app_w)

    def _on_logout(self):
        S.user=None; S.role='guest'
        S.page='home'; S.filt_cont='Tümü'; S.search=''; S.sort_key='puan'
        if self.app_w:
            self.stack.removeWidget(self.app_w); self.app_w.deleteLater(); self.app_w=None
        self.login._show_select(); self.stack.setCurrentWidget(self.login)

def main():
    app = QApplication(sys.argv); app.setApplicationName("Voyager"); app.setStyle("Fusion")
    app.setWindowIcon(_make_voyager_icon(64))
    pal = QPalette()
    pal.setColor(QPalette.Window,QColor(P['bg'])); pal.setColor(QPalette.WindowText,QColor(P['txt']))
    pal.setColor(QPalette.Base,QColor(P['bg2'])); pal.setColor(QPalette.AlternateBase,QColor(P['bg3']))
    pal.setColor(QPalette.Text,QColor(P['txt'])); pal.setColor(QPalette.Button,QColor(P['bg3']))
    pal.setColor(QPalette.ButtonText,QColor(P['txt'])); pal.setColor(QPalette.Highlight,QColor(P['gold']))
    pal.setColor(QPalette.HighlightedText,QColor(P['bg'])); app.setPalette(pal)
    w = VoyagerWindow(); w.show(); sys.exit(app.exec_())

if __name__ == "__main__":
    main()