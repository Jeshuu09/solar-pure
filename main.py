from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from pwdlib import PasswordHash
import os

from database import engine, Base, SessionLocal
import models

load_dotenv()
password_hash = PasswordHash.recommended()
app = FastAPI(title="Solar Pure", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "change-this-secret"))
Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.post("/submit", response_class=HTMLResponse)
async def submit(request: Request, name: str = Form(...), phone: str = Form(...), email: str = Form(""), place: str = Form(...), purpose: str = Form(...), users: str = Form(...), message: str = Form("")):
    db: Session = SessionLocal()
    try:
        new_request = models.InstallationRequest(name=name.strip(), phone=phone.strip(), email=email.strip(), place=place.strip(), purpose=purpose.strip(), users=users.strip(), message=message.strip(), status="Pending")
        db.add(new_request)
        db.commit()
    finally:
        db.close()
    return HTMLResponse(f'''<!DOCTYPE html><html><head><title>Solar Pure</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{font-family:Arial;background:#eefbfe;min-height:100vh;display:grid;place-items:center;margin:0}}.card{{background:#fff;padding:45px;border-radius:20px;text-align:center;box-shadow:0 18px 45px rgba(5,72,105,.14);max-width:520px}}h1{{color:#063970}}p{{color:#60758a}}a{{display:inline-block;margin-top:15px;background:#063970;color:#fff;padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:700}}</style></head><body><div class="card"><h1>✓ Request Submitted</h1><p>Thank you, {name}. Your Solar Pure installation request has been received.</p><a href="/">Back to Solar Pure</a></div></body></html>''')

@app.get("/admin", include_in_schema=False)
async def admin_redirect():
    return RedirectResponse(url="/admin/login", status_code=303)

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin_login.html", context={})

@app.post("/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if username == admin_username and admin_password_hash and password_hash.verify(password, admin_password_hash):
        request.session["admin_logged_in"] = True
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse('<h2 style="font-family:Arial;color:#c62828;text-align:center;margin-top:50px">Invalid username or password</h2><p style="text-align:center"><a href="/admin/login">Try again</a></p>', status_code=401)

@app.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin/login", status_code=303)
    db: Session = SessionLocal()
    try:
        rows = db.query(models.InstallationRequest).order_by(models.InstallationRequest.id.desc()).all()
    finally:
        db.close()
    return templates.TemplateResponse(request=request, name="admin_dashboard.html", context={"rows": rows})

@app.get("/approve/{id}")
async def approve(request: Request, id: int):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin/login", status_code=303)
    db: Session = SessionLocal()
    try:
        row = db.query(models.InstallationRequest).filter(models.InstallationRequest.id == id).first()
        if row:
            row.status = "Approved"
            db.commit()
    finally:
        db.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/delete/{id}")
async def delete(request: Request, id: int):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin/login", status_code=303)
    db: Session = SessionLocal()
    try:
        row = db.query(models.InstallationRequest).filter(models.InstallationRequest.id == id).first()
        if row:
            db.delete(row)
            db.commit()
    finally:
        db.close()
    return RedirectResponse(url="/dashboard", status_code=303)
