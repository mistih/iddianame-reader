import hashlib
from fastapi import FastAPI, HTTPException, Request, Response, APIRouter, File, UploadFile

from app.parser import Parser
from app.sahis.magdur import Magdur
from app.sahis.musteki import Musteki
from app.sahis.supheli import Supheli

import os

router = APIRouter(
    prefix="/udf",
    tags=["udf"],
    responses={404: {"description": "Not found"}},
)
@router.post("/upload")
async def upload_udf(file: UploadFile = File(...)):
    if file.filename.split(".")[-1] != "udf":
        return {"error": "File type not supported."}
    if file.size > 4194304:
        return {"error": "File size too large."}
    if file.content_type != "application/octet-stream":
        return {"error": "File type not supported."}
    
    if not os.path.exists("uploads/udf"):
        os.makedirs("uploads/udf")
    
    # create hash for file if it already exists prevent reupload
    content = file.file.read()
    hash = hashlib.sha256(content).hexdigest()
    if os.path.exists(f"uploads/udf/{hash}"):
         return {"fileId": hash}
        
    with open(f"uploads/udf/{hash}", "wb") as buffer:
        buffer.write(content)
    return {"fileId": hash}

@router.get("/parse")
async def parse_udf(fileId: str):
    parser = Parser(f"uploads/udf/{fileId}")
    multi_keys = parser.clean_anahtarlar()
    anahtarlar = parser.anahtarlar

    if multi_keys["mustekiler"]:
        mustekiler = []
        for musteki in anahtarlar["MÜŞTEKİLER"]:
            parser.sahis(musteki)
    else:
        parser.sahis(anahtarlar["MÜŞTEKİ"][0])

    return parser.anahtarlar

@router.get("/ping")
async def ping():
    return {"ping": "pong"}