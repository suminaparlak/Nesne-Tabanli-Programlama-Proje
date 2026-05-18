from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import List


@dataclass
class Hasta:
    hasta_id: int
    ad: str
    tc: str
    telefon: str

    def randevu_al(self, sistem: "RandevuSistemi", doktor: "Doktor", tarih: date, saat: time) -> "Randevu":
        return sistem.randevu_olustur(self, doktor, tarih, saat)


@dataclass
class Doktor:
    doktor_id: int
    ad: str
    uzmanlik: str
    uygun_saatler: List[time] = field(default_factory=list)

    def uygunluk_kontrol(self, saat: time) -> bool:
        return saat in self.uygun_saatler


@dataclass
class Randevu:
    randevu_id: int
    tarih: date
    saat: time
    doktor: Doktor
    hasta: Hasta
