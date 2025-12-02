# Microservicio FastAPI para gestión completa de CloudFleet
import os
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from app.cloudfleet import (
        get_clientes, get_cliente, get_sedes, get_sede,
        get_rutas, get_ruta, get_camiones, get_personas,
        get_persona, get_travels, get_travel
    )
except Exception:
    # Permite ejecutar aunque no exista cloudfleet.py configurado
    get_clientes = None
    get_cliente = None
    get_sedes = None
    get_sede = None
    get_rutas = None
    get_ruta = None
    get_camiones = None
    get_personas = None
    get_persona = None
    get_travels = None
    get_travel = None

# Parámetros de negocio
MAX_DIAS_CONSECUTIVOS = int(os.getenv("MAX_DIAS_CONSECUTIVOS", "6"))
FORCE_CLOUDFLEET = os.getenv("FORCE_CLOUDFLEET", "false").lower() == "true"
TARGET_PLACA = os.getenv("TARGET_PLACA", "FKL 92H")
TARGET_CONDUCTOR_DOC = os.getenv("TARGET_CONDUCTOR_DOC", "1143865250")

app = FastAPI(
    title="CloudFleet Manager API",
    version="1.0.0",
    description="API para gestión completa de clientes, sedes, rutas, vehículos y personal"
)


# ============= MODELOS PYDANTIC =============

class Cliente(BaseModel):
    id: str
    nombre: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    datos_adicionales: Optional[Dict[str, Any]] = None


class Sede(BaseModel):
    id: str
    cliente_id: str
    nombre: str
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    datos_adicionales: Optional[Dict[str, Any]] = None


class Ruta(BaseModel):
    id: str
    cliente_id: Optional[str] = None
    sede_id: Optional[str] = None
    codigo: str
    nombre: str
    origen: Optional[str] = None
    destino: Optional[str] = None
    distancia_km: Optional[float] = None
    activa: bool = True
    datos_adicionales: Optional[Dict[str, Any]] = None


class Vehiculo(BaseModel):
    id: str
    sede_id: Optional[str] = None
    placa: str
    tipo: Optional[str] = None
    capacidad: Optional[int] = None
    ubicacion_ciudad: Optional[str] = None
    activo: bool = True
    datos_adicionales: Optional[Dict[str, Any]] = None


class Persona(BaseModel):
    id: str
    sede_id: Optional[str] = None
    nombre: str
    rol: str  # 'conductor', 'auxiliar'
    documento: Optional[str] = None
    telefono: Optional[str] = None
    ubicacion_ciudad: Optional[str] = None
    activo: bool = True
    datos_adicionales: Optional[Dict[str, Any]] = None


class ClienteCompleto(BaseModel):
    cliente: Cliente
    sedes: List[Sede]
    total_sedes: int


class SedeCompleta(BaseModel):
    sede: Sede
    vehiculos: List[Vehiculo]
    personal: List[Persona]
    rutas: List[Ruta]
    total_vehiculos: int
    total_personal: int
    total_rutas: int


class ScheduleRequest(BaseModel):
    fecha: str
    cliente_id: int
    sede_id: int


class Asignacion(BaseModel):
    ruta_id: int
    vehiculo_id: int
    conductor_id: int
    auxiliar_id: int
    notas: Optional[str] = None


class ResumenOperacional(BaseModel):
    cliente_id: str
    cliente_nombre: str
    total_sedes: int
    total_vehiculos: int
    total_conductores: int
    total_auxiliares: int
    total_rutas: int
    vehiculos_activos: int
    personal_activo: int


# ============= FUNCIONES AUXILIARES =============

def _parse_fecha(fecha_str: str) -> date:
    return datetime.strptime(fecha_str, "%Y-%m-%d").date()


def _filtrar_consecutivos(personas: list[dict]) -> list[dict]:
    filtradas = []
    for p in personas:
        dias = int(p.get("dias_consecutivos", 0) or 0)
        if dias >= MAX_DIAS_CONSECUTIVOS:
            continue
        filtradas.append(p)
    return filtradas


def _filtrar_permisos(personas: list[dict], permisos_requeridos: set[str]) -> list[dict]:
    if not permisos_requeridos:
        return personas
    filtradas = []
    for p in personas:
        permisos = set(p.get("permisos", []))
        if permisos_requeridos.issubset(permisos):
            filtradas.append(p)
    return filtradas


