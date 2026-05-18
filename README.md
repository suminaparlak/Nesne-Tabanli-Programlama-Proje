# 💻 Projelere Genel Bakış: Kütüphane Otomasyonu & Etkinlik Yönetim Sistemi

---

## 📚 Kütüphane Yönetim Sistemi (KütüphaneX)

Kullanıcıların kitap kataloğunu inceleyip ödünç alabildiği, yöneticilerin ise dinamik olarak envanteri, üyeleri ve geciken emanet işlemlerini takip edebildiği, çift rollü (Admin/Üye) ve çift temalı (Dark/Light) Python tabanlı gelişmiş bir otomasyon sistemidir.

### 🚀 Özellikler

#### 📖 Kitap ve Envanter Yönetimi
* **Dinamik Filtreleme ve Arama:** Kitap adı, yazar veya kategori bazlı anlık arama motoru.
* **Gelişmiş CRUD Altyapısı:** Yöneticiler için hata dökümlü ve veri doğrulamalı yeni kitap ekleme, güncelleme ve silme paneli.
* **Ödünç Alma & Stok Kontrolü:** Kitapların mevcut durumunu (`Mevcut`, `Ödünçte`) anlık günceller ve ödünçteki kitapların silinmesini engeller.

#### 💰 Akıllı Ödünç ve İşlem Motoru
* **Kullanıcı Bazlı Adil Ödünç Limiti:** Standart üyelerin aynı anda en fazla 3 kitap ödünç alabilmesini sağlayan dinamik limit kontrolü.
* **Otomatik İade Tarihi Hesaplama:** Ödünç alma esnasında 14 günlük standart iade süresini otomatik hesaplayan takvim entegrasyonu.
* **Gecikme Takip Sistemi:** Son iade tarihi geçmiş kitapları gün farkıyla birlikte dashboard üzerinde kırmızı alarm ile listeleyen akıllı takip motoru.

#### 🔒 Güvenlik ve Çift Rol Tabanlı Yönetim
* **Çoklu Kullanıcı Altyapısı:** Giriş yapan hesaba göre sistemi otomatik şekillendiren "Admin" ve "Standart Kullanıcı" panelleri.
* **Gelişmiş Kayıt Doğrulaması:** Mükerrer kullanıcı adı ve e-posta kontrolü sağlayan veritabanı koruma mekanizması.
* **Giriş Güvenliği:** Regex tabanlı veri giriş kısıtlamaları (Kullanıcı adında sadece harf, telefonda sadece 11 haneli sayı kuralı).

#### 📊 Modern Dashboard & Kullanıcı Deneyimi
* **Dinamik Tema Motoru:** Uygulama genelinde çalışma zamanında (runtime) dinamik olarak değişebilen Koyu (Dark) ve Açık (Light) tema desteği.
* **İstatistik Kartları:** Toplam kitap, mevcut kitap, ödünçtekiler, kayıtlı üyeler ve geciken kitap sayılarını anlık yansıtan renk kodlu kart yapısı.

---

## 🎭 Etkinlik Yönetim Sistemi (EtkinlikApp)

Sosyal ve kültürel organizasyonların (Sinema, Konser, Festival) biletleme süreçlerini dijitalleştiren; koltuk şemalı sinema rezervasyonu, kategori bazlı bilet fiyatlandırması ve görsel afiş desteği sunan Python ve PyQt5 tabanlı interaktif bir biletleme platformudur.

### 🚀 Özellikler

#### 🎫 Kategori Tabanlı Etkinlik ve Vitrin Yönetimi
* **Gelişmiş Sinema Portalı:** Film seçimi, şehir/salon filtreleme ve 3 adımlı (Seans $\rightarrow$ Koltuk $\rightarrow$ Ödeme) ilerici rezervasyon sihirbazı (Wizard UI).
* **Görsel Afiş Desteği:** Klasördeki film ve sanatçı görsellerini otomatik olarak bularak arayüze dinamik olarak giydiren görsel altyapısı.
* **Yatay Konser Kartları:** Konser organizasyonlarını ve turne tarihlerini alt alta, özel bilet butonlarıyla listeleyen modern vitrin düzeni.

