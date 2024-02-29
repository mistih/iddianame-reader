import json
from app.sahis.supheli import Supheli
from app.sahis.musteki import Musteki
from app.sahis.magdur import Magdur

from app.parser import Parser

import os
import logging

logging.basicConfig(filename="tests.log", level=logging.INFO, encoding="utf-8", filemode="w")

musteki = Musteki(
    ad="Ahmet", soyad="Yılmaz", dogum_tarihi=1980, sevk_maddesi="", suc_tarihi=0, dogum_yeri="Ankara", cinsiyet=1, medeni_durum=1,
    egitim_durumu="Lisans", meslek="Doktor", adres="Ankara", tc_kimlik_no=12345678901, 
    anne_adi="Fatma", baba_adi="Mehmet"
)

magdur = Magdur(
    ad="Veli", soyad="Yılmaz", dogum_tarihi=1980, sevk_maddesi="", suc_tarihi=0, dogum_yeri="Ankara", cinsiyet=1, medeni_durum=1, 
    egitim_durumu="Lisans", meslek="Doktor", adres="Ankara", tc_kimlik_no=12345678901, 
    anne_adi="Fatma", baba_adi="Mehmet"
)

supheli = Supheli(
    ad="Ali", soyad="Kılıç", dogum_tarihi=1980, dogum_yeri="Ankara", cinsiyet=1, medeni_durum=1, 
    egitim_durumu="Lisans", meslek="Doktor", adres="Ankara", tc_kimlik_no=12345678901, 
    anne_adi="Fatma", baba_adi="Mehmet", musteki=musteki, magdur=magdur
)