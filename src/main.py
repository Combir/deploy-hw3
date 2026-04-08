from fastapi import FastAPI, Depends, HTTPException, Header, status
from typing import List
from schemas import UserCreate, FileMetadata

app = FastAPI(title="File Manager RBAC")

users_db = {
    "alice": {"username": "alice", "role": "user"},
    "bob": {"username": "bob", "role": "user"},
    "admin": {"username": "admin", "role": "admin"}
}

files_db = [
    {"id": 1, "name": "report_alice.pdf", "size": 1024, "owner": "alice"},
    {"id": 2, "name": "secret_bob.docx", "size": 2048, "owner": "bob"},
    {"id": 3, "name": "admin_config.yaml", "size": 512, "owner": "admin"},
]

def get_current_user(x_user: str = Header(...)):
    user = users_db.get(x_user.lower())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found"
        )
    return user

def check_file_permissions(file_id: int, current_user: dict = Depends(get_current_user)):
    # Поиск файла в БД
    file = next((f for f in files_db if f["id"] == file_id), None)
    
    if not file:
        raise HTTPException(status_code=404, detail="Not Found")
    
    if current_user["role"] == "admin" or file["owner"] == current_user["username"]:
        return file
    
    # Если зашел чужой юзер, возвращаем 404 вместо 403.
    raise HTTPException(status_code=404, detail="Not Found")

@app.get("/files/my", response_model=List[FileMetadata])
async def get_my_files(current_user: dict = Depends(get_current_user)):
    """Возвращает список файлов только текущего пользователя"""
    return [f for f in files_db if f["owner"] == current_user["username"]]

@app.get("/files/all", response_model=List[FileMetadata])
async def get_all_files(current_user: dict = Depends(get_current_user)):
    """Доступно только админу — возвращает все файлы"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return files_db

@app.get("/files/{file_id}", response_model=FileMetadata)
async def get_file(file: dict = Depends(check_file_permissions)):
    """Получение метаданных файла (проверка прав через Dependency)"""
    return file

@app.delete("/files/{file_id}")
async def delete_file(file: dict = Depends(check_file_permissions)):
    """Удаление файла (проверка прав через ту же Dependency)"""
    files_db.remove(file)
    return {"message": "Success"}