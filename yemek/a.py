#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yemek Tarif Platformu - Gelişmiş PyQt5 Uygulaması
Admin ve Kullanıcı Paneli + Gece/Gündüz Modu
Corelytics-style Modern Dashboard UI
"""

import sys
import hashlib
import random
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


# ─────────────────────────── YARDIMCI ───────────────────────────

def hash_sifre(sifre: str) -> str:
    return hashlib.sha256(sifre.encode()).hexdigest()


# ─────────────────────────── VERİ MODELLERİ ───────────────────────────

class Malzeme:
    def __init__(self, malzeme_adi, miktar, birim="adet"):
        self.malzeme_adi = malzeme_adi
        self.miktar = miktar
        self.birim = birim

    def to_dict(self):
        return {"malzeme_adi": self.malzeme_adi, "miktar": self.miktar, "birim": self.birim}

    @staticmethod
    def from_dict(d):
        return Malzeme(d["malzeme_adi"], d["miktar"], d.get("birim", "adet"))


class Tarif:
    def __init__(self, tarif_id, tarif_adi, kategori, hazirlama_suresi,
                 malzemeler=None, talimatlar="", puan=0.0, puan_sayisi=0,
                 gorsel_emoji="🍽️", ekleyen="admin", tarih=None, gorsel_yolu=None):
        self.tarif_id = tarif_id
        self.tarif_adi = tarif_adi
        self.kategori = kategori
        self.hazirlama_suresi = hazirlama_suresi
        self.malzemeler = malzemeler or []
        self.talimatlar = talimatlar
        self.puan = puan
        self.puan_sayisi = puan_sayisi
        self.gorsel_emoji = gorsel_emoji
        self.gorsel_yolu = gorsel_yolu or ""   # ← yeni: gerçek görsel dosya yolu
        self.ekleyen = ekleyen
        self.tarih = tarih or datetime.now().strftime("%d.%m.%Y")
        self.yorumlar = []
        self.goruntuleme = random.randint(50, 500)

    def tarif_guncelle(self, tarif_adi=None, kategori=None, hazirlama_suresi=None,
                       malzemeler=None, talimatlar=None, gorsel_yolu=None):
        if tarif_adi: self.tarif_adi = tarif_adi
        if kategori: self.kategori = kategori
        if hazirlama_suresi is not None: self.hazirlama_suresi = hazirlama_suresi
        if malzemeler is not None: self.malzemeler = malzemeler
        if talimatlar is not None: self.talimatlar = talimatlar
        if gorsel_yolu is not None: self.gorsel_yolu = gorsel_yolu

    def to_dict(self):
        return {
            "tarif_id": self.tarif_id, "tarif_adi": self.tarif_adi,
            "kategori": self.kategori, "hazirlama_suresi": self.hazirlama_suresi,
            "malzemeler": [m.to_dict() for m in self.malzemeler],
            "talimatlar": self.talimatlar, "puan": self.puan,
            "puan_sayisi": self.puan_sayisi, "gorsel_emoji": self.gorsel_emoji,
            "gorsel_yolu": self.gorsel_yolu,
            "ekleyen": self.ekleyen, "tarih": self.tarih,
            "yorumlar": self.yorumlar, "goruntuleme": self.goruntuleme,
        }

    @staticmethod
    def from_dict(d):
        t = Tarif(
            tarif_id=d["tarif_id"], tarif_adi=d["tarif_adi"],
            kategori=d["kategori"], hazirlama_suresi=d["hazirlama_suresi"],
            malzemeler=[Malzeme.from_dict(m) for m in d.get("malzemeler", [])],
            talimatlar=d.get("talimatlar", ""), puan=d.get("puan", 0.0),
            puan_sayisi=d.get("puan_sayisi", 0), gorsel_emoji=d.get("gorsel_emoji", "🍽️"),
            ekleyen=d.get("ekleyen", "admin"), tarih=d.get("tarih", ""),
            gorsel_yolu=d.get("gorsel_yolu", ""),
        )
        t.yorumlar = d.get("yorumlar", [])
        t.goruntuleme = d.get("goruntuleme", random.randint(50, 500))
        return t


class Kullanici:
    def __init__(self, kullanici_id, ad, email, sifre_hash, rol="kullanici"):
        self.kullanici_id = kullanici_id
        self.ad = ad
        self.email = email
        self.sifre_hash = sifre_hash
        self.rol = rol
        self.favori_tarifler = []
        self.puan_verdigi_tarifler = {}
        self.profil_emoji = "👤"
        self.kayit_tarihi = datetime.now().strftime("%d.%m.%Y")
        self.aktif = True

    def sifre_dogru_mu(self, sifre: str) -> bool:
        return self.sifre_hash == hash_sifre(sifre)

    def sifre_degistir(self, yeni_sifre: str):
        self.sifre_hash = hash_sifre(yeni_sifre)

    def tarif_degerlendir(self, tarif, puan, db_tarifler):
        if tarif.tarif_id in self.puan_verdigi_tarifler:
            eski = self.puan_verdigi_tarifler[tarif.tarif_id]
            toplam = tarif.puan * tarif.puan_sayisi - eski + puan
            tarif.puan = toplam / tarif.puan_sayisi
        else:
            toplam = tarif.puan * tarif.puan_sayisi + puan
            tarif.puan_sayisi += 1
            tarif.puan = toplam / tarif.puan_sayisi
        self.puan_verdigi_tarifler[tarif.tarif_id] = puan

    def to_dict(self):
        return {
            "kullanici_id": self.kullanici_id, "ad": self.ad,
            "email": self.email, "sifre_hash": self.sifre_hash,
            "rol": self.rol, "favori_tarifler": self.favori_tarifler,
            "puan_verdigi_tarifler": self.puan_verdigi_tarifler,
            "profil_emoji": self.profil_emoji, "kayit_tarihi": self.kayit_tarihi,
            "aktif": self.aktif,
        }

    @staticmethod
    def from_dict(d):
        k = Kullanici(d["kullanici_id"], d["ad"], d["email"], d["sifre_hash"], d.get("rol", "kullanici"))
        k.favori_tarifler = d.get("favori_tarifler", [])
        k.puan_verdigi_tarifler = d.get("puan_verdigi_tarifler", {})
        k.profil_emoji = d.get("profil_emoji", "👤")
        k.kayit_tarihi = d.get("kayit_tarihi", "")
        k.aktif = d.get("aktif", True)
        return k


# ─────────────────────────── VERİTABANI ───────────────────────────

class Veritabani:
    def __init__(self):
        self.tarifler = {}
        self.kullanicilar = {}
        self.aktivite_logu = []
        self.bekleyen_tarifler = {}   # onay bekleyen (id -> Tarif)
        self._varsayilan_yukle()

    def _varsayilan_yukle(self):
        admin = Kullanici(1, "Admin", "admin", hash_sifre("admin"), "admin")
        user1 = Kullanici(2, "Eslem", "eslem@email.com", hash_sifre("123456"))
        user2 = Kullanici(3, "Navid", "navid@email.com", hash_sifre("123456"))
        user3 = Kullanici(4, "Zeynep", "zeynep@email.com", hash_sifre("123456"))
        self.kullanicilar = {1: admin, 2: user1, 3: user2, 4: user3}

        tarifler_data = [
            ("Menemen", "Kahvaltı", 20, "🍳",
             [("Yumurta", 3, "adet"), ("Domates", 2, "adet"), ("Biber", 2, "adet"), ("Soğan", 1, "adet"), ("Zeytinyağı", 2, "yemek kaşığı")],
             "1. Soğanı yağda kavurun.\n2. Domates ve biberleri ekleyin, pişirin.\n3. Yumurtaları kırıp karıştırın.\n4. Tuz ve baharatla tatlandırın.", 4.7, 23, "Admin"),
            ("Mercimek Çorbası", "Çorba", 40, "🥣",
             [("Kırmızı Mercimek", 1, "su bardağı"), ("Soğan", 1, "adet"), ("Havuç", 1, "adet"), ("Tereyağı", 2, "yemek kaşığı"), ("Tuz", 1, "tatlı kaşığı")],
             "1. Soğan ve havucu soteleyin.\n2. Mercimeği ekleyip su ilave edin.\n3. Pişince blenderdan geçirin.\n4. Üzerine kızdırılmış tereyağı gezdirin.", 4.9, 47, "Admin"),
            ("Karnıyarık", "Ana Yemek", 60, "🍆",
             [("Patlıcan", 4, "adet"), ("Kıyma", 250, "gram"), ("Soğan", 2, "adet"), ("Domates", 3, "adet"), ("Sarımsak", 3, "diş")],
             "1. Patlıcanları soyup kızartın.\n2. Kıymayı soğanla kavurun.\n3. Patlıcanları ortadan yarak kıymayı doldurun.\n4. Üzerine domates koyup fırında pişirin.", 4.8, 35, "Eslem"),
            ("Sütlaç", "Tatlı", 45, "🍮",
             [("Pirinç", 0.5, "su bardağı"), ("Süt", 1, "litre"), ("Şeker", 1, "su bardağı"), ("Nişasta", 2, "yemek kaşığı"), ("Vanilya", 1, "paket")],
             "1. Pirinci haşlayın.\n2. Sütü şekerle kaynatın.\n3. Nişastayı ekleyin ve karıştırın.\n4. Fırında üzerini kızartın.", 4.6, 28, "Admin"),
            ("Sigara Böreği", "Kahvaltı", 30, "🥐",
             [("Yufka", 5, "adet"), ("Beyaz Peynir", 200, "gram"), ("Maydanoz", 1, "demet"), ("Yumurta", 1, "adet"), ("Kızartma Yağı", 2, "su bardağı")],
             "1. Peyniri maydanozla karıştırın.\n2. Yufkaları dörde bölün.\n3. Her parçaya iç doldurup rulo yapın.\n4. Kızgın yağda kızartın.", 4.5, 19, "Navid"),
            ("Tavuk Sote", "Ana Yemek", 35, "🍗",
             [("Tavuk Göğsü", 500, "gram"), ("Biber", 2, "adet"), ("Mantar", 200, "gram"), ("Sarımsak", 3, "diş"), ("Zeytinyağı", 3, "yemek kaşığı")],
             "1. Tavuğu küp kesin.\n2. Sarımsak ve biberi kavurun.\n3. Tavuğu ekleyip pişirin.\n4. Mantarları ekleyin ve servis yapın.", 4.4, 31, "Eslem"),
            ("Ayran", "İçecek", 5, "🥛",
             [("Yoğurt", 2, "su bardağı"), ("Su", 1, "su bardağı"), ("Tuz", 1, "tutam")],
             "1. Yoğurdu blendara alın.\n2. Su ekleyip çırpın.\n3. Tuz ilave edin.\n4. Soğuk servis yapın.", 4.3, 15, "Admin"),
            ("Baklava", "Tatlı", 120, "🍯",
             [("Yufka", 1, "paket"), ("Ceviz", 500, "gram"), ("Tereyağı", 250, "gram"), ("Şeker", 2, "su bardağı"), ("Su", 1, "su bardağı")],
             "1. Tepsiye yağlanmış yufkaları serin.\n2. Ceviz serpin.\n3. Katlayıp kesin.\n4. Fırınlayıp şerbetini gezdirin.", 4.9, 52, "Admin"),
            ("Cacık", "Salata", 10, "🥗",
             [("Yoğurt", 2, "su bardağı"), ("Salatalık", 1, "adet"), ("Sarımsak", 2, "diş"), ("Dereotu", 1, "tutam"), ("Zeytinyağı", 1, "yemek kaşığı")],
             "1. Salatalığı rendeleyin.\n2. Yoğurtla karıştırın.\n3. Sarımsak ekleyin.\n4. Dereotu ve zeytinyağıyla süsleyin.", 4.5, 22, "Zeynep"),
            ("İmam Bayıldı", "Ana Yemek", 55, "🫑",
             [("Patlıcan", 3, "adet"), ("Soğan", 2, "adet"), ("Domates", 3, "adet"), ("Sarımsak", 4, "diş"), ("Zeytinyağı", 4, "yemek kaşığı")],
             "1. Patlıcanları yağda kızartın.\n2. Soğan, sarımsak ve domatesi kavurun.\n3. Patlıcanların içini doldurun.\n4. Fırında pişirin.", 4.7, 18, "Navid"),
            ("Köfte", "Ana Yemek", 30, "🥩",
             [("Kıyma", 500, "gram"), ("Soğan", 1, "adet"), ("Ekmek İçi", 2, "dilim"), ("Yumurta", 1, "adet"), ("Tuz", 1, "tatlı kaşığı"), ("Karabiber", 1, "tatlı kaşığı")],
             "1. Kıymayı rendelenmiş soğan, ekmek içi ve yumurtayla yoğurun.\n2. Baharat ekleyip karıştırın.\n3. Yuvarlak şekil verin.\n4. Mangal veya tavada pişirin.", 4.8, 42, "Eslem"),
            ("Domates Çorbası", "Çorba", 25, "🍅",
             [("Domates", 6, "adet"), ("Soğan", 1, "adet"), ("Sarımsak", 2, "diş"), ("Tereyağı", 1, "yemek kaşığı"), ("Tuz", 1, "tatlı kaşığı"), ("Şeker", 1, "tatlı kaşığı")],
             "1. Soğan ve sarımsağı tereyağında kavurun.\n2. Domatesleri ekleyip 15 dakika pişirin.\n3. Blenderdan geçirin.\n4. Tuz ve şekerle tatlandırın.", 4.5, 27, "Admin"),
            ("Sütlü Pirinç Pilavı", "Ana Yemek", 35, "🍚",
             [("Pirinç", 2, "su bardağı"), ("Su", 3, "su bardağı"), ("Tereyağı", 2, "yemek kaşığı"), ("Tuz", 1, "tatlı kaşığı")],
             "1. Pirinci yıkayın.\n2. Tereyağını eritip pirinci kavurun.\n3. Suyu ve tuzu ekleyin.\n4. Kısık ateşte kapağı kapalı pişirin.", 4.4, 33, "Zeynep"),
            ("Limonata", "İçecek", 10, "🍋",
             [("Limon", 4, "adet"), ("Su", 1, "litre"), ("Şeker", 3, "yemek kaşığı"), ("Nane", 1, "tutam")],
             "1. Limonları sıkın.\n2. Suyu şekerle karıştırın.\n3. Limon suyunu ekleyin.\n4. Nane ile süsleyip buzla servis yapın.", 4.6, 21, "Admin"),
            ("Kabak Mücveri", "Kahvaltı", 25, "🥦",
             [("Kabak", 3, "adet"), ("Un", 3, "yemek kaşığı"), ("Yumurta", 2, "adet"), ("Beyaz Peynir", 100, "gram"), ("Maydanoz", 1, "demet")],
             "1. Kabakları rendeleyin ve sıkın.\n2. Un, yumurta ve peyniri ekleyin.\n3. Maydanoz ve tuzla karıştırın.\n4. Yağda kızartın.", 4.5, 19, "Navid"),
            ("Tavuk Çorbası", "Çorba", 45, "🍜",
             [("Tavuk Göğsü", 300, "gram"), ("Arpa Şehriyesi", 1, "su bardağı"), ("Havuç", 1, "adet"), ("Soğan", 1, "adet"), ("Tuz", 1, "tatlı kaşığı")],
             "1. Tavuğu haşlayın ve parçalayın.\n2. Havuç ve soğanı doğrayıp ekleyin.\n3. Şehriyeyi ekleyin.\n4. Tuzlayıp pişirin.", 4.7, 38, "Eslem"),
            ("Çikolatalı Kek", "Tatlı", 60, "🎂",
             [("Un", 2, "su bardağı"), ("Şeker", 1.5, "su bardağı"), ("Kakao", 0.5, "su bardağı"), ("Yumurta", 3, "adet"), ("Süt", 1, "su bardağı"), ("Zeytinyağı", 0.5, "su bardağı")],
             "1. Kuru malzemeleri karıştırın.\n2. Yumurta, süt ve yağı ekleyin.\n3. Yağlanmış kalıba dökün.\n4. 180°C'de 35 dakika pişirin.", 4.9, 55, "Admin"),
            ("Gavurdağı Salatası", "Salata", 15, "🥗",
             [("Domates", 3, "adet"), ("Salatalık", 2, "adet"), ("Soğan", 1, "adet"), ("Maydanoz", 1, "demet"), ("Ceviz", 100, "gram"), ("Nar Ekşisi", 2, "yemek kaşığı")],
             "1. Domatesi ve salatalığı doğrayın.\n2. Soğan ve maydanozu ekleyin.\n3. Cevizi kırın ve ilave edin.\n4. Nar ekşisi ve zeytinyağıyla karıştırın.", 4.6, 24, "Zeynep"),
            ("Fırında Patates", "Ana Yemek", 50, "🥔",
             [("Patates", 6, "adet"), ("Zeytinyağı", 3, "yemek kaşığı"), ("Sarımsak", 3, "diş"), ("Kekik", 1, "tatlı kaşığı"), ("Tuz", 1, "tatlı kaşığı")],
             "1. Patatesleri soyup dilimleyin.\n2. Yağ, sarımsak ve baharatlarla karıştırın.\n3. Fırın tepsisine yayın.\n4. 200°C'de 40 dakika pişirin.", 4.5, 29, "Navid"),
            ("Pekmezli Gözleme", "Kahvaltı", 20, "🫓",
             [("Yufka", 2, "adet"), ("Pekmez", 3, "yemek kaşığı"), ("Tereyağı", 1, "yemek kaşığı"), ("Ceviz", 50, "gram")],
             "1. Yufkayı büyük kare kesin.\n2. Bir tarafına pekmez ve ceviz sürün.\n3. Katlayıp tereyağında kızartın.\n4. Sıcak servis yapın.", 4.4, 16, "Admin"),
            ("Maş Fasulyesi Yemeği", "Ana Yemek", 60, "🫘",
             [("Maş Fasulyesi", 1, "su bardağı"), ("Soğan", 1, "adet"), ("Domates", 2, "adet"), ("Zeytinyağı", 2, "yemek kaşığı"), ("Tuz", 1, "tatlı kaşığı")],
             "1. Fasulyeleri ıslatıp haşlayın.\n2. Soğanı yağda kavurun.\n3. Domates ve fasulyeleri ekleyin.\n4. Kısık ateşte pişirin.", 4.3, 14, "Eslem"),
        ]

        for i, (ad, kat, sure, emoji, malzemeler, talimat, puan, puan_sayisi, ekleyen) in enumerate(tarifler_data, 1):
            malz_list = [Malzeme(m[0], m[1], m[2]) for m in malzemeler]
            t = Tarif(i, ad, kat, sure, malz_list, talimat, puan, puan_sayisi, emoji, ekleyen)
            t.yorumlar = [
                {"kullanici": "Eslem", "yorum": "Harika bir tarif, herkese tavsiye ederim!", "tarih": "01.01.2025"},
                {"kullanici": "Navid", "yorum": "Ailem çok beğendi, teşekkürler.", "tarih": "15.01.2025"},
            ]
            self.tarifler[i] = t

        # Aktivite logu
        self.aktivite_logu = [
            {"tip": "tarif", "mesaj": "Eslem yeni tarif ekledi: Karnıyarık", "zaman": "2 saat önce", "renk": "#4CAF7D"},
            {"tip": "kullanici", "mesaj": "Zeynep sisteme kaydoldu", "zaman": "4 saat önce", "renk": "#5B9CF6"},
            {"tip": "yorum", "mesaj": "Navid Mercimek Çorbası'na yorum yaptı", "zaman": "5 saat önce", "renk": "#F97316"},
            {"tip": "puan", "mesaj": "Baklava tarifi 5 yıldız aldı!", "zaman": "1 gün önce", "renk": "#F59E0B"},
            {"tip": "tarif", "mesaj": "Admin yeni tarif ekledi: Ayran", "zaman": "2 gün önce", "renk": "#3B82F6"},
        ]

    def kullanici_bul(self, email: str, sifre: str):
        for k in self.kullanicilar.values():
            if k.email == email and k.sifre_dogru_mu(sifre):
                return k
        return None

    def email_mevcut_mu(self, email: str) -> bool:
        return any(k.email == email for k in self.kullanicilar.values())

    def sonraki_tarif_id(self):
        tum_idler = list(self.tarifler.keys()) + list(self.bekleyen_tarifler.keys())
        return max(tum_idler, default=0) + 1

    def sonraki_kullanici_id(self):
        return max(self.kullanicilar.keys(), default=0) + 1


# ─────────────────────────── TEMA SİSTEMİ ───────────────────────────

GECE_MODU = {
    "bg_primary": "#111314",
    "bg_secondary": "#161A1D",
    "bg_card": "#1C2127",
    "bg_hover": "#21272E",
    "accent": "#4CAF7D",
    "accent_hover": "#66BB8F",
    "accent_secondary": "#5B9CF6",
    "neon_cyan": "#5B9CF6",
    "neon_purple": "#CE93D8",
    "neon_green": "#4CAF7D",
    "text_primary": "#E8EAED",
    "text_secondary": "#9AA0A6",
    "text_muted": "#5F6368",
    "border": "#2D3339",
    "border_neon": "#4CAF7D",
    "border_purple": "#5B9CF6",
    "success": "#4CAF7D",
    "danger": "#F28B82",
    "warning": "#FDD663",
    "star": "#FDD663",
    "sidebar_active_bg": "#4CAF7D1A",
    "sidebar_active_border": "#4CAF7D",
    "chart1": "#4CAF7D",
    "chart2": "#5B9CF6",
    "chart3": "#F28B82",
    "chart4": "#FDD663",
    "chart5": "#CE93D8",
    "gradient_start": "#4CAF7D",
    "gradient_end": "#5B9CF6",
}

GUNDUZ_MODU = {
    "bg_primary": "#F5F7FA",
    "bg_secondary": "#EAECF0",
    "bg_card": "#FFFFFF",
    "bg_hover": "#EDF0F5",
    "accent": "#2E8B57",
    "accent_hover": "#3CAF72",
    "accent_secondary": "#2563EB",
    "neon_cyan": "#2563EB",
    "neon_purple": "#7C3AED",
    "neon_green": "#2E8B57",
    "text_primary": "#111827",
    "text_secondary": "#4B5563",
    "text_muted": "#9CA3AF",
    "border": "#D1D5DB",
    "border_neon": "#2E8B57",
    "border_purple": "#2563EB",
    "success": "#16A34A",
    "danger": "#DC2626",
    "warning": "#D97706",
    "star": "#D97706",
    "sidebar_active_bg": "#2E8B5718",
    "sidebar_active_border": "#2E8B57",
    "chart1": "#2E8B57",
    "chart2": "#2563EB",
    "chart3": "#DC2626",
    "chart4": "#D97706",
    "chart5": "#7C3AED",
    "gradient_start": "#2E8B57",
    "gradient_end": "#2563EB",
}


def get_stylesheet(tema):
    T = tema
    return f"""
    QMainWindow, QDialog {{
        background-color: {T['bg_primary']};
        color: {T['text_primary']};
        font-family: 'Segoe UI', 'Inter', Arial;
    }}
    QWidget {{
        background-color: transparent;
        color: {T['text_primary']};
        font-family: 'Segoe UI', 'Inter', Arial;
        font-size: 13px;
    }}
    QScrollArea {{ border: none; background-color: transparent; }}
    QScrollBar:vertical {{
        background: transparent;
        width: 5px; border-radius: 2px; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {T['border']}; border-radius: 2px; min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {T['text_muted']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: {T['bg_secondary']};
        height: 6px; border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {T['text_muted']}; border-radius: 3px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {T['bg_secondary']};
        border: 1.5px solid {T['border']};
        border-radius: 8px;
        padding: 8px 12px;
        color: {T['text_primary']};
        selection-background-color: {T['accent']};
    }}
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {T['accent']};
        background-color: {T['bg_card']};
    }}
    QComboBox {{
        background-color: {T['bg_secondary']};
        border: 1.5px solid {T['border']};
        border-radius: 8px;
        padding: 8px 12px;
        color: {T['text_primary']};
    }}
    QComboBox:focus {{ border-color: {T['accent']}; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox::down-arrow {{ width: 10px; height: 10px; }}
    QComboBox QAbstractItemView {{
        background-color: {T['bg_card']};
      
        selection-background-color: {T['accent']};
        color: {T['text_primary']};
        border-radius: 6px; padding: 4px;
    }}
    QPushButton {{
        background-color: {T['accent']};
        color: white; border: none; border-radius: 8px;
        padding: 9px 20px; font-weight: 600; font-size: 13px;
    }}
    QPushButton:hover {{ background-color: {T['accent_hover']}; }}
    QPushButton:pressed {{ background-color: {T['accent_hover']}; }}
    QPushButton:disabled {{ background-color: {T['text_muted']}; color: {T['bg_secondary']}; }}
    QPushButton#secondary_btn {{
        background-color: transparent;
        color: {T['text_primary']};
        border: 1.5px solid {T['border']};
    }}
    QPushButton#secondary_btn:hover {{
        background-color: {T['bg_hover']};
        border-color: {T['accent']}66;
        color: {T['accent']};
    }}
    QPushButton#secondary_btn:checked {{
        background-color: {T['sidebar_active_bg']};
        border-left: 3px solid {T['sidebar_active_border']};
        color: {T['accent']};
        font-weight: 700;
        border-top: 1px solid {T['border']};
        border-right: 1px solid {T['border']};
        border-bottom: 1px solid {T['border']};
    }}
    QPushButton#danger_btn {{ background-color: {T['danger']}; color: white; }}
    QPushButton#danger_btn:hover {{ background-color: #b91c1c; }}
    QPushButton#success_btn {{ background-color: {T['success']}; color: white; }}
    QPushButton#success_btn:hover {{ background-color: #15803d; }}
    QPushButton#ghost_btn {{
        background-color: transparent; color: {T['text_secondary']};
        border: none; padding: 6px 12px;
    }}
    QPushButton#ghost_btn:hover {{ color: {T['accent']}; background-color: {T['bg_hover']}; }}
    QTableWidget {{
        background-color: {T['bg_card']};
        border: none;
        border-radius: 8px;
        gridline-color: {T['border']};
        color: {T['text_primary']};
        alternate-background-color: transparent;
    }}
    QTableWidget::item {{ padding: 8px; border: none; }}
    QTableWidget::item:selected {{
        background-color: {T['accent']}22;
        color: {T['text_primary']};
        border-left: 2px solid {T['accent']};
    }}
    QHeaderView::section {{
        background-color: {T['bg_secondary']};
        color: {T['text_secondary']};
        border: none;
        border-bottom: 2px solid {T['border']};
        padding: 10px 8px;
        font-weight: 700; font-size: 11px;
        letter-spacing: 0.8px; text-transform: uppercase;
    }}
    QTabWidget::pane {{
        border-radius: 10px;
        background-color: {T['bg_card']};
        margin-top: -1px;
    }}
    QTabBar::tab {{
        background-color: {T['bg_secondary']};
        color: {T['text_secondary']};
    
        border-bottom: none;
        padding: 10px 20px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 4px; font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background-color: {T['bg_card']};
        color: {T['accent']}; font-weight: 700;
    }}
    QListWidget {{
        background-color: {T['bg_card']};
       
        border-radius: 10px; color: {T['text_primary']};
    }}
    QListWidget::item {{ padding: 8px 12px; border-radius: 6px; }}
    QListWidget::item:selected {{ background-color: {T['accent']}33; color: {T['text_primary']}; }}
    QListWidget::item:hover {{ background-color: {T['bg_hover']}; }}
    QLabel#header_label {{
        font-size: 16px; font-weight: 700;
        color: {T['text_primary']}; background: transparent;
    }}
    QLabel#subheader_label {{
        font-size: 13px; color: {T['text_secondary']}; background: transparent;
    }}
    QLabel#accent_label {{
        color: {T['accent']}; font-weight: 700; background: transparent;
    }}
    QFrame#card_frame {{
        background-color: {T['bg_card']};
        border: 1px solid {T['border']};
        border-radius: 8px;
    }}
    QFrame#card_frame_highlight {{
        background-color: {T['bg_card']};
        border: 1.5px solid {T['accent']};
        border-radius: 14px;
    }}
    QFrame#sidebar_frame {{
        background-color: {T['bg_secondary']};
        border-right: 1px solid {T['border']};
    }}
    QFrame#topbar_frame {{
        background-color: {T['bg_secondary']};
        border-bottom: 1px solid {T['border']};
    }}
    QProgressBar {{
        background-color: {T['bg_secondary']};
        border-radius: 5px; height: 10px;
        text-align: center; font-size: 10px; color: {T['text_primary']};
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {T['accent']}, stop:1 {T['accent_secondary']});
        border-radius: 4px;
    }}
    QSlider::groove:horizontal {{
        height: 6px; background: {T['border']}; border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {T['accent']}; width: 18px; height: 18px;
        margin: -6px 0; border-radius: 9px; border: 2px solid {T['bg_card']};
    }}
    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {T['accent']}, stop:1 {T['accent_secondary']});
        border-radius: 3px;
    }}
    QMessageBox {{ background-color: {T['bg_card']}; color: {T['text_primary']}; }}
    QCheckBox {{ spacing: 8px; color: {T['text_primary']}; background: transparent; }}
    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border: 2px solid {T['border']};
        border-radius: 4px; background: {T['bg_secondary']};
    }}
    QCheckBox::indicator:checked {{
        background: {T['accent']}; border-color: {T['accent']};
    }}
    QGroupBox {{
      
        margin-top: 12px; font-weight: 600;
        color: {T['text_secondary']}; padding-top: 8px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 12px; top: -2px;
        background: {T['bg_card']}; padding: 0 6px;
    }}
    QToolTip {{
        background-color: {T['bg_card']};
        color: {T['text_primary']};
        border-radius: 6px; padding: 4px 8px;
        font-size: 12px;
    }}
    """


# ─────────────────────────── GÖZ İKONU WİDGET ───────────────────────────

class GozIkonu(QWidget):
    """Şifre göster/gizle için özel çizimli göz ikonu"""
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._goster = False
        self.setFixedSize(42, 48)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Şifreyi göster / gizle")

    def is_goster(self):
        return self._goster

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._goster = not self._goster
            self.update()
            self.toggled.emit(self._goster)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        cx, cy = W // 2, H // 2

        if self.underMouse():
            painter.setBrush(QBrush(QColor(189, 147, 249, 50)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(2, 4, W - 4, H - 8, 8, 8)

        color = QColor(255, 255, 255, 200) if self._goster else QColor(255, 255, 255, 110)
        pen = QPen(color, 1.8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        eye_w, eye_h = 18, 11
        path = QPainterPath()
        path.moveTo(cx - eye_w, cy)
        path.cubicTo(cx - eye_w, cy - eye_h, cx - 4, cy - eye_h, cx, cy - eye_h // 2)
        path.cubicTo(cx + 4, cy - eye_h, cx + eye_w, cy - eye_h, cx + eye_w, cy)
        path.cubicTo(cx + eye_w, cy + eye_h, cx + 4, cy + eye_h, cx, cy + eye_h // 2)
        path.cubicTo(cx - 4, cy + eye_h, cx - eye_w, cy + eye_h, cx - eye_w, cy)
        painter.drawPath(path)

        if self._goster:
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), 4, 4)
            painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
            painter.drawEllipse(QPointF(cx + 1.5, cy - 1.5), 1.2, 1.2)
        else:
            pen2 = QPen(color, 1.8)
            pen2.setCapStyle(Qt.RoundCap)
            painter.setPen(pen2)
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(QPointF(cx - 10, cy + 6), QPointF(cx + 10, cy - 6))

        painter.end()

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()


# ─────────────────────────── MİNİ BAR GRAFİK WİDGET ───────────────────────────

class MiniBarChart(QWidget):
    """Corelytics-style inline mini bar chart"""
    def __init__(self, veriler, renkler=None, yukseklik=60, parent=None):
        super().__init__(parent)
        self.veriler = veriler
        self.renkler = renkler or ["#F97316"] * len(veriler)
        self.setFixedHeight(yukseklik)
        self.setMinimumWidth(len(veriler) * 14)

    def paintEvent(self, event):
        if not self.veriler:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height() - 4
        n = len(self.veriler)
        max_val = max(self.veriler) if max(self.veriler) > 0 else 1
        bar_w = max(6, (w - (n - 1) * 4) // n)
        gap = 4

        for i, val in enumerate(self.veriler):
            bar_h = int((val / max_val) * h)
            x = i * (bar_w + gap)
            y = h - bar_h + 2
            color = QColor(self.renkler[i % len(self.renkler)])
            # Gradient fill
            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0, color)
            c2 = QColor(color)
            c2.setAlpha(60)
            grad.setColorAt(1, c2)
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            rect = QRectF(x, y, bar_w, bar_h)
            painter.drawRoundedRect(rect, 3, 3)
        painter.end()


# ─────────────────────────── MİNİ ALAN GRAFİK WİDGET ───────────────────────────

class MiniLineChart(QWidget):
    """Mini smooth line/area chart"""
    def __init__(self, veriler, renk="#F97316", yukseklik=60, parent=None):
        super().__init__(parent)
        self.veriler = veriler
        self.renk = renk
        self.setFixedHeight(yukseklik)

    def paintEvent(self, event):
        if len(self.veriler) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height() - 4
        mn = min(self.veriler)
        mx = max(self.veriler)
        rng = mx - mn if mx != mn else 1

        def px(i): return int(i * (w - 1) / (len(self.veriler) - 1))
        def py(v): return int(h - (v - mn) / rng * (h - 4)) + 2

        pts = [QPointF(px(i), py(v)) for i, v in enumerate(self.veriler)]

        # Area fill
        path = QPainterPath()
        path.moveTo(pts[0].x(), h + 2)
        path.lineTo(pts[0])
        for p in pts[1:]:
            path.lineTo(p)
        path.lineTo(pts[-1].x(), h + 2)
        path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, h)
        c = QColor(self.renk)
        c2 = QColor(self.renk)
        c2.setAlpha(0)
        grad.setColorAt(0, QColor(self.renk + "55"))
        grad.setColorAt(1, c2)
        painter.fillPath(path, QBrush(grad))

        # Line
        line_path = QPainterPath()
        line_path.moveTo(pts[0])
        for p in pts[1:]:
            line_path.lineTo(p)
        painter.setPen(QPen(QColor(self.renk), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(line_path)

        # End dot
        painter.setBrush(QBrush(QColor(self.renk)))
        painter.setPen(QPen(QColor("#0D1117"), 2))
        painter.drawEllipse(pts[-1], 4, 4)
        painter.end()


# ─────────────────────────── DONUT GRAFİK WİDGET ───────────────────────────

class DonutChart(QWidget):
    """Mini donut chart for category distribution"""
    def __init__(self, veriler, renkler, boyut=120, parent=None):
        super().__init__(parent)
        self.veriler = veriler
        self.renkler = renkler
        self.setFixedSize(boyut, boyut)

    def paintEvent(self, event):
        if not self.veriler:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        margin = 8
        rect = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)
        total = sum(self.veriler)
        if total == 0:
            return

        start = -90 * 16
        for i, val in enumerate(self.veriler):
            span = int(val / total * 360 * 16)
            color = QColor(self.renkler[i % len(self.renkler)])
            painter.setPen(QPen(color, 14, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(rect, start, span)
            start += span
        painter.end()


# ─────────────────────────── STAT KARTI (GELİŞMİŞ) ───────────────────────────

class StatKarti(QFrame):
    def __init__(self, icon, value, label, color, trend=None, chart_data=None, tema=None, parent=None):
        super().__init__(parent)
        self.setObjectName("card_frame")
        self.setMinimumHeight(120)
        T = tema or GECE_MODU

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        # Top row: icon + trend badge
        top = QHBoxLayout()
        icon_bg = QFrame()
        icon_bg.setFixedSize(42, 42)
        icon_bg.setStyleSheet(f"background: {color}22; border-radius: 11px;")
        il = QVBoxLayout(icon_bg)
        il.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 20px; background: transparent; color: {color};")
        il.addWidget(icon_lbl)
        top.addWidget(icon_bg)
        top.addStretch()

        if trend:
            trend_lbl = QLabel(trend)
            trend_color = T['success'] if "+" in trend else T['danger']
            trend_lbl.setStyleSheet(f"""
                background: {trend_color}22; color: {trend_color};
                border-radius: 10px; padding: 2px 8px;
                font-size: 11px; font-weight: 700;
            """)
            top.addWidget(trend_lbl)
        layout.addLayout(top)

        # Value
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {color}; background: transparent;")
        layout.addWidget(val_lbl)

        # Label + mini chart row
        bot = QHBoxLayout()
        lbl_w = QLabel(label)
        lbl_w.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 500; background: transparent;")
        bot.addWidget(lbl_w)
        bot.addStretch()

        if chart_data:
            mini = MiniBarChart(chart_data, [color] * len(chart_data), yukseklik=36)
            mini.setFixedWidth(80)
            bot.addWidget(mini)
        layout.addLayout(bot)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


# ─────────────────────────── AREA CHART WIDGET ───────────────────────────

class AreaChartWidget(QWidget):
    """Gerçek tarif platformu verilerine dayalı alan grafiği"""
    def __init__(self, tema, db=None, parent=None):
        super().__init__(parent)
        self.tema = tema
        self.db = db
        self._guncelle_veri()
        self.colors = [tema['chart1'], tema['chart2'], tema['chart3']]

    def _guncelle_veri(self):
        """
        3 seri - Tarif platformu metriklerine dayalı:
          1) Tarif Puanları  — her tarifte ortalama puan * 50
          2) Oy Sayıları     — her tarifte oy sayısı * 10
          3) Görüntüleme     — her tarifte görüntüleme / 10
        """
        if self.db and self.db.tarifler:
            tarifler = list(self.db.tarifler.values())
            # en fazla 10 nokta al
            sample = tarifler[:10] if len(tarifler) >= 10 else tarifler
            while len(sample) < 10:
                sample = sample + sample   # tekrar doldur
            sample = sample[:10]
            self.months = [t.tarif_adi[:5] for t in sample]
            self.series = [
                [round(t.puan * 50) for t in sample],          # Tarif Puanı skalası
                [round(t.puan_sayisi * 10) for t in sample],   # Oy skalası
                [round(t.goruntuleme / 10) for t in sample],   # Görüntüleme skalası
            ]
            self.legends = ["Tarif Puanı ×50", "Oy Sayısı ×10", "Görüntüleme ÷10"]
        else:
            self.months = ["T1","T2","T3","T4","T5","T6","T7","T8","T9","T10"]
            self.series = [[0]*10, [0]*10, [0]*10]
            self.legends = ["Tarif Puanı", "Oy Sayısı", "Görüntüleme"]

    def paintEvent(self, event):
        T = self.tema
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        W = self.width()
        H = self.height()
        pad_l, pad_r, pad_t, pad_b = 40, 20, 10, 30

        all_vals = [v for s in self.series for v in s]
        min_v = 0
        max_v = max(all_vals) * 1.15 if all_vals and max(all_vals) > 0 else 1

        def tx(i):
            return pad_l + i * (W - pad_l - pad_r) / (len(self.months) - 1)

        def ty(v):
            return pad_t + (H - pad_t - pad_b) * (1 - (v - min_v) / (max_v - min_v))

        # Izgara
        grid_pen = QPen(QColor(T['border']))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for gi in range(5):
            y = pad_t + gi * (H - pad_t - pad_b) / 4
            painter.drawLine(int(pad_l), int(y), int(W - pad_r), int(y))

        # Her seri
        for si, (series, color) in enumerate(zip(self.series, self.colors)):
            pts = [QPointF(tx(i), ty(v)) for i, v in enumerate(series)]
            path = QPainterPath()
            path.moveTo(pts[0].x(), H - pad_b)
            path.lineTo(pts[0])
            for p in pts[1:]:
                path.lineTo(p)
            path.lineTo(pts[-1].x(), H - pad_b)
            path.closeSubpath()

            grad = QLinearGradient(0, pad_t, 0, H - pad_b)
            c = QColor(color); c.setAlpha(80)
            c2 = QColor(color); c2.setAlpha(0)
            grad.setColorAt(0.0, c)
            grad.setColorAt(1.0, c2)
            painter.fillPath(path, QBrush(grad))

            line_pen = QPen(QColor(color))
            line_pen.setWidth(2)
            line_pen.setCapStyle(Qt.RoundCap)
            line_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(line_pen)
            for i in range(len(pts) - 1):
                painter.drawLine(pts[i], pts[i + 1])

        # X ekseni
        painter.setPen(QColor(T['text_muted']))
        font = painter.font()
        font.setPixelSize(9)
        painter.setFont(font)
        for i, m in enumerate(self.months):
            x = int(tx(i))
            painter.drawText(x - 18, H - 2, 36, 16, Qt.AlignCenter, m)

        painter.end()


# ═══════════════════════════════════════════════════════
# ─────────── GAMING HUD WİDGET SINIFLAR ───────────────
# ═══════════════════════════════════════════════════════

class HUDCornerFrame(QWidget):
    """Görseldeki gibi köşe süslemeli cyberpunk çerçeve"""
    def __init__(self, parent=None, corner_color="#00E5FF", bg_color="#0D0D22",
                 border_color="#1A1A3A", corner_size=14, border_width=1):
        super().__init__(parent)
        self.corner_color = QColor(corner_color)
        self.bg_color = QColor(bg_color)
        self.border_color = QColor(border_color)
        self.corner_size = corner_size
        self.border_width = border_width

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        cs = self.corner_size

        # Arka plan
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, W, H)

        # Kenarlık
        pen = QPen(self.border_color, self.border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(1, 1, W-2, H-2)

        # Neon köşe köşebentleri - Görseldeki gibi
        neon_pen = QPen(self.corner_color, 2)
        painter.setPen(neon_pen)

        # Sol üst köşe
        painter.drawLine(0, cs, 0, 0)
        painter.drawLine(0, 0, cs, 0)

        # Sağ üst köşe
        painter.drawLine(W-cs, 0, W, 0)
        painter.drawLine(W, 0, W, cs)

        # Sol alt köşe
        painter.drawLine(0, H-cs, 0, H)
        painter.drawLine(0, H, cs, H)

        # Sağ alt köşe
        painter.drawLine(W-cs, H, W, H)
        painter.drawLine(W, H, W, H-cs)

        # Küçük dekor noktaları (görseldeki gibi)
        dot_pen = QPen(self.corner_color, 3)
        dot_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(dot_pen)

        # Üst orta dekor
        mid_x = W // 2
        for dx in [-8, 0, 8]:
            painter.drawPoint(mid_x + dx, 1)

        # Alt orta dekor
        for dx in [-8, 0, 8]:
            painter.drawPoint(mid_x + dx, H-1)

        painter.end()


class HUDTopBar(QWidget):
    """Sidebar için üst HUD profil alanı"""
    def __init__(self, kullanici, tema, parent=None):
        super().__init__(parent)
        self.kullanici = kullanici
        T = tema
        neon = T.get('border_neon', '#00E5FF')
        purple = T.get('accent', '#7B2FBE')
        self.setFixedHeight(160)

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Logo alanı
        logo_frame = QWidget()
        logo_frame.setFixedHeight(56)
        logo_frame.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {purple}44, stop:0.5 {neon}22, stop:1 {purple}44);
            border-bottom: 1px solid {neon}44;
        """)
        logo_hl = QHBoxLayout(logo_frame)
        logo_hl.setContentsMargins(16, 0, 16, 0)

        logo_icon = QLabel("🍳")
        logo_icon.setStyleSheet("font-size: 22px; background: transparent;")
        logo_hl.addWidget(logo_icon)
        logo_hl.addSpacing(8)

        logo_col = QVBoxLayout()
        logo_col.setSpacing(0)
        logo_title = QLabel("TARİFTİRİUM")
        logo_title.setStyleSheet(f"""
            font-size: 14px; font-weight: 900; letter-spacing: 2px;
            color: {neon}; background: transparent;
        """)
        logo_sub = QLabel("YEMEK TARIF PLATFORMU")
        logo_sub.setStyleSheet(f"""
            font-size: 7px; letter-spacing: 2px; font-weight: 700;
            color: {purple}; background: transparent;
        """)
        logo_col.addWidget(logo_title)
        logo_col.addWidget(logo_sub)
        logo_hl.addLayout(logo_col)
        logo_hl.addStretch()

        v.addWidget(logo_frame)

        # Profil alanı
        profil_frame = QWidget()
        profil_frame.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {purple}22, stop:1 {neon}11);
            border-bottom: 1px solid {neon}33;
        """)
        pl = QHBoxLayout(profil_frame)
        pl.setContentsMargins(16, 10, 16, 10)
        pl.setSpacing(12)

        # Avatar - köşebentli
        av_container = QWidget()
        av_container.setFixedSize(52, 52)
        av_container.setStyleSheet("background: transparent;")
        av_layout = QVBoxLayout(av_container)
        av_layout.setContentsMargins(2, 2, 2, 2)

        avatar = QLabel(kullanici.ad[0].upper() if kullanici.ad else "?")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(48, 48)
        avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {purple}, stop:1 {neon});
            color: white; font-size: 20px; font-weight: 900;
            border-radius: 4px;
        """)
        av_layout.addWidget(avatar)
        pl.addWidget(av_container)

        info_v = QVBoxLayout()
        info_v.setSpacing(3)
        name_lbl = QLabel(kullanici.ad)
        name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: white; background: transparent;")
        role_lbl = QLabel("◈ KULLANICI")
        role_lbl.setStyleSheet(f"font-size: 9px; font-weight: 800; letter-spacing: 2px; color: {neon}; background: transparent;")
        info_v.addWidget(name_lbl)
        info_v.addWidget(role_lbl)
        pl.addLayout(info_v)
        pl.addStretch()

        # Online indicator
        online_w = QWidget()
        online_w.setFixedSize(10, 10)
        online_w.setStyleSheet(f"background: #39FF14; border-radius: 5px;")
        pl.addWidget(online_w)

        v.addWidget(profil_frame)

    def paintEvent(self, event):
        pass


