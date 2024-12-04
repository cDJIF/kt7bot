import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis

app = FastAPI()
db = redis.Redis(host='localhost', port=6379, db=0)


class User(BaseModel):
    user_id: int
    username: str
    full_name: str


@app.post("/create")
async def create(user: User):
    """Создать пользователя"""
    if db.exists(f"user:{user.user_id}"):
        raise HTTPException(status_code=400, detail="User already exists")
    db.hset(f"user:{user.user_id}", mapping={"username": user.username, "full_name": user.full_name})
    return {"status": "User created successfully"}


@app.put("/update_user/{user_id}")
async def update_user(user_id: int, username: str = None, full_name: str = None):
    redis_key = f"user:{user_id}"
    
    if not db.exists(redis_key):
        raise HTTPException(status_code=404, detail="User does not exist")

    if username:
        db.hset(redis_key, "username", username)
    if full_name:
        db.hset(redis_key, "full_name", full_name)
    return {f"{user_id}: {username} , Updated full_name for user {user_id}: {full_name}"}



@app.delete("/delete_user/{user_id}")
async def delete_user(user_id: int):
    """Удалить пользователя"""
    redis_key = f"user:{user_id}"
    if not db.exists(redis_key):
        raise HTTPException(status_code=404, detail="User does not exist")

    db.delete(redis_key)
    return {"status": "User deleted successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
