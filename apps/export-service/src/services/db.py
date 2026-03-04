from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config import settings
import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    metadata_json = Column(JSON, nullable=True)

class DBService:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def add_job(self, job_id: str, status: str, meta: dict = None):
        db = self.SessionLocal()
        try:
            job = Job(id=job_id, status=status, metadata_json=meta)
            db.add(job)
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    def update_job(self, job_id: str, status: str):
        db = self.SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = status
                db.commit()
        finally:
            db.close()

    def get_recent_jobs(self, limit: int = 50):
        db = self.SessionLocal()
        try:
            jobs = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
            return [{"id": j.id, "status": j.status, "created_at": j.created_at, "metadata": j.metadata_json} for j in jobs]
        finally:
            db.close()

    def delete_job(self, job_id: str):
        db = self.SessionLocal()
        try:
            db.query(Job).filter(Job.id == job_id).delete()
            db.commit()
        finally:
            db.close()

db_service = DBService()