def _rotar_personas(personas: list[dict]) -> list[dict]:
    return sorted(
        personas,
        key=lambda p: (
            p.get("ultima_asignacion") or "",
            p.get("id") or 0,
        ),
    )


def _ciudades_por_cliente(cliente_id: Optional[str]) -> set[str]:
    """
    Retorna las ciudades asociadas a las sedes del cliente para poder filtrar
    vehiculos y personal por pertenencia.
    """
    if not cliente_id or not get_sedes:
        return set()

    try:
        sedes = get_sedes(cliente_id) or []
    except Exception:
        return set()

    ciudades: set[str] = set()
    for sede in sedes:
        ciudad_val = sede.get("city", sede.get("ciudad"))
        if isinstance(ciudad_val, dict):
            ciudad = ciudad_val.get("name", "")
        else:
            ciudad = ciudad_val or ""
        if ciudad:
            ciudades.add(str(ciudad).lower())
    return ciudades


# ============= ENDPOINTS DE CLIENTES =============

@app.get("/")
def health():
    return {
        "message": "CloudFleet Manager API OK",
        "version": "1.0.0",
        "endpoints": {
            "clientes": "/clientes",
            "cliente": "/clientes/{cliente_id}",
            "sedes": "/sedes",
            "sede_detalle": "/sedes/{sede_id}",
            "rutas": "/rutas",
            "vehiculos": "/vehiculos",
            "personal": "/personal",
            "resumen": "/clientes/{cliente_id}/resumen"
        }
    }


@app.get("/clientes", response_model=List[Cliente])
def listar_clientes():
    """
    Obtiene el listado completo de clientes desde CloudFleet API
    """
    if not get_clientes:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        data = get_clientes()
        clientes = []
        for item in data:
            clientes.append(Cliente(
                id=str(item.get("id", "")),
                nombre=item.get("name", item.get("nombre", "Sin nombre")),
                contacto=item.get("contact", item.get("contacto")),
                telefono=item.get("phone", item.get("telefono")),
                email=item.get("email"),
                datos_adicionales=item
            ))
        return clientes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener clientes: {str(e)}")