#### 💺 Dinamik Koltuk Seçim & Ödeme Motoru
* **Dinamik Matris Koltuk Şeması:** 10x10 boyutunda, sinema perdesi hizalamalı ve koridor boşluklu interaktif koltuk seçim paneli.
* **Çakışma Önleyici Koruma:** Veritabanından o seansa ait dolu koltukları çekerek kırmızı renkle bloke eden ve mükerrer bilet alımını engelleyen kontrol mekanizması.
* **Akıllı Yaş ve Fatura Doğrulaması:** Kart, CVV ve fatura verilerini Regex ile denetleyen; öğrenci biletlerinde yaş sınırına göre kural ihlallerini engelleyen filtreler.
* **Kategori Bazlı Çarpanlı Fiyatlandırma:** Etkinlik türüne (VIP, Loca, Sahne Önü) veya salon formatına (IMAX, GOLD CLASS, 4DX) göre bilet fiyatlarını otomatik hesaplayan fiyat motoru.

#### 📊 Gelişmiş Raporlama & Veri Yönetimi
* **Anlık Doluluk Barları:** Etkinliklerin doluluk oranlarını grafiksel arayüz üzerinde dinamik renk geçişleriyle (%70 altı Yeşil, %70-100 Turuncu, %100 Dolu Kırmızı) gösteren sistem.
* **ASCII Karakter Tabanlı Doluluk Grafiği:** Özel karakterleri kullanarak harici kütüphaneye ihtiyaç duymadan metinsel doluluk grafiği üreten gelişmiş raporlama alanı.
* **CSV Dışa Aktarım Sistemi:** Etkinlik ve genel katılım verilerini tek tıkla Excel uyumlu `.csv` formatında dışarı aktarma yeteneği.

---

1. carshare: Araç kiralama sistemi grafiksel kullanıcı dağıtımını (GUI) ve arka plan veri tabanının yönetilen ana Python kaynak kodu dosyası. Bu kod dosyası; segmentlere göre araç depolama, yeni müşteri kayıt oluşturma, kiralama süresi programlama, faturalandırma ve teslimat tarihlerini takip etme gibi temel işlevleri barındırır. 
2. doktorrandevu: Hasta kayıtları, doktor çalışma takvimleri, poliklinik bilgileri ve aktif/geçmiş randevuların güvenli bir şekilde saklandığı SQLite veritabanı dosyası. Sistemdeki randevu saatlerinin çakışmasını önlemek için durumlarını dinamik olarak yönetir.
3. dijitalkütüphane: Kütüphane sistemi grafiksel kullanıcı dağıtımının (GUI) adı ve veri tabanı işlemlerinin arka planında yürütülen ana Python kaynak kod dosyası. Python ve PyQt5 detaylı bu dosya; kitap arama, yeni üye ekleme, kitap eksik verme, iade alma ve geciken kitapları listeleme gibi temel yönetim yapılmasına izin verir.
4. etkinlikapp: Sistemdeki sinema seansları, konser programları, kayıtlı dosyalar ve sunulanların güvenli bir şekilde saklandığı Python ve PyQt5 veri tabanı dosyası. Etkinlik kapasitelerini, koltuk doluluk oranlarını ve bilet satış kayıtlarını dinamik olarak takip etmek için kullanılır.
5. onlinekurs: enilerin sistemlerinin kaydedilmesi, eğitmenlerin ders programlarının düzenlenmesi ve kurs kontenjanlarının anlık olarak kaydedilmesini sağlayan modern kullanıcı arayüzü kodudur.
6. Yemek:Mutfağın günlük menüleri, güncel yemek tariflerinin içerikleri, müşteri yorum/puanlarını ve anında mutfak sipariş kuyruğunu yönetilen ilişkisel veri tabanı dosyasıdır.
7. fitness: Salona gelen Üyelerin kayıt sürelerini, boy-kilo gibi gelişim grafiklerini ve kendilerine özel hazırlanan antrenman programlarını hafızasında tutan bilgi bankasıdır.
8. depo: şirket ambarındaki zararlı barkod numaralarını, güncel adetlerini ve raflara giren-çıkan malların tüm hareketlerini kaydeden veri tablodur.
9. seyahat: Yolculuk yapacak kişilerin Nereden nereye gideceğini seçtiği uygun seferleri saniyeler içinde listelediği ve kendi koltuğunu ayırabildiği bilet ayırtabildiği biletleme arayüzüdür.
10. crm: Satış ekibinin her sabahki müşteri dinlemesini yöneten, yeni potansiyel müşterilerin eklendiği bağlantıların güncellendiği şirket içi takip programıdır.

## 🛠 Kullanılan Kütüphaneler

```bash
# 1. Temel Arayüz ve GUI Grafik Bileşenleri
pip install PyQt5

# 2. Veritabanı, Dosya ve Ağ Yönetimi
# (Python standart kütüphanesinde dahili olarak gelirler)
# sqlite3, datetime, csv, os, sys, urllib
