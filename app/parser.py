
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
        if path != "default":
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
            content = content.replace("SORUŞTURMA EVRAKI", " ")
            content = content.replace("Soruşturma Evrakı", " ")
            content = content.replace("soruşturma evrakı", "")
            first_part = content

            variatons = ["İNCELENDİ", "İncelendi", "incelendi"]
            for variation in variatons:
                if variation in content:
                    first_part = content.split(variation)[0]
                    break
            lastAnahtar = None
            lastFollowKey = None
            lastVariation = None
            lastSupheli = None

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
                    try:
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

                            sanik_keys = [
                                "ŞÜPHELİ", "ŞÜPHELİLER", "S.S.ÇOCUK", 
                                "S.S.ÇOCUKLAR", "SUÇA SÜRÜKLENEN ÇOCUKLAR", "SUÇA SÜRÜKLENEN ÇOCUK",
                                "SSÇ", "SSÇLER", "SSÇ'LER"
                            ]

                            sahis_keys = [
                                "MÜŞTEKİ", "MÜŞTEKİLER", "DAVACI", "DAVACILAR", "MAĞDUR", "MAĞDURLAR"
                            ]

                            if lastFollowKey in sanik_keys:
                                try:
                                    lastSupheli = data
                                    sahis = self.sahis(data)
                                    data = {"id": self.get_hash(lastSupheli), "data": data, "ad": sahis["ad"], "soyad": sahis["soyad"], "tamAdi":sahis["tamAdi"], "dogumTarihi": sahis["dogumTarihi"], "anneAdi": sahis["anneAdi"], "babaAdi": sahis["babaAdi"], "isPerson":sahis["isPerson"]}
                                except Exception as e:
                                    print("Hata:", str(e))
                                    pass
                            if lastFollowKey in sahis_keys:
                                try:
                                    sahis = self.sahis(data)
                                    data = {"id": self.get_hash(data), "data": data, "ad": sahis["ad"], "soyad": sahis["soyad"], "tamAdi":sahis["tamAdi"], "dogumTarihi": sahis["dogumTarihi"], "anneAdi": sahis["anneAdi"], "babaAdi": sahis["babaAdi"], "isPerson":sahis["isPerson"]}
                                except Exception as e:
                                    print("Hata:", str(e))
                                    pass
                            if lastFollowKey == "SEVK MADDESİ" or lastFollowKey == "SEVK MADDELERİ":
                                maddeler = self.madde_bul(data)
                                if len(maddeler) > 0:
                                    data = maddeler

                            if "TARİH" in lastFollowKey:
                                tarih = self.tarih_bul([data])
                                if tarih["datetime"] is not None:
                                    rawData = data
                                    tarih["data"] = rawData
                                    data = tarih

                            if lastFollowKey in sequential_keys:
                                self.anahtarlar[lastFollowKey][self.get_hash(lastSupheli)] = data
                            else:
                                self.anahtarlar[lastFollowKey].append(data)
                        continue
                    except:
                        continue

                # fix
                for anahtar in self.anahtarlar:
                    # "in" expression replaced with re.search to match whole words
                    if re.search(r'\b' + re.escape(anahtar) + r'\b', line):
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

                                sanik_keys = [
                                    "ŞÜPHELİ", "ŞÜPHELİLER", "S.S.ÇOCUK", 
                                    "S.S.ÇOCUKLAR", "SUÇA SÜRÜKLENEN ÇOCUKLAR", "SUÇA SÜRÜKLENEN ÇOCUK",
                                    "SSÇ", "SSÇLER", "SSÇ'LER"
                                ]

                                sahis_keys = [
                                    "MÜŞTEKİ", "MÜŞTEKİLER", "DAVACI", "DAVACILAR", "MAĞDUR", "MAĞDURLAR"
                                ]

                                if lastAnahtar in sanik_keys:
                                    try:
                                        lastAnahtar = "ŞÜPHELİLER"
                                        lastSupheli = data
                                        sahis = self.sahis(data)
                                        data = {"id": self.get_hash(lastSupheli), "data": data, "ad": sahis["ad"], "soyad": sahis["soyad"], "tamAdi":sahis["tamAdi"], "dogumTarihi": sahis["dogumTarihi"], "anneAdi": sahis["anneAdi"], "babaAdi": sahis["babaAdi"], "isPerson":sahis["isPerson"]}
                                    except Exception as e:
                                        print("Hata:", str(e))
                                        pass
                                if lastAnahtar in sahis_keys:
                                    try:
                                        lastAnahtar = "MÜŞTEKİLER"
                                        sahis = self.sahis(data)
                                        data = {"id": self.get_hash(data), "data": data, "ad": sahis["ad"], "soyad": sahis["soyad"], "tamAdi":sahis["tamAdi"], "dogumTarihi": sahis["dogumTarihi"], "anneAdi": sahis["anneAdi"], "babaAdi": sahis["babaAdi"], "isPerson":sahis["isPerson"]}
                                    except Exception as e:
                                        print("Hata:", str(e))
                                        pass
                                if lastAnahtar == "SEVK MADDESİ" or lastAnahtar == "SEVK MADDELERİ":
                                    maddeler = self.madde_bul(data)
                                    if len(maddeler) > 0:
                                        data = maddeler

                                if "TARİH" in lastAnahtar :
                                    tarih = self.tarih_bul([data])
                                    if tarih["datetime"] is not None:
                                        rawData = data
                                        tarih["data"] = rawData
                                        data = tarih
                                
                                if anahtar in sequential_keys:
                                    try:
                                        self.anahtarlar[anahtar][self.get_hash(lastSupheli)] = data
                                    except:
                                        continue
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

                        sanik_keys = [
                            "ŞÜPHELİ", "ŞÜPHELİLER", "S.S.ÇOCUK", 
                            "S.S.ÇOCUKLAR", "SUÇA SÜRÜKLENEN ÇOCUKLAR", "SUÇA SÜRÜKLENEN ÇOCUK",
                            "SSÇ", "SSÇLER", "SSÇ'LER"
                        ]

                        sahis_keys = [
                            "MÜŞTEKİ", "MÜŞTEKİLER", "DAVACI", "DAVACILAR", "MAĞDUR", "MAĞDURLAR"
                        ]

                        if lastAnahtar in sanik_keys:
                            try:
                                lastAnahtar = "ŞÜPHELİLER"
                                lastSupheli = data
                                sahis = self.sahis(data)
                                data = {"id": self.get_hash(lastSupheli), "data": data, "ad": sahis["ad"], "soyad": sahis["soyad"], "tamAdi":sahis["tamAdi"], "dogumTarihi": sahis["dogumTarihi"], "anneAdi": sahis["anneAdi"], "babaAdi": sahis["babaAdi"], "isPerson":sahis["isPerson"]}
                            except Exception as e:
                                print("Hata:", str(e))
                                pass
                        if lastAnahtar in sahis_keys:
                            try:
                                lastAnahtar = "MÜŞTEKİLER"
                                sahis = self.sahis(data)
                                data = {"id": self.get_hash(data), "data": data, "ad": sahis["ad"], "soyad": sahis["soyad"], "tamAdi":sahis["tamAdi"], "dogumTarihi": sahis["dogumTarihi"], "anneAdi": sahis["anneAdi"], "babaAdi": sahis["babaAdi"], "isPerson":sahis["isPerson"]}
                            except Exception as e:
                                print("Hata:", str(e))
                                pass
                        if lastAnahtar == "SEVK MADDESİ" or lastAnahtar == "SEVK MADDELERİ":
                            maddeler = self.madde_bul(data)
                            if len(maddeler) > 0:
                                data = maddeler

                        if "TARİH" in lastAnahtar:
                            tarih = self.tarih_bul([data])
                            if tarih["datetime"] is not None:
                                rawData = data
                                tarih["data"] = rawData
                                data = tarih

                        if lastAnahtar in sequential_keys:
                            self.anahtarlar[lastAnahtar][self.get_hash(lastSupheli)] = data
                        else:
                            self.anahtarlar[lastAnahtar].append(data)    
            return content
        except:
            raise ValueError("Iddianame içeriğini okurken bir hata oluştu. Lütfen dosyanın içeriğini kontrol edin.")

    def madde_bul(self, content: str):
        content = self.metin_arindir(content)
        madde_regex = r"\d{2,3}(?:[\/\-]\d{1,2}(?:\.[a-zA-Z])?)?(?:\-[a-zA-Z])?|\d{2,3}$"
        maddeler = re.findall(madde_regex, content)
        return maddeler

    def metin_arindir(self, text):
        # Tarih desenlerini tanımla
        tarih_desenleri = [
            r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b",  # gg.aa.yyyy veya gg-aa-yyyy veya yyyy.aa.gg
            r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b",  # yyyy.aa.gg veya yyyy-aa-gg veya gg.aa.yyyy
            r"\b\d{1,2}[./-]\d{4}[./-]\d{1,2}\b",   # gg.yyyy.aa veya gg-yyyy-aa veya aa.yyyy.gg
            r"\d{4}",
        ]

        once_sil = [
            "TL",
            "USD",
            "EURO",
            "TURK LIRASI",
            "TÜRK LİRASI",
            "YTL",
            "YENİ TÜRK LİRASI",
            "YENİ TURK LIRASI",
        ]

        for param in once_sil:
            param_location = text.find(param)
            # parametreden bir önceki kelimeyi bul
            if param_location != -1:
                onceki_kelime = text[:param_location].split(" ")[-2]
                text = text.replace(onceki_kelime, "")

        # Her deseni arayıp bul ve tarihleri sil
        for desen in tarih_desenleri:
            text = re.sub(desen, "", text)

        return text

    def convert_date_to_unix_timestamp(self, year, month, day):
        given_date = datetime.datetime(year, month, day)
        
        start_date = datetime.datetime(1970, 1, 1)
        time_difference = given_date - start_date
        
        unix_timestamp = time_difference.total_seconds()
        
        return int(unix_timestamp)

    def tarih_bul(self, content: list):
        formats = {
            "dd.mm.yyyy": {"pattern": r'\d{2}.\d{2}.\d{4}', "min_year": None, "max_year": None, "format_type": "dd.mm.yyyy"},
            "dd/mm/yyyy": {"pattern": r'\d{2}\/\d{2}\/\d{4}', "min_year": None, "max_year": None, "format_type": "dd/mm/yyyy"},
            "dd-mm-yyyy": {"pattern": r'\d{2}-\d{2}-\d{4}', "min_year": None, "max_year": None, "format_type": "dd-mm-yyyy"},
            "yyyy.mm.dd": {"pattern": r'\d{4}.\d{2}.\d{2}', "min_year": None, "max_year": None, "format_type": "yyyy.mm.dd"},
            "yyyy/mm/dd": {"pattern": r'\d{4}\/\d{2}\/\d{2}', "min_year": None, "max_year": None, "format_type": "yyyy/mm/dd"},
            "yyyy-mm-dd": {"pattern": r'\d{4}-/d{2}-/d{2}', "min_year": None, "max_year": None, "format_type": "yyyy-mm-dd"},
            "yyyy": {"pattern": r'\d{4}', "min_year": 1923, "max_year": datetime.datetime.now().year, "format_type": "yyyy"},
            "mm-yyyy": {"pattern": r'\d{2}-\d{4}', "min_year": 1923, "max_year": datetime.datetime.now().year, "format_type": "mm-yyyy"},
            "mm.yyyy": {"pattern": r'\d{2}.\d{4}', "min_year": 1923, "max_year": datetime.datetime.now().year, "format_type": "mm.yyyy"},
            "mm/yyyy": {"pattern": r'\d{2}/\d{4}', "min_year": 1923, "max_year": datetime.datetime.now().year, "format_type": "mm/yyyy"},
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

                    if len(date[0]) == 2 and len(date[1]) == 4 and date[2] == '':
                        isEdited = True
                        date = ['1', date[0], date[1]]

                    if len(date) != 3 and len(date[0]) == 4:
                        isEdited = True
                        date = ['1', '1', date[0]]
                    
                    if len(date) == 2:
                        date = ['1', date[0], date[1]]
                        isEdited = True

                    current_year = datetime.datetime.now().year
                    day = int(date[0])
                    month = int(date[1])
                    year = int(date[2])

                    if day < 1 or day > 31:
                        day = 1
                    
                    if month < 1 or month > 12:
                        month = 1

                    if year < 1923 or year > current_year:
                        if len(str(year)) > 4:
                            year = str(year)[:4]
                            year = int(year)
                        else:
                            year = 2038

                    if min_year is not None and max_year is not None:
                        if year >= min_year and year <= max_year:
                            date = datetime.datetime(year, month, day)
                            try:
                                int_timestamp_11 = self.convert_date_to_unix_timestamp(year, month, day)
                            except:
                                int_timestamp_11 = None
                            return {"datetime": date, "timestamp": int_timestamp_11, "format": formats[format]["format_type"], "isEdited": isEdited}
                        else:
                            return {"datetime": None, "timestamp": None, "format":  formats[format]["format_type"], "isEdited": isEdited}
                    else:
                        date = datetime.datetime(year, month, day)
                        try:
                            int_timestamp_11 = self.convert_date_to_unix_timestamp(year, month, day)
                        except Exception as e:
                            print(f"[{date}] Timestamp Hatası:", str(e))
                            int_timestamp_11 = None
                        return {"datetime": date, "timestamp": int_timestamp_11, "format":  formats[format]["format_type"], "isEdited": isEdited}
                else:
                    continue

        return {"datetime": None, "timestamp": None, "format": None, "isEdited": False}

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

        anahtarlar = self.anahtarlar.copy()

        if len(self.anahtarlar["MÜŞTEKİ"]) > 0:
            mustekiler = True
            if len(self.anahtarlar["MÜŞTEKİLER"]) == 0:
                anahtarlar["MÜŞTEKİLER"] = (self.anahtarlar["MÜŞTEKİ"])
            else:
                anahtarlar["MÜŞTEKİLER"].append(self.anahtarlar["MÜŞTEKİ"])
            anahtarlar.pop("MÜŞTEKİ")

        if len(self.anahtarlar["ŞÜPHELİ"]) > 0:
            supheliler = True
            if len(self.anahtarlar["ŞÜPHELİLER"]) == 0:
                anahtarlar["ŞÜPHELİLER"] = (self.anahtarlar["ŞÜPHELİ"])
            else:
                anahtarlar["ŞÜPHELİLER"].append(self.anahtarlar["ŞÜPHELİ"])
            anahtarlar.pop("ŞÜPHELİ")
        
        if len(self.anahtarlar["MAĞDUR"]) > 0:
            magdurlar = True
            if len(self.anahtarlar["MAĞDURLAR"]) == 0:
                anahtarlar["MAĞDURLAR"] = (self.anahtarlar["MAĞDUR"])
            else:
                anahtarlar["MAĞDURLAR"].append(self.anahtarlar["MAĞDUR"])
            anahtarlar.pop("MAĞDUR")
        
        if len(self.anahtarlar["DAVACI"]) > 0:
            davacilar = True
            if len(self.anahtarlar["DAVACILAR"]) == 0:
                anahtarlar["DAVACILAR"] = (self.anahtarlar["DAVACI"])
            else:
                anahtarlar["DAVACILAR"].append(self.anahtarlar["DAVACI"])
            anahtarlar.pop("DAVACI")

        if len(self.anahtarlar["MÜŞTEKİLER"]) > 1:
            mustekiler = True
        
        if len(self.anahtarlar["ŞÜPHELİ"]) > 1:
            supheliler = True

        if len(self.anahtarlar["MAĞDUR"]) > 1:
            magdurlar = True
            
        if len(self.anahtarlar["DAVACI"]) > 1:
            davacilar = True

        for anahtar in list(anahtarlar.keys()):
            if anahtarlar[anahtar] == [] or anahtarlar[anahtar] == {} or anahtarlar[anahtar] == "[]" or anahtarlar[anahtar] == "":
                anahtarlar.pop(anahtar)
        
        self.anahtarlar = anahtarlar
        return {"mustekiler": mustekiler, "magdurlar": magdurlar, "supheliler": supheliler, "davacilar": davacilar}

    def create_hash(self, content):
        content_str = str(content)
        hash_value = 0
        for char in content_str:
            hash_value = (hash_value * 31 + ord(char)) % (2**32)
        
        return hash_value

    def get_hash(self, content: str):
        try:
            sahis = self.sahis(content)
            hash = self.create_hash(f"{sahis['tamAdi'], sahis['dogumTarihi']['datetime'], sahis['isPerson']}")
        except:
            hash = 0
        return int(hash)

    def sahis(self, content: str):
        try:
            content = re.sub(r"\b\d+-", "", content)
            content = self.string_temizle(content)
        except:
            pass

        person_keys = ["oğlu", "Oğlu", "OĞLU", "kızı", "Kızı", "KIZI"]
        isPerson = False
        for anahtar in person_keys:
            if anahtar in content:
                isPerson = True
                break
        
        tam_adi = None  
        try:
            tam_adi = content.split(",")[0]
        except:
            pass
        ad = None
        soyad = None
        anne_adi = None
        baba_adi = None
        adres = None
        dogum_tarihi = {"datetime": None, "timestamp": None, "format": None, "isEdited": False}

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
            try:
                adres = content.replace(tam_adi, "").strip()[1:]
            except:
                pass

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