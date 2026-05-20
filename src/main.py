import os
import uuid
from typing import List
from urllib.parse import quote
from fastapi import FastAPI, Depends, HTTPException, Header, status, UploadFile
from fastapi.responses import FileResponse
from schemas import UserCreate, FileMetadata

import filetype

app = FastAPI(title="File Manager RBAC")

STORAGE_DIR = "storage"
MAX_FILE_SIZE = 2 * 1024 * 1024 
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png"]

os.makedirs(STORAGE_DIR, exist_ok=True)

users_db = {
    "alice": {"username": "alice", "role": "user"},
    "bob": {"username": "bob", "role": "user"},
    "admin": {"username": "admin", "role": "admin"}
}

files_db = [
    {"id": 1, "name": "report_alice.pdf", "size": 1024, "owner": "alice", "path": "storage/mock1.bin"},
    {"id": 2, "name": "secret_bob.docx", "size": 2048, "owner": "bob", "path": "storage/mock2.bin"},
    {"id": 3, "name": "admin_config.yaml", "size": 512, "owner": "admin", "path": "storage/mock3.bin"},
]

file_id_counter = 4


def get_current_user(x_user: str = Header(...)):
    user = users_db.get(x_user.lower())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found"
        )
    return user


def check_file_permissions(file_id: int, current_user: dict = Depends(get_current_user)):
    file = next((f for f in files_db if f["id"] == file_id), None)
    
    if not file:
        raise HTTPException(status_code=404, detail="Not Found")
    
    if current_user["role"] == "admin" or file["owner"] == current_user["username"]:
        return file
    
    raise HTTPException(status_code=404, detail="Not Found")


# ==================== ЭНДПОИНТЫ (УРОК 9) ====================

@app.post("/files/upload", response_model=FileMetadata, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile, 
    current_user: dict = Depends(get_current_user)
):
    global file_id_counter
    
    # Проверяем Magic Bytes (fake.jpg)
    head = await file.read(2048)
    kind = filetype.guess(head)
    
    if kind is None or kind.mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Only JPEG and PNG images are allowed (invalid file signature)."
        )
    
    await file.seek(0)
    
    file_uuid = str(uuid.uuid4())
    extension = kind.extension 
    physical_filename = f"{file_uuid}.{extension}"
    file_path = os.path.join(STORAGE_DIR, physical_filename)
    
    # Читаем чанками (защита от DoS)
    total_bytes_written = 0
    chunk_size = 64 * 1024
    
    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                
                total_bytes_written += len(chunk)
                if total_bytes_written > MAX_FILE_SIZE:
                    buffer.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File is too large. Max allowed size is {MAX_FILE_SIZE // (1024*1024)} MB."
                    )
                
                buffer.write(chunk)
    except Exception as e:
        if os.path.exists(file_path) and total_bytes_written > MAX_FILE_SIZE:
            os.remove(file_path)
        raise e

    new_file_record = {
        "id": file_id_counter,
        "name": file.filename,
        "size": total_bytes_written,
        "owner": current_user["username"],
        "path": file_path
    }
    
    files_db.append(new_file_record)
    file_id_counter += 1
    
    return new_file_record


@app.get("/files/{file_id}/download")
async def download_file(
    file_record: dict = Depends(check_file_permissions)
):
    file_path = file_record["path"]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Physical file not found on disk")
    
    encoded_filename = quote(file_record["name"])
    
    headers = {
        "Content-Disposition": f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    }
    
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        headers=headers
    )


# ==================== ЭНДПОИНТЫ ИЗ УРОКА 8 ====================

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
    if os.path.exists(file["path"]) and "mock" not in file["path"]:
        os.remove(file["path"])
    return {"message": "Success"}