class HUDNavButton(QPushButton):
    """Görseldeki menü butonlarına benzer HUD stil nav butonu"""
    def __init__(self, icon, text, subtitle, tema, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedHeight(58)
        self.setCursor(Qt.PointingHandCursor)
        T = tema
        neon = T.get('border_neon', '#00E5FF')
        purple = T.get('accent', '#7B2FBE')
        bg = T.get('bg_primary', '#050510')
        hover = T.get('bg_hover', '#12122A')

        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {T.get('border','#1A1A3A')};
                border-radius: 4px;
                text-align: left;
                padding-left: 0px;
                font-size: 14px;
                font-weight: 600;
                color: {T.get('text_secondary','#A0A0C0')};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {purple}22, stop:1 transparent);
                border: 1px solid {purple}88;
                color: white;
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {purple}55, stop:1 {neon}11);
                border: 1px solid {neon}88;
                color: {neon};
                font-weight: 700;
            }}
        """)

        # Inner layout
        inner = QWidget(self)
        inner.setAttribute(Qt.WA_TransparentForMouseEvents)
        inner.setGeometry(0, 0, 300, 58)
        inner.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(inner)
        hl.setContentsMargins(12, 6, 12, 6)
        hl.setSpacing(10)

        # Indicator bar (sol kenar)
        self._indicator = QWidget(self)
        self._indicator.setFixedWidth(3)
        self._indicator.setFixedHeight(36)
        self._indicator.move(0, 11)
        self._indicator.setStyleSheet(f"background: transparent; border-radius: 1px;")

        # Icon background
        icon_bg = QWidget()
        icon_bg.setFixedSize(36, 36)
        icon_bg.setStyleSheet(f"""
            background: {purple}22;
            border: 1px solid {purple}44;
            border-radius: 4px;
        """)
        icon_layout = QVBoxLayout(icon_bg)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 16px; background: transparent;")
        icon_layout.addWidget(icon_lbl)
        hl.addWidget(icon_bg)

        # Text column
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        main_lbl = QLabel(text)
        main_lbl.setStyleSheet("font-size: 13px; font-weight: 700; background: transparent;")
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"font-size: 10px; color: {T.get('text_muted','#606080')}; background: transparent;")
        text_col.addWidget(main_lbl)
        text_col.addWidget(sub_lbl)
        hl.addLayout(text_col)
        hl.addStretch()

        # Arrow
        arrow_lbl = QLabel("›")
        arrow_lbl.setStyleSheet(f"font-size: 18px; color: {T.get('text_muted','#606080')}; background: transparent;")
        hl.addWidget(arrow_lbl)

        self._neon = neon
        self._purple = purple
        self.toggled.connect(self._on_toggle)

    def _on_toggle(self, checked):
        if checked:
            self._indicator.setStyleSheet(f"background: {self._neon}; border-radius: 1px;")
        else:
            self._indicator.setStyleSheet("background: transparent; border-radius: 1px;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update inner widget size
        for child in self.children():
            if isinstance(child, QWidget):
                child.setGeometry(0, 0, self.width(), self.height())
                break


class HUDActionButton(QPushButton):
    """Tema değiştir / çıkış gibi aksiyon butonları"""
    def __init__(self, text, tema, style="secondary", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        T = tema
        neon = T.get('border_neon', '#00E5FF')
        purple = T.get('accent', '#7B2FBE')

        if style == "danger":
            danger = T.get('danger', '#FF2244')
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {danger}11;
                    border: 1px solid {danger}44;
                    border-radius: 4px;
                    color: {danger};
                    font-size: 12px; font-weight: 600;
                    text-align: left; padding-left: 14px;
                }}
                QPushButton:hover {{
                    background: {danger}33;
                    border-color: {danger};
                    color: white;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {purple}11;
                    border: 1px solid {purple}44;
                    border-radius: 4px;
                    color: {T.get('text_secondary','#A0A0C0')};
                    font-size: 12px; font-weight: 600;
                    text-align: left; padding-left: 14px;
                }}
                QPushButton:hover {{
                    background: {purple}33;
                    border-color: {neon}88;
                    color: {neon};
                }}
            """)


