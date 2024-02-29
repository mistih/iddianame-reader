from app.sahis.musteki import Musteki
from app.sahis.magdur import Magdur

import hashlib

# Davacı genelde şikayete tabi olmayan suçlarda olur.
# Şikayete tabi suçlarda davacı olmaz. (K.H.) Olmaz.

class Supheli:
    """
    Sanık sınıfı
    Bir sanık nesnesi oluşturulurken aşağıdaki bilgileri içermelidir:
        ad: Şüphelinin adı
        soyad: Şüphelinin soyadı
        dogum_tarihi: Şüphelinin doğum tarihi
        dogum_yeri: Şüphelinin doğum yeri
        musteki: Şüphelinin hangi müşteki ile ilişkili olduğu
        magdur: Şüphelinin hangi mağdur ile ilişkili olduğu
        cinsiyet: Şüphelinin cinsiyeti
        medeni_durum: Şüphelinin medeni durumu
        egitim_durumu: Şüphelinin eğitim durumu
        meslek: Şüphelinin mesleği
        adres: Şüphelinin adresi
        tc_kimlik_no: Şüphelinin TC kimlik numarası
        anne_adi: Şüphelinin annesinin adı
        baba_adi: Şüphelinin babasının adı
    """
    def __init__(
        self, ad: str, soyad: str, dogum_tarihi: int, musteki: Musteki, magdur: Magdur, dogum_yeri: str = None, 
        cinsiyet: int = None, medeni_durum: int = None, egitim_durumu: str = None, meslek: str = None,
        adres: str = None, tc_kimlik_no: int = None, anne_adi: str = None, baba_adi: str = None
    ):
        self.ad = ad
        self.soyad = soyad
        self.dogum_tarihi = dogum_tarihi
        self.mustekiler = [musteki]
        self.magdurlar = [magdur]
        self.dogum_yeri = dogum_yeri
        self.cinsiyet = cinsiyet
        self.medeni_durum = medeni_durum
        self.egitim_durumu = egitim_durumu
        self.meslek = meslek
        self.adres = adres
        self.tc_kimlik_no = tc_kimlik_no
        self.anne_adi = anne_adi
        self.baba_adi = baba_adi
        self.id = self.hash()

    def hash(self):
        m = hashlib.sha256()
        string = (f"{self.ad}{self.soyad}{self.anne_adi}{self.baba_adi}{self.dogum_tarihi}{self.dogum_yeri}")
        m.update(string.encode('utf-8'))
        return m.hexdigest()
    
    def suc_hash(self, suc_tarihi, sevk_maddesi):
        return hash(suc_tarihi, sevk_maddesi)
    
    def musteki_ekle(self, musteki: Musteki):
        if musteki not in self.mustekiler:
            self.mustekiler.append(musteki)
        else:
            raise ValueError("Bu müşteki zaten ekli.")

    def magdur_ekle(self, magdur: Magdur):
        if magdur not in self.magdurlar:
            self.magdurlar.append(magdur)
        else:
            raise ValueError("Bu mağdur zaten ekli.")
    
    def musteki_sil(self, musteki: Musteki):
        if musteki in self.mustekiler:
            self.mustekiler.remove(musteki)
        else:
            raise ValueError("Bu müşteki zaten ekli değil.")

    def magdur_sil(self, magdur: Magdur):
        if magdur in self.magdurlar:
            self.magdurlar.remove(magdur)
        else:
            raise ValueError("Bu mağdur zaten ekli değil.")

    def musteki_guncelle(self, musteki: Musteki):
        if musteki in self.mustekiler:
            self.mustekiler[self.mustekiler.index(musteki)] = musteki
        else:
            raise ValueError("Bu müşteki ekli değil.")

    def magdur_guncelle(self, magdur: Magdur):
        if magdur in self.magdurlar:
            self.magdurlar[self.magdurlar.index(magdur)] = magdur
        else:
            raise ValueError("Bu mağdur ekli değil.")