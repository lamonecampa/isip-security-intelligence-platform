from datetime import datetime,timezone
from sqlalchemy import Column,Integer,String,Text,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
def utcnow(): return datetime.now(timezone.utc)
class Case(Base):
    __tablename__="cases"
    id=Column(Integer,primary_key=True)
    title=Column(String(180),nullable=False)
    scope=Column(Text,nullable=False)
    status=Column(String(30),default="open",nullable=False)
    created_at=Column(DateTime(timezone=True),default=utcnow,nullable=False)
    evidence=relationship("Evidence",back_populates="case",cascade="all, delete-orphan")
    findings=relationship("Finding",back_populates="case",cascade="all, delete-orphan")
class Evidence(Base):
    __tablename__="evidence"
    id=Column(Integer,primary_key=True)
    case_id=Column(Integer,ForeignKey("cases.id"),nullable=False)
    original_name=Column(String(255),nullable=False)
    stored_name=Column(String(80),unique=True,nullable=False)
    media_type=Column(String(120))
    size_bytes=Column(Integer,nullable=False)
    sha256=Column(String(64),nullable=False,index=True)
    collected_at=Column(DateTime(timezone=True),default=utcnow,nullable=False)
    notes=Column(Text,default="")
    case=relationship("Case",back_populates="evidence")
class Finding(Base):
    __tablename__="findings"
    id=Column(Integer,primary_key=True)
    case_id=Column(Integer,ForeignKey("cases.id"),nullable=False)
    category=Column(String(60),nullable=False)
    title=Column(String(200),nullable=False)
    detail=Column(Text,nullable=False)
    source=Column(String(500),default="")
    confidence=Column(String(20),default="unverified")
    created_at=Column(DateTime(timezone=True),default=utcnow,nullable=False)
    case=relationship("Case",back_populates="findings")
class AuditLog(Base):
    __tablename__="audit_logs"
    id=Column(Integer,primary_key=True)
    actor=Column(String(120),nullable=False)
    action=Column(String(100),nullable=False)
    object_type=Column(String(60),nullable=False)
    object_id=Column(String(80))
    detail=Column(Text,default="")
    created_at=Column(DateTime(timezone=True),default=utcnow,nullable=False)
