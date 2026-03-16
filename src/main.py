from fastapi import FastAPI
from schemas import UserCreate

app = FastAPI(title="Corporate File Manager — Регистрация")

@app.post("/registration")
async def register_user(user: UserCreate):
    return {"msg": "User created", "user": user.username}