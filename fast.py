import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from typing import Optional, Annotated
import httpx
from dotenv import load_dotenv
import os



load_dotenv()

urlProdia = "https://api.prodia.com/v1/sd/generate"
urlTogether = "https://api.together.xyz/v1/images/generations"
urlJob = "https://api.prodia.com/v1/job/"

PRODIA_KEY = os.getenv("PRODIA_API_KEY")
TOGETHER_KEY = os.getenv("TOGETHER_API_KEY")

app = FastAPI(docs_url=None,redoc_url=None,openapi_url=None)

origins = [
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



async def api_call_send(data: dict):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-Prodia-Key": PRODIA_KEY
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(urlProdia, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()
        
    if response.status_code == 402:
            raise HTTPException(402,'API access not Enabled or problem with API')
        
    raise HTTPException(
        status_code=response.status_code,
        detail="Prodia image generation failed."
    )

# Flux model request
async def api_call_flux(data: dict):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {TOGETHER_KEY}"
    }

    if data.get("seed") == -1:
        data.pop("seed")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(urlTogether, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()

    if response.status_code == 422:
        raise HTTPException(422, "NSFW content detected.")

    if response.status_code == 429:
        raise HTTPException(429, "Too many requests. Try later.")

    raise HTTPException(
        status_code=response.status_code,
        detail="Flux image generation failed."
    )


async def fromjobId(job_id: str):
    headers = {
        "accept": "application/json",
        "X-Prodia-Key": PRODIA_KEY
    }

    max_attempts = 20
    attempt = 0

    async with httpx.AsyncClient(timeout=30) as client:
        while attempt < max_attempts:
            await asyncio.sleep(2)

            response = await client.get(urlJob + job_id, headers=headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail="Error fetching job status."
                )

            data = response.json()
            status = data.get("status")

            if status == "succeeded":
                return data

            attempt += 1

    raise HTTPException(
        status_code=504,
        detail="Image generation timeout."
    )




@app.get("/")
async def home():
    return {"message": "API running successfully 🚀"}

@app.post("/generate")
async def generate(data: Request):
    payload = data.model_dump()
    job_response = await api_call_send(payload)
    job_id = job_response.get("job")

    if not job_id:
        raise HTTPException(500, "Job ID not returned.")

    return await fromjobId(job_id)


@app.post("/flux")
async def flux(data: RequestFlux):
    return await api_call_flux(jsonable_encoder(data))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
