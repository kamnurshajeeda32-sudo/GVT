import os, secrets, hashlib, uuid, smtplib
from email.message import EmailMessage
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from redis import Redis
from .db import session
from .models import User, Token
router = APIRouter(prefix="/auth")
ph = PasswordHasher(time_cost=2, memory_cost=32768, parallelism=1)
def digest(t): return hashlib.sha256(t.encode()).hexdigest()
def now(): return datetime.now(timezone.utc)
def issue(db, user, purpose, minutes):
    raw = secrets.token_urlsafe(32)
    db.add(Token(digest=digest(raw), user_id=user.id, purpose=purpose, expires=now()+timedelta(minutes=minutes)))
    return raw
def consume(db, raw, purpose):
    token = db.scalar(select(Token).where(Token.digest==digest(raw), Token.purpose==purpose, Token.expires>now()).with_for_update())
    if not token: raise HTTPException(400,"Invalid or expired token")
    user = db.get(User, token.user_id)
    db.delete(token)
    return user
def send(email, purpose, token):
    msg=EmailMessage()
    msg["From"]=os.environ["SMTP_FROM"]
    msg["To"]=email
    msg["Subject"]="GRTAlgo account verification" if purpose=="verify" else "GRTAlgo password reset"
    msg.set_content("Open https://grtalgo.com/account and enter this one-time code: "+token)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT","587")), timeout=10) as smtp:
        smtp.starttls()
        smtp.login(os.environ["SMTP_USER"],os.environ["SMTP_PASSWORD"])
        smtp.send_message(msg)
def guard(request: Request):
    if request.method != "GET" and request.headers.get("origin") != os.getenv("APP_ORIGIN","https://grtalgo.com"):
        raise HTTPException(403,"Invalid origin")
    if request.method != "GET":
        r=Redis(host="redis",socket_timeout=2)
        key="auth:"+str(request.client.host)+":"+request.url.path
        with r.pipeline() as p:
            p.incr(key); p.expire(key,60,nx=True); count,_=p.execute()
        if count>20: raise HTTPException(429,"Try again later")
class Email(BaseModel): email: EmailStr
class Login(Email): password: str = Field(min_length=12,max_length=128)
class Register(Login): name: str = Field(min_length=1,max_length=100)
class Code(BaseModel): token: str = Field(min_length=20,max_length=128)
class Reset(Code): password: str = Field(min_length=12,max_length=128)
class Profile(BaseModel): name: str = Field(min_length=1,max_length=100)
def current(request: Request, db=Depends(session)):
    raw=request.cookies.get("__Host-grt","")
    t=db.scalar(select(Token).where(Token.digest==digest(raw),Token.purpose=="session",Token.expires>now()))
    u=db.get(User,t.user_id) if t else None
    if not u or not u.verified: raise HTTPException(401,"Authentication required")
    return u
def public(u): return {"id":u.id,"email":u.email,"name":u.name,"role":u.role}
@router.post("/register",dependencies=[Depends(guard)])
def register(data:Register,db=Depends(session)):
    u=User(id=str(uuid.uuid4()),email=data.email.lower(),name=data.name,password_hash=ph.hash(data.password),role="customer",verified=False)
    db.add(u)
    try:
        db.flush()
        raw=issue(db,u,"verify",60)
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"message":"Check your email if eligible"}
    send(u.email,"verify",raw)
    return {"message":"Check your email if eligible"}
@router.post("/resend",dependencies=[Depends(guard)])
def resend(data:Email,db=Depends(session)):
    u=db.scalar(select(User).where(User.email==data.email.lower(),User.verified==False))
    if u:
        raw=issue(db,u,"verify",60); db.commit(); send(u.email,"verify",raw)
    return {"message":"Check your email if eligible"}
@router.post("/verify",dependencies=[Depends(guard)])
def verify(data:Code,db=Depends(session)):
    u=consume(db,data.token,"verify"); u.verified=True; db.commit()
    return {"message":"Email verified"}
@router.post("/login",dependencies=[Depends(guard)])
def login(data:Login,response:Response,db=Depends(session)):
    u=db.scalar(select(User).where(User.email==data.email.lower()))
    try:
        valid=ph.verify(u.password_hash if u else ph.hash("invalid-account-password"),data.password)
    except VerificationError: valid=False
    if not u or not valid or not u.verified: raise HTTPException(401,"Invalid credentials or unverified account")
    raw=issue(db,u,"session",480); db.commit()
    response.set_cookie("__Host-grt",raw,max_age=28800,secure=True,httponly=True,samesite="strict",path="/")
    return public(u)
@router.post("/logout",dependencies=[Depends(guard)])
def logout(request:Request,response:Response,db=Depends(session)):
    db.execute(delete(Token).where(Token.digest==digest(request.cookies.get("__Host-grt","")),Token.purpose=="session")); db.commit()
    response.delete_cookie("__Host-grt",path="/",secure=True,httponly=True,samesite="strict")
    return {"message":"Logged out"}
@router.post("/forgot",dependencies=[Depends(guard)])
def forgot(data:Email,db=Depends(session)):
    u=db.scalar(select(User).where(User.email==data.email.lower(),User.verified==True))
    if u:
        raw=issue(db,u,"reset",30); db.commit(); send(u.email,"reset",raw)
    return {"message":"Check your email if eligible"}
@router.post("/reset",dependencies=[Depends(guard)])
def reset(data:Reset,db=Depends(session)):
    u=consume(db,data.token,"reset"); u.password_hash=ph.hash(data.password)
    db.flush()
    db.execute(delete(Token).where(Token.user_id==u.id,Token.purpose.in_(["session","reset"]))); db.commit()
    return {"message":"Password changed"}
@router.get("/me")
def me(u=Depends(current)): return public(u)
@router.patch("/me",dependencies=[Depends(guard)])
def profile(data:Profile,u=Depends(current),db=Depends(session)):
    u.name=data.name; db.commit(); return public(u)
@router.get("/admin/check")
def admin(u=Depends(current)):
    if u.role not in ("admin","super_admin"): raise HTTPException(403,"Forbidden")
    return {"authorized":True}
