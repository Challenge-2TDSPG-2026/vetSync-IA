from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from .connection import Base

class Agendamento(Base):
    __tablename__ = "agendamentos"
    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(String(100), index=True)
    patient_name = Column(String(100), nullable=True)
    doctor_name = Column(String(100), nullable=True)
    date_reference = Column(String(50), nullable=True)
    time_reference = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Triagem(Base):
    __tablename__ = "triagens"
    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(String(100), index=True)
    pet_id = Column(String(100), nullable=True)
    urgency_level = Column(String(50))
    symptoms = Column(String(1000), nullable=True)
    notify_team = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PosAtendimento(Base):
    __tablename__ = "pos_atendimentos"
    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(String(100), index=True)
    pet_name = Column(String(100), nullable=True)
    days_until_follow_up = Column(Integer, nullable=True)
    attach_prescription = Column(Boolean, default=False)
    attach_medical_record = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Checkin(Base):
    __tablename__ = "checkins"
    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(String(100), index=True)
    surgery_id = Column(String(100), index=True, nullable=True)
    recovery_status = Column(String(50))
    red_flags = Column(String(1000), nullable=True)
    notify_veterinarian = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