@app.get("/clientes/{cliente_id}", response_model=ClienteCompleto)
def obtener_cliente_completo(cliente_id: str):
    """
    Obtiene un cliente específico con todas sus sedes
    """
    if not get_cliente or not get_sedes:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        # Obtener cliente
        cliente_data = get_cliente(cliente_id)
        cliente = Cliente(
            id=str(cliente_data.get("id", cliente_id)),
            nombre=cliente_data.get("name", cliente_data.get("nombre", "Sin nombre")),
            contacto=cliente_data.get("contact", cliente_data.get("contacto")),
            telefono=cliente_data.get("phone", cliente_data.get("telefono")),
            email=cliente_data.get("email"),
            datos_adicionales=cliente_data
        )
        
        # Obtener sedes del cliente
        sedes_data = get_sedes(cliente_id)
        sedes = []
        for item in sedes_data:
            sedes.append(Sede(
                id=str(item.get("id", "")),
                cliente_id=cliente_id,
                nombre=item.get("name", item.get("nombre", "Sin nombre")),
                ciudad=item.get("city", item.get("ciudad")),
                direccion=item.get("address", item.get("direccion")),
                telefono=item.get("phone", item.get("telefono")),
                datos_adicionales=item
            ))
        
        return ClienteCompleto(
            cliente=cliente,
            sedes=sedes,
            total_sedes=len(sedes)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cliente: {str(e)}")


# ============= ENDPOINTS DE SEDES =============

@app.get("/sedes", response_model=List[Sede])
def listar_sedes(cliente_id: Optional[str] = Query(None, description="ID del cliente para filtrar")):
    """
    Obtiene el listado de sedes. Opcionalmente filtra por cliente_id
    """
    if not get_sedes:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        sedes_data = get_sedes(cliente_id)
        sedes = []
        for item in sedes_data:
            sedes.append(Sede(
                id=str(item.get("id", "")),
                cliente_id=str(item.get("customerId", item.get("cliente_id", ""))),
                nombre=item.get("name", item.get("nombre", "Sin nombre")),
                ciudad=item.get("city", item.get("ciudad")),
                direccion=item.get("address", item.get("direccion")),
                telefono=item.get("phone", item.get("telefono")),
                datos_adicionales=item
            ))
        return sedes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sedes: {str(e)}")


@app.get("/sedes/{sede_id}", response_model=SedeCompleta)
def obtener_sede_completa(sede_id: str):
    """
    Obtiene una sede específica con todos sus vehículos, personal y rutas
    """
    if not get_sede or not get_camiones or not get_personas or not get_rutas:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        # Obtener sede
        sede_data = get_sede(sede_id)
        sede = Sede(
            id=str(sede_data.get("id", sede_id)),
            cliente_id=str(sede_data.get("customerId", sede_data.get("cliente_id", ""))),
            nombre=sede_data.get("name", sede_data.get("nombre", "Sin nombre")),
            ciudad=sede_data.get("city", sede_data.get("ciudad")),
            direccion=sede_data.get("address", sede_data.get("direccion")),
            telefono=sede_data.get("phone", sede_data.get("telefono")),
            datos_adicionales=sede_data
        )
        
        # Obtener vehículos (filtramos por ciudad de la sede si aplica)
        vehiculos_data = get_camiones()
        ciudad_sede = sede.ciudad
        vehiculos = []
        for item in vehiculos_data:
            # Filtrar por ubicación si coincide
            ubicacion = item.get("location", item.get("ubicacion_ciudad", ""))
            if ciudad_sede and ubicacion and ciudad_sede.lower() in ubicacion.lower():
                vehiculos.append(Vehiculo(
                    id=str(item.get("id", "")),
                    sede_id=sede_id,
                    placa=item.get("code", item.get("placa", "SIN-PLACA")),
                    tipo=item.get("type", item.get("tipo")),
                    capacidad=item.get("capacity", item.get("capacidad")),
                    ubicacion_ciudad=ubicacion,
                    activo=item.get("active", item.get("activo", True)),
                    datos_adicionales=item
                ))
        
        # Obtener personal (filtramos por ciudad de la sede si aplica)
        personal_data = get_personas()
        personal = []
        for item in personal_data:
            ubicacion = item.get("location", item.get("ubicacion_ciudad", ""))
            if ciudad_sede and ubicacion and ciudad_sede.lower() in ubicacion.lower():
                personal.append(Persona(
                    id=str(item.get("id", item.get("personalId", ""))),
                    sede_id=sede_id,
                    nombre=item.get("name", item.get("nombre", "Sin nombre")),
                    rol=item.get("role", item.get("rol", "conductor")),
                    documento=item.get("document", item.get("documento")),
                    telefono=item.get("phone", item.get("telefono")),
                    ubicacion_ciudad=ubicacion,
                    activo=item.get("active", item.get("activo", True)),
                    datos_adicionales=item
                ))
        
        # Obtener rutas del cliente de la sede
        rutas_data = get_rutas(sede.cliente_id) if sede.cliente_id else []
        rutas = []
        for item in rutas_data:
            rutas.append(Ruta(
                id=str(item.get("id", "")),
                cliente_id=sede.cliente_id,
                sede_id=sede_id,
                codigo=item.get("code", item.get("codigo", "SIN-COD")),
                nombre=item.get("name", item.get("nombre", "Sin nombre")),
                origen=item.get("origin", item.get("origen")),
                destino=item.get("destination", item.get("destino")),
                distancia_km=item.get("distance", item.get("distancia_km")),
                activa=item.get("active", item.get("activa", True)),
                datos_adicionales=item
            ))
        
        return SedeCompleta(
            sede=sede,
            vehiculos=vehiculos,
            personal=personal,
            rutas=rutas,
            total_vehiculos=len(vehiculos),
            total_personal=len(personal),
            total_rutas=len(rutas)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sede completa: {str(e)}")


# ============= ENDPOINTS DE RUTAS =============

@app.get("/rutas", response_model=List[Ruta])
def listar_rutas(cliente_id: Optional[str] = Query(None, description="ID del cliente para filtrar")):
    """
    Obtiene el listado de rutas. Opcionalmente filtra por cliente_id
    """
    if not get_rutas:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        rutas_data = get_rutas(cliente_id)
        rutas = []
        for item in rutas_data:
            rutas.append(Ruta(
                id=str(item.get("id", "")),
                cliente_id=str(item.get("customerId", item.get("cliente_id", ""))),
                sede_id=str(item.get("locationId", item.get("sede_id", ""))),
                codigo=item.get("code", item.get("codigo", "SIN-COD")),
                nombre=item.get("name", item.get("nombre", "Sin nombre")),
                origen=item.get("origin", item.get("origen")),
                destino=item.get("destination", item.get("destino")),
                distancia_km=item.get("distance", item.get("distancia_km")),
                activa=item.get("active", item.get("activa", True)),
                datos_adicionales=item
            ))
        return rutas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener rutas: {str(e)}")


@app.get("/rutas/{ruta_id}", response_model=Ruta)
def obtener_ruta(ruta_id: str):
    """
    Obtiene una ruta específica por ID
    """
    if not get_ruta:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        item = get_ruta(ruta_id)
        return Ruta(
            id=str(item.get("id", ruta_id)),
            cliente_id=str(item.get("customerId", item.get("cliente_id", ""))),
            sede_id=str(item.get("locationId", item.get("sede_id", ""))),
            codigo=item.get("code", item.get("codigo", "SIN-COD")),
            nombre=item.get("name", item.get("nombre", "Sin nombre")),
            origen=item.get("origin", item.get("origen")),
            destino=item.get("destination", item.get("destino")),
            distancia_km=item.get("distance", item.get("distancia_km")),
            activa=item.get("active", item.get("activa", True)),
            datos_adicionales=item
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener ruta: {str(e)}")


# ============= ENDPOINTS DE VEHÍCULOS =============

@app.get("/vehiculos", response_model=List[Vehiculo])
def listar_vehiculos(
    sede_id: Optional[str] = Query(None, description="ID de la sede para filtrar"),
    ciudad: Optional[str] = Query(None, description="Ciudad para filtrar"),
    centro_costo: Optional[str] = Query(None, description="Centro de costo para filtrar"),
    cliente_id: Optional[str] = Query(None, description="ID del cliente para filtrar por sus sedes")
):
    """
    Obtiene el listado de vehiculos. Opcionalmente filtra por sede, ciudad,
    centro de costo o cliente (usando las ciudades de sus sedes).
    """
    if not get_camiones:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        vehiculos_data = get_camiones()
        ciudades_cliente = _ciudades_por_cliente(cliente_id)
        vehiculos = []
        for item in vehiculos_data:
            # Obtener ciudad (puede ser objeto o string)
            city_obj = item.get("city")
            ubicacion = city_obj.get("name", "") if isinstance(city_obj, dict) else (city_obj or "")
            
            # Obtener centro de costo
            cost_center = item.get("costCenter")
            centro_costo_nombre = cost_center.get("name", "") if isinstance(cost_center, dict) else ""
            centro_costo_code = cost_center.get("code", "") if isinstance(cost_center, dict) else ""
            
            # Filtrar por ciudad si se especifica
            if ciudad:
                if not ubicacion or ciudad.lower() not in ubicacion.lower():
                    continue

            # Filtrar por cliente usando las ciudades de sus sedes
            if cliente_id:
                match_cliente = False
                if ciudades_cliente:
                    match_cliente = bool(ubicacion and ubicacion.lower() in ciudades_cliente)
                else:
                    customer_val = str(item.get("customerId", item.get("cliente_id", "")) or "")
                    if customer_val:
                        match_cliente = customer_val == str(cliente_id)
                if not match_cliente:
                    continue
            
            # Filtrar por centro de costo si se especifica
            if centro_costo:
                if not cost_center:
                    continue
                if (centro_costo.lower() not in centro_costo_nombre.lower() and 
                    centro_costo.lower() not in centro_costo_code.lower()):
                    continue
            
            vehiculos.append(Vehiculo(
                id=str(item.get("id", "")),
                sede_id=sede_id,
                placa=item.get("code", "SIN-PLACA"),
                tipo=item.get("typeName"),
                capacidad=None,
                ubicacion_ciudad=ubicacion,
                activo=True,
                datos_adicionales=item
            ))
        return vehiculos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener vehiculos: {str(e)}")


# ============= ENDPOINTS DE PERSONAL =============

@app.get("/personal", response_model=List[Persona])
def listar_personal(
    sede_id: Optional[str] = Query(None, description="ID de la sede para filtrar"),
    ciudad: Optional[str] = Query(None, description="Ciudad para filtrar"),
    rol: Optional[str] = Query(None, description="Rol: conductor, auxiliar"),
    cliente_id: Optional[str] = Query(None, description="ID del cliente para filtrar por sus sedes")
):
    """
    Obtiene el listado de personal. Opcionalmente filtra por sede, ciudad, rol
    o cliente (usando las ciudades de sus sedes).
    NOTA: El personal NO se filtra por centro de costo, solo por ciudad.
    """
    if not get_personas:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        personal_data = get_personas()
        ciudades_cliente = _ciudades_por_cliente(cliente_id)
        personal = []
        for item in personal_data:
            # Obtener ciudad (puede ser objeto o string)
            city_obj = item.get("city")
            ubicacion = city_obj.get("name", "") if isinstance(city_obj, dict) else (city_obj or "")
            
            # Obtener posicion/rol
            position_type = item.get("positionType", {})
            rol_persona = position_type.get("name", "other") if isinstance(position_type, dict) else "other"
            
            # Construir nombre completo
            first_name = item.get("firstName", "")
            last_name = item.get("lastName", "")
            nombre_completo = f"{first_name} {last_name}".strip() or "Sin nombre"
            
            # Filtrar por ciudad si se especifica
            if ciudad:
                if not ubicacion or ciudad.lower() not in ubicacion.lower():
                    continue

            # Filtrar por cliente usando las ciudades de sus sedes
            if cliente_id:
                match_cliente = False
                if ciudades_cliente:
                    match_cliente = bool(ubicacion and ubicacion.lower() in ciudades_cliente)
                else:
                    customer_val = str(item.get("customerId", item.get("cliente_id", "")) or "")
                    if customer_val:
                        match_cliente = customer_val == str(cliente_id)
                if not match_cliente:
                    continue
            
            # Filtrar por rol si se especifica
            if rol and rol.lower() not in rol_persona.lower():
                continue
            
            personal.append(Persona(
                id=str(item.get("id", item.get("personalId", ""))),
                sede_id=sede_id,
                nombre=nombre_completo,
                rol=item.get("position", rol_persona),
                documento=item.get("personalId", ""),
                telefono=item.get("mobilePhone", item.get("landlinePhone", "")),
                ubicacion_ciudad=ubicacion,
                activo=item.get("isActive", True),
                datos_adicionales=item
            ))
        return personal
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener personal: {str(e)}")


# ============= ENDPOINT DE RESUMEN OPERACIONAL =============

@app.get("/clientes/{cliente_id}/resumen", response_model=ResumenOperacional)
def obtener_resumen_operacional(cliente_id: str):
    """
    Obtiene un resumen operacional completo de un cliente:
    - Total de sedes
    - Total de vehículos y cuántos están activos
    - Total de personal (conductores y auxiliares) y cuántos están activos
    - Total de rutas
    """
    if not get_cliente or not get_sedes or not get_rutas:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        # Obtener cliente
        cliente_data = get_cliente(cliente_id)
        cliente_nombre = cliente_data.get("name", cliente_data.get("nombre", "Sin nombre"))
        
        # Obtener sedes
        sedes_data = get_sedes(cliente_id)
        total_sedes = len(sedes_data)
        
        # Obtener rutas
        rutas_data = get_rutas(cliente_id)
        total_rutas = len(rutas_data)
        
        # Obtener vehículos y personal de todas las sedes
        vehiculos_data = get_camiones() if get_camiones else []
        personal_data = get_personas() if get_personas else []
        
        # Contar vehículos activos
        vehiculos_activos = sum(1 for v in vehiculos_data if v.get("active", v.get("activo", True)))
        
        # Separar y contar personal
        conductores = [p for p in personal_data if p.get("role", p.get("rol")) == "conductor"]
        auxiliares = [p for p in personal_data if p.get("role", p.get("rol")) == "auxiliar"]
        personal_activo = sum(1 for p in personal_data if p.get("active", p.get("activo", True)))
        
        return ResumenOperacional(
            cliente_id=cliente_id,
            cliente_nombre=cliente_nombre,
            total_sedes=total_sedes,
            total_vehiculos=len(vehiculos_data),
            total_conductores=len(conductores),
            total_auxiliares=len(auxiliares),
            total_rutas=total_rutas,
            vehiculos_activos=vehiculos_activos,
            personal_activo=personal_activo
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")


# ============= ENDPOINTS DE PROGRAMACIÓN (LEGACY) =============

def _asignaciones_dummy() -> List[Asignacion]:
    """Fallback simple para pruebas locales con IDs que existan en la BD."""
    return [
        Asignacion(
            ruta_id=1,
            vehiculo_id=178,
            conductor_id=1,
            auxiliar_id=2,
            notas="Asignacion de prueba usando datos locales",
        ),
    ]


def _asignaciones_desde_cloudfleet(req: ScheduleRequest) -> List[Asignacion]:
    """
    Obtiene datos desde Cloudfleet. Completa URLs/keys y logica en cloudfleet.py.
    """
    if not get_camiones or not get_personas:
        raise RuntimeError("Cliente Cloudfleet no configurado")

    fecha = _parse_fecha(req.fecha)
    
    # Si tenemos placa y documento objetivo, intentamos asignar directo esos recursos
    if TARGET_PLACA and TARGET_CONDUCTOR_DOC:
        camiones = get_camiones(TARGET_PLACA)
        personas = get_personas()

        camion = camiones[0] if isinstance(camiones, list) and camiones else None
        conductor = next(
            (
                p
                for p in personas
                if str(p.get("personalId") or p.get("documento") or "").strip()
                == str(TARGET_CONDUCTOR_DOC).strip()
            ),
            None,
        )
        auxiliar = next((p for p in personas if p.get("rol") == "auxiliar"), None)

        if camion and conductor and auxiliar:
            return [
                Asignacion(
                    ruta_id=1,
                    vehiculo_id=int(camion.get("id")),
                    conductor_id=int(conductor.get("id")),
                    auxiliar_id=int(auxiliar.get("id")),
                    notas=f"Asignacion API (placa {TARGET_PLACA}, doc {TARGET_CONDUCTOR_DOC}) {fecha.isoformat()}",
                )
            ]

    camiones = get_camiones()
    personas = get_personas()

    # Separar conductores y auxiliares
    conductores = [p for p in personas if p.get("rol") == "conductor"]
    auxiliares = [p for p in personas if p.get("rol") == "auxiliar"]

    conductores = _filtrar_consecutivos(conductores)
    auxiliares = _filtrar_consecutivos(auxiliares)
    conductores = _rotar_personas(conductores)
    auxiliares = _rotar_personas(auxiliares)

    asignaciones: List[Asignacion] = []
    rutas_placeholder = list(range(1, len(camiones) + 1))

    for idx, ruta_id in enumerate(rutas_placeholder):
        if idx >= len(camiones) or idx >= len(conductores) or idx >= len(auxiliares):
            break

        camion = camiones[idx]
        conductor = conductores[idx]
        auxiliar = auxiliares[idx]

        asignaciones.append(
            Asignacion(
                ruta_id=ruta_id,
                vehiculo_id=int(camion.get("id", idx + 1)),
                conductor_id=int(conductor.get("id", idx + 1)),
                auxiliar_id=int(auxiliar.get("id", idx + 1000)),
                notas=f"Asignacion automatica {fecha.isoformat()}",
            )
        )

    if not asignaciones:
        raise RuntimeError("Cloudfleet no devolvio datos suficientes para asignar")

    return asignaciones


@app.post("/schedule", response_model=List[Asignacion])
def schedule(req: ScheduleRequest):
    """
    Endpoint de programación (legacy).
    - Si Cloudfleet está configurado, intenta usarlo.
    - Si falla o no está configurado, devuelve asignaciones dummy.
    """
    try:
        return _asignaciones_desde_cloudfleet(req)
    except Exception as exc:
        if FORCE_CLOUDFLEET:
            raise HTTPException(status_code=500, detail=str(exc))
        return _asignaciones_dummy()


# ============= SERVIR INTERFAZ WEB =============

@app.get("/dashboard")
def dashboard():
    """
    Sirve la interfaz web para visualizar vehículos y personal
    """
    import pathlib
    html_path = pathlib.Path(__file__).parent.parent / "public" / "index.html"
    return FileResponse(html_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
