from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Urun:
    urun_id: int
    ad: str
    stok: int
    fiyat: float

    def stok_arttir(self, miktar: int) -> None:
        if miktar <= 0: raise ValueError("Artirilan miktar pozitif olmali.")
        self.stok += miktar

    def stok_azalt(self, miktar: int) -> None:
        if miktar <= 0: raise ValueError("Azaltilan miktar pozitif olmali.")
        if miktar > self.stok: raise ValueError(f"Yetersiz stok. Mevcut: {self.stok}, Istenen: {miktar}")
        self.stok -= miktar

@dataclass
class Siparis:
    siparis_id: int
    urun: Urun
    adet: int

    @property
    def toplam_fiyat(self) -> float:
        return self.urun.fiyat * self.adet

    @classmethod
    def siparis_olustur(cls, siparis_id: int, urun: Urun, adet: int) -> "Siparis":
        if adet <= 0: raise ValueError("Siparis adedi pozitif olmali.")
        return cls(siparis_id=siparis_id, urun=urun, adet=adet)
