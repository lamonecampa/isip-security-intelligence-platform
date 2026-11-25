import secrets
from fastapi import Request,HTTPException
from app.config import APP_SECRET_KEY,ADMIN_USERNAME,ADMIN_PASSWORD
def validate_startup_config():
    if len(APP_SECRET_KEY)<32 or APP_SECRET_KEY.startswith("replace-"):
        raise RuntimeError("Set a unique APP_SECRET_KEY of at least 32 characters.")
    if len(ADMIN_PASSWORD)<14 or ADMIN_PASSWORD.startswith("change-"):
        raise RuntimeError("Set a unique ADMIN_PASSWORD of at least 14 characters.")
def verify_login(username,password):
    return secrets.compare_digest(username,ADMIN_USERNAME) and secrets.compare_digest(password,ADMIN_PASSWORD)
def require_user(request:Request):
    if not request.session.get("user"): raise HTTPException(401,"Authentication required")
    return request.session["user"]
