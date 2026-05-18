# Online Doktor Randevu Sistemi

Bu proje, **PyQt5 + SQLite** kullanan masaustu doktor randevu uygulamasidir.

## Ozellikler (hocanin istedigi tipik maddeler)

- **Login + rol**: `admin` ve `personel`
- **CRUD**: Doktor / Hasta yonetimi
- **Randevu olusturma + iptal**
- **Cakisma kontrolu**: Ayni doktor + ayni tarih/saat icin 2 randevu olamaz
- **Arama/filtre**: Doktor/Hasta listeleri ve gunluk randevu listesi
- **Rapor**: Gunluk randevu listesi
- **Disari aktarma**: Gunluk listeyi CSV olarak kaydetme

## Varsayilan kullanicilar

- **admin / admin123** (doktor CRUD yetkisi var)
- **personel / 1234** (doktor CRUD kilitli)

## Calistirma

```bash
pip install -r requirements.txt
python main.py
```
