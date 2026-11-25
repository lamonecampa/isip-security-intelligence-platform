import os
from pathlib import Path
APP_SECRET_KEY=os.getenv("APP_SECRET_KEY","")
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","admin")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./data/isip.db")
EVIDENCE_DIR=Path(os.getenv("EVIDENCE_DIR","./data/evidence"))
MAX_UPLOAD_MB=int(os.getenv("MAX_UPLOAD_MB","15"))
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
URLSCAN_API_KEY=os.getenv("URLSCAN_API_KEY","")
URLSCAN_VISIBILITY=os.getenv("URLSCAN_VISIBILITY","private")
ENABLE_URLSCAN=os.getenv("ENABLE_URLSCAN","false").lower()=="true"
