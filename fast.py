import uvicorn
import json
from fastapi import Body, FastAPI, Header,HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
import requests
from dotenv import load_dotenv
import os

# import json

# urlx1 = "https://api.prodia.com/v1/sdx1/generate"
urlProdia = "https://api.prodia.com/v1/sd/generate" #send generate request to prodia
urlTogether = "https://api.together.xyz/v1/images/generations" #send generate request to together ai
urlJob = "https://api.prodia.com/v1/job/" #get generated images

app = FastAPI(docs_url=None,redoc_url=None,openapi_url=None)

origins = [
    # "http://localhost.tiangolo.com",
    # "https://localhost.tiangolo.com",
    "http://localhost",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:5550",
    "https://vic-k-y.github.io",
    "http://vic-k-y.github.io/",
    "https://vic-k-y.github.io/imagto-v2.1/",
    "https://imagto.netlify.app",
    "https://imagto.netlify.app/",
    "https://imagto.tech",
    "https://imagto.tech/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# defines body content
class Request(BaseModel):
    model: str
    prompt: str
    negative_prompt: str | None = None
    style_preset:str
    steps: int
    cfg_scale: int
    seed: int
    upscale: bool
    sampler: str
    width: int
    height: int

class RequestFlux(BaseModel):
    model: str
    prompt: str
    negative_prompt: str | None = 'bad image'
    n:int | None = 1
    steps: int | None = 4
    seed: int | None = -1
    width: int
    height: int
    response_format: str | None = 'url'
    image_url:str | None = 'string'


headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-Prodia-Key": "596e85a1-b3ae-49fb-ae11-cee1c4f78eee"
}

def api_call_send(data):
    dt = json.loads(data.json())

    try:
        response = requests.post(urlProdia, json=dt, headers=headers)
        if response.status_code == 200:
            return response
        if response.status_code == 402:
            raise HTTPException(402,'API access not Enabled or problem with API')
        if response.status_code == 400:
            raise HTTPException(400,'Input parameters Invalid')
    except HTTPException as exc:
        # Rethrow the caught HTTPException
        raise exc

# Flux model request
def api_call_flux(data):
    ds = jsonable_encoder(data) 
    head = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {os.getenv('apiT')}"
    }
    
    if ds['seed'] == -1 :
        ds.pop('seed')

    try:
        response = requests.post(urlTogether, json=ds, headers=head)
        # print('response',response.text)
        if response.status_code == 200:
            res = response.json()
            return res
        if response.status_code == 422:
            raise HTTPException(422,'Bro I caught you. No NSFW images.')
        if response.status_code == 429:
            raise HTTPException(429,'Request trsffic is high. Try later.')
    except HTTPException as exc:
        # print('text',response.text,response.reason)
        raise HTTPException(exc.status_code,exc.detail)


def fromjobId(jobDetail):
    try:
        responseJob = requests.get(urlJob + jobDetail.json()['job'], headers=headers)
        status = responseJob.json()['status']
        # print(status)
        if responseJob.status_code == 402:
            raise HTTPException(402,'API access not Enabled')
        if responseJob.status_code != 200:
            raise HTTPException(500,'Error happened while fetching image.')
            # return {'Error':'Error occurred while fetching image code:"400"'}

        while(status != 'succeeded'):
            responseJob = requests.get(urlJob + jobDetail.json()['job'], headers=headers)
            status = responseJob.json()['status']
            # print( status)
        return responseJob.json()
    except HTTPException as exc:
        # Rethrow the caught HTTPException
        raise exc

@app.get('/')
async def home():
    return 'Hi Bro u r not allowed.'

@app.post('/generate')
async def generate(data: Request):
    first = api_call_send(data)
    f = fromjobId(first)
    return f

@app.post('/flux')
async def flux(data: RequestFlux):
    url =  api_call_flux(data)
    return url

if __name__ == '__main_':
    uvicorn.run("fast:app", host="0.0.0.0", port=8000)
