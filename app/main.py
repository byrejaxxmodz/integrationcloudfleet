# Microservicio FastAPI de prueba para devolver asignaciones dummy
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Scheduler", version="0.1.0")


class ScheduleRequest(BaseModel):
    fecha: str
    cliente_id: int
    sede_id: int


class Asignacion(BaseModel):
    ruta_id: int
    vehiculo_id: int
    conductor_id: int
    auxiliar_id: int
    notas: str | None = None


@app.get("/")
def health():
    return {"message": "Scheduler OK"}


@app.post("/schedule", response_model=List[Asignacion])
def schedule(req: ScheduleRequest):
    # Respuesta mock para probar el flujo PHP → Python → PHP
    return [
        Asignacion(
            ruta_id=1,
            vehiculo_id=1,
            conductor_id=1,
            auxiliar_id=2,
            notas="Asignación de prueba 1",
        ),
        Asignacion(
            ruta_id=2,
            vehiculo_id=2,
            conductor_id=3,
            auxiliar_id=4,
            notas="Asignación de prueba 2",
        ),
    ]
