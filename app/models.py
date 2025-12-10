from sqlalchemy import Column, Integer, String, Date, Text, Enum, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Viaje(Base):
    __tablename__ = "viajes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(String(50), nullable=False) # String ID from CloudFleet
    sede_id = Column(String(50), nullable=False)    # String ID from CloudFleet
    fecha = Column(Date, nullable=False)
    estado = Column(Enum('borrador', 'confirmado', 'cancelado'), default='borrador')
    creado_en = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    detalle = relationship("ViajeDetalle", back_populates="viaje", cascade="all, delete-orphan")

class ViajeDetalle(Base):
    __tablename__ = "viaje_detalle"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    viaje_id = Column(Integer, nullable=False) # Manual link if ForeignKey fails, but usually we map filtering. 
    # Actually, if we use relationship, we need a ForeignKey.
    # But since Viaje is defined here, we CAN use ForeignKey to "viajes.id".
    
    # We re-add FK only to LOCAL table 'viajes'
    from sqlalchemy import ForeignKey
    viaje_id = Column(Integer, ForeignKey("viajes.id"), nullable=False)
    
    # Resources (Nullable for Draft slots, String for CloudFleet compatibility)
    ruta_id = Column(String(50), nullable=True)
    vehiculo_id = Column(String(50), nullable=True)
    conductor_id = Column(String(50), nullable=True)
    auxiliar_id = Column(String(50), nullable=True)
    
    notas = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    viaje = relationship("Viaje", back_populates="detalle")
