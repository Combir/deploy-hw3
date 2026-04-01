import os
import bleach
from typing import Any, List
from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .schemas import UserCreate

app = FastAPI(title="Corporate File Manager - Task 6")

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

templates_path = os.path.join(project_root, "templates")
if not os.path.exists(templates_path):
    templates_path = os.path.join(current_dir, "templates")

templates = Jinja2Templates(directory=templates_path)

comments_db: List[str] = []

@app.middleware("http")
async def add_security_headers(request: Request, call_next: Any) -> Any:
    response: Response = await call_next(request)
    
    if "/unsafe" in request.url.path:
        return response
        
    policy = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "object-src 'none';"
    )
    response.headers["Content-Security-Policy"] = policy
    return response

@app.post("/registration")
async def register_user(user: UserCreate):
    return {"msg": "User created", "user": user.username}

@app.get("/comments", response_class=HTMLResponse)
async def safe_get(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="comments.html", 
        context={"comments": comments_db, "title": "SAFE"}
    )

@app.post("/comments", response_class=HTMLResponse)
async def safe_post(request: Request, comment: str = Form(...)):
    if comment and comment.strip():
        safe_comment = bleach.clean(
            comment,
            tags=["b", "i", "u", "strong", "em"],
            strip=True
        )
        comments_db.append(safe_comment)
    return templates.TemplateResponse(
        request=request,
        name="comments.html", 
        context={"comments": comments_db, "title": "SAFE"}
    )

@app.get("/unsafe", response_class=HTMLResponse)
async def unsafe_get(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="comments.html",
        context={"comments": comments_db, "title": "UNSAFE"}
    )

@app.post("/unsafe", response_class=HTMLResponse)
async def unsafe_post(request: Request, comment: str = Form(...)):
    if comment and comment.strip():
        comments_db.append(comment)
    return templates.TemplateResponse(
        request=request,
        name="comments.html", 
        context={"comments": comments_db, "title": "UNSAFE"}
    )