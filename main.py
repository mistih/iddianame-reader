import json
from app.sahis.supheli import Supheli
from app.sahis.musteki import Musteki
from app.sahis.magdur import Magdur

from app.parser import Parser

import os
import logging
import json

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from app.routes import udf

app = FastAPI(
    title="UDF Parser",
    description="UDF Parser",
    version="0.0.1",
    docs_url="/",
    redoc_url=None,
    openapi_url="/openapi.json",
)

app.include_router(udf.router)

#allow cors
@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)