import zipfile
import os
import shutil
import re
import json
import sys
import datetime
import time

from app.sahis.musteki import Musteki
from app.sahis.magdur import Magdur
from app.sahis.supheli import Supheli


class Parser:
    def __init__(self, path: str):
        self.path = path
        self.anahtarlar = {
            "DAVACI": [],
            "MÜŞTEKİ": [],
            "ŞÜPHELİ": [],
            "SUÇ": [],
            "SUÇ TARİHİ": [],
            "SUÇ TARİHİ VE YERİ": [],
            "ŞİKAYET TARİHİ": [],
            "SEVK MADDESİ": [],
            "DELİLLER": [],
        }

        self.content = self.read()
        self.data = self.parse()

    def read(self):
        udfFile = zipfile.ZipFile(self.path, 'r')
        content = udfFile.read("content.xml").decode('utf-8')
        udfFile.close()
        return content
    
    def parse(self):
        content = self.content
        try:
            content = content.split("<content><![CDATA[")[1]
            content = content.split("]]>")[0]
            content = content.replace("\n", "~~")
            content = re.sub(r'\s+', ' ', content)
            content = content.replace("~~", "\n")
            content = content.replace('"', "'")

            for anahtar in self.anahtarlar:
                if anahtar in content:
                    variations = [anahtar + " : ", anahtar + ": ", anahtar + " :"]
                    for variation in variations:
                        start = 0  # İlk arama noktasını belirle
                        while variation in content[start:]:  # Varyasyon içeriğin içinde olduğu sürece
                            index = content[start:].find(variation) + start  # Varyasyonun başlangıç indeksini bul
                            if index != -1:
                                # Varyasyonun sonrasındaki veriyi al ve işle
                                data = content[index + len(variation):].split("\n")[0].strip().replace("\n", " ").lstrip().rstrip()
                                if data not in self.anahtarlar[anahtar]:
                                    self.anahtarlar[anahtar].append(data)
                                start = index + len(variation)  # Sonraki arama için başlangıç noktasını güncelle
                            else:
                                break  # Eğer varyasyon bulunamazsa döngüyü kır


            return content
        except:
            raise ValueError("Veri okunamadı.")

    def tarih_bul(self, content: list):
        formats = {
            "dd.mm.yyyy": {"pattern": r'\d{2}.\d{2}.\d{4}', "min_year": None, "max_year": None},
            "dd/mm/yyyy": {"pattern": r'\d{2}/\d{2}/\d{4}', "min_year": None, "max_year": None},
            "dd-mm-yyyy": {"pattern": r'\d{2}-\d{2}-\d{4}', "min_year": None, "max_year": None},
            "yyyy.mm.dd": {"pattern": r'\d{4}.\d{2}.\d{2}', "min_year": None, "max_year": None},
            "yyyy/mm/dd": {"pattern": r'\d{4}/\d{2}/\d{2}', "min_year": None, "max_year": None},
            "yyyy-mm-dd": {"pattern": r'\d{4}-\d{2}-\d{2}', "min_year": None, "max_year": None},
            "yyyy": {"pattern": r'\d{4}', "min_year": 1923, "max_year": datetime.datetime.now().year},
        }

        if len(content) == 0:
            return {"datetime": None, "timestamp": None, "format": None, "isEdited": False}
        
        if not any(char.isdigit() for char in content[0]):
            return {"datetime": None, "timestamp": None, "format": None, "isEdited": False}

        for format in formats:
            pattern = formats[format]["pattern"]
            min_year = formats[format]["min_year"]
            max_year = formats[format]["max_year"]
            for date in content:
                date = date.replace(" ", "")
                date = date.replace(",", "")
                date = re.sub(r'[a-zA-Z]', '', date)
                date = re.sub(r'[^0-9/.-]', '', date)

                if date.count("/") == 1:
                    date = date.replace("/", "")
                if date.count(".") == 1:
                    date = date.replace(".", "")
                if date.count("-") == 1:
                    date = date.replace("-", "")
                
                isEdited = False

                if re.match(pattern, date):
                    date = date.split(" ")[0]
                    date = date.replace(".", "/").replace("-", "/")
                    date = date.split("/")

                    if len(date) != 3 and len(date[0]) == 4:
                        isEdited = True
                        date = [1, 1, date[0]]
                        
                    print("temiz date", date)

                    day = int(date[0]) if int(date[0]) < 32 else 1;isEdited = True
                    month = int(date[1]) if int(date[1]) < 13 else 1;isEdited = True
                    year = int(date[2]) if int(date[2]) > 1923 and int(date[2]) < datetime.datetime.now().year else 9999

                    if min_year is not None and max_year is not None:
                        if year >= min_year and year <= max_year:
                            date = datetime.datetime(year, month, day)
                            try:
                                int_timestamp_11 = int(time.mktime(date.timetuple()))
                            except:
                                int_timestamp_11 = None
                            return {"datetime": date, "timestamp": int_timestamp_11, "format": format, "isEdited": isEdited}
                        else:
                            return {"datetime": None, "timestamp": None, "format": format, "isEdited": isEdited}
                    else:
                        date = datetime.datetime(year, month, day)
                        try:
                            int_timestamp_11 = int(time.mktime(date.timetuple()))
                        except:
                            int_timestamp_11 = None
                        return {"datetime": date, "timestamp": int_timestamp_11, "format": format, "isEdited": isEdited}
                else:
                    continue

    def musteki(self, content: str):
        person_keys = ["oğlu", "Oğlu", "OĞLU", "kızı", "Kızı", "KIZI"]
        isPerson = False
        for anahtar in person_keys:
            if anahtar in content:
                isPerson = True
                break
        
        tam_adi = content.split(",")[0]
        ad = None
        soyad = None
        anne_adi = None
        baba_adi = None
        adres = None

        if isPerson:
            dogum_tarihi = self.tarih_bul([content])
            anne_adi = content.split("'den olma")[0].split(" ")[-1].strip()
            baba_adi = content.split(",")[1].split(" ")[1].strip()
            ad, soyad = tam_adi.split(" ")[0], tam_adi.split(" ")[1]

        else:
            adres = content.replace(tam_adi, "").strip()[1:]

        print("ad", ad)
        print("soyad", soyad)
        print("anne_adi", anne_adi)
        print("baba_adi", baba_adi)

        


        

        