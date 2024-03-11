import json
from app.sahis.supheli import Supheli
from app.sahis.musteki import Musteki
from app.sahis.magdur import Magdur

from app.parser import Parser

import os
import logging

logging.basicConfig(filename="tests.log", level=logging.INFO, encoding="utf-8", filemode="w")

parser = Parser("tests/2.udf")
anahtarlar = parser.anahtarlar
open("result.json", "w", encoding="utf-8").write(json.dumps(anahtarlar, indent=4, ensure_ascii=False))
for musteki in anahtarlar["ŞÜPHELİ"]:
    musteki = parser.musteki(musteki)