class HUDBottomBar(QWidget):
    """Sidebar alt durum çubuğu"""
    def __init__(self, tema, parent=None):
        super().__init__(parent)
        T = tema
        neon = T.get('border_neon', '#00E5FF')
        purple = T.get('accent', '#7B2FBE')
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {purple}33, stop:0.5 {neon}11, stop:1 {purple}33);
            border-top: 1px solid {neon}44;
        """)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(6)

        v1 = QLabel("● SYS:OK")
        v1.setStyleSheet(f"font-size: 8px; font-weight: 800; letter-spacing: 1px; color: #39FF14; background: transparent;")
        hl.addWidget(v1)
        hl.addStretch()

        from datetime import datetime
        time_lbl = QLabel(datetime.now().strftime("%H:%M"))
        time_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {neon}; background: transparent;")
        hl.addWidget(time_lbl)


class HUDTarifKarti(QFrame):
    """"""
    tiklandi = pyqtSignal(int)

    # Kategori bazlı arka plan renkleri (lezzet.co tarzı, koyu tonlar)
    KAT_RENKLER = {
        "Kahvaltı":  "#1a1208",
        "Çorba":     "#0e1208",
        "Ana Yemek": "#140e08",
        "Tatlı":     "#140d0e",
        "İçecek":    "#0d1114",
        "Salata":    "#0d1208",
    }
    ACCENT = "#c9713a"

    def __init__(self, tarif, tema, kullanici, parent=None):
        super().__init__(parent)
        self.tarif = tarif
        self.kullanici = kullanici
        self._T = tema
        self._hovered = False

        bg_img = self.KAT_RENKLER.get(tarif.kategori, "#141414")
        self._bg_img = bg_img

        self.setFixedSize(260, 210)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(False)

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── Üst resim alanı (emoji ortalı, renkli arka plan) ──
        img_frame = QWidget()
        img_frame.setFixedHeight(100)
        img_frame.setStyleSheet(f"background: {bg_img}; border: none;")
        img_layout = QVBoxLayout(img_frame)
        img_layout.setContentsMargins(0, 0, 0, 0)
        img_layout.setAlignment(Qt.AlignCenter)

        gorsel_yolu = getattr(tarif, 'gorsel_yolu', '')
        if gorsel_yolu:
            px = QPixmap(gorsel_yolu)
            if not px.isNull():
                px = px.scaled(260, 100, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                # Merkeze kırp
                px = px.copy((px.width() - 260) // 2 if px.width() > 260 else 0,
                             (px.height() - 100) // 2 if px.height() > 100 else 0,
                             min(px.width(), 260), min(px.height(), 100))
                img_lbl = QLabel()
                img_lbl.setPixmap(px)
                img_lbl.setAlignment(Qt.AlignCenter)
                img_lbl.setStyleSheet("background: transparent; border: none;")
                img_layout.addWidget(img_lbl)
            else:
                emoji_lbl = QLabel(tarif.gorsel_emoji)
                emoji_lbl.setAlignment(Qt.AlignCenter)
                emoji_lbl.setStyleSheet("font-size: 38px; background: transparent; border: none;")
                img_layout.addWidget(emoji_lbl)
        else:
            emoji_lbl = QLabel(tarif.gorsel_emoji)
            emoji_lbl.setAlignment(Qt.AlignCenter)
            emoji_lbl.setStyleSheet("font-size: 38px; background: transparent; border: none;")
            img_layout.addWidget(emoji_lbl)

        # Rozet (Popüler / Favori) - sağ üst köşe
        fav_icon = "❤" if tarif.tarif_id in kullanici.favori_tarifler else "♡"
        self.fav_btn = QPushButton(fav_icon)
        self.fav_btn.setParent(img_frame)
        self.fav_btn.setFixedSize(26, 22)
        self.fav_btn.move(img_frame.width() - 34, 8)
        self.fav_btn.setStyleSheet(f"""
            QPushButton {{
                background: #1a1a1a88; border: 0.5px solid #3a3a3a;
                border-radius: 4px; color: #c9713a; font-size: 13px;
            }}
            QPushButton:hover {{ background: #c9713a22; border-color: #c9713a; }}
        """)
        self.fav_btn.clicked.connect(self._toggle_fav)
        self.fav_btn.raise_()

        v.addWidget(img_frame)

        # ── Gövde ──
        body = QWidget()
        body.setStyleSheet("background: #141414; border: none;")
        bv = QVBoxLayout(body)
        bv.setContentsMargins(14, 10, 14, 0)
        bv.setSpacing(4)

        # Kategori etiketi
        kat_lbl = QLabel(tarif.kategori.upper())
        kat_lbl.setStyleSheet(
            "font-size: 9px; font-weight: 700; letter-spacing: 1px;"
            "color: #4d4d4d; background: transparent;"
        )
        bv.addWidget(kat_lbl)

        # Tarif adı
        name_lbl = QLabel(tarif.tarif_adi[:22] + ("..." if len(tarif.tarif_adi) > 22 else ""))
        name_lbl.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #e8d5b0; background: transparent;"
        )
        bv.addWidget(name_lbl)

        # Meta bilgi: süre · kişi · puan
        meta = QHBoxLayout()
        meta.setSpacing(10)
        meta.setContentsMargins(0, 2, 0, 0)

        sure_lbl = QLabel(f"⏱ {tarif.hazirlama_suresi} dk")
        sure_lbl.setStyleSheet("font-size: 11px; color: #4d4d4d; background: transparent;")
        puan_lbl = QLabel(f"★ {tarif.puan:.1f}")
        puan_lbl.setStyleSheet("font-size: 11px; color: #c9713a; background: transparent; font-weight: 700;")
        goruntuleme_lbl = QLabel(f"👁 {tarif.goruntuleme}")
        goruntuleme_lbl.setStyleSheet("font-size: 10px; color: #3d3d3d; background: transparent;")

        meta.addWidget(sure_lbl)
        meta.addWidget(puan_lbl)
        meta.addStretch()
        meta.addWidget(goruntuleme_lbl)
        bv.addLayout(meta)

        v.addWidget(body)

        # ── Alt footer ──
        footer = QFrame()
        footer.setStyleSheet(
            "background: #141414; border: none; border-top: 0.5px solid #1f1f1f;"
        )
        footer.setFixedHeight(36)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(14, 0, 10, 0)

        ekleyen_lbl = QLabel(f"— {tarif.ekleyen}")
        ekleyen_lbl.setStyleSheet("font-size: 10px; color: #3d3d3d; background: transparent;")
        fl.addWidget(ekleyen_lbl)
        fl.addStretch()

        detay_btn = QPushButton("Detay →")
        detay_btn.setFixedHeight(24)
        detay_btn.setFixedWidth(70)
        detay_btn.setCursor(Qt.PointingHandCursor)
        detay_btn.setStyleSheet(f"""
            QPushButton {{
                background: #1e1a15; border: 0.5px solid #c9713a55;
                border-radius: 6px; color: #c9713a;
                font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{
                background: #c9713a22; border-color: #c9713a;
            }}
        """)
        detay_btn.clicked.connect(lambda: self.tiklandi.emit(tarif.tarif_id))
        fl.addWidget(detay_btn)
        v.addWidget(footer)

    def _apply_style(self, hovered):
        border = "#3a3a3a" if hovered else "#2a2a2a"
        self.setStyleSheet(f"""
            QFrame {{
                background: #141414;
                border: 0.5px solid {border};
                border-radius: 12px;
            }}
        """)

    def _toggle_fav(self):
        if self.tarif.tarif_id in self.kullanici.favori_tarifler:
            self.kullanici.favori_tarifler.remove(self.tarif.tarif_id)
            self.fav_btn.setText("♡")
        else:
            self.kullanici.favori_tarifler.append(self.tarif.tarif_id)
            self.fav_btn.setText("❤")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.tiklandi.emit(self.tarif.tarif_id)

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style(True)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Fav butonunu her zaman sağ üst köşeye sabitle
        for child in self.findChildren(QPushButton):
            if child.text() in ("❤", "♡"):
                parent_w = child.parent()
                if parent_w:
                    child.move(parent_w.width() - 34, 8)
                break


# ── HUD Durum Göstergesi Wiget ──
class HUDStatWidget(QWidget):
    """Cyberpunk tarzı istatistik göstergesi"""
    def __init__(self, icon, value, label, color, tema, parent=None):
        super().__init__(parent)
        T = tema
        neon = T.get('border_neon', '#00E5FF')
        self.setMinimumHeight(80)

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        frame = QWidget()
        frame.setStyleSheet(f"""
            background: {T.get('bg_card','#0D0D22')};
            border: 1px solid {color}44;
            border-radius: 3px;
        """)
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(12, 10, 12, 10)
        fl.setSpacing(4)

        top_r = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 18px; background: transparent;")
        top_r.addWidget(icon_lbl)
        top_r.addStretch()

        # Tiny indicator bar at top
        bar = QWidget()
        bar.setFixedHeight(2)
        bar.setStyleSheet(f"background: {color}; border-radius: 1px;")
        fl.addWidget(bar)
        fl.addLayout(top_r)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {color}; background: transparent;")
        lbl_lbl = QLabel(label.upper())
        lbl_lbl.setStyleSheet(f"font-size: 9px; letter-spacing: 1px; font-weight: 700; color: {T.get('text_muted','#606080')}; background: transparent;")
        fl.addWidget(val_lbl)
        fl.addWidget(lbl_lbl)

        v.addWidget(frame)


# ─────────────────────────── GİRİŞ EKRANI ───────────────────────────

class GirisEkrani(QDialog):
    def __init__(self, db, tema):
        super().__init__()
        self.db = db
        self.tema = tema
        self.kullanici = None
        self.kullanici_cikti = False
        self.setWindowTitle("Tariftirium")
        self.setFixedSize(1100, 700)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build_ui()

    def keyPressEvent(self, event):
        # ESC tuşu ile dialog kapanmasın
        if event.key() == Qt.Key_Escape:
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        """Mor gradient arka plan"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0, QColor("#1a0533"))
        grad.setColorAt(0.4, QColor("#2d1057"))
        grad.setColorAt(0.7, QColor("#1e0a3c"))
        grad.setColorAt(1.0, QColor("#0d0520"))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 16, 16)
        # Dekoratif daireler
        painter.setBrush(QBrush(QColor(120, 50, 200, 40)))
        painter.drawEllipse(QPoint(-60, -60), 200, 200)
        painter.setBrush(QBrush(QColor(180, 80, 255, 30)))
        painter.drawEllipse(QPoint(self.width() + 40, self.height() + 40), 220, 220)
        painter.setBrush(QBrush(QColor(100, 40, 180, 25)))
        painter.drawEllipse(QPoint(80, self.height() - 50), 160, 160)
        painter.end()

    def _build_ui(self):
        T = self.tema
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sol panel: marka / dekorasyon ──
        sol = QWidget()
        sol.setFixedWidth(500)
        sol.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        sol_v = QVBoxLayout(sol)
        sol_v.setContentsMargins(60, 60, 40, 60)
        sol_v.setSpacing(0)

        # Logo ikon
        logo_bg = QFrame()
        logo_bg.setFixedSize(64, 64)
        logo_bg.setStyleSheet("""
           
        """)
        lb_l = QVBoxLayout(logo_bg)
        lb_l.setContentsMargins(0, 0, 0, 0)
        lb_lbl = QLabel("")
        lb_lbl.setAlignment(Qt.AlignCenter)
        lb_lbl.setStyleSheet("font-size: 30px; background: transparent;")
        lb_l.addWidget(lb_lbl)
        sol_v.addWidget(logo_bg)
        sol_v.addSpacing(28)

        brand = QLabel("Tariftirium")
        brand.setStyleSheet("""
            font-size: 42px; font-weight: 900;
            color: white; background: transparent;
            letter-spacing: -1px;
        """)
        sol_v.addWidget(brand)
        sol_v.addSpacing(12)

        tagline = QLabel("Lezzetli tarifleri keşfet,\npaylaş ve değerlendir.")
        tagline.setStyleSheet("color: rgba(255,255,255,0.65); font-size: 16px; background: transparent; line-height: 1.6;")
        tagline.setWordWrap(True)
        sol_v.addWidget(tagline)
        sol_v.addSpacing(48)

        # Feature chips
        for chip_text in ["🍳  20+ Tarif Kategorisi", "⭐  Kullanıcı Değerlendirmesi", "👤  Kişisel Profil"]:
            chip = QLabel(chip_text)
            chip.setStyleSheet("""
                color: rgba(255,255,255,0.80);
                background: rgba(255,255,255,0.10);
                border-radius: 20px;
                padding: 8px 18px;
                font-size: 13px; font-weight: 500;
            """)
            chip.setFixedHeight(38)
            sol_v.addWidget(chip)
            sol_v.addSpacing(8)

        sol_v.addStretch()

        hint = QLabel("Demo:  admin / admin    •    eslem@email.com / 123456")
        hint.setStyleSheet("color: rgba(255,255,255,0.40); font-size: 11px; background: transparent;")
        sol_v.addWidget(hint)

        main_layout.addWidget(sol)

        # ── Sağ panel: Glassmorphism kart ──
        sag = QWidget()
        sag_v = QVBoxLayout(sag)
        sag_v.setContentsMargins(0, 0, 0, 0)
        sag_v.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedSize(420, 560)
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.10);
                border-radius: 14px;
            }
        """)
        card_shadow = QGraphicsDropShadowEffect()
        card_shadow.setBlurRadius(60)
        card_shadow.setColor(QColor(0, 0, 0, 100))
        card_shadow.setOffset(0, 20)
        card.setGraphicsEffect(card_shadow)

        cv = QVBoxLayout(card)
        cv.setContentsMargins(44, 40, 44, 40)
        cv.setSpacing(0)

        # Kapat
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                color: white; border: none; border-radius: 14px;
                font-size: 12px; font-weight: 700;
            }
            QPushButton:hover { background: rgba(255,80,80,0.7); }
        """)
        def _kapat():
            self.kullanici_cikti = True
            self.reject()
        close_btn.clicked.connect(_kapat)
        close_row.addWidget(close_btn)
        cv.addLayout(close_row)
        cv.addSpacing(8)

        # Avatar icon
        av_row = QHBoxLayout()
        av_row.setAlignment(Qt.AlignCenter)
        av_bg = QFrame()
        av_bg.setFixedSize(56, 56)
        av_bg.setStyleSheet("""
        """)
        av_l = QVBoxLayout(av_bg)
        av_l.setContentsMargins(0, 0, 0, 0)
        av_icon = QLabel("👤")
        av_icon.setAlignment(Qt.AlignCenter)
        av_icon.setStyleSheet("font-size: 24px; background: transparent;")
        av_l.addWidget(av_icon)
        av_row.addWidget(av_bg)
        cv.addLayout(av_row)
        cv.addSpacing(16)

        title_lbl = QLabel("Giriş Yap")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: white; background: transparent;")
        cv.addWidget(title_lbl)
        cv.addSpacing(4)

        sub_lbl = QLabel("Hesabınıza giriş yapın")
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.60); background: transparent;")
        cv.addWidget(sub_lbl)
        cv.addSpacing(28)

        def make_input(placeholder, echo=False):
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setMinimumHeight(48)
            if echo:
                inp.setEchoMode(QLineEdit.Password)
            inp.setStyleSheet("""
                QLineEdit {
                    background: rgba(255,255,255,0.12);
                    border-radius: 12px;
                    color: white;
                    font-size: 14px;
                    padding: 0 16px;
                    selection-background-color: #BD93F9;
                }
                QLineEdit:focus {
                    border: 1.5px solid #BD93F9;
                    background: rgba(189,147,249,0.15);
                }
                QLineEdit::placeholder {
                    color: rgba(255,255,255,0.45);
                }
            """)
            return inp

        self.email_input = make_input("E-posta veya kullanıcı adı")
        # Giriş ekranında boşluk yasak
        def email_bosluk_kaldir(t):
            if " " in t:
                self.email_input.blockSignals(True)
                cursor_pos = self.email_input.cursorPosition()
                spaces_before_cursor = t[:cursor_pos].count(" ")
                self.email_input.setText(t.replace(" ", ""))
                self.email_input.setCursorPosition(max(0, cursor_pos - spaces_before_cursor))
                self.email_input.blockSignals(False)
        self.email_input.textChanged.connect(email_bosluk_kaldir)
        cv.addWidget(self.email_input)
        cv.addSpacing(12)

        # Şifre alanı + göster/gizle butonu
        sifre_row = QHBoxLayout()
        sifre_row.setSpacing(0)
        self.sifre_input = make_input("Şifre", echo=True)
        def sifre_bosluk_kaldir(t):
            if " " in t:
                self.sifre_input.blockSignals(True)
                cursor_pos = self.sifre_input.cursorPosition()
                spaces_before_cursor = t[:cursor_pos].count(" ")
                self.sifre_input.setText(t.replace(" ", ""))
                self.sifre_input.setCursorPosition(max(0, cursor_pos - spaces_before_cursor))
                self.sifre_input.blockSignals(False)
        self.sifre_input.textChanged.connect(sifre_bosluk_kaldir)
        self.sifre_input.returnPressed.connect(self.giris_yap)

        # Göster/gizle toggle butonu (özel çizimli göz ikonu)
        goster_btn = GozIkonu()
        def _toggle_sifre(goster):
            self.sifre_input.setEchoMode(
                QLineEdit.Normal if goster else QLineEdit.Password
            )
        goster_btn.toggled.connect(_toggle_sifre)

        sifre_row.addWidget(self.sifre_input)
        sifre_row.addWidget(goster_btn)
        cv.addLayout(sifre_row)
        cv.addSpacing(8)

        self.hata_lbl = QLabel("")
        self.hata_lbl.setStyleSheet("color: #FF6B6B; font-size: 12px; background: transparent;")
        self.hata_lbl.setAlignment(Qt.AlignCenter)
        cv.addWidget(self.hata_lbl)
        cv.addSpacing(16)

        # Giriş butonu
        giris_btn = QPushButton("Giriş Yap")
        giris_btn.setMinimumHeight(50)
        giris_btn.setCursor(Qt.PointingHandCursor)
        giris_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #BD93F9, stop:1 #FF79C6);
                color: white; border: none; border-radius: 12px;
                font-size: 15px; font-weight: 700; letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #A67FE8, stop:1 #E868B0);
            }
        """)
        giris_btn.clicked.connect(self.giris_yap)
        cv.addWidget(giris_btn)
        cv.addSpacing(12)

        # Kayıt ol
        kayit_btn = QPushButton("Hesabın yok mu? Kayıt Ol →")
        kayit_btn.setCursor(Qt.PointingHandCursor)
        kayit_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255,255,255,0.65);
                border-radius: 12px;
                font-size: 13px; font-weight: 500;
                padding: 10px;
            }
            QPushButton:hover {
                color: white;
                border-color: rgba(255,255,255,0.45);
                background: rgba(255,255,255,0.08);
            }
        """)
        kayit_btn.clicked.connect(self.kayit_ol)
        cv.addWidget(kayit_btn)
        cv.addStretch()

        sag_v.addWidget(card)
        main_layout.addWidget(sag, 1)

    def giris_yap(self):
        email = self.email_input.text().strip()
        sifre = self.sifre_input.text()
        if not email or not sifre:
            self.hata_lbl.setText("⚠️ E-posta ve şifre boş bırakılamaz.")
            return
        k = self.db.kullanici_bul(email, sifre)
        if k is None:
            self.hata_lbl.setText("⚠️ E-posta veya şifre hatalı!")
            self.sifre_input.clear()
            self.sifre_input.setFocus()
            return
        if not k.aktif:
            self.hata_lbl.setStyleSheet(
                "color: #FF4444; font-size: 12px; background: transparent; font-weight: 600;")
            self.hata_lbl.setText("🚫 Hesabınız askıya alınmıştır. Yönetici ile iletişime geçin.")
            self.sifre_input.clear()
            self._shake_widget(self.email_input)
            return
        k.son_giris = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.kullanici = k
        self.accept()

    def _shake_widget(self, widget):
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(300)
        orig = widget.pos()
        anim.setKeyValueAt(0.0,  orig)
        anim.setKeyValueAt(0.15, orig + QPoint(-6, 0))
        anim.setKeyValueAt(0.30, orig + QPoint(6, 0))
        anim.setKeyValueAt(0.45, orig + QPoint(-4, 0))
        anim.setKeyValueAt(0.60, orig + QPoint(4, 0))
        anim.setKeyValueAt(0.80, orig + QPoint(-2, 0))
        anim.setKeyValueAt(1.0,  orig)
        anim.start(QAbstractAnimation.DeleteWhenStopped)
        self._shake_anim = anim

    def kayit_ol(self):
        d = KayitDialog(self.db, self.tema, self)
        if d.exec_() == QDialog.Accepted:
            self.email_input.setText(d.email)
            self.sifre_input.clear()
            self.hata_lbl.setText("")
            QMessageBox.information(self, "Hoş Geldiniz!", "Hesabınız oluşturuldu! Şimdi giriş yapabilirsiniz.")


class KayitDialog(QDialog):
    def __init__(self, db, tema, parent=None):
        super().__init__(parent)
        self.db = db
        self.tema = tema
        self.email = ""
        self.setWindowTitle("Yeni Hesap Oluştur")
        self.setFixedSize(520, 680)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build_ui()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0, QColor("#1a0533"))
        grad.setColorAt(0.4, QColor("#2d1057"))
        grad.setColorAt(0.7, QColor("#1e0a3c"))
        grad.setColorAt(1.0, QColor("#0d0520"))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)
        painter.setBrush(QBrush(QColor(120, 50, 200, 35)))
        painter.drawEllipse(QPoint(-40, -40), 180, 180)
        painter.setBrush(QBrush(QColor(180, 80, 255, 25)))
        painter.drawEllipse(QPoint(self.width() + 30, self.height() + 30), 200, 200)
        painter.end()

    def _build_ui(self):
        main_v = QVBoxLayout(self)
        main_v.setContentsMargins(0, 0, 0, 0)
        main_v.setSpacing(0)

        # ── Glassmorphism kart ──
        card = QFrame(self)
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.09);
                border-radius: 20px;
            }
        """)
        card_shadow = QGraphicsDropShadowEffect()
        card_shadow.setBlurRadius(50)
        card_shadow.setColor(QColor(0, 0, 0, 90))
        card_shadow.setOffset(0, 16)
        card.setGraphicsEffect(card_shadow)

        cv = QVBoxLayout(card)
        cv.setContentsMargins(44, 36, 44, 36)
        cv.setSpacing(0)

        # Kapat
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                color: white; border: none; border-radius: 14px;
                font-size: 12px; font-weight: 700;
            }
            QPushButton:hover { background: rgba(255,80,80,0.7); }
        """)
        def _kapat():
            self.kullanici_cikti = True
            self.reject()
        close_btn.clicked.connect(_kapat)
        close_row.addWidget(close_btn)
        cv.addLayout(close_row)
        cv.addSpacing(4)

        # İkon
        icon_row = QHBoxLayout()
        icon_row.setAlignment(Qt.AlignCenter)
        icon_lbl = QLabel("🎉")
        icon_lbl.setStyleSheet("font-size: 32px; background: transparent;")
        icon_row.addWidget(icon_lbl)
        cv.addLayout(icon_row)
        cv.addSpacing(10)

        title_lbl = QLabel("Hesap Oluştur")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: white; background: transparent;")
        cv.addWidget(title_lbl)
        cv.addSpacing(4)

        sub_lbl = QLabel("Ücretsiz kayıt olun, tarifleri keşfedin")
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.55); background: transparent;")
        cv.addWidget(sub_lbl)
        cv.addSpacing(22)

        INPUT_SS = """
            QLineEdit {
                background: rgba(255,255,255,0.10);
                border: 1.5px solid rgba(255,255,255,0.18);
                border-radius: 10px;
                color: white;
                font-size: 13px;
                padding: 0 14px;
                selection-background-color: #BD93F9;
            }
            QLineEdit:focus {
                border: 1.5px solid #BD93F9;
                background: rgba(189,147,249,0.13);
            }
        """
        LABEL_SS = "font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.65); background: transparent; letter-spacing: 0.5px;"

        def make_labeled_input(label_text, placeholder, echo=False):
            lbl = QLabel(label_text.upper())
            lbl.setStyleSheet(LABEL_SS)
            cv.addWidget(lbl)
            cv.addSpacing(4)
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setMinimumHeight(44)
            if echo:
                inp.setEchoMode(QLineEdit.Password)
            inp.setStyleSheet(INPUT_SS)
            cv.addWidget(inp)
            cv.addSpacing(10)
            return inp

        self.ad_input = make_labeled_input("Ad Soyad", "Adınızı ve soyadınızı girin")
        self.kayit_email_input = make_labeled_input("E-posta", "ornek@email.com")
        self.kayit_sifre_input = make_labeled_input("Şifre", "En az 6 karakter", echo=True)
        self.sifre_tekrar_input = make_labeled_input("Şifre Tekrar", "Şifrenizi tekrar girin", echo=True)

        # Boşluk filtresi — hiçbir alana boşluk girilemesin
        for inp in [self.ad_input, self.kayit_email_input, self.kayit_sifre_input, self.sifre_tekrar_input]:
            inp.textChanged.connect(lambda text, i=inp: (
                i.setText(text.replace(" ", "")) if " " in text else None
            ))

        # Ad alanı: sadece harf (Türkçe dahil) — sayı ve özel karakter yasak
        import re as _re
        def _ad_filtrele(text):
            temiz = _re.sub(r'[^a-zA-ZçÇğĞıİöÖşŞüÜ\s]', '', text)
            temiz = temiz.replace(" ", "")
            if temiz != text:
                cur = self.ad_input.cursorPosition()
                self.ad_input.blockSignals(True)
                self.ad_input.setText(temiz)
                self.ad_input.setCursorPosition(max(0, cur - (len(text) - len(temiz))))
                self.ad_input.blockSignals(False)
        self.ad_input.textChanged.connect(_ad_filtrele)

        # Şifre alanları: boşluk zaten engellendi üstte
        # Email: boşluk engellendi, diğer karakterler serbest

        # Kuvvet barı
        self.kuvvet_bar = QProgressBar()
        self.kuvvet_bar.setRange(0, 4)
        self.kuvvet_bar.setValue(0)
        self.kuvvet_bar.setMaximumHeight(6)
        self.kuvvet_bar.setTextVisible(False)
        self.kuvvet_bar.setStyleSheet("""
            QProgressBar { background: rgba(255,255,255,0.10); border-radius: 3px; border: none; }
            QProgressBar::chunk { background: #6B7280; border-radius: 3px; }
        """)
        self.kayit_sifre_input.textChanged.connect(self._sifre_kuvveti_guncelle)
        cv.addWidget(self.kuvvet_bar)
        cv.addSpacing(3)

        self.kuvvet_lbl = QLabel("")
        self.kuvvet_lbl.setStyleSheet("font-size: 10px; background: transparent; color: rgba(255,255,255,0.45);")
        cv.addWidget(self.kuvvet_lbl)
        cv.addSpacing(8)

        self.hata_lbl = QLabel("")
        self.hata_lbl.setStyleSheet("color: #FF6B6B; font-size: 12px; background: transparent;")
        self.hata_lbl.setAlignment(Qt.AlignCenter)
        self.hata_lbl.setWordWrap(True)
        cv.addWidget(self.hata_lbl)
        cv.addSpacing(10)

        kayit_btn = QPushButton("Kayıt Ol")
        kayit_btn.setMinimumHeight(48)
        kayit_btn.setCursor(Qt.PointingHandCursor)
        kayit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #BD93F9, stop:1 #FF79C6);
                color: white; border: none; border-radius: 12px;
                font-size: 14px; font-weight: 700; letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #A67FE8, stop:1 #E868B0);
            }
        """)
        kayit_btn.clicked.connect(self.kayit_et)
        cv.addWidget(kayit_btn)
        cv.addSpacing(8)

        iptal_btn = QPushButton("Vazgeç")
        iptal_btn.setCursor(Qt.PointingHandCursor)
        iptal_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255,255,255,0.55);
                border: 1.5px solid rgba(255,255,255,0.15);
                border-radius: 12px;
                font-size: 13px; font-weight: 500;
                padding: 10px;
            }
            QPushButton:hover {
                color: white;
                border-color: rgba(255,255,255,0.40);
                background: rgba(255,255,255,0.07);
            }
        """)
        iptal_btn.setMinimumHeight(40)
        iptal_btn.clicked.connect(self.reject)
        cv.addWidget(iptal_btn)

        main_v.addWidget(card)

    def _sifre_kuvveti_guncelle(self, text):
        puan = 0
        if len(text) >= 8: puan += 1
        if any(c.isupper() for c in text): puan += 1
        if any(c.isdigit() for c in text): puan += 1
        if any(c in "!@#$%^&*()-_=+[]{}|;:',.<>?/" for c in text): puan += 1
        self.kuvvet_bar.setValue(puan)
        renk_harita = {0: "#6B7280", 1: "#EF4444", 2: "#F59E0B", 3: "#10B981", 4: "#3B82F6"}
        metin_harita = {0: "", 1: "Çok Zayıf", 2: "Orta", 3: "Güçlü", 4: "Çok Güçlü ✓"}
        renk = renk_harita.get(puan, "#6B7280")
        self.kuvvet_lbl.setText(f"Şifre kuvveti: {metin_harita.get(puan, '')}")
        self.kuvvet_lbl.setStyleSheet(f"font-size: 11px; background: transparent; color: {renk};")
        self.kuvvet_bar.setStyleSheet(f"QProgressBar::chunk {{ background: {renk}; border-radius: 4px; }}")

    def kayit_et(self):
        import re as _re
        ad = self.ad_input.text().strip()
        email = self.kayit_email_input.text().strip()
        sifre = self.kayit_sifre_input.text()
        sifre2 = self.sifre_tekrar_input.text()

        if not all([ad, email, sifre, sifre2]):
            self.hata_lbl.setText("⚠️ Tüm alanları doldurun!"); return
        if " " in ad or " " in email or " " in sifre or " " in sifre2:
            self.hata_lbl.setText("⚠️ Hiçbir alana boşluk girilemez!"); return
        if not _re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ]+$', ad):
            self.hata_lbl.setText("⚠️ Ad Soyad alanına yalnızca harf girilebilir!"); return
        if sifre != sifre2:
            self.hata_lbl.setText("⚠️ Şifreler eşleşmiyor!"); return
        if len(sifre) < 6:
            self.hata_lbl.setText("⚠️ Şifre en az 6 karakter olmalı!"); return
        if "@" not in email or "." not in email:
            self.hata_lbl.setText("⚠️ Geçerli bir e-posta girin!"); return
        if self.db.email_mevcut_mu(email):
            self.hata_lbl.setText("⚠️ Bu e-posta zaten kayıtlı!"); return

        kid = self.db.sonraki_kullanici_id()
        k = Kullanici(kid, ad, email, hash_sifre(sifre))
        self.db.kullanicilar[kid] = k
        self.email = email
        self.accept()


# ─────────────────────────── YILDIZ WIDGET ───────────────────────────

class YildizWidget(QWidget):
    puan_degisti = pyqtSignal(int)

    def __init__(self, puan=0, salt_okunur=False, boyut=20, parent=None):
        super().__init__(parent)
        self.puan = puan
        self.salt_okunur = salt_okunur
        self.boyut = boyut
        self.hover_puan = 0
        self.setFixedSize(boyut * 5 + 4, boyut + 4)
        self.setCursor(Qt.PointingHandCursor if not salt_okunur else Qt.ArrowCursor)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        goster = self.hover_puan if self.hover_puan > 0 else self.puan
        font = painter.font()
        font.setPixelSize(self.boyut)
        painter.setFont(font)
        for i in range(5):
            x = i * (self.boyut + 1)
            if i < int(goster):
                painter.setPen(QColor("#F59E0B"))
                painter.setBrush(QColor("#F59E0B"))
            elif i < goster:
                painter.setPen(QColor("#F59E0B"))
                painter.setBrush(QColor("#FCD34D"))
            else:
                painter.setPen(QColor("#D1D5DB"))
                painter.setBrush(QColor("#E5E7EB"))
            painter.drawText(x, 2, self.boyut, self.boyut, Qt.AlignCenter, "★")
        painter.end()

    def mouseMoveEvent(self, event):
        if not self.salt_okunur:
            self.hover_puan = min(5, max(1, int(event.x() / (self.boyut + 1)) + 1))
            self.update()

    def leaveEvent(self, event):
        self.hover_puan = 0
        self.update()

    def mousePressEvent(self, event):
        if not self.salt_okunur:
            self.puan = min(5, max(1, int(event.x() / (self.boyut + 1)) + 1))
            self.puan_degisti.emit(self.puan)
            self.update()


# ─────────────────────────── TARİF KARTI ───────────────────────────

class TarifKarti(QFrame):
    tiklandi = pyqtSignal(int)

    def __init__(self, tarif, tema, kullanici, parent=None):
        super().__init__(parent)
        self.tarif = tarif
        self.tema = tema
        self.kullanici = kullanici
        self.setFixedSize(236, 290)
        self.setCursor(Qt.PointingHandCursor)
        self._build()
        self._apply_style()

    def _apply_style(self):
        T = self.tema
        self.setStyleSheet(f"""
            TarifKarti {{
                background-color: {T['bg_card']};
                border-radius: 16px;
            }}
            TarifKarti:hover {{
                border-color: {T['accent']}88;
                background-color: {T['bg_hover']};
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 28))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def _build(self):
        T = self.tema
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 14)
        v.setSpacing(8)

        top = QHBoxLayout()
        emoji_bg = QFrame()
        emoji_bg.setFixedSize(54, 54)
        emoji_bg.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {T['accent']}28, stop:1 {T['accent_secondary']}28);
            border-radius: 15px;
        """)
        el = QHBoxLayout(emoji_bg)
        el.setContentsMargins(0, 0, 0, 0)

        # Gerçek görsel varsa onu göster, yoksa emoji
        gorsel_yolu = getattr(self.tarif, 'gorsel_yolu', '')
        if gorsel_yolu:
            pixmap = QPixmap(gorsel_yolu)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                gorsel_widget = QLabel()
                gorsel_widget.setPixmap(pixmap)
                gorsel_widget.setAlignment(Qt.AlignCenter)
                gorsel_widget.setStyleSheet("background: transparent; border-radius: 13px;")
                el.addWidget(gorsel_widget)
            else:
                emoji_lbl = QLabel(self.tarif.gorsel_emoji)
                emoji_lbl.setAlignment(Qt.AlignCenter)
                emoji_lbl.setStyleSheet("font-size: 28px; background: transparent;")
                el.addWidget(emoji_lbl)
        else:
            emoji_lbl = QLabel(self.tarif.gorsel_emoji)
            emoji_lbl.setAlignment(Qt.AlignCenter)
            emoji_lbl.setStyleSheet("font-size: 28px; background: transparent;")
            el.addWidget(emoji_lbl)

        top.addWidget(emoji_bg)
        top.addStretch()

        fav_icon = "❤️" if self.tarif.tarif_id in self.kullanici.favori_tarifler else "🤍"
        self.fav_btn = QPushButton(fav_icon)
        self.fav_btn.setFixedSize(34, 34)
        self.fav_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T['bg_secondary']};
                border: 1px solid {T['border']};
                border-radius: 17px; font-size: 15px;
            }}
            QPushButton:hover {{
                background: {T['danger']}22; border-color: {T['danger']};
            }}
        """)
        self.fav_btn.clicked.connect(self._toggle_fav)
        top.addWidget(self.fav_btn)
        v.addLayout(top)

        ad = QLabel(self.tarif.tarif_adi)
        ad.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        ad.setWordWrap(True)
        v.addWidget(ad)

        kat_badge = QLabel(self.tarif.kategori)
        kat_badge.setStyleSheet(f"""
            background: {T['accent_secondary']}22; color: {T['accent_secondary']};
            border-radius: 8px; padding: 2px 8px;
            font-size: 11px; font-weight: 600;
        """)
        kat_badge.setFixedHeight(22)
        v.addWidget(kat_badge)

        meta = QHBoxLayout()
        sure_lbl = QLabel(f"⏱ {self.tarif.hazirlama_suresi} dk")
        sure_lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; background: transparent;")
        meta.addWidget(sure_lbl)
        meta.addStretch()
        goruntuleme_lbl = QLabel(f"👁 {self.tarif.goruntuleme}")
        goruntuleme_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 11px; background: transparent;")
        meta.addWidget(goruntuleme_lbl)
        v.addLayout(meta)

        # Ekleyen kullanıcı adı
        ekleyen_lbl = QLabel(f"👤 {self.tarif.ekleyen}")
        ekleyen_lbl.setStyleSheet(f"""
            color: {T['accent']}; font-size: 11px; font-weight: 600;
            background: {T['accent']}15; border-radius: 6px; padding: 2px 7px;
        """)
        ekleyen_lbl.setFixedHeight(20)
        v.addWidget(ekleyen_lbl)

        v.addStretch()

        bottom = QHBoxLayout()
        star_widget = YildizWidget(int(self.tarif.puan), salt_okunur=True, boyut=14)
        star_widget.setStyleSheet("background: transparent;")
        bottom.addWidget(star_widget)
        puan_lbl = QLabel(f"{self.tarif.puan:.1f}")
        puan_lbl.setStyleSheet(f"color: {T['star']}; font-size: 12px; font-weight: 700; background: transparent;")
        bottom.addWidget(puan_lbl)
        bottom.addStretch()

        detay_btn = QPushButton("Detay →")
        detay_btn.setFixedHeight(30)
        detay_btn.setCursor(Qt.PointingHandCursor)
        detay_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T['accent']}18; color: {T['accent']};
                border: 1px solid {T['accent']}44; border-radius: 8px;
                font-size: 12px; font-weight: 600; padding: 0 10px;
            }}
            QPushButton:hover {{
                background: {T['accent']}; color: white;
            }}
        """)
        detay_btn.clicked.connect(lambda: self.tiklandi.emit(self.tarif.tarif_id))
        bottom.addWidget(detay_btn)
        v.addLayout(bottom)

    def _toggle_fav(self):
        if self.tarif.tarif_id in self.kullanici.favori_tarifler:
            self.kullanici.favori_tarifler.remove(self.tarif.tarif_id)
            self.fav_btn.setText("🤍")
        else:
            self.kullanici.favori_tarifler.append(self.tarif.tarif_id)
            self.fav_btn.setText("❤️")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.tiklandi.emit(self.tarif.tarif_id)


