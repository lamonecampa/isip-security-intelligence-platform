import hashlib,mimetypes,secrets
from pathlib import Path
from urllib.parse import urlparse
import httpx
from fastapi import FastAPI,Depends,HTTPException,Request,UploadFile,File,Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware
from app.config import APP_SECRET_KEY,EVIDENCE_DIR,MAX_UPLOAD_MB,ENABLE_URLSCAN,URLSCAN_API_KEY,URLSCAN_VISIBILITY
from app.db import Base,engine,get_db
from app.models import Case,Evidence,Finding,AuditLog
from app.schemas import LoginInput,CaseInput
from app.security import require_user,verify_login,validate_startup_config
validate_startup_config(); EVIDENCE_DIR.mkdir(parents=True,exist_ok=True); Base.metadata.create_all(bind=engine)
app=FastAPI(title="ISIP Security Intelligence Platform",version="0.1.0")
app.add_middleware(SessionMiddleware,secret_key=APP_SECRET_KEY,https_only=False,same_site="strict",max_age=3600)
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates=Jinja2Templates(directory="app/templates")
def log(db,actor,action,obj_type,obj_id=None,detail=""):
    db.add(AuditLog(actor=actor,action=action,object_type=obj_type,object_id=str(obj_id) if obj_id is not None else None,detail=detail[:3000])); db.commit()
def serialize(c):
    return {"id":c.id,"title":c.title,"scope":c.scope,"status":c.status,"created_at":c.created_at.isoformat(),"evidence_count":len(c.evidence),"finding_count":len(c.findings)}
def case_or_404(db,cid):
    c=db.get(Case,cid)
    if not c: raise HTTPException(404,"Case not found")
    return c
@app.get("/api/health")
def health(): return {"status":"ok","service":"isip","version":"0.1.0"}
@app.get("/",response_class=HTMLResponse)
def dashboard(request:Request):
    template="dashboard.html" if request.session.get("user") else "login.html"
    return templates.TemplateResponse(template,{"request":request,"username":request.session.get("user","")})
@app.post("/api/login")
def login(payload:LoginInput,request:Request,db:Session=Depends(get_db)):
    if not verify_login(payload.username,payload.password):
        log(db,"anonymous","login_failed","session"); raise HTTPException(401,"Invalid credentials")
    request.session.clear(); request.session["user"]=payload.username; log(db,payload.username,"login","session"); return {"ok":True}
@app.post("/api/logout")
def logout(request:Request,user=Depends(require_user),db:Session=Depends(get_db)):
    log(db,user,"logout","session"); request.session.clear(); return {"ok":True}
@app.get("/api/cases")
def list_cases(user=Depends(require_user),db:Session=Depends(get_db)):
    return [serialize(c) for c in db.scalars(select(Case).order_by(Case.created_at.desc())).all()]
@app.post("/api/cases")
def create_case(payload:CaseInput,user=Depends(require_user),db:Session=Depends(get_db)):
    c=Case(title=payload.title,scope=payload.scope); db.add(c); db.commit(); db.refresh(c); log(db,user,"case_created","case",c.id,payload.title); return serialize(c)
@app.post("/api/cases/{case_id}/evidence")
async def upload_evidence(case_id:int,file:UploadFile=File(...),notes:str=Form(""),user=Depends(require_user),db:Session=Depends(get_db)):
    c=case_or_404(db,case_id)
    if not file.filename or Path(file.filename).name!=file.filename: raise HTTPException(400,"Invalid filename")
    suffix=Path(file.filename).suffix.lower()
    if suffix not in {".png",".jpg",".jpeg",".webp",".pdf",".txt",".csv",".json"}: raise HTTPException(415,"File type not allowed")
    content=await file.read(MAX_UPLOAD_MB*1024*1024+1)
    if len(content)>MAX_UPLOAD_MB*1024*1024: raise HTTPException(413,"File too large")
    digest=hashlib.sha256(content).hexdigest(); stored=secrets.token_hex(20)+suffix; (EVIDENCE_DIR/stored).write_bytes(content)
    e=Evidence(case_id=c.id,original_name=file.filename,stored_name=stored,media_type=mimetypes.guess_type(file.filename)[0] or file.content_type,size_bytes=len(content),sha256=digest,notes=notes[:1000])
    db.add(e); db.commit(); db.refresh(e); log(db,user,"evidence_uploaded","evidence",e.id,f"sha256={digest}; {file.filename}")
    return {"id":e.id,"filename":e.original_name,"size_bytes":e.size_bytes,"sha256":digest,"collected_at":e.collected_at.isoformat()}
@app.post("/api/cases/{case_id}/username-check")
def username_check(case_id:int,username:str=Form(...),user=Depends(require_user),db:Session=Depends(get_db)):
    c=case_or_404(db,case_id)
    if not username or len(username)>30 or not username.replace("_","").replace(".","").isalnum(): raise HTTPException(400,"Invalid username")
    from app.worker_tasks import run_username_check
    task=run_username_check.delay(case_id,username); log(db,user,"username_check_queued","case",c.id,username)
    return {"task_id":task.id,"status":"queued","notice":"Matches are unverified leads, not identity proof."}
def validate_public_url(value):
    p=urlparse(value)
    if p.scheme not in ("http","https") or not p.hostname: raise HTTPException(400,"Valid public HTTP(S) URL required")
    host=p.hostname.lower()
    if host in {"localhost","127.0.0.1","::1"} or host.endswith(".local"): raise HTTPException(400,"Local URLs are not allowed")
@app.post("/api/cases/{case_id}/url-check")
async def url_check(case_id:int,url:str=Form(...),confirmed_external_submission:bool=Form(False),user=Depends(require_user),db:Session=Depends(get_db)):
    c=case_or_404(db,case_id); validate_public_url(url)
    if not ENABLE_URLSCAN or not URLSCAN_API_KEY: raise HTTPException(503,"urlscan integration disabled")
    if not confirmed_external_submission: raise HTTPException(400,"Explicit third-party submission confirmation required")
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post("https://urlscan.io/api/v1/scan/",headers={"API-Key":URLSCAN_API_KEY,"Content-Type":"application/json"},json={"url":url,"visibility":URLSCAN_VISIBILITY})
    if r.status_code>=400: raise HTTPException(502,f"urlscan error: HTTP {r.status_code}")
    data=r.json(); db.add(Finding(case_id=c.id,category="url",title="URL submitted to urlscan.io",detail="Review external scan before conclusions.",source=data.get("result",""),confidence="unverified")); db.commit()
    log(db,user,"url_submitted_external","case",c.id,url)
    return {"scan_id":data.get("uuid"),"result_url":data.get("result"),"visibility":URLSCAN_VISIBILITY}
@app.get("/api/cases/{case_id}/findings")
def findings(case_id:int,user=Depends(require_user),db:Session=Depends(get_db)):
    c=case_or_404(db,case_id); return [{"id":f.id,"category":f.category,"title":f.title,"detail":f.detail,"source":f.source,"confidence":f.confidence} for f in c.findings]
@app.get("/api/cases/{case_id}/report")
def report(case_id:int,user=Depends(require_user),db:Session=Depends(get_db)):
    c=case_or_404(db,case_id)
    return {"case":serialize(c),"evidence":[{"id":e.id,"filename":e.original_name,"sha256":e.sha256,"size_bytes":e.size_bytes,"collected_at":e.collected_at.isoformat()} for e in c.evidence],"findings":[{"id":f.id,"category":f.category,"title":f.title,"detail":f.detail,"source":f.source,"confidence":f.confidence} for f in c.findings],"disclaimer":"Automated findings require human verification."}
