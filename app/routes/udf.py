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
@router.get("/upload")
async def upload_udf(filepath: str):
    file = open(filepath, "rb")
    file = file.read()
    
    if not os.path.exists("uploads/udf"):
        os.makedirs("uploads/udf")
    
    # create hash for file if it already exists prevent reupload
    content = file
    hash = hashlib.sha256(content).hexdigest()
    if os.path.exists(f"uploads/udf/{hash}"):
         return {"fileId": hash}
        
    with open(f"uploads/udf/{hash}", "wb") as buffer:
        buffer.write(content)
    return {"fileId": hash}

@router.get("/parse")
async def parse_udf(fileId: str):
    try:
        parser = Parser(f"uploads/udf/{fileId}")
        multi_keys = parser.clean_anahtarlar()
        anahtarlar = parser.anahtarlar

        return parser.anahtarlar
    except Exception as e:
        # set status code to 400
        raise HTTPException(status_code=400, detail=str(e))
@router.get("/ping")
async def ping():
    return {"ping": "pong"}