from fastapi import FastAPI,HTTPException
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
import openai
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import uuid
import json
import os
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class prompt(BaseModel) : 
    message : str
    uuid : str

openai.api_key = os.environ['openai_api_key']

def get_session(uuid):
    if r.get(uuid) is None:
        print(uuid)
        print(r.get(uuid))
        raise HTTPException(status_code=404, detail="session not found")
def create_session(uuid):
    message = []
    r.set(uuid, json.dumps(message))
def get_message(uuid):
    message = r.get(uuid)
    message_list = json.loads(message)
    return message_list

def add_message(uuid,role,prompt):
    messages = get_message(uuid)
    messages.append(
        {"role": role, 
         "content": prompt}
    )
    r.set(uuid, json.dumps(messages))
    return messages

def stream_chat(uuid:str,prompt: str):
    result = ""
    messages = add_message(uuid,'user',prompt)
    for chunk in openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True,
    ):
        content = chunk["choices"][0].get("delta", {}).get("content")
        if content is not None:
            result = result + content
            yield content
    add_message(uuid,'assistant',result)
    
@app.get("/session")
def session():
    client_uuid = uuid.uuid4()
    create_session(str(client_uuid))
    result = {
        "uuid" : str(client_uuid)
    }
    return JSONResponse(content=result)
@app.get("/query")
async def main(uuid:str,message:str):
    get_session(uuid)
    return StreamingResponse(
        stream_chat(
            uuid = uuid,
            prompt= message
        ), media_type="text/event-stream"
    )