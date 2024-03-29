
import hashlib
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
        # check if the file exists
        self.path = path
        if not os.path.exists(self.path):
            raise ValueError("Dosya bulunamadı.")
        
        # check if the file is a zip file
        if not zipfile.is_zipfile(self.path):
            raise ValueError("Geçersiz dosya biçimi.")

        
        # read the json/anahtarlar.json
        self.anahtarlar = json.load(open("app/json/anahtarlar.json", "r", encoding="utf-8"))

        # read json/anahtar_info.json
        self.anahtar_info = json.load(open("app/json/anahtar_info.json", "r", encoding="utf-8"))

        self.content = self.read()
        self.data = self.parse()

    def read(self):
        udfFile = zipfile.ZipFile(self.path, 'r')
        content = udfFile.read("content.xml").decode('utf-8')
        udfFile.close()
        return content
    
    def editLine(self, line: str, variation: str):
        return line.replace(variation, "").split("\n")[0].strip().replace("\n", " ").lstrip().rstrip()
  
    def parse(self):
        content = self.content
        try:
            content = content.split("<content><![CDATA[")[1]
            content = content.split("]]>")[0]
            content = content.replace("\n", "~~")
            content = re.sub(r'\s+', ' ', content)
            content = content.replace("~~", "\n")
            content = content.replace('"', "'")
            first_part = content

            variatons = ["SORUŞTURMA", "Soruşturma", "soruşturma", "İNCELENDİ", "İncelendi"]
            for variation in variatons:
                if variation in content:
                    first_part = content.split(variation)[0]
                    break
           
            lastAnahtar = None
            lastFollowKey = None
            lastVariation = None
            lastSüpheli = None
            lastMusteki = None

            follow_keys = ["MÜŞTEKİ", "ŞÜPHELİ", "MAĞDUR", "DAVACI", "MÜŞTEKİLER", "ŞÜPHELİLER", "MAĞDURLAR", "DAVACILAR"]
            
            sequential_keys = [
                "SUÇ",
                "SUÇ TARİHİ",
                "SUÇ TARİHİ VE YERİ",
                "GÖZALTI TARİHİ",
                "SALIVERİLME TARİHİ",
                "TUTUKLAMA TARİHİ",
                "TAHLİYE TARİHİ",
                "YAKALAMA KARAR TARİHİ",
                "ŞİKAYET TARİHİ",
                "SEVK MADDESİ",
                "SEVK MADDELERİ"
            ]

            for index, line in enumerate(first_part.split("\n")):
                hasVariation = False
                isInList = False
                follow = False

                if re.search(r"\b\d+-", line[0:5]):
                    data = self.editLine(line, lastVariation)
                    if len(data) > 0:
                        if self.anahtarlar["ŞÜPHELİLER"] != [] and lastFollowKey == "ŞÜPHELİ":
                            lastFollowKey = "ŞÜPHELİLER"
                        if self.anahtarlar["MÜŞTEKİLER"] != [] and lastFollowKey == "MÜŞTEKİ":
                            lastFollowKey = "MÜŞTEKİLER"
                        if self.anahtarlar["MAĞDURLAR"] != [] and lastFollowKey == "MAĞDUR":
                            lastFollowKey = "MAĞDURLAR"
                        if self.anahtarlar["DAVACILAR"] != [] and lastFollowKey == "DAVACI":
                            lastFollowKey = "DAVACILAR"

                        if lastFollowKey == "ŞÜPHELİ" or lastFollowKey == "ŞÜPHELİLER":
                            lastSupheli = data
                            sahis = self.sahis(data)
                            data = {"hash": self.get_hash(lastSupheli), "data": data, "ad": sahis["ad"], "soyad": sahis["soyad"], "tamAdi":sahis["tamAdi"], "dogumTarihi": sahis["dogumTarihi"]["timestamp"], "anneAdi": sahis["anneAdi"], "babaAdi": sahis["babaAdi"], "isPerson":sahis["isPerson"]}

                        if lastFollowKey in sequential_keys:
                            self.anahtarlar[lastFollowKey][self.get_hash(lastSupheli)] = data
                        else:
                            self.anahtarlar[lastFollowKey].append(data)
                    continue

                # fix
                for anahtar in self.anahtarlar:
                    if anahtar in line:
                        lastAnahtar = anahtar
                        isInList = True
                        variations = [anahtar + " : ", anahtar + ": ", anahtar + " :"]
                        for variation in variations:
                            index = line.find(variation)
                            if index != -1:
                                if anahtar in follow_keys:
                                    lastFollowKey = anahtar
                                hasVariation = True
                                lastVariation = variation
                                data = self.editLine(line, variation)
                            
                        if hasVariation:
                            data = self.editLine(line, lastVariation)
                            if len(data) > 0:
                                if self.anahtarlar["ŞÜPHELİLER"] != [] and anahtar == "ŞÜPHELİ":
                                    anahtar = "ŞÜPHELİLER"
                                if self.anahtarlar["MÜŞTEKİLER"] != [] and anahtar == "MÜŞTEKİ":
                                    anahtar = "MÜŞTEKİLER"
                                if self.anahtarlar["MAĞDURLAR"] != [] and anahtar == "MAĞDUR":
                                    anahtar = "MAĞDURLAR"
                                if self.anahtarlar["DAVACILAR"] != [] and anahtar == "DAVACI":
                                    anahtar = "DAVACILAR"

                                if lastAnahtar == "ŞÜPHELİ" or lastAnahtar == "ŞÜPHELİLER":
                                    lastSupheli = data
                                    sahis = self.sahis(data)
                                    data = {"hash": self.get_hash(lastSupheli), "data": data, "ad": sahis["ad"], "soyad": sahis["soyad"], "tamAdi":sahis["tamAdi"], "dogumTarihi": sahis["dogumTarihi"]["timestamp"], "anneAdi": sahis["anneAdi"], "babaAdi": sahis["babaAdi"], "isPerson":sahis["isPerson"]}

                                if anahtar in sequential_keys:
                                    self.anahtarlar[anahtar][self.get_hash(lastSupheli)] = data
                                else:
                                    self.anahtarlar[anahtar].append(data)

                if lastAnahtar is not None and isInList is False:
                    data = self.editLine(line, lastVariation)
                    if len(data) > 0:
                        if self.anahtarlar["ŞÜPHELİLER"] != [] and lastAnahtar == "ŞÜPHELİ":
                            lastAnahtar = "ŞÜPHELİLER"
                        if self.anahtarlar["MÜŞTEKİLER"] != [] and lastAnahtar == "MÜŞTEKİ":
                            lastAnahtar = "MÜŞTEKİLER"
                        if self.anahtarlar["MAĞDURLAR"] != [] and lastAnahtar == "MAĞDUR":
                            lastAnahtar = "MAĞDURLAR"
                        if self.anahtarlar["DAVACILAR"] != [] and lastAnahtar == "DAVACI":
                            lastAnahtar = "DAVACILAR"

                        if lastAnahtar == "ŞÜPHELİ" or lastAnahtar == "ŞÜPHELİLER":
                            lastSupheli = data
                            sahis = self.sahis(data)
                            data = {"hash": self.get_hash(lastSupheli), "data": data, "ad": sahis["ad"], "soyad": sahis["soyad"], "tamAdi":sahis["tamAdi"], "dogumTarihi": sahis["dogumTarihi"]["timestamp"], "anneAdi": sahis["anneAdi"], "babaAdi": sahis["babaAdi"], "isPerson":sahis["isPerson"]}

                        if lastAnahtar in sequential_keys:
                            self.anahtarlar[lastAnahtar][self.get_hash(lastSupheli)] = data
                        else:
                            self.anahtarlar[lastAnahtar].append(data)
     
            return content
        except:
            raise ValueError("Iddianame içeriğini okurken bir hata oluştu. Lütfen dosyanın içeriğini kontrol edin.")

        
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

    def string_temizle(self, string):
        for index, harf in enumerate(string):
            if harf.isalpha() or harf.isspace():
                return string[index:].lstrip().rstrip()
        return ""
    
    def full_upper_turkish(self, string):
        if "i" in string:
            string = string.replace("i", "İ")
        if "ç" in string:
            string = string.replace("ç", "Ç")
        if "ş" in string:
            string = string.replace("ş", "Ş")
        if "ğ" in string:
            string = string.replace("ğ", "Ğ")
        if "ü" in string:
            string = string.replace("ü", "Ü")
        if "ö" in string:
            string = string.replace("ö", "Ö")
        if "ı" in string:
            string = string.replace("ı", "I")

        string = string.upper() 
        return string

    def clean_anahtarlar(self):
        mustekiler = False
        magdurlar = False
        supheliler = False
        davacilar = False

        if len(self.anahtarlar["MÜŞTEKİLER"]) > 0:
            mustekiler = True
        
        if len(self.anahtarlar["ŞÜPHELİ"]) > 1:
            supheliler = True

        if len(self.anahtarlar["MAĞDUR"]) > 1:
            magdurlar = True
            
        if len(self.anahtarlar["DAVACI"]) > 1:
            davacilar = True

        anahtarlar = self.anahtarlar.copy()
        
        for anahtar in list(anahtarlar.keys()):
            if anahtarlar[anahtar] == []:
                anahtarlar.pop(anahtar)
        
        self.anahtarlar = anahtarlar
        return {"mustekiler": mustekiler, "magdurlar": magdurlar, "supheliler": supheliler, "davacilar": davacilar}

    def get_hash(self, content: str):
        sahis = self.sahis(content)
        sha1 = hashlib.sha1()
        sha1.update(sahis["tamAdi"].encode("utf-8"))
        sha1.update(str(sahis["dogumTarihi"]["datetime"]).encode("utf-8"))
        sha1.update(str(sahis["isPerson"]).encode("utf-8"))
        return sha1.hexdigest()


    def sahis(self, content: str):
        content = re.sub(r"\b\d+-", "", content)
        content = self.string_temizle(content)

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
        dogum_tarihi = None

        if isPerson:
            anneKeys = ["'den Olma", "'den olma", "'DEN OLMA", "'DEN OLMA", "'dan Olma", "'dan olma", "'DAN OLMA", "'DAN OLMA"]
            anneKey = "'den olma"
            for key in anneKeys:
                if key in content:
                    anneKey = key
            dogum_tarihi = self.tarih_bul([content])
            anne_adi = self.full_upper_turkish(content.split(anneKey)[0].split(" ")[-1].strip())
            baba_adi = self.full_upper_turkish(content.split(",")[1].split(" ")[1].strip())
            ad, soyad = tam_adi.split(" ")[0], tam_adi.split(" ")[1]

        else:
            adres = content.replace(tam_adi, "").strip()[1:]

        return {
            "ad": ad,
            "soyad": soyad,
            "tamAdi": tam_adi,
            "dogumTarihi": dogum_tarihi,
            "anneAdi": anne_adi,
            "babaAdi": baba_adi,
            "adres": adres,
            "isPerson": isPerson
        }