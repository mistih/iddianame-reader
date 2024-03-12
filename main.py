import json
from app.sahis.supheli import Supheli
from app.sahis.musteki import Musteki
from app.sahis.magdur import Magdur

from app.parser import Parser

import os
import logging
import json

logging.basicConfig(filename="tests.log", level=logging.INFO, encoding="utf-8", filemode="w")

parser = Parser("tests/37.udf")
open("result.json", "w", encoding="utf-8").write(json.dumps(parser.anahtarlar, indent=4, ensure_ascii=False))
multi_keys = parser.clean_anahtarlar()
open("result_parsed.json", "w", encoding="utf-8").write(json.dumps(parser.anahtarlar, indent=4, ensure_ascii=False))
anahtarlar = parser.anahtarlar

if multi_keys["mustekiler"]:
    mustekiler = []
    for musteki in anahtarlar["MÜŞTEKİLER"]:
        parser.sahis(musteki)
else:
    parser.sahis(anahtarlar["MÜŞTEKİ"][0])
        


    