import json,re,subprocess,tempfile
from pathlib import Path
from app.worker import celery_app
from app.db import SessionLocal
from app.models import Case,Finding,AuditLog
USERNAME_RE=re.compile(r"^[A-Za-z0-9_.]{1,30}$")
@celery_app.task(name="isip.username_check")
def run_username_check(case_id:int,username:str):
    if not USERNAME_RE.fullmatch(username): raise ValueError("Invalid username")
    db=SessionLocal()
    try:
        if not db.get(Case,case_id): raise ValueError("Case not found")
        matches=[]
        with tempfile.TemporaryDirectory(prefix="isip-") as tmp:
            output=Path(tmp)/"sherlock.txt"
            try:
                proc=subprocess.run(["sherlock",username,"--print-found","--timeout","10","--output",str(output)],capture_output=True,text=True,timeout=180,check=False)
                if output.exists(): matches=[x.strip() for x in output.read_text(errors="replace").splitlines() if x.strip().startswith("[+]")]
                else: matches=[x.strip() for x in proc.stdout.splitlines() if x.strip().startswith("[+]")]
            except (FileNotFoundError,subprocess.TimeoutExpired): matches=["Sherlock unavailable or timed out."]
        db.add(Finding(case_id=case_id,category="username",title=f"Public username search: {username}",detail=json.dumps({"matches":matches[:100],"interpretation":"Unverified presence leads only; no common-ownership inference."}),source="Sherlock",confidence="unverified"))
        db.add(AuditLog(actor="worker",action="username_check_completed",object_type="case",object_id=str(case_id),detail=username))
        db.commit()
        return {"case_id":case_id,"match_lines":len(matches)}
    finally: db.close()
