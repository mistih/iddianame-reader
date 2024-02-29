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





# TESTS
open("tests.log", "w").close()
logging.info("TESTS STARTED")
anyError = False

totalFiles = 0
successfulFiles = 0
errorFiles = 0

for file in os.listdir("tests"):
    hata = 0
    if file.endswith(".udf"):
        parser = Parser(f"tests/{file}")
        anahtarlar = parser.anahtarlar
        
        logging.info(f"----------------- {file} dosyası test ediliyor. -----------------")
        print(f"--------------------------------- {file} dosyası test ediliyor. ---------------------------------")
        data = (parser.anahtarlar)
        json_data = json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True, default=str)
        f = open(f"tests/{file}.json", "w", encoding="utf-8")
        f.write(json_data)
        f.close()

        
        if anahtarlar["ŞÜPHELİ"] is None:
            logging.info(f"{file} dosyasında şüpheli bulunamadı."),
            hata += 1
            anyError = True

        if anahtarlar["MÜŞTEKİ"] is None:
            logging.info(f"{file} dosyasında müşteki bulunamadı.")
            hata += 1
            anyError = True

        if anahtarlar["SUÇ"] is None:
            logging.info(f"{file} dosyasında suç bulunamadı.")
            hata += 1
            anyError = True

        if anahtarlar["SEVK MADDESİ"] is None:
            logging.info(f"{file} dosyasında sevk maddesi bulunamadı.")
            hata += 1
            anyError = True

    if anyError:
        logging.info(f"{file} dosyasında {hata} adet anahtar hatası bulundu. ❌")
        errorFiles += 1
    else:
        logging.info(f"{file} dosyası için test başarılı. ✅")
        successfulFiles += 1

    anyError = False
    print(parser.tarih_bul(parser.anahtarlar["SUÇ TARİHİ VE YERİ"]))
    

logging.info(f"Toplam {totalFiles} dosya test edildi. {successfulFiles} dosya başarılı, {errorFiles} dosya hatalı.")