# ─────────────────────────── TARİF DETAY DİALOG ───────────────────────────

class TarifDetayDialog(QDialog):
    def __init__(self, tarif, db, kullanici, tema, parent=None):
        super().__init__(parent)
        self.tarif = tarif
        self.db = db
        self.kullanici = kullanici
        self.tema = tema
        self.setWindowTitle(f"{tarif.gorsel_emoji} {tarif.tarif_adi}")
        self.resize(640, 760)
        self.setStyleSheet(get_stylesheet(tema))
        self._build_ui()

    def _build_ui(self):
        T = self.tema
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {T['bg_card']}, stop:1 {T['bg_secondary']});
                border-bottom: 1px solid {T['border']};
            }}
        """)
        header.setFixedHeight(100)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(28, 20, 28, 20)

        emoji_bg = QFrame()
        emoji_bg.setFixedSize(60, 60)
        emoji_bg.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {T['accent']}33, stop:1 {T['accent_secondary']}33);
                border-radius: 16px;
            }}
        """)
        el = QVBoxLayout(emoji_bg)
        el.setContentsMargins(0, 0, 0, 0)

        gorsel_yolu = getattr(self.tarif, 'gorsel_yolu', '')
        if gorsel_yolu:
            px = QPixmap(gorsel_yolu)
            if not px.isNull():
                px = px.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                gorsel_det_lbl = QLabel()
                gorsel_det_lbl.setPixmap(px)
                gorsel_det_lbl.setAlignment(Qt.AlignCenter)
                gorsel_det_lbl.setStyleSheet("background: transparent;")
                el.addWidget(gorsel_det_lbl)
            else:
                emoji_lbl = QLabel(self.tarif.gorsel_emoji)
                emoji_lbl.setAlignment(Qt.AlignCenter)
                emoji_lbl.setStyleSheet("font-size: 32px; background: transparent;")
                el.addWidget(emoji_lbl)
        else:
            emoji_lbl = QLabel(self.tarif.gorsel_emoji)
            emoji_lbl.setAlignment(Qt.AlignCenter)
            emoji_lbl.setStyleSheet("font-size: 32px; background: transparent;")
            el.addWidget(emoji_lbl)

        hl.addWidget(emoji_bg)

        info_v = QVBoxLayout()
        info_v.setSpacing(4)
        title_l = QLabel(self.tarif.tarif_adi)
        title_l.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {T['text_primary']}; background: transparent;")
        sub_l = QLabel(f"{self.tarif.kategori}  •  ⏱ {self.tarif.hazirlama_suresi} dk  •  👁 {self.tarif.goruntuleme} görüntüleme")
        sub_l.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; background: transparent;")
        info_v.addWidget(title_l)
        info_v.addWidget(sub_l)
        hl.addLayout(info_v)
        hl.addStretch()

        puan_frame = QFrame()
        puan_frame.setStyleSheet(f"background: {T['star']}18; border-radius: 12px;")
        pl = QVBoxLayout(puan_frame)
        pl.setContentsMargins(16, 10, 16, 10)
        pl.setSpacing(2)
        puan_big = QLabel(f"{self.tarif.puan:.1f}")
        puan_big.setAlignment(Qt.AlignCenter)
        puan_big.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {T['star']}; background: transparent;")
        puan_sub = QLabel(f"⭐ {self.tarif.puan_sayisi} oy")
        puan_sub.setAlignment(Qt.AlignCenter)
        puan_sub.setStyleSheet(f"font-size: 11px; color: {T['text_secondary']}; background: transparent;")
        pl.addWidget(puan_big)
        pl.addWidget(puan_sub)
        hl.addWidget(puan_frame)
        v.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background: {T['bg_primary']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 24, 28, 28)
        cl.setSpacing(20)

        # Malzemeler
        malz_title = QLabel("🧂 Malzemeler")
        malz_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        cl.addWidget(malz_title)

        malz_grid = QGridLayout()
        malz_grid.setSpacing(8)
        for i, m in enumerate(self.tarif.malzemeler):
            malz_frame = QFrame()
            malz_frame.setStyleSheet(f"""
                background: {T['bg_card']}; border: 1px solid {T['border']};
                border-radius: 10px;
            """)
            mfl = QHBoxLayout(malz_frame)
            mfl.setContentsMargins(12, 8, 12, 8)
            mfl.setSpacing(8)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {T['accent']}; background: transparent; font-size: 8px;")
            name_l = QLabel(m.malzeme_adi)
            name_l.setStyleSheet(f"color: {T['text_primary']}; background: transparent; font-weight: 500;")
            qty_l = QLabel(f"{m.miktar} {m.birim}")
            qty_l.setStyleSheet(f"color: {T['accent']}; background: transparent; font-weight: 700; font-size: 12px;")
            mfl.addWidget(dot)
            mfl.addWidget(name_l)
            mfl.addStretch()
            mfl.addWidget(qty_l)
            malz_grid.addWidget(malz_frame, i // 2, i % 2)
        cl.addLayout(malz_grid)

        # Talimatlar
        tal_title = QLabel("📋 Hazırlanış")
        tal_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        cl.addWidget(tal_title)

        for i, adim in enumerate(self.tarif.talimatlar.split("\n"), 1):
            adim = adim.strip()
            if not adim: continue
            adim_frame = QFrame()
            adim_frame.setStyleSheet(f"""
                background: {T['bg_card']}; border-radius: 10px;
                border-left: 3px solid {T['accent']};
                border-top: 1px solid {T['border']};
                border-right: 1px solid {T['border']};
                border-bottom: 1px solid {T['border']};
            """)
            adim_layout = QHBoxLayout(adim_frame)
            adim_layout.setContentsMargins(14, 10, 14, 10)
            adim_layout.setSpacing(12)
            num = QLabel(str(i))
            num.setFixedSize(28, 28)
            num.setAlignment(Qt.AlignCenter)
            num.setStyleSheet(f"""
                background-color: {T['accent']}; color: white;
                border-radius: 14px; font-weight: 700; font-size: 12px;
            """)
            text_clean = adim.lstrip("0123456789. ")
            text = QLabel(text_clean)
            text.setStyleSheet(f"color: {T['text_primary']}; background: transparent; line-height: 1.4;")
            text.setWordWrap(True)
            adim_layout.addWidget(num)
            adim_layout.addWidget(text, 1)
            cl.addWidget(adim_frame)

        # Değerlendirme
        onceki_puan = self.kullanici.puan_verdigi_tarifler.get(self.tarif.tarif_id)
        deger_title = QLabel("⭐ Değerlendirmeniz" if onceki_puan is not None else "⭐ Değerlendirme Yap")
        deger_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        cl.addWidget(deger_title)

        deger_frame = QFrame()
        deger_frame.setStyleSheet(f"""
            background-color: {T['bg_card']}; border-radius: 12px;
            border: 1px solid {T['border']};
        """)
        deger_layout = QVBoxLayout(deger_frame)
        deger_layout.setContentsMargins(18, 16, 18, 16)
        deger_layout.setSpacing(10)

        puan_row_w = QHBoxLayout()
        puan_lbl2 = QLabel("Puanınız:")
        puan_lbl2.setStyleSheet(f"color: {T['text_secondary']}; background: transparent; font-weight: 600;")
        puan_row_w.addWidget(puan_lbl2)

        if onceki_puan is not None:
            # Daha önce oy verilmiş — salt okunur göster
            self.yildiz_sec = YildizWidget(onceki_puan, salt_okunur=True, boyut=30)
            self.yildiz_sec.setStyleSheet("background: transparent;")
            puan_row_w.addWidget(self.yildiz_sec)
            puan_row_w.addStretch()
            deger_layout.addLayout(puan_row_w)
            zaten_lbl = QLabel(f"Bu tarife daha önce {onceki_puan} yıldız verdiniz. Değerlendirme değiştirilemez.")
            zaten_lbl.setStyleSheet(f"color: {T['text_muted']}; background: transparent; font-size: 12px;")
            zaten_lbl.setWordWrap(True)
            deger_layout.addWidget(zaten_lbl)
        else:
            # İlk kez oy veriyor
            self.yildiz_sec = YildizWidget(0, salt_okunur=False, boyut=30)
            self.yildiz_sec.setStyleSheet("background: transparent;")
            puan_row_w.addWidget(self.yildiz_sec)
            puan_row_w.addStretch()
            deger_layout.addLayout(puan_row_w)
            self.puan_lbl_goster = QLabel("Yukarıdan puan seçin")
            self.puan_lbl_goster.setStyleSheet(f"color: {T['text_muted']}; background: transparent; font-size: 12px;")
            self.yildiz_sec.puan_degisti.connect(lambda p: self.puan_lbl_goster.setText(
                f"{'⭐' * p}  —  {'Mükemmel! 🎉' if p == 5 else 'Çok İyi! 👍' if p == 4 else 'İyi 😊' if p == 3 else 'Orta 😐' if p == 2 else 'Kötü 😕'}"
            ))
            deger_layout.addWidget(self.puan_lbl_goster)
            self.yorum_input = QLineEdit()
            self.yorum_input.setPlaceholderText("Yorumunuzu yazın... (opsiyonel)")
            self.yorum_input.setMinimumHeight(40)
            deger_layout.addWidget(self.yorum_input)
            gonder_btn = QPushButton("  Değerlendirmeyi Gönder")
            gonder_btn.setMaximumWidth(240)
            gonder_btn.setMinimumHeight(38)
            gonder_btn.clicked.connect(self._degerlendir)
            deger_layout.addWidget(gonder_btn)

        cl.addWidget(deger_frame)

        # Yorumlar
        if self.tarif.yorumlar:
            yor_title = QLabel(f"💬 Yorumlar ({len(self.tarif.yorumlar)})")
            yor_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
            cl.addWidget(yor_title)

            for yor in reversed(self.tarif.yorumlar[-10:]):
                yor_frame = QFrame()
                yor_frame.setStyleSheet(f"""
                    background-color: {T['bg_secondary']}; border-radius: 10px;

                """)
                yl = QVBoxLayout(yor_frame)
                yl.setContentsMargins(14, 10, 14, 10)
                yl.setSpacing(4)
                kul = QLabel(f"👤 {yor['kullanici']}  •  {yor.get('tarih', '')}")
                kul.setStyleSheet(f"color: {T['text_secondary']}; font-size: 11px; font-weight: 600; background: transparent;")
                yorum = QLabel(yor['yorum'])
                yorum.setStyleSheet(f"color: {T['text_primary']}; background: transparent;")
                yorum.setWordWrap(True)
                yl.addWidget(kul)
                yl.addWidget(yorum)
                cl.addWidget(yor_frame)

        cl.addStretch()
        scroll.setWidget(content)
        v.addWidget(scroll)

    def _degerlendir(self):
        if self.tarif.tarif_id in self.kullanici.puan_verdigi_tarifler:
            QMessageBox.warning(self, "Uyarı", "Bu tarifi zaten değerlendirdiniz. Her tarife yalnızca bir kez oy verebilirsiniz.")
            return
        if self.yildiz_sec.puan == 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir puan seçin!")
            return
        self.kullanici.tarif_degerlendir(self.tarif, self.yildiz_sec.puan, self.db.tarifler)
        yorum_text = self.yorum_input.text().strip()
        if yorum_text:
            self.tarif.yorumlar.append({
                "kullanici": self.kullanici.ad,
                "yorum": yorum_text,
                "tarih": datetime.now().strftime("%d.%m.%Y"),
            })
        QMessageBox.information(self, "Teşekkürler!", f"Değerlendirmeniz kaydedildi! Verdiğiniz puan: {'⭐' * self.yildiz_sec.puan}")
        self.accept()


# ─────────────────────────── ŞİFRE DEĞİŞTİR DİALOG ───────────────────────────

class SifreDegistirDialog(QDialog):
    def __init__(self, kullanici, tema, parent=None):
        super().__init__(parent)
        self.kullanici = kullanici
        self.tema = tema
        self.setWindowTitle("Şifre Değiştir")
        self.setFixedSize(400, 360)
        self.setStyleSheet(get_stylesheet(tema))
        self._build_ui()

    def _build_ui(self):
        T = self.tema
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(10)

        title = QLabel("🔒 Şifre Değiştir")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        v.addWidget(title)

        def mk_field(label, placeholder):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setEchoMode(QLineEdit.Password)
            inp.setMinimumHeight(42)
            v.addWidget(lbl)
            v.addWidget(inp)
            return inp

        self.mevcut_inp = mk_field("Mevcut Şifre", "Mevcut şifreniz")
        self.yeni_inp = mk_field("Yeni Şifre", "Yeni şifreniz (en az 6 karakter)")
        self.tekrar_inp = mk_field("Yeni Şifre Tekrar", "Yeni şifrenizi tekrar girin")

        self.hata_lbl = QLabel("")
        self.hata_lbl.setStyleSheet(f"color: {T['danger']}; font-size: 12px; background: transparent;")
        v.addWidget(self.hata_lbl)

        btn_row = QHBoxLayout()
        iptal = QPushButton("İptal")
        iptal.setObjectName("secondary_btn")
        iptal.clicked.connect(self.reject)
        kaydet = QPushButton("Değiştir")
        kaydet.clicked.connect(self._degistir)
        btn_row.addWidget(iptal)
        btn_row.addWidget(kaydet)
        v.addLayout(btn_row)

    def _degistir(self):
        mevcut = self.mevcut_inp.text()
        yeni = self.yeni_inp.text()
        tekrar = self.tekrar_inp.text()
        if not self.kullanici.sifre_dogru_mu(mevcut):
            self.hata_lbl.setText("⚠️ Mevcut şifre yanlış!"); return
        if len(yeni) < 6:
            self.hata_lbl.setText("⚠️ Yeni şifre en az 6 karakter olmalı!"); return
        if yeni != tekrar:
            self.hata_lbl.setText("⚠️ Şifreler eşleşmiyor!"); return
        self.kullanici.sifre_degistir(yeni)
        QMessageBox.information(self, "Başarılı", "Şifreniz güncellendi!")
        self.accept()


# ─────────────────────────── KULLANICI BİLGİ KARTI ───────────────────────────

class KullaniciBilgiDialog(QDialog):
    """Admin panelinde kullanıcı satırına tıklanınca açılan detay kartı."""

    RESULT_DELETE = 2   # özel dönüş kodu → silindi

    def __init__(self, kullanici, db, tema, parent=None):
        super().__init__(parent)
        self.kullanici = kullanici
        self.db = db
        self.tema = tema
        self._silindi = False
        self.setWindowTitle("Kullanıcı Bilgisi")
        self.setFixedSize(470, 560)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build_ui()

    # ── Arka plan ──────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0, QColor("#0e1117"))
        grad.setColorAt(1.0, QColor("#161b27"))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)

        T = self.tema
        is_admin = self.kullanici.rol == "admin"
        border_c = QColor(T.get("warning","#FDD663") if is_admin else T.get("accent_secondary","#5B9CF6"))
        border_c.setAlpha(70)
        painter.setPen(QPen(border_c, 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 20, 20)

        glow = QColor("#5B9CF6" if not is_admin else "#FDD663")
        glow.setAlpha(15)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QPoint(self.width(), 0), 220, 220)
        painter.end()

    # ── UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        k   = self.kullanici
        T   = self.tema
        is_admin = k.rol == "admin"
        ACCENT  = T.get("warning","#FDD663") if is_admin else T.get("accent_secondary","#5B9CF6")
        DANGER  = T.get("danger",  "#F28B82")
        SUCCESS = T.get("success", "#4CAF7D")
        TEXT    = T.get("text_primary",  "#E8EAED")
        MUTED   = T.get("text_muted",    "#5F6368")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 18, 28, 24)
        root.setSpacing(0)

        # ── X kapat ──
        xrow = QHBoxLayout()
        xrow.addStretch()
        x_btn = QPushButton("✕")
        x_btn.setFixedSize(28, 28)
        x_btn.setCursor(Qt.PointingHandCursor)
        x_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.07); color: {MUTED};
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 14px; font-size: 11px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {DANGER}bb; color: white; border-color: {DANGER}; }}
        """)
        x_btn.clicked.connect(self.reject)
        xrow.addWidget(x_btn)
        root.addLayout(xrow)
        root.addSpacing(6)

        # ── Avatar + isim ──
        av_row = QHBoxLayout()
        av_row.setSpacing(16)

        av = QFrame()
        av.setFixedSize(68, 68)
        av.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {ACCENT}, stop:1 {ACCENT}99);
                border-radius: 16px; border: 2px solid {ACCENT}55;
            }}
        """)
        avl = QVBoxLayout(av); avl.setContentsMargins(0,0,0,0)
        avlbl = QLabel((k.ad[0] if k.ad else "?").upper())
        avlbl.setAlignment(Qt.AlignCenter)
        avlbl.setStyleSheet("font-size: 28px; font-weight: 900; color: white; background: transparent;")
        avl.addWidget(avlbl)
        av_row.addWidget(av)

        name_col = QVBoxLayout(); name_col.setSpacing(4)
        parts = k.ad.split()
        full_lbl = QLabel(k.ad)
        full_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {TEXT}; background: transparent;")
        name_col.addWidget(full_lbl)

        rol_badge = QLabel(f"{'🛡️  ADMİN' if is_admin else '👤  KULLANICI'}")
        rol_badge.setFixedHeight(22)
        rol_badge.setStyleSheet(f"""
            font-size: 9px; font-weight: 900; letter-spacing: 2px;
            color: {ACCENT}; background: {ACCENT}22; border-radius: 8px; padding: 0 10px;
        """)
        name_col.addWidget(rol_badge)

        if not k.aktif:
            ban_badge = QLabel("🚫  YASAKLI")
            ban_badge.setFixedHeight(22)
            ban_badge.setStyleSheet(f"""
                font-size: 9px; font-weight: 900; letter-spacing: 2px;
                color: {DANGER}; background: {DANGER}22; border-radius: 8px; padding: 0 10px;
            """)
            name_col.addWidget(ban_badge)

        av_row.addLayout(name_col)
        av_row.addStretch()
        root.addLayout(av_row)
        root.addSpacing(18)

        # ── Bilgi satırı yardımcısı ──
        def info_row(icon, label, value, val_color=None):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.04);
                    border-radius: 10px;
                    border: 1px solid rgba(255,255,255,0.08);
                }
            """)
            hl = QHBoxLayout(frame)
            hl.setContentsMargins(14, 11, 14, 11)
            hl.setSpacing(12)
            ico = QLabel(icon)
            ico.setFixedWidth(22)
            ico.setStyleSheet(f"font-size: 14px; color: {ACCENT}; background: transparent;")
            lbl = QLabel(label)
            lbl.setFixedWidth(118)
            lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {MUTED}; background: transparent;")
            val = QLabel(str(value))
            val.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {val_color or TEXT}; background: transparent;")
            val.setWordWrap(True)
            hl.addWidget(ico); hl.addWidget(lbl); hl.addWidget(val, 1)
            return frame

        parts = k.ad.split()
        ad_str    = parts[0] if parts else k.ad
        soyad_str = " ".join(parts[1:]) if len(parts) > 1 else "—"

        root.addWidget(info_row("👤", "İsim",       ad_str))
        root.addSpacing(6)
        root.addWidget(info_row("👤", "Soyisim",    soyad_str))
        root.addSpacing(6)
        root.addWidget(info_row("✉️", "E-posta",     k.email))
        root.addSpacing(6)
        root.addWidget(info_row("📅", "Kayıt Tarihi", k.kayit_tarihi or "—"))
        root.addSpacing(6)

        eklenen = sum(1 for t in self.db.tarifler.values() if t.ekleyen == k.ad)
        root.addWidget(info_row("🍽️", "Eklenen Tarif", f"{eklenen} tarif", ACCENT))
        root.addSpacing(6)

        durum_renk = SUCCESS if k.aktif else DANGER
        durum_txt  = "✅  Aktif" if k.aktif else "🚫  Yasaklı"
        root.addWidget(info_row("📡", "Hesap Durumu", durum_txt, durum_renk))
        root.addSpacing(6)
        _sg = k.son_giris if hasattr(k, "son_giris") and k.son_giris else "Henüz giriş yapılmadı"
        root.addWidget(info_row("🕐", "Son Giriş", _sg))

        root.addSpacing(22)

        # ── Butonlar ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        if is_admin:
            # Admin kartı: sadece Kapat butonu
            kapat_btn = QPushButton("✕  Kapat")
            kapat_btn.setMinimumHeight(44)
            kapat_btn.setCursor(Qt.PointingHandCursor)
            kapat_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.06);
                    color: {MUTED};
                    border: 1.5px solid rgba(255,255,255,0.12);
                    border-radius: 10px; font-size: 13px; font-weight: 700;
                }}
                QPushButton:hover {{
                    background: rgba(255,255,255,0.12);
                    color: {TEXT};
                    border-color: rgba(255,255,255,0.25);
                }}
            """)
            kapat_btn.clicked.connect(self.reject)
            btn_row.addWidget(kapat_btn)

        # Kullanıcıyı Sil (admin silinemez)
        if not is_admin:
            sil_btn = QPushButton("🗑️  Kullanıcıyı Sil")
            sil_btn.setMinimumHeight(44)
            sil_btn.setCursor(Qt.PointingHandCursor)
            sil_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {DANGER}1A;
                    color: {DANGER};
                    border: 1.5px solid {DANGER}66;
                    border-radius: 10px; font-size: 13px; font-weight: 700;
                }}
                QPushButton:hover {{
                    background: {DANGER};
                    color: white;
                    border-color: {DANGER};
                }}
            """)

            def sil_kullanici():
                cevap = QMessageBox.question(
                    self, "Kullanıcıyı Sil",
                    f"<b>{k.ad}</b> adlı kullanıcı kalıcı olarak silinecek.\n"
                    f"Bu işlem geri alınamaz. Emin misiniz?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if cevap == QMessageBox.Yes:
                    self.db.kullanicilar.pop(k.kullanici_id, None)
                    self._silindi = True
                    self.done(KullaniciBilgiDialog.RESULT_DELETE)

            sil_btn.clicked.connect(sil_kullanici)
            btn_row.addWidget(sil_btn)

        # Yasakla / Yasağı kaldır (admin hariç)
        if not is_admin:
            if k.aktif:
                ban_label = "🚫  Kullanıcıyı Yasakla"
                ban_color = "#F97316"
            else:
                ban_label = "✅  Yasağı Kaldır"
                ban_color = SUCCESS

            ban_btn = QPushButton(ban_label)
            ban_btn.setMinimumHeight(44)
            ban_btn.setCursor(Qt.PointingHandCursor)
            ban_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {ban_color}1A;
                    color: {ban_color};
                    border: 1.5px solid {ban_color}66;
                    border-radius: 10px; font-size: 13px; font-weight: 700;
                }}
                QPushButton:hover {{
                    background: {ban_color};
                    color: white;
                    border-color: {ban_color};
                }}
            """)

            def toggle_ban():
                k.aktif = not k.aktif
                durum = "yasaklandı" if not k.aktif else "yasağı kaldırıldı"
                QMessageBox.information(self, "İşlem Tamam",
                                        f"'{k.ad}' adlı kullanıcı {durum}.")
                self.accept()

            ban_btn.clicked.connect(toggle_ban)
            btn_row.addWidget(ban_btn)

        root.addLayout(btn_row)


# ─────────────────────────── TARİF EKLE/DÜZENLE DIALOG ───────────────────────────

