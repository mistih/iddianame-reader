import hashlib

class Magdur:
    def __init__(
        self, ad: str, soyad: str, dogum_tarihi: int, sevk_maddesi: str, suc_tarihi: int, dogum_yeri: str = None, 
        cinsiyet: int = None, medeni_durum: int = None, egitim_durumu: str = None, meslek: str = None,
        adres: str = None, tc_kimlik_no: int = None, anne_adi: str = None, baba_adi: str = None
    ):
        self.ad = ad
        self.soyad = soyad
        self.dogum_tarihi = dogum_tarihi
        self.dogum_yeri = dogum_yeri
        self.cinsiyet = cinsiyet
        self.medeni_durum = medeni_durum
        self.egitim_durumu = egitim_durumu
        self.meslek = meslek
        self.adres = adres
        self.tc_kimlik_no = tc_kimlik_no
        self.anne_adi = anne_adi
        self.baba_adi = baba_adi
        self.sevk_maddesi = sevk_maddesi
        self.suc_tarihi = suc_tarihi
        self.id = self.hash()

    def hash(self):
        m = hashlib.sha256()
        string = (f"{self.ad}{self.soyad}{self.anne_adi}{self.baba_adi}{self.dogum_tarihi}{self.dogum_yeri}")
        m.update(string.encode('utf-8'))
        return m.hexdigest()