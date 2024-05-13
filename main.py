import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import grpc
from pydantic import BaseModel
from contextlib import asynccontextmanager
from database import User, database
import yaml

from futuracommon.protos import healthcheck_pb2, healthcheck_pb2_grpc
from futuracommon.SessionManager import RedisSessionManager

services = {
}

with open('services.yaml') as fp:
    services = yaml.safe_load(fp)

sessionManager = RedisSessionManager(os.environ.get("REDIS_HOST", "session_manager"), 6379, 0)

class UserResponseModel(BaseModel):
    id: int
    folder_name: str
    name: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()
    
    
app = FastAPI(lifespan=lifespan)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/users", response_model=List[UserResponseModel])
async def read_users():
    query = User.__table__.select()
    return await database.fetch_all(query)


@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int):
    query = User.__table__.delete().where(User.id == user_id)
    result = await database.execute(query)
    if result:
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")


@app.get('/statuses')
async def statuses():
    res = []
    for k, v in services.items():
        try:
            with grpc.insecure_channel(v) as channel:
                stub = healthcheck_pb2_grpc.HealthServiceStub(channel)
                status = stub.Check(healthcheck_pb2.HealthRequest())
                res.append({"status": healthcheck_pb2.HealthResponse.ServiceStatus.Name(status.status), "backend": status.current_backend, 'name': k})
        except Exception as e:
            print(e)
            res.append({"status": "UNAVAILABLE", "backend": '', 'name': k})
    
    return res

@app.get('/sessionManager/{client_id}')
async def return_sessions(client_id: str):
    
    session = sessionManager.get_all(client_id=client_id)
    
    return session
    