class TarifFormDialog(QDialog):
    def __init__(self, db, tema, kullanici, tarif=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.tema = tema
        self.kullanici = kullanici
        self.tarif = tarif
        self.malzeme_satirlari = []
        self._gorsel_yolu = ""   # seçilen görsel dosya yolu
        self.setWindowTitle("Tarif Düzenle" if tarif else "Yeni Tarif Ekle")
        self.resize(640, 800)
        self.setStyleSheet(get_stylesheet(tema))
        self._build_ui()
        if tarif: self._doldur()

    def _build_ui(self):
        T = self.tema
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background: {T['bg_primary']};")
        v = QVBoxLayout(content)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(12)

        title_lbl = QLabel("Yeni Tarif Ekle" if not self.tarif else "✏️ Tarif Düzenle")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        v.addWidget(title_lbl)

        def add_row(label, widget):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
            v.addWidget(lbl)
            v.addWidget(widget)

        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Tarif adını girin")
        self.ad_input.setMinimumHeight(42)
        add_row("Tarif Adı *", self.ad_input)

        self.kategori_combo = QComboBox()
        self.kategori_combo.addItems(["Kahvaltı", "Çorba", "Ana Yemek", "Tatlı", "İçecek", "Salata"])
        self.kategori_combo.setMinimumHeight(42)
        add_row("Kategori", self.kategori_combo)

        self.sure_spin = QSpinBox()
        self.sure_spin.setRange(1, 480)
        self.sure_spin.setValue(30)
        self.sure_spin.setSuffix(" dakika")
        self.sure_spin.setMinimumHeight(42)
        add_row("Hazırlama Süresi", self.sure_spin)

        self.emoji_combo = QComboBox()
        emojiler = [("🍳", "Kahvaltı"), ("🥣", "Çorba"), ("🍆", "Sebze"), ("🍗", "Et"),
                    ("🍮", "Tatlı"), ("🥐", "Börek"), ("🥛", "İçecek"), ("🍯", "Hamur"),
                    ("🥗", "Salata"), ("🫑", "Dolma"), ("🍝", "Makarna"), ("🍕", "Pizza"),
                    ("🍔", "Burger"), ("🥘", "Güveç"), ("🍜", "Çorba"), ("🫕", "Yahni")]
        for emoji, desc in emojiler:
            self.emoji_combo.addItem(f"{emoji}  {desc}", emoji)
        self.emoji_combo.setMinimumHeight(42)
        add_row("Görsel (Emoji)", self.emoji_combo)

        # ── Fotoğraf Yükleme ──
        gorsel_lbl = QLabel("Tarif Görseli (İsteğe Bağlı)")
        gorsel_lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        v.addWidget(gorsel_lbl)

        gorsel_row = QHBoxLayout()
        self.gorsel_onizleme = QLabel()
        self.gorsel_onizleme.setFixedSize(80, 80)
        self.gorsel_onizleme.setAlignment(Qt.AlignCenter)
        self.gorsel_onizleme.setStyleSheet(f"""
            background: {T['bg_secondary']}; border: 2px dashed {T['border']};
            border-radius: 10px; font-size: 28px;
        """)
        self.gorsel_onizleme.setText("🖼️")
        gorsel_row.addWidget(self.gorsel_onizleme)

        gorsel_btn_col = QVBoxLayout()
        gorsel_btn_col.setSpacing(6)
        self.gorsel_sec_btn = QPushButton("📁  Görsel Seç")
        self.gorsel_sec_btn.setObjectName("secondary_btn")
        self.gorsel_sec_btn.setMinimumHeight(38)
        self.gorsel_sec_btn.setCursor(Qt.PointingHandCursor)
        self.gorsel_sec_btn.clicked.connect(self._gorsel_sec)
        gorsel_temizle_btn = QPushButton("✕  Kaldır")
        gorsel_temizle_btn.setMinimumHeight(32)
        gorsel_temizle_btn.setStyleSheet(f"""
            QPushButton {{ background: {T['danger']}18; color: {T['danger']};
                border: 1px solid {T['danger']}44; border-radius: 8px; font-size: 11px; }}
            QPushButton:hover {{ background: {T['danger']}; color: white; }}
        """)
        gorsel_temizle_btn.setCursor(Qt.PointingHandCursor)
        gorsel_temizle_btn.clicked.connect(self._gorsel_temizle)
        self.gorsel_yol_lbl = QLabel("Görsel seçilmedi")
        self.gorsel_yol_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 11px; background: transparent;")
        self.gorsel_yol_lbl.setWordWrap(True)
        gorsel_btn_col.addWidget(self.gorsel_sec_btn)
        gorsel_btn_col.addWidget(gorsel_temizle_btn)
        gorsel_btn_col.addWidget(self.gorsel_yol_lbl)
        gorsel_row.addLayout(gorsel_btn_col)
        gorsel_row.addStretch()
        v.addLayout(gorsel_row)

        malz_lbl = QLabel("Malzemeler *")
        malz_lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        v.addWidget(malz_lbl)

        self.malzeme_container = QWidget()
        self.malzeme_container.setStyleSheet("background: transparent;")
        self.malzeme_layout = QVBoxLayout(self.malzeme_container)
        self.malzeme_layout.setContentsMargins(0, 0, 0, 0)
        self.malzeme_layout.setSpacing(6)
        v.addWidget(self.malzeme_container)
        self._malzeme_satiri_ekle()
        self._malzeme_satiri_ekle()

        malz_ekle_btn = QPushButton("+ Malzeme Ekle")
        malz_ekle_btn.setObjectName("secondary_btn")
        malz_ekle_btn.setMaximumWidth(160)
        malz_ekle_btn.setMinimumHeight(34)
        malz_ekle_btn.clicked.connect(self._malzeme_satiri_ekle)
        v.addWidget(malz_ekle_btn)

        tal_lbl = QLabel("Hazırlanış Talimatları *")
        tal_lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        v.addWidget(tal_lbl)

        tal_hint = QLabel("Her adımı yeni satıra yazın: '1. Soğanı kavurun.'")
        tal_hint.setStyleSheet(f"color: {T['text_muted']}; font-size: 11px; background: transparent;")
        v.addWidget(tal_hint)

        self.talimat_input = QTextEdit()
        self.talimat_input.setPlaceholderText("1. İlk adım...\n2. İkinci adım...\n3. Üçüncü adım...")
        self.talimat_input.setMinimumHeight(160)
        v.addWidget(self.talimat_input)

        self.hata_lbl = QLabel("")
        self.hata_lbl.setStyleSheet(f"color: {T['danger']}; font-size: 12px; background: transparent;")
        v.addWidget(self.hata_lbl)

        btn_row = QHBoxLayout()
        iptal = QPushButton("İptal")
        iptal.setObjectName("secondary_btn")
        iptal.setMinimumHeight(42)
        iptal.clicked.connect(self.reject)
        kaydet = QPushButton("💾  Kaydet")
        kaydet.setMinimumHeight(42)
        kaydet.clicked.connect(self.kaydet)
        btn_row.addWidget(iptal)
        btn_row.addWidget(kaydet)
        v.addLayout(btn_row)

        scroll.setWidget(content)
        main_l = QVBoxLayout(self)
        main_l.setContentsMargins(0, 0, 0, 0)
        main_l.addWidget(scroll)

    def _malzeme_satiri_ekle(self, malzeme=None):
        T = self.tema
        row = QHBoxLayout()
        row.setSpacing(6)

        ad = QLineEdit()
        ad.setPlaceholderText("Malzeme adı")
        ad.setMinimumHeight(38)

        miktar = QDoubleSpinBox()
        miktar.setRange(0.1, 9999)
        miktar.setValue(1)
        miktar.setMinimumHeight(38)
        miktar.setFixedWidth(90)

        birim = QComboBox()
        birim.addItems(["adet", "gram", "kg", "ml", "litre", "su bardağı",
                        "çay kaşığı", "tatlı kaşığı", "yemek kaşığı", "demet", "diş", "tutam", "paket"])
        birim.setMinimumHeight(38)
        birim.setFixedWidth(120)

        sil_btn = QPushButton("✕")
        sil_btn.setFixedSize(36, 36)
        sil_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T['danger']}22; color: {T['danger']};
                border: 1px solid {T['danger']}44; border-radius: 8px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {T['danger']}; color: white; }}
        """)

        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row_widget)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)
        rl.addWidget(ad, 1)
        rl.addWidget(miktar)
        rl.addWidget(birim)
        rl.addWidget(sil_btn)

        if malzeme:
            ad.setText(malzeme.malzeme_adi)
            miktar.setValue(float(malzeme.miktar))
            idx = birim.findText(malzeme.birim)
            if idx >= 0: birim.setCurrentIndex(idx)

        self.malzeme_satirlari.append((ad, miktar, birim, row_widget))
        self.malzeme_layout.addWidget(row_widget)
        sil_btn.clicked.connect(lambda: self._malzeme_satiri_sil(row_widget, (ad, miktar, birim, row_widget)))

    def _malzeme_satiri_sil(self, widget, satir):
        if len(self.malzeme_satirlari) <= 1: return
        if satir in self.malzeme_satirlari: self.malzeme_satirlari.remove(satir)
        widget.setParent(None)

    def _doldur(self):
        t = self.tarif
        self.ad_input.setText(t.tarif_adi)
        idx = self.kategori_combo.findText(t.kategori)
        if idx >= 0: self.kategori_combo.setCurrentIndex(idx)
        self.sure_spin.setValue(t.hazirlama_suresi)
        for i in range(self.emoji_combo.count()):
            if self.emoji_combo.itemData(i) == t.gorsel_emoji:
                self.emoji_combo.setCurrentIndex(i); break
        self.talimat_input.setPlainText(t.talimatlar)
        for _ in range(len(self.malzeme_satirlari)):
            w = self.malzeme_satirlari[0][-1]
            self.malzeme_satirlari.pop(0)
            w.setParent(None)
        for m in t.malzemeler:
            self._malzeme_satiri_ekle(m)
        # Mevcut görseli doldur
        if hasattr(t, 'gorsel_yolu') and t.gorsel_yolu:
            self._gorsel_yolu = t.gorsel_yolu
            pixmap = QPixmap(t.gorsel_yolu)
            T = self.tema
            if not pixmap.isNull():
                pixmap = pixmap.scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.gorsel_onizleme.setPixmap(pixmap)
                self.gorsel_onizleme.setStyleSheet(f"""
                    background: {T['bg_secondary']}; border: 2px solid {T['accent']};
                    border-radius: 10px;
                """)
            kisa_ad = t.gorsel_yolu.split("/")[-1] if "/" in t.gorsel_yolu else t.gorsel_yolu.split("\\")[-1]
            self.gorsel_yol_lbl.setText(kisa_ad)

    def kaydet(self):
        import re
        ad = self.ad_input.text().strip()
        if not ad:
            self.hata_lbl.setText("⚠️ Tarif adı boş olamaz!"); return
        if not re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ0-9 ]+$', ad):
            self.hata_lbl.setText("⚠️ Tarif adında yalnızca harf ve rakam kullanılabilir!"); return
        malzemeler = []
        for (ad_inp, miktar_inp, birim_inp, _) in self.malzeme_satirlari:
            if ad_inp.text().strip():
                malzemeler.append(Malzeme(ad_inp.text().strip(), miktar_inp.value(), birim_inp.currentText()))
        if not malzemeler:
            self.hata_lbl.setText("⚠️ En az bir malzeme gerekli!"); return
        if not self.talimat_input.toPlainText().strip():
            self.hata_lbl.setText("⚠️ Talimatlar boş olamaz!"); return

        if self.tarif:
            self.tarif.tarif_guncelle(
                tarif_adi=ad, kategori=self.kategori_combo.currentText(),
                hazirlama_suresi=self.sure_spin.value(), malzemeler=malzemeler,
                talimatlar=self.talimat_input.toPlainText(),
                gorsel_yolu=self._gorsel_yolu,
            )
            self.tarif.gorsel_emoji = self.emoji_combo.currentData()
        else:
            yeni_id = self.db.sonraki_tarif_id()
            tarif = Tarif(
                tarif_id=yeni_id, tarif_adi=ad,
                kategori=self.kategori_combo.currentText(),
                hazirlama_suresi=self.sure_spin.value(),
                malzemeler=malzemeler, talimatlar=self.talimat_input.toPlainText(),
                gorsel_emoji=self.emoji_combo.currentData(), ekleyen=self.kullanici.ad,
                gorsel_yolu=self._gorsel_yolu,
            )
            self.db.tarifler[yeni_id] = tarif
        self.accept()

    def _gorsel_sec(self):
        T = self.tema
        dosya, _ = QFileDialog.getOpenFileName(
            self, "Tarif Görseli Seç", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if dosya:
            self._gorsel_yolu = dosya
            kisa_ad = dosya.split("/")[-1] if "/" in dosya else dosya.split("\\")[-1]
            self.gorsel_yol_lbl.setText(kisa_ad)
            pixmap = QPixmap(dosya)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.gorsel_onizleme.setPixmap(pixmap)
                self.gorsel_onizleme.setStyleSheet(f"""
                    background: {T['bg_secondary']}; border: 2px solid {T['accent']};
                    border-radius: 10px;
                """)

    def _gorsel_temizle(self):
        T = self.tema
        self._gorsel_yolu = ""
        self.gorsel_yol_lbl.setText("Görsel seçilmedi")
        self.gorsel_onizleme.setPixmap(QPixmap())
        self.gorsel_onizleme.setText("🖼️")
        self.gorsel_onizleme.setStyleSheet(f"""
            background: {T['bg_secondary']}; border: 2px dashed {T['border']};
            border-radius: 10px; font-size: 28px;
        """)


# ─────────────────────────── KULLANICI PANELİ ───────────────────────────

class KullaniciPaneli(QWidget):
    def __init__(self, db, kullanici, tema_degistir_cb, cikas_cb, parent=None):
        super().__init__(parent)
        self.db = db
        self.kullanici = kullanici
        self.tema_degistir_cb = tema_degistir_cb
        self.cikas_cb = cikas_cb
        self.aktif_tema = GECE_MODU
        self._build_ui()

    def set_tema(self, tema):
        self.aktif_tema = tema

    def _build_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        self.main_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack, 1)

        self.tarifler_sayfasi = self._build_tarifler_sayfasi()
        self.favoriler_sayfasi = self._build_favoriler_sayfasi()
        self.tarif_ekle_sayfasi = self._build_tarif_ekle_sayfasi()
        self.profil_sayfasi = self._build_profil_sayfasi()

        self.stack.addWidget(self.tarifler_sayfasi)
        self.stack.addWidget(self.favoriler_sayfasi)
        self.stack.addWidget(self.tarif_ekle_sayfasi)
        self.stack.addWidget(self.profil_sayfasi)

    def _build_sidebar(self):
        T = self.aktif_tema
        sidebar = QFrame()
        sidebar.setObjectName("sidebar_frame")
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet(f"""
            QFrame#sidebar_frame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #050510, stop:0.5 #080818, stop:1 #050510);
                border-right: 1px solid {T.get('border_neon','#00E5FF')}44;
            }}
        """)

        v = QVBoxLayout(sidebar)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── TOP HUD BAR ──
        top_bar = HUDTopBar(self.kullanici, T)
        v.addWidget(top_bar)

        # ── NAV ITEMS ──
        nav_scroll_area = QWidget()
        nav_scroll_area.setStyleSheet("background: transparent;")
        nav_v = QVBoxLayout(nav_scroll_area)
        nav_v.setContentsMargins(12, 16, 12, 12)
        nav_v.setSpacing(6)

        self.nav_btns = []
        nav_items = [
            ("🍽", "Tarifler", "Tüm tarifleri keşfet", 0),
            ("❤", "Favorilerim", "Kayıtlı tariflerim", 1),
            ("✚", "Tarif Ekle", "Yeni tarif paylaş", 2),
            ("◉", "Profilim", "Hesap bilgilerim", 3),
        ]
        for icon, metin, aciklama, idx in nav_items:
            btn = HUDNavButton(icon, metin, aciklama, T)
            btn.clicked.connect(lambda checked, i=idx: self._sayfa_degistir(i))
            self.nav_btns.append(btn)
            nav_v.addWidget(btn)

        nav_v.addStretch()

        # Divider
        div_frame = QFrame()
        div_frame.setFixedHeight(1)
        div_frame.setStyleSheet(f"background: {T.get('border_neon','#00E5FF')}33; border: none;")
        nav_v.addWidget(div_frame)
        nav_v.addSpacing(8)

        # Ayarlar
        settings_lbl = QLabel("◈  SISTEM")
        settings_lbl.setStyleSheet(f"""
            font-size: 9px; font-weight: 900; letter-spacing: 3px;
            color: {T.get('border_neon','#00E5FF')}99; background: transparent;
            padding-left: 16px;
        """)
        nav_v.addWidget(settings_lbl)
        nav_v.addSpacing(4)

        cikis_btn = HUDActionButton("⏻  Çıkış Yap", T, "danger")
        cikis_btn.clicked.connect(self.cikas_cb)
        nav_v.addWidget(cikis_btn)

        v.addWidget(nav_scroll_area, 1)

        # ── BOTTOM STATUS BAR ──
        bottom_bar = HUDBottomBar(T)
        v.addWidget(bottom_bar)

        self.nav_btns[0].setChecked(True)
        return sidebar

    def _sayfa_degistir(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == idx)
        if idx == 1:
            self._favoriler_guncelle()
        elif idx == 3:
            self._profil_guncelle()

    def _build_tarifler_sayfasi(self):
        page = QWidget()
        page.setStyleSheet("background: #0f0f0f;")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setFixedHeight(64)
        topbar.setStyleSheet("background: #0f0f0f; border-bottom: 0.5px solid #2a2a2a;")
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(28, 0, 28, 0)
        tbl.setSpacing(12)

        title = QLabel("Tarifler")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #e8d5b0; background: transparent;")
        tbl.addWidget(title)
        tbl.addStretch()

        self.arama_input = QLineEdit()
        self.arama_input.setPlaceholderText("Tarif ara...")
        self.arama_input.setFixedWidth(200)
        self.arama_input.setMinimumHeight(36)
        self.arama_input.setStyleSheet("""
            QLineEdit {
                background: #141414; border: 0.5px solid #2a2a2a;
                border-radius: 8px; padding: 0 12px;
                color: #b0a090; font-size: 13px;
            }
            QLineEdit:focus { border-color: #3a3a3a; }
        """)
        self.arama_input.textChanged.connect(self._filtrele)
        tbl.addWidget(self.arama_input)

        self.kategori_filtre = QComboBox()
        self.kategori_filtre.addItems(["Tümü", "Kahvaltı", "Çorba", "Ana Yemek", "Tatlı", "İçecek", "Salata"])
        self.kategori_filtre.setMinimumHeight(36)
        self.kategori_filtre.setStyleSheet("""
            QComboBox {
                background: #141414; border: 0.5px solid #2a2a2a;
                border-radius: 8px; padding: 0 12px;
                color: #b0a090; font-size: 13px; min-width: 130px;
            }
            QComboBox:focus { border-color: #c9713a; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background: #1a1a1a; border: 0.5px solid #2a2a2a;
                color: #b0a090; selection-background-color: #1e1a15;
            }
        """)
        self.kategori_filtre.currentTextChanged.connect(self._filtrele)
        tbl.addWidget(self.kategori_filtre)

        sirala_combo = QComboBox()
        sirala_combo.addItems(["★ Puana Göre", "⏱ Süreye Göre", "A-Z Alfabetik", "👁 Görüntüleme"])
        sirala_combo.setMinimumHeight(36)
        sirala_combo.setStyleSheet("""
            QComboBox {
                background: #141414; border: 0.5px solid #2a2a2a;
                border-radius: 8px; padding: 0 12px;
                color: #b0a090; font-size: 13px; min-width: 140px;
            }
            QComboBox:focus { border-color: #c9713a; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background: #1a1a1a; border: 0.5px solid #2a2a2a;
                color: #b0a090; selection-background-color: #1e1a15;
            }
        """)
        sirala_combo.currentIndexChanged.connect(lambda i: self._sirala(i))
        tbl.addWidget(sirala_combo)
        v.addWidget(topbar)

        # ── İçerik alanı: sol kart grid + sağ sabit trendler paneli ──
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)

        # ── Sol: Kart grid alanı ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: #0f0f0f; border: none; }
            QScrollBar:vertical {
                background: transparent; width: 5px; border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #2a2a2a; border-radius: 2px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: #0f0f0f;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(24, 20, 24, 20)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll.setWidget(self.grid_widget)
        content_row.addWidget(scroll, 1)

        # ── Sağ: SABİT Trendler Paneli ──
        trend_panel = QFrame()
        trend_panel.setFixedWidth(230)
        trend_panel.setStyleSheet("""
            QFrame {
                background: #0c0c0c;
                border-left: 0.5px solid #2a2a2a;
            }
        """)
        trend_v = QVBoxLayout(trend_panel)
        trend_v.setContentsMargins(16, 20, 16, 20)
        trend_v.setSpacing(14)

        trend_title = QLabel("🔥 Trendler")
        trend_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #e8d5b0; background: transparent;")
        trend_v.addWidget(trend_title)

        # En çok puanlı tarifler
        top_tarifler = sorted(self.db.tarifler.values(), key=lambda t: t.puan, reverse=True)[:5]
        for i, tarif in enumerate(top_tarifler):
            item_frame = QFrame()
            item_frame.setStyleSheet("""
                QFrame {
                    background: #141414;
                    border-radius: 8px;
                    border: 0.5px solid #2a2a2a;
                }
                QFrame:hover { border-color: #c9713a44; }
            """)
            item_frame.setCursor(Qt.PointingHandCursor)
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(10, 8, 10, 8)
            item_layout.setSpacing(8)

            rank_lbl = QLabel(["🥇","🥈","🥉","4️⃣","5️⃣"][i])
            rank_lbl.setStyleSheet("font-size: 14px; background: transparent;")
            rank_lbl.setFixedWidth(22)
            item_layout.addWidget(rank_lbl)

            info_v = QVBoxLayout()
            info_v.setSpacing(1)
            name_lbl = QLabel(tarif.tarif_adi)
            name_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #c8b89a; background: transparent;")
            name_lbl.setWordWrap(False)
            star_lbl = QLabel(f"⭐ {tarif.puan:.1f}  •  {tarif.kategori}")
            star_lbl.setStyleSheet("font-size: 9px; color: #666; background: transparent;")
            info_v.addWidget(name_lbl)
            info_v.addWidget(star_lbl)
            item_layout.addLayout(info_v)

            trend_v.addWidget(item_frame)

        # Kategori dağılımı
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #2a2a2a; border: none;")
        trend_v.addWidget(div)

        cat_title = QLabel("📊 Kategori Dağılımı")
        cat_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #888; background: transparent;")
        trend_v.addWidget(cat_title)

        from collections import Counter
        kat_sayilari = Counter(t.kategori for t in self.db.tarifler.values())
        kat_renkler = {"Kahvaltı": "#c9713a", "Çorba": "#6b8a6b", "Ana Yemek": "#5B9CF6",
                       "Tatlı": "#CE93D8", "İçecek": "#4CAF7D", "Salata": "#FDD663"}

        for kat, sayi in kat_sayilari.most_common(6):
            kat_row = QHBoxLayout()
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background: {kat_renkler.get(kat, '#888')}; border-radius: 4px;")
            kat_row.addWidget(dot)
            kat_lbl = QLabel(kat)
            kat_lbl.setStyleSheet("font-size: 10px; color: #888; background: transparent;")
            kat_row.addWidget(kat_lbl)
            kat_row.addStretch()
            sayi_lbl = QLabel(str(sayi))
            sayi_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {kat_renkler.get(kat, '#888')}; background: transparent;")
            kat_row.addWidget(sayi_lbl)
            trend_v.addLayout(kat_row)

        trend_v.addStretch()

        content_row.addWidget(trend_panel)
        v.addLayout(content_row)

        self._tarifleri_yukle()
        return page

    def _tarifleri_yukle(self, tarifler=None):
        T = self.aktif_tema
        if tarifler is None:
            tarifler = list(self.db.tarifler.values())
            tarifler.sort(key=lambda t: t.puan, reverse=True)

        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        cols = 3
        for i, tarif in enumerate(tarifler):
            kart = HUDTarifKarti(tarif, T, self.kullanici)
            kart.tiklandi.connect(self._tarif_detay_goster)
            self.grid_layout.addWidget(kart, i // cols, i % cols)

    def _filtrele(self):
        arama = self.arama_input.text().lower()
        kat = self.kategori_filtre.currentText()
        sonuclar = [
            t for t in self.db.tarifler.values()
            if (not arama or arama in t.tarif_adi.lower() or
                arama in t.kategori.lower() or
                any(arama in m.malzeme_adi.lower() for m in t.malzemeler))
            and (kat == "Tümü" or t.kategori == kat)
        ]
        # Mevcut sıralama tercihini koru
        idx = self._aktif_siralama if hasattr(self, '_aktif_siralama') else 0
        if idx == 0: sonuclar.sort(key=lambda t: t.puan, reverse=True)
        elif idx == 1: sonuclar.sort(key=lambda t: t.hazirlama_suresi)
        elif idx == 2: sonuclar.sort(key=lambda t: t.tarif_adi)
        elif idx == 3: sonuclar.sort(key=lambda t: t.goruntuleme, reverse=True)
        self._tarifleri_yukle(sonuclar)

    def _sirala(self, idx):
        self._aktif_siralama = idx
        self._filtrele()

    def _tarif_detay_goster(self, tarif_id):
        tarif = self.db.tarifler.get(tarif_id)
        if tarif:
            tarif.goruntuleme += 1
            d = TarifDetayDialog(tarif, self.db, self.kullanici, self.aktif_tema, self)
            d.exec_()

    def _build_favoriler_sayfasi(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        v = QVBoxLayout(page)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(16)

        title = QLabel("Favorilerim")
        title.setObjectName("header_label")
        v.addWidget(title)

        self.fav_scroll = QScrollArea()
        self.fav_scroll.setWidgetResizable(True)
        self.fav_scroll.setFrameShape(QFrame.NoFrame)

        self.fav_widget = QWidget()
        self.fav_widget.setStyleSheet("background: transparent;")
        self.fav_grid = QGridLayout(self.fav_widget)
        self.fav_grid.setSpacing(16)
        self.fav_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.fav_scroll.setWidget(self.fav_widget)
        v.addWidget(self.fav_scroll)
        return page

    def _favoriler_guncelle(self):
        T = self.aktif_tema
        while self.fav_grid.count():
            child = self.fav_grid.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        favoriler = [self.db.tarifler[fid] for fid in self.kullanici.favori_tarifler
                     if fid in self.db.tarifler]
        if not favoriler:
            lbl = QLabel("Henüz favori tarifiniz yok.\nTarif kartlarındaki  butonuna tıklayın!")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 15px; background: transparent;")
            self.fav_grid.addWidget(lbl, 0, 0)
            return

        cols = 4
        for i, tarif in enumerate(favoriler):
            kart = HUDTarifKarti(tarif, T, self.kullanici)
            kart.tiklandi.connect(self._tarif_detay_goster)
            self.fav_grid.addWidget(kart, i // cols, i % cols)

    def _build_tarif_ekle_sayfasi(self):
        T = self.aktif_tema
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar_frame")
        topbar.setFixedHeight(64)
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(28, 0, 28, 0)
        title = QLabel("Yeni Tarif Ekle")
        title.setObjectName("header_label")
        tbl.addWidget(title)
        tbl.addStretch()
        v.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background: {T['bg_primary']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 32, 40, 32)
        cl.setSpacing(14)

        form_frame = QFrame()
        form_frame.setObjectName("card_frame")
        fl = QVBoxLayout(form_frame)
        fl.setContentsMargins(32, 28, 32, 28)
        fl.setSpacing(12)

        def add_row(label, widget):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
            fl.addWidget(lbl)
            fl.addWidget(widget)

        ad_input = QLineEdit()
        ad_input.setPlaceholderText("Tarif adını girin")
        ad_input.setMinimumHeight(44)
        add_row("Tarif Adı *", ad_input)

        row1 = QHBoxLayout()
        row1.setSpacing(16)

        kat_col = QVBoxLayout()
        kat_lbl = QLabel("Kategori")
        kat_lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        kategori_combo = QComboBox()
        kategori_combo.addItems(["Kahvaltı", "Çorba", "Ana Yemek", "Tatlı", "İçecek", "Salata"])
        kategori_combo.setMinimumHeight(44)
        kat_col.addWidget(kat_lbl)
        kat_col.addWidget(kategori_combo)
        row1.addLayout(kat_col)

        sure_col = QVBoxLayout()
        sure_lbl_l = QLabel("Hazırlama Süresi")
        sure_lbl_l.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        sure_spin = QSpinBox()
        sure_spin.setRange(1, 480)
        sure_spin.setValue(30)
        sure_spin.setSuffix(" dakika")
        sure_spin.setMinimumHeight(44)
        sure_col.addWidget(sure_lbl_l)
        sure_col.addWidget(sure_spin)
        row1.addLayout(sure_col)

        fl.addLayout(row1)

        emoji_combo = QComboBox()
        emojiler = [("🍳", "Kahvaltı"), ("🥣", "Çorba"), ("🍆", "Sebze"), ("🍗", "Et"),
                    ("🍮", "Tatlı"), ("🥐", "Börek"), ("🥛", "İçecek"), ("🍯", "Hamur"),
                    ("🥗", "Salata"), ("🫑", "Dolma"), ("🍝", "Makarna"), ("🍕", "Pizza")]
        for emoji, desc in emojiler:
            emoji_combo.addItem(f"{emoji}  {desc}", emoji)
        emoji_combo.setMinimumHeight(44)
        add_row("Görsel (Emoji)", emoji_combo)

        # ── Fotoğraf Yükleme ──
        gorsel_secilen_yol = [""]   # mutable container

        gorsel_lbl_h = QLabel("Tarif Görseli (İsteğe Bağlı)")
        gorsel_lbl_h.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        fl.addWidget(gorsel_lbl_h)

        gorsel_row_h = QHBoxLayout()
        gorsel_onizleme_h = QLabel()
        gorsel_onizleme_h.setFixedSize(80, 80)
        gorsel_onizleme_h.setAlignment(Qt.AlignCenter)
        gorsel_onizleme_h.setStyleSheet(f"""
            background: {T['bg_secondary']}; border: 2px dashed {T['border']};
            border-radius: 10px; font-size: 28px;
        """)
        gorsel_onizleme_h.setText("🖼️")
        gorsel_row_h.addWidget(gorsel_onizleme_h)

        gorsel_btn_col_h = QVBoxLayout()
        gorsel_btn_col_h.setSpacing(6)
        gorsel_sec_btn_h = QPushButton("📁  Görsel Seç")
        gorsel_sec_btn_h.setObjectName("secondary_btn")
        gorsel_sec_btn_h.setMinimumHeight(38)
        gorsel_sec_btn_h.setCursor(Qt.PointingHandCursor)
        gorsel_temizle_btn_h = QPushButton("✕  Kaldır")
        gorsel_temizle_btn_h.setMinimumHeight(32)
        gorsel_temizle_btn_h.setStyleSheet(f"""
            QPushButton {{ background: {T['danger']}18; color: {T['danger']};
                border: 1px solid {T['danger']}44; border-radius: 8px; font-size: 11px; }}
            QPushButton:hover {{ background: {T['danger']}; color: white; }}
        """)
        gorsel_temizle_btn_h.setCursor(Qt.PointingHandCursor)
        gorsel_yol_lbl_h = QLabel("Görsel seçilmedi")
        gorsel_yol_lbl_h.setStyleSheet(f"color: {T['text_muted']}; font-size: 11px; background: transparent;")
        gorsel_yol_lbl_h.setWordWrap(True)

        def gorsel_sec_h():
            dosya, _ = QFileDialog.getOpenFileName(
                None, "Tarif Görseli Seç", "",
                "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
            )
            if dosya:
                gorsel_secilen_yol[0] = dosya
                kisa_ad = dosya.split("/")[-1] if "/" in dosya else dosya.split("\\")[-1]
                gorsel_yol_lbl_h.setText(kisa_ad)
                pixmap = QPixmap(dosya)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    gorsel_onizleme_h.setPixmap(pixmap)
                    gorsel_onizleme_h.setStyleSheet(f"""
                        background: {T['bg_secondary']}; border: 2px solid {T['accent']};
                        border-radius: 10px;
                    """)

        def gorsel_temizle_h():
            gorsel_secilen_yol[0] = ""
            gorsel_yol_lbl_h.setText("Görsel seçilmedi")
            gorsel_onizleme_h.setPixmap(QPixmap())
            gorsel_onizleme_h.setText("🖼️")
            gorsel_onizleme_h.setStyleSheet(f"""
                background: {T['bg_secondary']}; border: 2px dashed {T['border']};
                border-radius: 10px; font-size: 28px;
            """)

        gorsel_sec_btn_h.clicked.connect(gorsel_sec_h)
        gorsel_temizle_btn_h.clicked.connect(gorsel_temizle_h)
        gorsel_btn_col_h.addWidget(gorsel_sec_btn_h)
        gorsel_btn_col_h.addWidget(gorsel_temizle_btn_h)
        gorsel_btn_col_h.addWidget(gorsel_yol_lbl_h)
        gorsel_row_h.addLayout(gorsel_btn_col_h)
        gorsel_row_h.addStretch()
        fl.addLayout(gorsel_row_h)

        malz_lbl_w = QLabel("Malzemeler *")
        malz_lbl_w.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        fl.addWidget(malz_lbl_w)

        malzeme_satirlari = []
        malzeme_container = QWidget()
        malzeme_container.setStyleSheet("background: transparent;")
        malzeme_layout_w = QVBoxLayout(malzeme_container)
        malzeme_layout_w.setContentsMargins(0, 0, 0, 0)
        malzeme_layout_w.setSpacing(6)
        fl.addWidget(malzeme_container)

        def malzeme_satiri_ekle(malzeme=None):
            row_widget = QWidget()
            row_widget.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row_widget)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(8)
            ad_f = QLineEdit()
            ad_f.setPlaceholderText("Malzeme adı")
            ad_f.setMinimumHeight(38)
            miktar_f = QDoubleSpinBox()
            miktar_f.setRange(0.1, 9999)
            miktar_f.setValue(1)
            miktar_f.setMinimumHeight(38)
            miktar_f.setFixedWidth(90)
            birim_f = QComboBox()
            birim_f.addItems(["adet", "gram", "kg", "ml", "litre", "su bardağı", "yemek kaşığı", "tutam", "paket"])
            birim_f.setMinimumHeight(38)
            birim_f.setFixedWidth(120)
            sil_btn = QPushButton("✕")
            sil_btn.setFixedSize(36, 36)
            sil_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {T['danger']}22; color: {T['danger']};
                    border: 1px solid {T['danger']}44; border-radius: 8px; font-weight: 700;
                }}
                QPushButton:hover {{ background: {T['danger']}; color: white; }}
            """)
            rl.addWidget(ad_f, 1)
            rl.addWidget(miktar_f)
            rl.addWidget(birim_f)
            rl.addWidget(sil_btn)
            satir = (ad_f, miktar_f, birim_f, row_widget)
            malzeme_satirlari.append(satir)
            malzeme_layout_w.addWidget(row_widget)
            sil_btn.clicked.connect(lambda: (
                malzeme_satirlari.remove(satir) if satir in malzeme_satirlari else None,
                row_widget.setParent(None)
            ) if len(malzeme_satirlari) > 1 else None)

        malzeme_satiri_ekle()
        malzeme_satiri_ekle()

        malz_ekle_btn = QPushButton("+ Malzeme Ekle")
        malz_ekle_btn.setObjectName("secondary_btn")
        malz_ekle_btn.setMaximumWidth(160)
        malz_ekle_btn.setMinimumHeight(36)
        malz_ekle_btn.clicked.connect(malzeme_satiri_ekle)
        fl.addWidget(malz_ekle_btn)

        tal_lbl_w = QLabel("Hazırlanış Talimatları *")
        tal_lbl_w.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        fl.addWidget(tal_lbl_w)
        talimat_input = QTextEdit()
        talimat_input.setPlaceholderText("1. İlk adım...\n2. İkinci adım...\n3. Üçüncü adım...")
        talimat_input.setMinimumHeight(160)
        fl.addWidget(talimat_input)

        hata_lbl_w = QLabel("")
        hata_lbl_w.setStyleSheet(f"color: {T['danger']}; font-size: 12px; background: transparent;")
        fl.addWidget(hata_lbl_w)

        kaydet_btn = QPushButton("💾  Tarifi Kaydet")
        kaydet_btn.setMinimumHeight(48)
        kaydet_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {T['accent']}, stop:1 {T['accent_secondary']});
                color: white; border: none; border-radius: 12px;
                font-size: 15px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {T['accent_hover']}, stop:1 {T['accent_secondary']});
            }}
        """)

        def kaydet():
            ad = ad_input.text().strip()
            if not ad:
                hata_lbl_w.setText("⚠️ Tarif adı boş olamaz!"); return

            # Sadece harf (Türkçe dahil), rakam ve boşluğa izin ver
            import re
            if not re.match(r'^[a-zA-ZçÇğĞıİöÖşŞüÜ0-9 ]+$', ad):
                hata_lbl_w.setStyleSheet(f"color: {T['danger']}; font-size: 12px; background: transparent;")
                hata_lbl_w.setText("⚠️ Tarif adında yalnızca harf ve rakam kullanılabilir!"); return

            malzemeler = [
                Malzeme(a.text().strip(), m.value(), b.currentText())
                for a, m, b, _ in malzeme_satirlari if a.text().strip()
            ]
            if not malzemeler:
                hata_lbl_w.setStyleSheet(f"color: {T['danger']}; font-size: 12px; background: transparent;")
                hata_lbl_w.setText("⚠️ En az bir malzeme gerekli!"); return
            if not talimat_input.toPlainText().strip():
                hata_lbl_w.setStyleSheet(f"color: {T['danger']}; font-size: 12px; background: transparent;")
                hata_lbl_w.setText("⚠️ Talimatlar boş olamaz!"); return

            # Admin onayı bekleyen listeye ekle
            yeni_id = self.db.sonraki_tarif_id()
            tarif = Tarif(
                tarif_id=yeni_id,
                tarif_adi=ad,
                kategori=kategori_combo.currentText(),
                hazirlama_suresi=sure_spin.value(),
                malzemeler=malzemeler,
                talimatlar=talimat_input.toPlainText(),
                gorsel_emoji=emoji_combo.currentData(),
                ekleyen=self.kullanici.ad,
                gorsel_yolu=gorsel_secilen_yol[0],
            )
            self.db.bekleyen_tarifler[yeni_id] = tarif
            self.db.aktivite_logu.insert(0, {
                "tip": "tarif",
                "mesaj": f"{self.kullanici.ad} yeni tarif gönderdi: {ad} (onay bekliyor)",
                "zaman": "az önce",
                "renk": "#F59E0B"
            })

            # Formu temizle
            ad_input.clear()
            talimat_input.clear()
            hata_lbl_w.setStyleSheet(f"color: {T['success']}; font-size: 13px; background: transparent;")
            hata_lbl_w.setText(f"✅ '{ad}' tarifiniz admin onayına gönderildi! Onaylandıktan sonra görünecek.")

        kaydet_btn.clicked.connect(kaydet)
        fl.addWidget(kaydet_btn)

        cl.addWidget(form_frame)
        cl.addStretch()
        scroll.setWidget(content)
        v.addWidget(scroll)
        return page

    def _build_profil_sayfasi(self):
        T = self.aktif_tema
        page = QWidget()
        page.setStyleSheet("background: #0f0f0f;")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── Top bar ──
        topbar = QFrame()
        topbar.setFixedHeight(64)
        topbar.setStyleSheet("background: #0f0f0f; border-bottom: 0.5px solid #2a2a2a;")
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(28, 0, 28, 0)
        title_lbl = QLabel("Profilim")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #e8d5b0; background: transparent;")
        tbl.addWidget(title_lbl)
        tbl.addStretch()
        v.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: #0f0f0f; border: none; }
            QScrollBar:vertical { background: transparent; width: 5px; border-radius: 2px; }
            QScrollBar::handle:vertical { background: #2a2a2a; border-radius: 2px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        content = QWidget()
        content.setStyleSheet("background: #0f0f0f;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 24, 28, 28)
        cl.setSpacing(20)

        # ── Avatar + Kullanıcı Bilgi Kartı ──
        profil_card = QFrame()
        profil_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1208, stop:0.5 #141414, stop:1 #0e1208);
                border: 0.5px solid #2a2a2a;
                border-radius: 16px;
            }
        """)
        profil_card.setMinimumHeight(140)
        pl = QHBoxLayout(profil_card)
        pl.setContentsMargins(28, 24, 28, 24)
        pl.setSpacing(24)

        # Avatar (büyük, gradient arka plan)
        avatar_container = QFrame()
        avatar_container.setFixedSize(88, 88)
        avatar_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #c9713a, stop:1 #6b8a6b);
                border-radius: 12px;
                border: none;
            }
        """)
        abl = QVBoxLayout(avatar_container)
        abl.setContentsMargins(0, 0, 0, 0)
        self.profil_avatar_lbl = QLabel(self.kullanici.ad[0].upper() if self.kullanici.ad else "?")
        self.profil_avatar_lbl.setAlignment(Qt.AlignCenter)
        self.profil_avatar_lbl.setStyleSheet("font-size: 36px; font-weight: 900; color: white; background: transparent;")
        abl.addWidget(self.profil_avatar_lbl)
        pl.addWidget(avatar_container)

        # İsim + email + kayıt tarihi
        info_col = QVBoxLayout()
        info_col.setSpacing(6)
        self.profil_name_lbl = QLabel(self.kullanici.ad)
        self.profil_name_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #e8d5b0; background: transparent;")
        self.profil_email_lbl = QLabel(self.kullanici.email)
        self.profil_email_lbl.setStyleSheet("font-size: 13px; color: #7a7a7a; background: transparent;")
        since_lbl = QLabel(f"📅  Kayıt: {self.kullanici.kayit_tarihi}")
        since_lbl.setStyleSheet("font-size: 11px; color: #555555; background: transparent;")

        # Rol rozeti
        rol_badge = QLabel("◈  KULLANICI")
        rol_badge.setStyleSheet("""
            font-size: 9px; font-weight: 900; letter-spacing: 2px;
            color: #c9713a; background: #c9713a22;
            border-radius: 6px; padding: 3px 10px;
        """)
        rol_badge.setFixedHeight(20)

        info_col.addWidget(self.profil_name_lbl)
        info_col.addWidget(self.profil_email_lbl)
        info_col.addWidget(since_lbl)
        info_col.addSpacing(4)
        info_col.addWidget(rol_badge)
        pl.addLayout(info_col)
        pl.addStretch()

        # Şifre değiştir butonu (sağda)
        sifre_btn = QPushButton("🔒  Şifre Değiştir")
        sifre_btn.setFixedSize(160, 40)
        sifre_btn.setCursor(Qt.PointingHandCursor)
        sifre_btn.setStyleSheet("""
            QPushButton {
                background: #1e1e1e; border: 0.5px solid #3a3a3a;
                border-radius: 8px; color: #9a9a9a;
                font-size: 12px; font-weight: 600;
            }
            QPushButton:hover {
                background: #282828; border-color: #c9713a66;
                color: #c9713a;
            }
        """)
        sifre_btn.clicked.connect(self._sifre_degistir)
        pl.addWidget(sifre_btn, alignment=Qt.AlignVCenter)

        cl.addWidget(profil_card)

        # ── Platform İstatistikleri (Tariflerden Gelen) ──
        platform_title = QLabel("📊  Platform İstatistikleri")
        platform_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #7a7a7a; background: transparent; letter-spacing: 1px;")
        cl.addWidget(platform_title)

        platform_stats_row = QHBoxLayout()
        platform_stats_row.setSpacing(12)

        toplam_tarifler = len(self.db.tarifler)
        ort_puan = sum(t.puan for t in self.db.tarifler.values()) / max(1, toplam_tarifler)
        min_sure = min((t.hazirlama_suresi for t in self.db.tarifler.values()), default=0)
        min_sure_tarif = min(self.db.tarifler.values(), key=lambda t: t.hazirlama_suresi, default=None)

        platform_stat_items = [
            ("🍽", str(toplam_tarifler), "Toplam Tarif", "#c9713a",
             [random.randint(5, 12) for _ in range(7)]),
            ("★", f"{ort_puan:.1f}", "Ortalama Puan", "#d4a83a",
             [round(ort_puan * 10 + random.uniform(-5, 5)) for _ in range(7)]),
            ("⏱", f"{min_sure} dk", "En Hızlı Tarif", "#6b8a6b",
             [random.randint(5, min_sure + 10) for _ in range(7)]),
        ]

        for icon, value, label, color, chart_data in platform_stat_items:
            stat_w = QFrame()
            stat_w.setStyleSheet(f"""
                QFrame {{
                    background: #141414; border: 0.5px solid #2a2a2a;
                    border-radius: 12px;
                }}
            """)
            stat_w.setMinimumHeight(100)
            sl = QVBoxLayout(stat_w)
            sl.setContentsMargins(18, 14, 18, 14)
            sl.setSpacing(6)

            top_r = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(
                f"font-size: 18px; background: {color}22; border-radius: 8px;"
                f"padding: 4px 8px; color: {color};"
            )
            icon_lbl.setFixedSize(36, 36)
            icon_lbl.setAlignment(Qt.AlignCenter)
            top_r.addWidget(icon_lbl)
            top_r.addStretch()
            mini = MiniBarChart(chart_data, [color] * len(chart_data), yukseklik=36)
            mini.setFixedWidth(65)
            top_r.addWidget(mini)
            sl.addLayout(top_r)

            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; background: transparent; color: {color};")
            sl.addWidget(val_lbl)
            lab_lbl = QLabel(label)
            lab_lbl.setStyleSheet("font-size: 11px; background: transparent; color: #4d4d4d; font-weight: 600;")
            sl.addWidget(lab_lbl)

            platform_stats_row.addWidget(stat_w)

        cl.addLayout(platform_stats_row)

        # ── Kişisel Aktivite İstatistikleri ──
        kisisel_title = QLabel("👤  Kişisel Aktivitelerim")
        kisisel_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #7a7a7a; background: transparent; letter-spacing: 1px;")
        cl.addWidget(kisisel_title)

        self.profil_stats_row_layout = QHBoxLayout()
        self.profil_stats_row_layout.setSpacing(12)
        self._profil_stats_guncelle()
        cl.addLayout(self.profil_stats_row_layout)

        # ── Aktivite Grafiği (mini bar chart büyük) ──
        aktivite_card = QFrame()
        aktivite_card.setStyleSheet("""
            QFrame {
                background: #141414; border: 0.5px solid #2a2a2a; border-radius: 12px;
            }
        """)
        aktivite_card.setMinimumHeight(140)
        ak_layout = QVBoxLayout(aktivite_card)
        ak_layout.setContentsMargins(20, 16, 20, 16)
        ak_layout.setSpacing(8)

        ak_title_row = QHBoxLayout()
        ak_title = QLabel("📈  Haftalık Aktivite")
        ak_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #9a9a9a; background: transparent;")
        ak_title_row.addWidget(ak_title)
        ak_title_row.addStretch()
        ak_sub = QLabel("Son 7 gün")
        ak_sub.setStyleSheet("font-size: 10px; color: #555; background: transparent;")
        ak_title_row.addWidget(ak_sub)
        ak_layout.addLayout(ak_title_row)

        # Büyük bar chart (favoriler + değerlendirmeler bazlı simüle)
        favori_count = len(self.kullanici.favori_tarifler)
        puan_count = len(self.kullanici.puan_verdigi_tarifler)
        haftalik_data = [
            max(1, favori_count + random.randint(-1, 2)),
            max(1, puan_count + random.randint(-1, 2)),
            max(1, favori_count + random.randint(0, 3)),
            max(1, puan_count + random.randint(-2, 1)),
            max(1, favori_count + random.randint(0, 2)),
            max(1, puan_count + random.randint(0, 4)),
            max(1, favori_count + puan_count),
        ]
        bar_colors = ["#c9713a", "#d4a83a", "#c9713a", "#6b8a6b", "#c9713a", "#d4a83a", "#c9713a"]
        big_bar = MiniBarChart(haftalik_data, bar_colors, yukseklik=70)
        ak_layout.addWidget(big_bar)

        gun_row = QHBoxLayout()
        gunler = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        for gun in gunler:
            g_lbl = QLabel(gun)
            g_lbl.setAlignment(Qt.AlignCenter)
            g_lbl.setStyleSheet("font-size: 9px; color: #444; background: transparent;")
            gun_row.addWidget(g_lbl)
        ak_layout.addLayout(gun_row)

        cl.addWidget(aktivite_card)

        # En çok hangi kategoride tarif baktı (favori dağılımı)
        kat_card = QFrame()
        kat_card.setStyleSheet("""
            QFrame {
                background: #141414; border: 0.5px solid #2a2a2a; border-radius: 12px;
            }
        """)
        kat_card.setMinimumHeight(100)
        kat_layout = QVBoxLayout(kat_card)
        kat_layout.setContentsMargins(20, 16, 20, 16)
        kat_layout.setSpacing(10)

        kat_title = QLabel("🍽  Favori Kategorilerim")
        kat_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #9a9a9a; background: transparent;")
        kat_layout.addWidget(kat_title)

        # Favori tariflerin kategori dağılımı
        kat_sayac = {}
        for fid in self.kullanici.favori_tarifler:
            t = self.db.tarifler.get(fid)
            if t:
                kat_sayac[t.kategori] = kat_sayac.get(t.kategori, 0) + 1

        if kat_sayac:
            toplam_fav = sum(kat_sayac.values())
            kat_colors = {"Kahvaltı": "#c9713a", "Çorba": "#6b8a6b", "Ana Yemek": "#5b7a8a",
                          "Tatlı": "#9a6b8a", "İçecek": "#6b8a6b", "Salata": "#7a9a6b"}
            for kat, sayi in sorted(kat_sayac.items(), key=lambda x: x[1], reverse=True)[:4]:
                oran = sayi / toplam_fav
                color = kat_colors.get(kat, "#5a5a5a")
                row = QHBoxLayout()
                kat_lbl = QLabel(kat)
                kat_lbl.setStyleSheet(f"font-size: 12px; color: #9a9a9a; background: transparent; min-width: 90px;")
                row.addWidget(kat_lbl)
                bar = QProgressBar()
                bar.setRange(0, 100)
                bar.setValue(int(oran * 100))
                bar.setFixedHeight(8)
                bar.setTextVisible(False)
                bar.setStyleSheet(
                    f"QProgressBar {{ background: #2a2a2a; border-radius: 4px; border: none; }}"
                    f" QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}"
                )
                row.addWidget(bar, 1)
                sayi_lbl = QLabel(str(sayi))
                sayi_lbl.setStyleSheet(f"font-size: 12px; color: {color}; font-weight: 700; background: transparent; min-width: 20px;")
                sayi_lbl.setAlignment(Qt.AlignRight)
                row.addWidget(sayi_lbl)
                kat_layout.addLayout(row)
        else:
            bos_lbl = QLabel("Henüz favori tarifiniz yok.")
            bos_lbl.setStyleSheet("font-size: 12px; color: #444; background: transparent;")
            kat_layout.addWidget(bos_lbl)

        cl.addWidget(kat_card)
        cl.addStretch()

        scroll.setWidget(content)
        v.addWidget(scroll)
        return page

    def _profil_stats_guncelle(self):
        T = self.aktif_tema
        # Clear existing stat widgets
        while self.profil_stats_row_layout.count():
            item = self.profil_stats_row_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        toplam_puan = len(self.kullanici.puan_verdigi_tarifler)
        ort = sum(self.kullanici.puan_verdigi_tarifler.values()) / max(1, toplam_puan)

        for icon, val, lbl, color in [
            ("❤️", str(len(self.kullanici.favori_tarifler)), "Favori Tarif", "#c9713a"),
            ("⭐", str(toplam_puan), "Değerlendirme", "#d4a83a"),
            ("📊", f"{ort:.1f}", "Ort. Verilen Puan", "#6b8a6b"),
        ]:
            stat = QFrame()
            stat.setStyleSheet(f"""
                QFrame {{
                    background: #141414;
                    border: 0.5px solid #2a2a2a;
                    border-radius: 12px;
                }}
            """)
            stat.setMinimumHeight(90)
            sl = QVBoxLayout(stat)
            sl.setContentsMargins(18, 14, 18, 14)
            sl.setAlignment(Qt.AlignCenter)
            icon_l = QLabel(icon)
            icon_l.setAlignment(Qt.AlignCenter)
            icon_l.setStyleSheet("font-size: 22px; background: transparent;")
            val_l = QLabel(val)
            val_l.setAlignment(Qt.AlignCenter)
            val_l.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {color}; background: transparent;")
            lbl_l = QLabel(lbl)
            lbl_l.setAlignment(Qt.AlignCenter)
            lbl_l.setStyleSheet("font-size: 10px; color: #4d4d4d; background: transparent; font-weight: 600;")
            sl.addWidget(icon_l)
            sl.addWidget(val_l)
            sl.addWidget(lbl_l)
            self.profil_stats_row_layout.addWidget(stat)

    def _profil_guncelle(self):
        """Profil sayfasındaki tüm bilgileri güncelle"""
        # Avatar ve isim güncelle
        self.profil_avatar_lbl.setText(self.kullanici.ad[0].upper() if self.kullanici.ad else "?")
        self.profil_name_lbl.setText(self.kullanici.ad)
        self.profil_email_lbl.setText(self.kullanici.email)
        # Sidebar'daki profil bilgilerini de güncelle
        if hasattr(self, 'sidebar_name_lbl'):
            self.sidebar_name_lbl.setText(self.kullanici.ad)
        if hasattr(self, 'sidebar_avatar_lbl'):
            self.sidebar_avatar_lbl.setText(self.kullanici.ad[0].upper() if self.kullanici.ad else "?")
        if hasattr(self, 'sidebar_email_lbl'):
            self.sidebar_email_lbl.setText(self.kullanici.email)
        # İstatistikleri güncelle
        self._profil_stats_guncelle()

    def _sifre_degistir(self):
        d = SifreDegistirDialog(self.kullanici, self.aktif_tema, self)
        d.exec_()

    def tema_guncelle(self, tema):
        self.aktif_tema = tema
        # Tarifleri yeniden yükle (yeni tema renkleriyle)
        self._tarifleri_yukle()


# ─────────────────────────── ADMİN PANELİ ───────────────────────────

class AdminPaneli(QWidget):
    def __init__(self, db, kullanici, tema_degistir_cb, cikas_cb, parent=None):
        super().__init__(parent)
        self.db = db
        self.kullanici = kullanici
        self.tema_degistir_cb = tema_degistir_cb
        self.cikas_cb = cikas_cb
        self.aktif_tema = GECE_MODU
        self._build_ui()

    def set_tema(self, tema):
        self.aktif_tema = tema

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        layout.addWidget(self.sidebar)

        main_area = QWidget()
        main_area.setStyleSheet("background: transparent;")
        main_v = QVBoxLayout(main_area)
        main_v.setContentsMargins(0, 0, 0, 0)
        main_v.setSpacing(0)

        self.stack = QStackedWidget()
        main_v.addWidget(self.stack)
        layout.addWidget(main_area, 1)

        self.dashboard = self._build_dashboard()
        self.tarif_yonetimi = self._build_tarif_yonetimi()
        self.kullanici_yonetimi = self._build_kullanici_yonetimi()
        self.bekleyen_onaylar_widget = self._build_bekleyen_onaylar()
        self.istatistikler_widget = QWidget()

        for widget in [self.dashboard, self.tarif_yonetimi, self.kullanici_yonetimi,
                       self.bekleyen_onaylar_widget, self.istatistikler_widget]:
            self.stack.addWidget(widget)

    def _build_sidebar(self):
        T = self.aktif_tema
        sidebar = QFrame()
        sidebar.setObjectName("sidebar_frame")
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QFrame#sidebar_frame {{
                background: {T['bg_secondary']};
                border-right: 1px solid {T['border']};
            }}
        """)

        v = QVBoxLayout(sidebar)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── Logo / Brand header ──
        brand_frame = QWidget()
        brand_frame.setFixedHeight(52)
        brand_frame.setStyleSheet(f"""
            background: {T['bg_secondary']};
            border-bottom: 1px solid {T['border']};
        """)
        bl = QHBoxLayout(brand_frame)
        bl.setContentsMargins(16, 0, 16, 0)
        bl.setSpacing(10)

        brand_icon = QLabel("🍽")
        brand_icon.setStyleSheet(f"""
            font-size: 18px; background: {T['accent']}22;
            border-radius: 6px; padding: 4px 6px;
        """)
        bl.addWidget(brand_icon)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        brand_title = QLabel("Tariftirium")
        brand_title.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {T['text_primary']}; background: transparent;")
        brand_sub = QLabel("Admin Panel")
        brand_sub.setStyleSheet(f"font-size: 9px; color: {T['accent']}; background: transparent; font-weight: 700; letter-spacing: 1px;")
        brand_col.addWidget(brand_title)
        brand_col.addWidget(brand_sub)
        bl.addLayout(brand_col)
        bl.addStretch()
        v.addWidget(brand_frame)

        # ── Admin profil satırı ──
        profil_frame = QWidget()
        profil_frame.setFixedHeight(60)
        profil_frame.setStyleSheet(f"background: {T['bg_card']}; border-bottom: 1px solid {T['border']};")
        pfl = QHBoxLayout(profil_frame)
        pfl.setContentsMargins(14, 10, 14, 10)
        pfl.setSpacing(10)

        av_lbl = QLabel(self.kullanici.ad[0].upper() if self.kullanici.ad else "A")
        av_lbl.setAlignment(Qt.AlignCenter)
        av_lbl.setFixedSize(36, 36)
        av_lbl.setStyleSheet(f"""
            background: {T['accent']}; color: white;
            border-radius: 6px; font-size: 14px; font-weight: 800;
        """)
        pfl.addWidget(av_lbl)

        inf = QVBoxLayout()
        inf.setSpacing(1)
        name_l = QLabel(self.kullanici.ad)
        name_l.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        role_l = QLabel("Administrator")
        role_l.setStyleSheet(f"font-size: 9px; color: {T['warning']}; background: transparent; font-weight: 600;")
        inf.addWidget(name_l)
        inf.addWidget(role_l)
        pfl.addLayout(inf)
        pfl.addStretch()

        online_dot = QWidget()
        online_dot.setFixedSize(8, 8)
        online_dot.setStyleSheet(f"background: {T['success']}; border-radius: 4px;")
        pfl.addWidget(online_dot)
        v.addWidget(profil_frame)

        # ── Nav ──
        nav_container = QWidget()
        nav_container.setStyleSheet("background: transparent;")
        nav_v = QVBoxLayout(nav_container)
        nav_v.setContentsMargins(10, 12, 10, 12)
        nav_v.setSpacing(2)

        section_lbl = QLabel("MENÜ")
        section_lbl.setStyleSheet(f"""
            font-size: 9px; font-weight: 800; letter-spacing: 2px;
            color: {T['text_muted']}; background: transparent;
            padding: 4px 8px 8px 8px;
        """)
        nav_v.addWidget(section_lbl)

        self.nav_btns = []
        nav_items = [
            ("📊", "Dashboard", "Genel bakış", 0),
            ("🍽", "Tarif Yönetimi", "Tarifleri düzenle", 1),
            ("👥", "Kullanıcılar", "Kullanıcı yönetimi", 2),
            ("⏳", "Bekleyen Onaylar", "Onay bekleyenler", 3),
            ("📈", "İstatistikler", "Detaylı raporlar", 4),
        ]

        for icon, metin, aciklama, idx in nav_items:
            btn_row = QWidget()
            btn_row.setStyleSheet("background: transparent;")
            btn_row.setFixedHeight(44)
            btn_row.setCursor(Qt.PointingHandCursor)
            brl = QHBoxLayout(btn_row)
            brl.setContentsMargins(0, 0, 0, 0)
            brl.setSpacing(0)

            # Active indicator
            indicator = QWidget()
            indicator.setFixedWidth(3)
            indicator.setFixedHeight(28)
            indicator.setObjectName(f"nav_indicator_{idx}")
            indicator.setStyleSheet("background: transparent; border-radius: 1px;")
            brl.addWidget(indicator)
            brl.addSpacing(2)

            btn = QPushButton()
            btn_lbl_text = f"  {icon}  {metin}"
            if idx == 3 and len(self.db.bekleyen_tarifler) > 0:
                btn_lbl_text = f"  {icon}  {metin}  ·{len(self.db.bekleyen_tarifler)}"
            btn.setText(btn_lbl_text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 6px;
                    text-align: left;
                    font-size: 12px;
                    font-weight: 500;
                    color: {T['text_secondary']};
                    padding-left: 8px;
                }}
                QPushButton:hover {{
                    background: {T['bg_hover']};
                    color: {T['text_primary']};
                }}
                QPushButton:checked {{
                    background: {T['sidebar_active_bg']};
                    color: {T['accent']};
                    font-weight: 700;
                }}
            """)
            btn.clicked.connect(lambda checked, i=idx: self._sayfa_degistir(i))
            brl.addWidget(btn, 1)
            nav_v.addWidget(btn_row)
            self.nav_btns.append(btn)

        nav_v.addStretch()

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {T['border']}; border: none;")
        nav_v.addWidget(div)
        nav_v.addSpacing(8)

        # Settings section
        settings_lbl = QLabel("SİSTEM")
        settings_lbl.setStyleSheet(f"""
            font-size: 9px; font-weight: 800; letter-spacing: 2px;
            color: {T['text_muted']}; background: transparent;
            padding: 4px 8px 8px 8px;
        """)
        nav_v.addWidget(settings_lbl)

        cikis_btn = QPushButton("  🚪  Çıkış Yap")
        cikis_btn.setFixedHeight(36)
        cikis_btn.setCursor(Qt.PointingHandCursor)
        cikis_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; border-radius: 6px;
                text-align: left; font-size: 12px; font-weight: 500;
                color: {T['danger']}; padding-left: 8px;
            }}
            QPushButton:hover {{ background: {T['danger']}22; }}
        """)
        cikis_btn.clicked.connect(self.cikas_cb)
        nav_v.addWidget(cikis_btn)

        v.addWidget(nav_container, 1)

        # ── Bottom status ──
        bottom = QWidget()
        bottom.setFixedHeight(36)
        bottom.setStyleSheet(f"background: {T['bg_card']}; border-top: 1px solid {T['border']};")
        bot_l = QHBoxLayout(bottom)
        bot_l.setContentsMargins(14, 0, 14, 0)
        ver_lbl = QLabel("v2.0 · Admin")
        ver_lbl.setStyleSheet(f"font-size: 9px; color: {T['text_muted']}; background: transparent;")
        bot_l.addWidget(ver_lbl)
        bot_l.addStretch()
        time_lbl = QLabel(datetime.now().strftime("%H:%M"))
        time_lbl.setStyleSheet(f"font-size: 9px; color: {T['accent']}; background: transparent; font-weight: 700;")
        bot_l.addWidget(time_lbl)
        v.addWidget(bottom)

        self.nav_btns[0].setChecked(True)
        return sidebar


    def _dashboard_ara(self, metin):
        T = self.aktif_tema
        if not hasattr(self, 'arama_sonuc_frame'):
            return
        metin = metin.strip().lower()
        if not metin:
            self.arama_sonuc_frame.setVisible(False)
            return
        sonuclar = [
            t for t in self.db.tarifler.values()
            if metin in t.tarif_adi.lower()
            or metin in t.kategori.lower()
            or metin in t.ekleyen.lower()
            or any(metin in m.malzeme_adi.lower() for m in t.malzemeler)
        ]
        self.arama_sonuc_title.setText(f"🔍 Arama: '{metin}' — {len(sonuclar)} tarif bulundu")
        self.arama_sonuc_tablo.setRowCount(len(sonuclar))
        for i, t in enumerate(sonuclar):
            ad_item = QTableWidgetItem(f"{t.gorsel_emoji}  {t.tarif_adi}")
            self.arama_sonuc_tablo.setItem(i, 0, ad_item)
            kat_item = QTableWidgetItem(t.kategori)
            kat_item.setTextAlignment(Qt.AlignCenter)
            self.arama_sonuc_tablo.setItem(i, 1, kat_item)
            ekl_item = QTableWidgetItem(f"👤 {t.ekleyen}")
            ekl_item.setForeground(QBrush(QColor(T['accent'])))
            ekl_item.setTextAlignment(Qt.AlignCenter)
            self.arama_sonuc_tablo.setItem(i, 2, ekl_item)
            puan_item = QTableWidgetItem(f"⭐ {t.puan:.1f}")
            puan_item.setForeground(QBrush(QColor(T['star'])))
            puan_item.setTextAlignment(Qt.AlignCenter)
            self.arama_sonuc_tablo.setItem(i, 3, puan_item)
            self.arama_sonuc_tablo.setRowHeight(i, 44)
        self.arama_sonuc_frame.setVisible(True)

    def _sayfa_degistir(self, idx):
        if idx == 0:
            # Dashboard'a geçince uyarı bandını güncelle
            old = self.stack.widget(0)
            yeni = self._build_dashboard()
            self.stack.insertWidget(0, yeni)
            self.stack.removeWidget(old)
            old.deleteLater()
            self.dashboard = self.stack.widget(0)
        elif idx == 4:
            old = self.stack.widget(4)
            yeni = self._build_istatistikler()
            self.stack.insertWidget(4, yeni)
            self.stack.removeWidget(old)
            old.deleteLater()
        elif idx == 3:
            # Bekleyen onaylar sayfasını yenile
            old = self.stack.widget(3)
            yeni = self._build_bekleyen_onaylar()
            self.stack.insertWidget(3, yeni)
            self.stack.removeWidget(old)
            old.deleteLater()
            self.bekleyen_onaylar_widget = self.stack.widget(3)

        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == idx)
        if idx == 1: self._tarif_tablosunu_guncelle()
        elif idx == 2: self._kullanici_tablosunu_guncelle()

    def _build_dashboard(self):
        T = self.aktif_tema
        page = QWidget()
        page.setStyleSheet(f"background: {T['bg_primary']};")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── Top bar (görseldeki gibi) ──
        topbar = QFrame()
        topbar.setFixedHeight(52)
        topbar.setStyleSheet(f"""
            background: {T['bg_secondary']};
            border-bottom: 1px solid {T['border']};
        """)
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(20, 0, 20, 0)
        tbl.setSpacing(12)

        page_title = QLabel("Dashboard")
        page_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        tbl.addWidget(page_title)
        tbl.addStretch()

        # Search
        self.dashboard_search = QLineEdit()
        self.dashboard_search.setPlaceholderText("🔍  Ara...")
        self.dashboard_search.setFixedSize(200, 32)
        self.dashboard_search.setStyleSheet(f"""
            QLineEdit {{
                background: {T['bg_card']}; border: 1px solid {T['border']};
                border-radius: 6px; padding: 0 12px; color: {T['text_primary']}; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {T['accent']}; }}
        """)
        self.dashboard_search.textChanged.connect(self._dashboard_ara)
        tbl.addWidget(self.dashboard_search)

        now_lbl = QLabel(datetime.now().strftime("%d %b %Y"))
        now_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 11px; background: transparent;")
        tbl.addWidget(now_lbl)
        v.addWidget(topbar)

        # ── Scrollable content ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        cw = QWidget()
        cw.setStyleSheet(f"background: {T['bg_primary']};")
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(20, 16, 20, 20)
        cl.setSpacing(14)

        # ── Bekleyen uyarı ──
        bekleyen_sayi = len(self.db.bekleyen_tarifler)
        if bekleyen_sayi > 0:
            warn = QFrame()
            warn.setFixedHeight(40)
            warn.setStyleSheet(f"""
                background: {T['warning']}18; border: 1px solid {T['warning']}44;
                border-radius: 6px;
            """)
            wl = QHBoxLayout(warn)
            wl.setContentsMargins(12, 0, 12, 0)
            wl.setSpacing(8)
            wi = QLabel("⚠")
            wi.setStyleSheet(f"font-size: 14px; color: {T['warning']}; background: transparent;")
            wl.addWidget(wi)
            wt = QLabel(f"{bekleyen_sayi} tarif onayınızı bekliyor")
            wt.setStyleSheet(f"color: {T['warning']}; font-size: 12px; background: transparent; font-weight: 600;")
            wl.addWidget(wt)
            wl.addStretch()
            gb = QPushButton("Onaylara Git →")
            gb.setFixedHeight(26)
            gb.setCursor(Qt.PointingHandCursor)
            gb.setStyleSheet(f"""
                QPushButton {{ background: {T['warning']}; color: #111; border: none;
                    border-radius: 5px; font-weight: 700; font-size: 11px; padding: 0 10px; }}
                QPushButton:hover {{ background: #e6c44a; }}
            """)
            gb.clicked.connect(lambda: self._sayfa_degistir(3))
            wl.addWidget(gb)
            cl.addWidget(warn)

        # ── 4 Stat Kartları (görseldeki gibi compact) ──
        toplam_tarif = len(self.db.tarifler)
        toplam_kullanici = len(self.db.kullanicilar)
        ort_puan = sum(t.puan for t in self.db.tarifler.values()) / max(1, toplam_tarif)
        toplam_oy = sum(t.puan_sayisi for t in self.db.tarifler.values())
        toplam_goruntuleme = sum(t.goruntuleme for t in self.db.tarifler.values())

        stat_row = QHBoxLayout()
        stat_row.setSpacing(10)

        stat_defs = [
            ("🍽", str(toplam_tarif), "Toplam Tarif", T['accent'],
             [random.randint(3,10) for _ in range(7)]),
            ("⭐", f"{ort_puan:.1f}", "Ort. Puan", T['chart2'],
             [random.randint(4,10) for _ in range(7)]),
            ("👥", str(toplam_kullanici), "Kullanıcı", T['chart4'],
             [random.randint(1,5) for _ in range(7)]),
            ("👁", f"{toplam_goruntuleme:,}", "Görüntüleme", T['chart3'],
             [random.randint(20,80) for _ in range(7)]),
        ]

        for icon, val, lbl, color, chart_data in stat_defs:
            card = QFrame()
            card.setMinimumHeight(100)
            card.setStyleSheet(f"""
                QFrame {{
                    background: {T['bg_card']};
                    border: 1px solid {T['border']};
                    border-radius: 8px;
                }}
            """)
            cl2 = QVBoxLayout(card)
            cl2.setContentsMargins(14, 12, 14, 12)
            cl2.setSpacing(6)

            top_r = QHBoxLayout()
            icon_bg = QWidget()
            icon_bg.setFixedSize(32, 32)
            icon_bg.setStyleSheet(f"background: {color}22; border-radius: 6px;")
            ibl = QVBoxLayout(icon_bg)
            ibl.setContentsMargins(0,0,0,0)
            il = QLabel(icon)
            il.setAlignment(Qt.AlignCenter)
            il.setStyleSheet(f"font-size: 16px; background: transparent;")
            ibl.addWidget(il)
            top_r.addWidget(icon_bg)
            top_r.addStretch()
            mini = MiniBarChart(chart_data, [color]*len(chart_data), yukseklik=32)
            mini.setFixedWidth(55)
            top_r.addWidget(mini)
            cl2.addLayout(top_r)

            val_l = QLabel(val)
            val_l.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {T['text_primary']}; background: transparent;")
            cl2.addWidget(val_l)

            lbl_l = QLabel(lbl)
            lbl_l.setStyleSheet(f"font-size: 10px; color: {T['text_muted']}; background: transparent; font-weight: 600;")
            cl2.addWidget(lbl_l)

            stat_row.addWidget(card)

        cl.addLayout(stat_row)

        # ── Orta bölüm: Chart + Sağ panel ──
        mid_row = QHBoxLayout()
        mid_row.setSpacing(12)

        # Sol: Area chart
        chart_card = QFrame()
        chart_card.setMinimumHeight(220)
        chart_card.setStyleSheet(f"""
            background: {T['bg_card']}; border: 1px solid {T['border']}; border-radius: 8px;
        """)
        ccl = QVBoxLayout(chart_card)
        ccl.setContentsMargins(16, 14, 16, 14)
        ccl.setSpacing(8)

        ch_header = QHBoxLayout()
        ch_title = QLabel("Performans Grafiği")
        ch_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        ch_header.addWidget(ch_title)
        ch_header.addStretch()
        for leg_name, leg_color in [("Puan", T['chart1']), ("Oy", T['chart2']), ("Görüntüleme", T['chart3'])]:
            dot = QFrame(); dot.setFixedSize(8,8)
            dot.setStyleSheet(f"background: {leg_color}; border-radius: 4px;")
            ch_header.addWidget(dot); ch_header.addSpacing(3)
            ll = QLabel(leg_name)
            ll.setStyleSheet(f"color: {T['text_secondary']}; font-size: 10px; background: transparent;")
            ch_header.addWidget(ll); ch_header.addSpacing(8)
        ccl.addLayout(ch_header)

        area_chart = AreaChartWidget(T, db=self.db)
        area_chart.setMinimumHeight(160)
        ccl.addWidget(area_chart)
        mid_row.addWidget(chart_card, 3)

        # Sağ: Son aktiviteler
        act_card = QFrame()
        act_card.setFixedWidth(220)
        act_card.setStyleSheet(f"""
            background: {T['bg_card']}; border: 1px solid {T['border']}; border-radius: 8px;
        """)
        acl = QVBoxLayout(act_card)
        acl.setContentsMargins(14, 12, 14, 12)
        acl.setSpacing(6)

        act_title = QLabel("Son Aktiviteler")
        act_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        acl.addWidget(act_title)

        for akt in self.db.aktivite_logu[:5]:
            act_row = QWidget()
            act_row.setFixedHeight(46)
            act_row.setStyleSheet(f"background: {T['bg_hover']}; border-radius: 6px;")
            arl = QHBoxLayout(act_row)
            arl.setContentsMargins(8, 6, 8, 6)
            arl.setSpacing(8)

            dot = QWidget()
            dot.setFixedSize(6,6)
            akt_color = T['success'] if akt['tip'] == 'tarif' else T['warning'] if akt['tip'] == 'yorum' else T['chart2']
            dot.setStyleSheet(f"background: {akt_color}; border-radius: 3px;")
            arl.addWidget(dot)

            mv = QVBoxLayout(); mv.setSpacing(0)
            ml = QLabel(akt['mesaj'][:28] + ("..." if len(akt['mesaj']) > 28 else ""))
            ml.setStyleSheet(f"font-size: 10px; color: {T['text_primary']}; background: transparent;")
            tl = QLabel(akt['zaman'])
            tl.setStyleSheet(f"font-size: 9px; color: {T['text_muted']}; background: transparent;")
            mv.addWidget(ml); mv.addWidget(tl)
            arl.addLayout(mv)
            acl.addWidget(act_row)

        acl.addStretch()
        mid_row.addWidget(act_card)
        cl.addLayout(mid_row)

        # ── Alt bölüm: Top tarifler tablosu + Son tarifler ──
        bot_row = QHBoxLayout()
        bot_row.setSpacing(12)

        # Sol: En iyi tarifler tablosu (görseldeki gibi)
        tablo_card = QFrame()
        tablo_card.setStyleSheet(f"""
            background: {T['bg_card']}; border: 1px solid {T['border']}; border-radius: 8px;
        """)
        tcl = QVBoxLayout(tablo_card)
        tcl.setContentsMargins(16, 14, 16, 14)
        tcl.setSpacing(8)

        t_header = QHBoxLayout()
        t_title = QLabel("En İyi Tarifler")
        t_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        t_header.addWidget(t_title)
        t_header.addStretch()
        # Filter tabs (görseldeki gibi)
        for tab_name, tab_col in [("Bekliyor", T['warning']), ("Onaylı", T['success']), ("Reddedildi", T['danger'])]:
            tab_btn = QPushButton(tab_name)
            tab_btn.setFixedHeight(24)
            tab_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {tab_col}18; color: {tab_col};
                    border: 1px solid {tab_col}33; border-radius: 4px;
                    font-size: 10px; font-weight: 600; padding: 0 8px;
                }}
                QPushButton:hover {{ background: {tab_col}33; }}
            """)
            t_header.addWidget(tab_btn)
        tcl.addLayout(t_header)

        top_tarifler = sorted(self.db.tarifler.values(), key=lambda t: t.puan, reverse=True)[:6]
        self.dashboard_top_tablo = QTableWidget()
        self.dashboard_top_tablo.setColumnCount(6)
        self.dashboard_top_tablo.setHorizontalHeaderLabels(["#", "Tarif Adı", "Ekleyen", "Kategori", "Puan", "Oy"])
        self.dashboard_top_tablo.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.dashboard_top_tablo.setRowCount(len(top_tarifler))
        self.dashboard_top_tablo.setMaximumHeight(230)
        self.dashboard_top_tablo.setMinimumHeight(200)
        self.dashboard_top_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.dashboard_top_tablo.verticalHeader().setVisible(False)
        self.dashboard_top_tablo.setAlternatingRowColors(False)
        self.dashboard_top_tablo.setShowGrid(False)
        self.dashboard_top_tablo.horizontalHeader().setDefaultSectionSize(70)

        madalya = ["🥇","🥈","🥉","4","5","6"]
        for i, t in enumerate(top_tarifler):
            sira = QTableWidgetItem(madalya[i])
            sira.setTextAlignment(Qt.AlignCenter)
            self.dashboard_top_tablo.setItem(i, 0, sira)

            self.dashboard_top_tablo.setItem(i, 1, QTableWidgetItem(f"{t.gorsel_emoji}  {t.tarif_adi}"))

            ekl = QTableWidgetItem(t.ekleyen)
            ekl.setForeground(QBrush(QColor(T['text_secondary'])))
            ekl.setTextAlignment(Qt.AlignCenter)
            self.dashboard_top_tablo.setItem(i, 2, ekl)

            kat_item = QTableWidgetItem(t.kategori)
            kat_item.setTextAlignment(Qt.AlignCenter)
            self.dashboard_top_tablo.setItem(i, 3, kat_item)

            puan_item = QTableWidgetItem(f"★ {t.puan:.1f}")
            puan_item.setForeground(QBrush(QColor(T['star'])))
            puan_item.setTextAlignment(Qt.AlignCenter)
            self.dashboard_top_tablo.setItem(i, 4, puan_item)

            oy_item = QTableWidgetItem(str(t.puan_sayisi))
            oy_item.setTextAlignment(Qt.AlignCenter)
            self.dashboard_top_tablo.setItem(i, 5, oy_item)
            self.dashboard_top_tablo.setRowHeight(i, 36)

        tcl.addWidget(self.dashboard_top_tablo)
        bot_row.addWidget(tablo_card, 3)

        # Sağ: Son tarifler listesi
        recent_card = QFrame()
        recent_card.setFixedWidth(220)
        recent_card.setStyleSheet(f"""
            background: {T['bg_card']}; border: 1px solid {T['border']}; border-radius: 8px;
        """)
        rcl = QVBoxLayout(recent_card)
        rcl.setContentsMargins(14, 12, 14, 12)
        rcl.setSpacing(6)

        rc_title = QLabel("Son Eklenen Tarifler")
        rc_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        rcl.addWidget(rc_title)

        tarifler_sorted = sorted(self.db.tarifler.values(), key=lambda t: t.tarif_id, reverse=True)[:5]
        for t in tarifler_sorted:
            rrow = QWidget()
            rrow.setFixedHeight(44)
            rrow.setStyleSheet(f"background: {T['bg_hover']}; border-radius: 6px;")
            rrl = QHBoxLayout(rrow)
            rrl.setContentsMargins(8, 6, 8, 6)
            rrl.setSpacing(8)

            em = QLabel(t.gorsel_emoji)
            em.setStyleSheet(f"font-size: 14px; background: {T['accent']}18; border-radius: 4px; padding: 2px 3px;")
            em.setFixedSize(26, 26)
            em.setAlignment(Qt.AlignCenter)
            rrl.addWidget(em)

            itv = QVBoxLayout(); itv.setSpacing(0)
            nl = QLabel(t.tarif_adi[:18] + ("..." if len(t.tarif_adi)>18 else ""))
            nl.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {T['text_primary']}; background: transparent;")
            sl = QLabel(f"{t.ekleyen}  ·  {t.tarih}")
            sl.setStyleSheet(f"font-size: 9px; color: {T['text_muted']}; background: transparent;")
            itv.addWidget(nl); itv.addWidget(sl)
            rrl.addLayout(itv)
            rrl.addStretch()

            puan_l = QLabel(f"★{t.puan:.1f}")
            puan_l.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {T['star']}; background: transparent;")
            rrl.addWidget(puan_l)
            rcl.addWidget(rrow)

        rcl.addStretch()
        bot_row.addWidget(recent_card)
        cl.addLayout(bot_row)

        # Arama sonuç alanı
        self.arama_sonuc_frame = QFrame()
        self.arama_sonuc_frame.setStyleSheet(f"""
            background: {T['bg_card']}; border: 1px solid {T['border']}; border-radius: 8px;
        """)
        self.arama_sonuc_frame.setVisible(False)
        asr_v = QVBoxLayout(self.arama_sonuc_frame)
        asr_v.setContentsMargins(16, 14, 16, 14)
        asr_v.setSpacing(8)
        self.arama_sonuc_title = QLabel("🔍 Arama Sonuçları")
        self.arama_sonuc_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
        asr_v.addWidget(self.arama_sonuc_title)
        self.arama_sonuc_tablo = QTableWidget()
        self.arama_sonuc_tablo.setColumnCount(4)
        self.arama_sonuc_tablo.setHorizontalHeaderLabels(["Tarif", "Kategori", "Ekleyen", "Puan"])
        self.arama_sonuc_tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.arama_sonuc_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.arama_sonuc_tablo.verticalHeader().setVisible(False)
        self.arama_sonuc_tablo.setMaximumHeight(200)
        asr_v.addWidget(self.arama_sonuc_tablo)
        cl.addWidget(self.arama_sonuc_frame)

        cl.addStretch()
        scroll.setWidget(cw)
        v.addWidget(scroll, 1)
        return page


    def _build_tarif_yonetimi(self):
        T = self.aktif_tema
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Top bar
        topbar = QFrame()
        topbar.setObjectName("topbar_frame")
        topbar.setFixedHeight(52)
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(20, 0, 20, 0)
        title = QLabel("🍽  Tarif Yönetimi")
        title.setObjectName("header_label")
        tbl.addWidget(title)
        tbl.addStretch()

        self.tarif_arama = QLineEdit()
        self.tarif_arama.setPlaceholderText("🔍  Tarif ara...")
        self.tarif_arama.setFixedWidth(200)
        self.tarif_arama.setMinimumHeight(38)
        self.tarif_arama.textChanged.connect(self._tarif_tablosunu_guncelle)
        tbl.addWidget(self.tarif_arama)

        self.kat_filtre_admin = QComboBox()
        self.kat_filtre_admin.addItems(["Tümü", "Kahvaltı", "Çorba", "Ana Yemek", "Tatlı", "İçecek", "Salata"])
        self.kat_filtre_admin.setMinimumHeight(38)
        self.kat_filtre_admin.currentTextChanged.connect(self._tarif_tablosunu_guncelle)
        tbl.addWidget(self.kat_filtre_admin)

        yeni_btn = QPushButton("  ➕  Yeni Tarif")
        yeni_btn.setMinimumHeight(38)
        yeni_btn.clicked.connect(self._yeni_tarif)
        tbl.addWidget(yeni_btn)
        v.addWidget(topbar)

        content = QWidget()
        content.setStyleSheet(f"")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 20, 28, 28)
        cl.setSpacing(12)

        self.tarif_tablo = QTableWidget()
        self.tarif_tablo.setColumnCount(8)
        self.tarif_tablo.setHorizontalHeaderLabels(["ID", "Tarif", "Kategori", "Ekleyen", "Süre", "Puan", "Görüntüleme", "İşlemler"])
        self.tarif_tablo.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tarif_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tarif_tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tarif_tablo.setAlternatingRowColors(True)
        self.tarif_tablo.verticalHeader().setVisible(False)
        cl.addWidget(self.tarif_tablo)
        self._tarif_tablosunu_guncelle()

        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QFrame.NoFrame)
        main_scroll.setWidget(content)
        v.addWidget(main_scroll)
        return page

    def _tarif_tablosunu_guncelle(self):
        T = self.aktif_tema
        arama = self.tarif_arama.text().lower() if hasattr(self, 'tarif_arama') else ""
        kat = self.kat_filtre_admin.currentText() if hasattr(self, 'kat_filtre_admin') else "Tümü"
        tarifler = [
            t for t in self.db.tarifler.values()
            if (not arama or arama in t.tarif_adi.lower())
            and (kat == "Tümü" or t.kategori == kat)
        ]

        self.tarif_tablo.setRowCount(len(tarifler))
        for i, t in enumerate(tarifler):
            self.tarif_tablo.setItem(i, 0, QTableWidgetItem(str(t.tarif_id)))
            ad_item = QTableWidgetItem(f"{t.gorsel_emoji}  {t.tarif_adi}")
            self.tarif_tablo.setItem(i, 1, ad_item)

            kat_item = QTableWidgetItem(t.kategori)
            kat_item.setTextAlignment(Qt.AlignCenter)
            self.tarif_tablo.setItem(i, 2, kat_item)

            ekleyen_item = QTableWidgetItem(f"👤 {t.ekleyen}")
            ekleyen_item.setForeground(QBrush(QColor(T["accent"])))
            ekleyen_item.setTextAlignment(Qt.AlignCenter)
            self.tarif_tablo.setItem(i, 3, ekleyen_item)

            sure_item = QTableWidgetItem(f"⏱ {t.hazirlama_suresi} dk")
            sure_item.setTextAlignment(Qt.AlignCenter)
            self.tarif_tablo.setItem(i, 4, sure_item)

            puan_item = QTableWidgetItem(f"⭐ {t.puan:.1f}")
            puan_item.setForeground(QBrush(QColor(T["star"])))
            puan_item.setTextAlignment(Qt.AlignCenter)
            self.tarif_tablo.setItem(i, 5, puan_item)

            goruntuleme_item = QTableWidgetItem(f"👁 {t.goruntuleme}")
            goruntuleme_item.setTextAlignment(Qt.AlignCenter)
            self.tarif_tablo.setItem(i, 6, goruntuleme_item)

            btn_widget = QWidget()
            btn_widget.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 3, 4, 3)
            btn_layout.setSpacing(4)

            duzenle_btn = QPushButton("✏️")
            duzenle_btn.setFixedSize(30, 30)
            duzenle_btn.setToolTip("Düzenle")
            duzenle_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {T['accent_secondary']}22;
                    border: 0px solid {T['accent_secondary']}55;
                    border-radius: 6px; font-size: 13px;
                }}
                QPushButton:hover {{ background: {T['accent_secondary']}; }}
            """)
            duzenle_btn.clicked.connect(lambda _, tid=t.tarif_id: self._tarif_duzenle(tid))

            sil_btn = QPushButton("🗑️")
            sil_btn.setFixedSize(30, 30)
            sil_btn.setToolTip("Sil")
            sil_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {T['danger']}22;
                    border-radius: 6px; font-size: 13px;
                }}
                QPushButton:hover {{ background: {T['danger']}; }}
            """)
            sil_btn.clicked.connect(lambda _, tid=t.tarif_id: self._tarif_sil(tid))

            goster_btn = QPushButton("👁")
            goster_btn.setFixedSize(30, 30)
            goster_btn.setToolTip("Detay Görüntüle")
            goster_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {T['success']}22;
                   
                    border-radius: 6px; font-size: 13px;
                }}
                QPushButton:hover {{ background: {T['success']}; }}
            """)
            goster_btn.clicked.connect(lambda _, tid=t.tarif_id: self._tarif_goster(tid))

            btn_layout.addWidget(goster_btn)
            btn_layout.addWidget(duzenle_btn)
            btn_layout.addWidget(sil_btn)
            btn_layout.addStretch()

            self.tarif_tablo.setCellWidget(i, 7, btn_widget)
            self.tarif_tablo.setRowHeight(i, 48)

    def _yeni_tarif(self):
        d = TarifFormDialog(self.db, self.aktif_tema, self.kullanici, parent=self)
        if d.exec_() == QDialog.Accepted:
            self._tarif_tablosunu_guncelle()
            self.db.aktivite_logu.insert(0, {
                "tip": "tarif", "mesaj": f"Yeni tarif eklendi",
                "zaman": "Az önce", "renk": self.aktif_tema['accent']
            })
            QMessageBox.information(self, "✅ Başarılı", "Tarif başarıyla eklendi!")

    def _tarif_duzenle(self, tarif_id):
        tarif = self.db.tarifler.get(tarif_id)
        if tarif:
            d = TarifFormDialog(self.db, self.aktif_tema, self.kullanici, tarif=tarif, parent=self)
            if d.exec_() == QDialog.Accepted:
                self._tarif_tablosunu_guncelle()
                QMessageBox.information(self, "✅ Başarılı", "Tarif güncellendi!")

    def _tarif_goster(self, tarif_id):
        tarif = self.db.tarifler.get(tarif_id)
        if tarif:
            d = TarifDetayDialog(tarif, self.db, self.kullanici, self.aktif_tema, self)
            d.exec_()

    def _tarif_sil(self, tarif_id):
        tarif = self.db.tarifler.get(tarif_id)
        if not tarif: return
        reply = QMessageBox.question(self, "⚠️ Onay",
            f"'{tarif.tarif_adi}' tarifini silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.db.tarifler[tarif_id]
            self._tarif_tablosunu_guncelle()

    def _build_kullanici_yonetimi(self):
        T = self.aktif_tema
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar_frame")
        topbar.setFixedHeight(52)
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(20, 0, 20, 0)
        title = QLabel("👥 Kullanıcı Yönetimi")
        title.setObjectName("header_label")
        tbl.addWidget(title)
        tbl.addStretch()

        toplam_badge = QLabel(f"{len(self.db.kullanicilar)} kullanıcı")
        toplam_badge.setStyleSheet(f"""
            box-shadow: 0px 3px 3px 1px red inset;
            font-size: 12px; font-weight: 700;
        """)
        tbl.addWidget(toplam_badge)
        v.addWidget(topbar)

        content = QWidget()
        content.setStyleSheet(f"background: {T['bg_primary']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 20, 28, 28)
        cl.setSpacing(12)

        self.kullanici_tablo = QTableWidget()
        self.kullanici_tablo.setColumnCount(6)
        self.kullanici_tablo.setHorizontalHeaderLabels(["ID", "Ad Soyad", "E-posta", "Rol", "Favoriler", "Kayıt Tarihi"])
        self.kullanici_tablo.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.kullanici_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.kullanici_tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.kullanici_tablo.setAlternatingRowColors(True)
        self.kullanici_tablo.verticalHeader().setVisible(False)
        self.kullanici_tablo.setCursor(Qt.PointingHandCursor)
        self.kullanici_tablo.cellClicked.connect(self._kullanici_bilgi_goster)
        cl.addWidget(self.kullanici_tablo)
        self._kullanici_tablosunu_guncelle()

        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QFrame.NoFrame)
        main_scroll.setWidget(content)
        v.addWidget(main_scroll)
        return page

    def _kullanici_tablosunu_guncelle(self):
        T = self.aktif_tema
        kullanicilar = list(self.db.kullanicilar.values())
        self.kullanici_tablo.setRowCount(len(kullanicilar))
        for i, k in enumerate(kullanicilar):
            id_item = QTableWidgetItem(str(k.kullanici_id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.kullanici_tablo.setItem(i, 0, id_item)

            # Avatar + name
            self.kullanici_tablo.setItem(i, 1, QTableWidgetItem(f"{'🛡️' if k.rol == 'admin' else '👤'}  {k.ad}"))
            self.kullanici_tablo.setItem(i, 2, QTableWidgetItem(k.email))

            rol_item = QTableWidgetItem(" Admin" if k.rol == "admin" else "👤 Kullanıcı")
            rol_item.setTextAlignment(Qt.AlignCenter)
            if k.rol == "admin":
                rol_item.setForeground(QBrush(QColor(T["warning"])))
            else:
                rol_item.setForeground(QBrush(QColor(T["accent_secondary"])))
            self.kullanici_tablo.setItem(i, 3, rol_item)

            fav_item = QTableWidgetItem(f"❤️ {len(k.favori_tarifler)}")
            fav_item.setTextAlignment(Qt.AlignCenter)
            self.kullanici_tablo.setItem(i, 4, fav_item)

            tarih_item = QTableWidgetItem(k.kayit_tarihi if k.kayit_tarihi else "—")
            tarih_item.setTextAlignment(Qt.AlignCenter)
            self.kullanici_tablo.setItem(i, 5, tarih_item)

            self.kullanici_tablo.setRowHeight(i, 46)

    def _kullanici_bilgi_goster(self, row, col):
        kullanicilar = list(self.db.kullanicilar.values())
        if row < 0 or row >= len(kullanicilar):
            return
        k = kullanicilar[row]
        d = KullaniciBilgiDialog(k, self.db, self.aktif_tema, self)
        sonuc = d.exec_()
        if sonuc in (QDialog.Accepted, KullaniciBilgiDialog.RESULT_DELETE):
            self._kullanici_tablosunu_guncelle()

    def _bekleyen_sayfayi_yenile(self):
        bekleyen = len(self.db.bekleyen_tarifler)
        self.nav_btns[3].setText(
            f"     Bekleyen Onaylar  [{bekleyen}]" if bekleyen > 0 else "    Bekleyen Onaylar"
        )
        # Bekleyen onaylar sayfasını yenile
        old3 = self.stack.widget(3)
        yeni3 = self._build_bekleyen_onaylar()
        self.stack.insertWidget(3, yeni3)
        self.stack.removeWidget(old3)
        old3.deleteLater()
        self.bekleyen_onaylar_widget = self.stack.widget(3)

        # Dashboard'u da yenile (uyarı bandı güncellensin)
        old0 = self.stack.widget(0)
        yeni0 = self._build_dashboard()
        self.stack.insertWidget(0, yeni0)
        self.stack.removeWidget(old0)
        old0.deleteLater()
        self.dashboard = self.stack.widget(0)

        self.stack.setCurrentIndex(3)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == 3)

    def _bildirim_goster(self, mesaj, tur="basari"):
        """Sağ altta kayan animasyonlu bildirim gösterir. tur: 'basari' | 'hata'"""
        T = self.aktif_tema
        renk   = T.get('success', '#10B981') if tur == "basari" else T.get('danger', '#EF4444')
        ikon   = "✅" if tur == "basari" else "❌"

        toast = QFrame(self)
        toast.setFixedSize(320, 56)
        toast.setStyleSheet(f"""
            QFrame {{
                background: {renk}ee;
                border-radius: 12px;
                border: 1px solid {renk};
            }}
        """)
        tl = QHBoxLayout(toast)
        tl.setContentsMargins(14, 0, 14, 0)
        tl.setSpacing(10)
        ikon_lbl = QLabel(ikon)
        ikon_lbl.setStyleSheet("font-size: 20px; background: transparent;")
        msg_lbl = QLabel(mesaj)
        msg_lbl.setStyleSheet("color: #fff; font-size: 13px; font-weight: 600; background: transparent;")
        msg_lbl.setWordWrap(True)
        tl.addWidget(ikon_lbl)
        tl.addWidget(msg_lbl, 1)

        # Konumlandır: sağ alt köşe
        def _reposition():
            pw, ph = self.width(), self.height()
            toast.move(pw - 336, ph - 76)
        _reposition()
        toast.show()
        toast.raise_()

        # 2.5 saniye sonra kapat
        QTimer.singleShot(2500, toast.deleteLater)

    def _tarif_onayla(self, t_id, t_ad, t_ekleyen):
        t = self.db.bekleyen_tarifler.pop(t_id, None)
        if t:
            self.db.tarifler[t_id] = t
            # Aktivite loguna başarı kaydı ekle
            self.db.aktivite_logu.insert(0, {
                "tip": "tarif",
                "mesaj": f"Admin {t_ekleyen}'ın '{t_ad}' tarifini onayladı",
                "zaman": "az önce",
                "renk": "#10B981"
            })
            # Bu tarife ait "onay bekliyor" bildirimini logdan sil
            self.db.aktivite_logu = [
                a for a in self.db.aktivite_logu
                if not (t_ad in a.get("mesaj", "") and "onay bekliyor" in a.get("mesaj", ""))
            ]
            self._bildirim_goster(f"'{t_ad}' tarifi yayınlandı!", "basari")
            self._bekleyen_sayfayi_yenile()

    def _tarif_reddet(self, t_id, t_ad):
        t = self.db.bekleyen_tarifler.pop(t_id, None)
        if t:
            # Bu tarife ait "onay bekliyor" bildirimini logdan sil
            self.db.aktivite_logu = [
                a for a in self.db.aktivite_logu
                if not (t_ad in a.get("mesaj", "") and "onay bekliyor" in a.get("mesaj", ""))
            ]
            self.db.aktivite_logu.insert(0, {
                "tip": "tarif",
                "mesaj": f"Admin '{t_ad}' tarifini reddetti",
                "zaman": "az önce",
                "renk": "#EF4444"
            })
            self._bildirim_goster(f"'{t_ad}' tarifi reddedildi.", "hata")
            self._bekleyen_sayfayi_yenile()

    def _build_bekleyen_onaylar(self):
        T = self.aktif_tema
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Top bar
        topbar = QFrame()
        topbar.setObjectName("topbar_frame")
        topbar.setFixedHeight(52)
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(20, 0, 20, 0)
        title = QLabel("⏳ Bekleyen Onaylar")
        title.setObjectName("header_label")
        tbl.addWidget(title)
        tbl.addStretch()
        bekleyen_sayi = len(self.db.bekleyen_tarifler)
        badge = QLabel(f"{bekleyen_sayi} bekliyor")
        badge.setStyleSheet(f"""
            background: {T['warning']}33; color: {T['warning']};
            border-radius: 10px; padding: 4px 14px;
            font-size: 12px; font-weight: 700;
        """)
        tbl.addWidget(badge)
        v.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background: {T['bg_primary']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 24, 28, 28)
        cl.setSpacing(16)

        if not self.db.bekleyen_tarifler:
            bos = QLabel("✅ Bekleyen onay bulunmuyor.")
            bos.setAlignment(Qt.AlignCenter)
            bos.setStyleSheet(f"font-size: 18px; color: {T['text_secondary']}; background: transparent;")
            cl.addWidget(bos)
        else:
            for tid, tarif in list(self.db.bekleyen_tarifler.items()):
                kart = QFrame()
                kart.setObjectName("card_frame")
                kl = QVBoxLayout(kart)
                kl.setContentsMargins(24, 20, 24, 20)
                kl.setSpacing(10)

                # Başlık satırı
                header_row = QHBoxLayout()
                emoji_lbl = QLabel(tarif.gorsel_emoji)
                emoji_lbl.setStyleSheet("font-size: 28px; background: transparent;")
                emoji_lbl.setFixedWidth(40)
                header_row.addWidget(emoji_lbl)

                info_v = QVBoxLayout()
                info_v.setSpacing(2)
                name_l = QLabel(tarif.tarif_adi)
                name_l.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {T['text_primary']}; background: transparent;")
                sub_l = QLabel(f"Ekleyen: 👤 {tarif.ekleyen}   •   {tarif.kategori}   •   ⏱ {tarif.hazirlama_suresi} dk   •   📅 {tarif.tarih}")
                sub_l.setStyleSheet(f"font-size: 12px; color: {T['text_secondary']}; background: transparent;")
                info_v.addWidget(name_l)
                info_v.addWidget(sub_l)
                header_row.addLayout(info_v)
                header_row.addStretch()

                bek_badge = QLabel("⏳ Onay Bekliyor")
                bek_badge.setStyleSheet(f"""
                    background: {T['warning']}22; color: {T['warning']};
                    border-radius: 8px; padding: 4px 12px;
                    font-size: 11px; font-weight: 700;
                """)
                header_row.addWidget(bek_badge)
                kl.addLayout(header_row)

                # Malzemeler özeti
                malz_text = ",  ".join([f"{m.malzeme_adi} ({m.miktar} {m.birim})" for m in tarif.malzemeler[:5]])
                if len(tarif.malzemeler) > 5:
                    malz_text += f" + {len(tarif.malzemeler)-5} daha"
                malz_lbl = QLabel(f"🧂 Malzemeler: {malz_text}")
                malz_lbl.setStyleSheet(f"font-size: 12px; color: {T['text_secondary']}; background: transparent;")
                malz_lbl.setWordWrap(True)
                kl.addWidget(malz_lbl)

                # Talimatlar önizleme
                tal_preview = tarif.talimatlar[:200] + ("..." if len(tarif.talimatlar) > 200 else "")
                tal_lbl = QLabel(f"📋 {tal_preview}")
                tal_lbl.setStyleSheet(f"font-size: 12px; color: {T['text_muted']}; background: transparent;")
                tal_lbl.setWordWrap(True)
                kl.addWidget(tal_lbl)

                # Buton satırı
                btn_row = QHBoxLayout()
                btn_row.addStretch()

                onayla_btn = QPushButton("✅  Onayla")
                onayla_btn.setMinimumHeight(40)
                onayla_btn.setMinimumWidth(130)
                onayla_btn.setCursor(Qt.PointingHandCursor)
                onayla_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {T['success']}; color: white;
                        border: none; border-radius: 10px;
                        font-size: 13px; font-weight: 700;
                    }}
                    QPushButton:hover {{ background: #15803d; }}
                """)

                reddet_btn = QPushButton("❌  Reddet")
                reddet_btn.setMinimumHeight(40)
                reddet_btn.setMinimumWidth(130)
                reddet_btn.setCursor(Qt.PointingHandCursor)
                reddet_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {T['danger']}; color: white;
                        border: none; border-radius: 10px;
                        font-size: 13px; font-weight: 700;
                    }}
                    QPushButton:hover {{ background: #b91c1c; }}
                """)

                onayla_btn.clicked.connect(lambda checked, t_id=tid, t_ad=tarif.tarif_adi, t_ekleyen=tarif.ekleyen: self._tarif_onayla(t_id, t_ad, t_ekleyen))
                reddet_btn.clicked.connect(lambda checked, t_id=tid, t_ad=tarif.tarif_adi: self._tarif_reddet(t_id, t_ad))

                btn_row.addWidget(reddet_btn)
                btn_row.addSpacing(8)
                btn_row.addWidget(onayla_btn)
                kl.addLayout(btn_row)

                cl.addWidget(kart)

        cl.addStretch()
        scroll.setWidget(content)
        v.addWidget(scroll)
        return page

    def _build_istatistikler(self):
        T = self.aktif_tema
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar_frame")
        topbar.setFixedHeight(52)
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(20, 0, 20, 0)
        title = QLabel("📈 İstatistikler")
        title.setObjectName("header_label")
        tbl.addWidget(title)
        tbl.addStretch()
        v.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background: {T['bg_primary']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 24, 28, 28)
        cl.setSpacing(20)

        # ── Özet stat satırı (istatistikler üstte) ──
        stat_row = QHBoxLayout()
        stat_row.setSpacing(12)
        toplam_t = len(self.db.tarifler)
        toplam_k = len(self.db.kullanicilar)
        toplam_yorum = sum(len(t.yorumlar) for t in self.db.tarifler.values())
        toplam_goruntulem = sum(t.goruntuleme for t in self.db.tarifler.values())
        for icon, val, lbl, color, gstart, gend in [
            ("🍽️", str(toplam_t), "Toplam Tarif", T['chart1'], "#1B3A6B", "#0D2144"),
            ("👥", str(toplam_k), "Kullanıcı", T['chart2'], "#6B1B5A", "#3D0D35"),
            ("💬", str(toplam_yorum), "Yorum", T['chart3'], "#1B5A3A", "#0D3020"),
            ("👁", f"{toplam_goruntulem:,}", "Görüntüleme", T['chart4'], "#5A4B1B", "#302A0D"),
        ]:
            s = QFrame()
            s.setMinimumHeight(90)
            s.setStyleSheet(f"""
                QFrame {{
                        stop:0 {gstart}, stop:1 {gend});
                    border-radius: 14px;
                }}
            """)
            sl = QVBoxLayout(s)
            sl.setContentsMargins(16, 12, 16, 12)
            sl.setSpacing(4)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 20px; background: transparent;")
            val_lbl = QLabel(val)
            val_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color}; background: transparent;")
            lbl_lbl = QLabel(lbl)
            lbl_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; letter-spacing: 1px; color: rgba(255,255,255,0.6); background: transparent;")
            sl.addWidget(icon_lbl)
            sl.addWidget(val_lbl)
            sl.addWidget(lbl_lbl)
            stat_row.addWidget(s)
        cl.addLayout(stat_row)

        # ── İki kolon: Kategori bar + Donut ──
        two = QHBoxLayout()
        two.setSpacing(16)

        # Sol: Kategori bar chart
        kat_frame = QFrame()
        kat_frame.setObjectName("card_frame")
        kat_v = QVBoxLayout(kat_frame)
        kat_v.setContentsMargins(20, 18, 20, 18)
        kat_v.setSpacing(12)

        kat_title = QLabel("📂 Kategori Dağılımı")
        kat_title.setStyleSheet(f"font-size: 15px; font-weight: 700; background: transparent; color: {T['text_primary']};")
        kat_v.addWidget(kat_title)

        kategoriler = {}
        for t in self.db.tarifler.values():
            kat = t.kategori
            if kat not in kategoriler:
                kategoriler[kat] = {"sayi": 0, "puan_toplam": 0.0, "goruntulem": 0}
            kategoriler[kat]["sayi"] += 1
            kategoriler[kat]["puan_toplam"] += t.puan
            kategoriler[kat]["goruntulem"] += t.goruntuleme

        bar_colors = [T['chart1'], T['chart2'], T['chart3'], T['chart4'], T['chart5'], "#CE93D8", "#F97316"]
        max_sayi = max((v["sayi"] for v in kategoriler.values()), default=1)

        for ci, (kat, bilgi) in enumerate(sorted(kategoriler.items(), key=lambda x: -x[1]["sayi"])):
            sayi = bilgi["sayi"]
            ort_puan = bilgi["puan_toplam"] / sayi if sayi else 0.0
            goruntulem = bilgi["goruntulem"]
            color = bar_colors[ci % len(bar_colors)]

            row = QHBoxLayout()
            row.setSpacing(8)

            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background: {color}; border-radius: 5px;")
            dot_wrap = QVBoxLayout()
            dot_wrap.setContentsMargins(0, 0, 0, 0)
            dot_wrap.addStretch()
            dot_wrap.addWidget(dot)
            dot_wrap.addStretch()
            row.addLayout(dot_wrap)

            lbl = QLabel(kat)
            lbl.setFixedWidth(110)
            lbl.setStyleSheet(f"background: transparent; color: {T['text_primary']}; font-weight: 600; font-size: 12px;")
            row.addWidget(lbl)

            bar = QProgressBar()
            bar.setMaximum(max_sayi)
            bar.setValue(sayi)
            bar.setFormat("")
            bar.setMinimumHeight(22)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background: {T['bg_secondary']}; border-radius: 6px;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {color}, stop:1 {color}88);
                    border-radius: 5px;
                }}
            """)
            row.addWidget(bar, 1)

            sayi_lbl = QLabel(f"{sayi} tarif")
            sayi_lbl.setFixedWidth(52)
            sayi_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            sayi_lbl.setStyleSheet(f"background: transparent; color: {color}; font-weight: 700; font-size: 12px;")
            row.addWidget(sayi_lbl)

            puan_lbl = QLabel(f"⭐{ort_puan:.1f}")
            puan_lbl.setFixedWidth(46)
            puan_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            puan_lbl.setStyleSheet(f"background: transparent; color: {T['star']}; font-size: 11px; font-weight: 600;")
            row.addWidget(puan_lbl)

            gor_lbl = QLabel(f"👁{goruntulem}")
            gor_lbl.setFixedWidth(54)
            gor_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            gor_lbl.setStyleSheet(f"background: transparent; color: {T['text_secondary']}; font-size: 11px;")
            row.addWidget(gor_lbl)

            kat_v.addLayout(row)

        kat_v.addStretch()
        two.addWidget(kat_frame, 2)

        # Sağ: Donut + legend
        donut_frame = QFrame()
        donut_frame.setObjectName("card_frame")
        donut_v = QVBoxLayout(donut_frame)
        donut_v.setContentsMargins(20, 18, 20, 18)
        donut_v.setSpacing(12)

        donut_title = QLabel("Kategori")
        donut_title.setStyleSheet(f"font-size: 15px; font-weight: 700; background: transparent; color: {T['text_primary']};")
        donut_v.addWidget(donut_title)

        sorted_kats = sorted(kategoriler.items(), key=lambda x: -x[1]["sayi"])
        vals = [x[1]["sayi"] for x in sorted_kats]
        colors = bar_colors[:len(vals)]

        donut_center_row = QHBoxLayout()
        donut_chart = DonutChart(vals, colors, boyut=140)
        donut_center_row.addStretch()
        donut_center_row.addWidget(donut_chart)
        donut_center_row.addStretch()
        donut_v.addLayout(donut_center_row)

        # Legend: kategori + sayı + % oran
        toplam_tarif = sum(vals) or 1
        for ci, (kat, bilgi) in enumerate(sorted_kats):
            sayi = bilgi["sayi"]
            pct = sayi * 100 // toplam_tarif
            leg_row = QHBoxLayout()
            leg_row.setSpacing(8)
            dot_frame = QFrame()
            dot_frame.setFixedSize(10, 10)
            dot_frame.setStyleSheet(f"background: {bar_colors[ci % len(bar_colors)]}; border-radius: 5px;")
            leg_lbl = QLabel(kat)
            leg_lbl.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; background: transparent;")
            c = bar_colors[ci % len(bar_colors)]
            leg_val = QLabel(f"{sayi}  %{pct}")
            leg_val.setStyleSheet(f"color: {c}; font-weight: 700; font-size: 12px; background: transparent;")
            leg_row.addWidget(dot_frame)
            leg_row.addWidget(leg_lbl)
            leg_row.addStretch()
            leg_row.addWidget(leg_val)
            donut_v.addLayout(leg_row)

        donut_v.addStretch()
        two.addWidget(donut_frame, 1)
        cl.addLayout(two)

        # ── Top tarifler tablosu ──
        top_frame = QFrame()
        top_frame.setObjectName("card_frame")
        top_v = QVBoxLayout(top_frame)
        top_v.setContentsMargins(20, 18, 20, 18)
        top_v.setSpacing(12)

        top_header = QHBoxLayout()
        top_title_lbl = QLabel("🏆 En Yüksek Puanlı Tarifler")
        top_title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; background: transparent; color: {T['text_primary']};")
        top_header.addWidget(top_title_lbl)
        top_v.addLayout(top_header)

        top_tarifler = sorted(self.db.tarifler.values(), key=lambda t: t.puan, reverse=True)[:5]
        top_tablo = QTableWidget()
        top_tablo.setColumnCount(5)
        top_tablo.setHorizontalHeaderLabels(["Sıra", "Tarif", "Puan", "Oy", "Görüntüleme"])
        top_tablo.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        top_tablo.setRowCount(len(top_tarifler))
        top_tablo.setMaximumHeight(250)
        top_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        top_tablo.verticalHeader().setVisible(False)
        top_tablo.setAlternatingRowColors(True)

        madalya = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, t in enumerate(top_tarifler):
            sira = QTableWidgetItem(madalya[i])
            sira.setTextAlignment(Qt.AlignCenter)
            top_tablo.setItem(i, 0, sira)
            top_tablo.setItem(i, 1, QTableWidgetItem(f"{t.gorsel_emoji}  {t.tarif_adi}"))
            puan_item = QTableWidgetItem(f"⭐ {t.puan:.2f}")
            puan_item.setForeground(QBrush(QColor(T['star'])))
            puan_item.setTextAlignment(Qt.AlignCenter)
            top_tablo.setItem(i, 2, puan_item)
            oy_item = QTableWidgetItem(f"{t.puan_sayisi}")
            oy_item.setTextAlignment(Qt.AlignCenter)
            top_tablo.setItem(i, 3, oy_item)
            gor_item = QTableWidgetItem(f"👁 {t.goruntuleme}")
            gor_item.setTextAlignment(Qt.AlignCenter)
            top_tablo.setItem(i, 4, gor_item)
            top_tablo.setRowHeight(i, 44)

        top_v.addWidget(top_tablo)
        cl.addWidget(top_frame)

        # ── Mini line charts row ──
        mini_row_title = QLabel("📊 Haftalık Trend")
        mini_row_title.setStyleSheet(f"font-size: 16px; font-weight: 700; background: transparent; color: {T['text_primary']};")
        cl.addWidget(mini_row_title)

        mini_charts_row = QHBoxLayout()
        mini_charts_row.setSpacing(16)
        trend_data = [
            ("Tarif Eklemeleri", [2, 3, 1, 4, 2, 5, 3], T['chart1']),
            ("Kullanıcı Kaydı", [1, 2, 1, 3, 2, 1, 4], T['chart2']),
            ("Yorum Sayısı", [5, 4, 6, 8, 7, 9, 11], T['chart3']),
            ("Değerlendirme", [3, 5, 4, 6, 5, 8, 7], T['chart4']),
        ]

        for name, data, color in trend_data:
            mc_frame = QFrame()
            mc_frame.setObjectName("card_frame")
            mc_v = QVBoxLayout(mc_frame)
            mc_v.setContentsMargins(16, 14, 16, 14)
            mc_v.setSpacing(8)
            mc_title = QLabel(name)
            mc_title.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {T['text_secondary']}; background: transparent;")
            mc_val = QLabel(str(data[-1]))
            mc_val.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color}; background: transparent;")
            mc_chart = MiniLineChart(data, color, yukseklik=50)
            mc_v.addWidget(mc_title)
            mc_v.addWidget(mc_val)
            mc_v.addWidget(mc_chart)
            mini_charts_row.addWidget(mc_frame)

        cl.addLayout(mini_charts_row)
        cl.addStretch()
        scroll.setWidget(content)
        v.addWidget(scroll)
        return page

    def tema_guncelle(self, tema):
        self.aktif_tema = tema
        self._tarif_tablosunu_guncelle()
        self._kullanici_tablosunu_guncelle()


# ─────────────────────────── ANA PENCERE ───────────────────────────

class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Veritabani()
        self.gece_modu = True
        self.aktif_tema = GECE_MODU
        self.kullanici = None
        self.aktif_panel = None
        self.setWindowTitle("Tariftirium — Yemek Tarif Platformu")
        self.resize(1920, 1080)
        self.setMinimumSize(1280, 720)
        self._tema_uygula()
        self._giris_goster()

    def _tema_uygula(self):
        self.aktif_tema = GECE_MODU if self.gece_modu else GUNDUZ_MODU
        self.setStyleSheet(get_stylesheet(self.aktif_tema))

    def _tema_degistir(self):
        self.gece_modu = not self.gece_modu
        self._tema_uygula()
        if self.aktif_panel:
            self.aktif_panel.set_tema(self.aktif_tema)
            self.aktif_panel.tema_guncelle(self.aktif_tema)

    def _giris_goster(self):
        d = GirisEkrani(self.db, self.aktif_tema)
        d.setStyleSheet(get_stylesheet(self.aktif_tema))
        if d.exec_() == QDialog.Accepted:
            self.kullanici = d.kullanici
            self._panel_yukle()
        else:
            # Kullanici X butonuna basti veya dialog kapandi - uygulamayi kapat
            self.close()

    def _panel_yukle(self):
        if self.centralWidget():
            self.centralWidget().deleteLater()

        if self.kullanici.rol == "admin":
            panel = AdminPaneli(self.db, self.kullanici, self._tema_degistir, self._cikas)
        else:
            panel = KullaniciPaneli(self.db, self.kullanici, self._tema_degistir, self._cikas)

        panel.set_tema(self.aktif_tema)
        panel.tema_guncelle(self.aktif_tema)

        self.aktif_panel = panel
        self.setCentralWidget(panel)
        self.setWindowTitle(f"Tariftirium — {self.kullanici.ad}")

    def _cikas(self):
        reply = QMessageBox.question(self, "Çıkış", "Çıkmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.kullanici = None
            self.aktif_panel = None
            d = GirisEkrani(self.db, self.aktif_tema)
            d.setStyleSheet(get_stylesheet(self.aktif_tema))
            if d.exec_() == QDialog.Accepted:
                self.kullanici = d.kullanici
                self._panel_yukle()
            else:
                self.close()


# ─────────────────────────── UYGULAMA BAŞLATICI ───────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Tariftirium")
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.PreferFullHinting)
    app.setFont(font)

    pencere = AnaPencere()
    pencere.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()