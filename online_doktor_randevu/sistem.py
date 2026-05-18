from __future__ import annotations

from datetime import date, time
from typing import List

from models import Doktor, Hasta, Randevu


class RandevuSistemi:
    def __init__(self) -> None:
        self._randevular: List[Randevu] = []
        self._son_id = 0

    def _sonraki_id(self) -> int:
        self._son_id += 1
        return self._son_id

    def randevu_olustur(self, hasta: Hasta, doktor: Doktor, tarih: date, saat: time) -> Randevu:
        if not doktor.uygunluk_kontrol(saat):
            raise ValueError(f"{doktor.ad} doktoru {saat.strftime('%H:%M')} saatinde uygun degil.")

        for r in self._randevular:
            if r.doktor.doktor_id == doktor.doktor_id and r.tarih == tarih and r.saat == saat:
                raise ValueError("Bu doktorun bu saatinde zaten bir randevu var.")

        yeni = Randevu(
            randevu_id=self._sonraki_id(),
            tarih=tarih,
            saat=saat,
            doktor=doktor,
            hasta=hasta,
        )
        self._randevular.append(yeni)
        return yeni

    def randevu_iptal(self, randevu_id: int) -> bool:
        for i, r in enumerate(self._randevular):
            if r.randevu_id == randevu_id:
                self._randevular.pop(i)
                return True
        return False

    def gunluk_randevu_listesi(self, tarih: date) -> List[Randevu]:
        return sorted(
            [r for r in self._randevular if r.tarih == tarih],
            key=lambda x: x.saat,
        )
