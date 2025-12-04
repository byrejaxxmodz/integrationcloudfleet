# Microservicio FastAPI para gestión completa de CloudFleet
import os
import time
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

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
# Vehiculos a muestrear para armar rutas desde travels; subirlo si necesitas mas cobertura
TRAVELS_SAMPLE_VEHICLES = int(os.getenv("TRAVELS_SAMPLE_VEHICLES", "50"))
# Tiempo maximo (segundos) para intentar fallback de rutas desde travels
TRAVELS_FALLBACK_MAX_SECONDS = float(os.getenv("TRAVELS_FALLBACK_MAX_SECONDS", "30"))
# Paginas maximas a recorrer en travels cuando se usan filtros
TRAVELS_MAX_PAGES = int(os.getenv("TRAVELS_MAX_PAGES", "20"))
# Dias hacia atras para el rango por defecto en travels (fecha de creacion)
TRAVELS_RANGE_DAYS = int(os.getenv("TRAVELS_RANGE_DAYS", "365"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cloudfleet")

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
    via_codigo: Optional[str] = None
    vias: List[str] = Field(default_factory=list)
    vias_detalle: List[Dict[str, Any]] = Field(default_factory=list)
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


def _clientes_desde_camiones() -> list[Cliente]:
    """
    Fallback simple para construir clientes a partir de los centros de costo
    presentes en los vehiculos cuando la API de clientes no esta disponible.
    """
    if not get_camiones:
        return []
    try:
        camiones = get_camiones()
    except Exception:
        return []

    clientes: list[Cliente] = []
    vistos: set[str] = set()
    for v in camiones or []:
        cost_center = v.get("costCenter") or {}
        cid = str(
            cost_center.get("id")
            or cost_center.get("code")
            or cost_center.get("name")
            or ""
        ).strip()
        if not cid or cid in vistos:
            continue
        vistos.add(cid)
        nombre = cost_center.get("name") or f"Cliente {cid}"
        clientes.append(
            Cliente(
                id=cid,
                nombre=nombre,
                contacto=None,
                telefono=None,
                email=None,
                datos_adicionales={"origen": "cost_center"},
            )
        )
    return clientes


def _rutas_dummy(cliente_id: Optional[str]) -> list[Ruta]:
    """
    Fallback de rutas basicas para que la UI no quede vacia cuando la API no
    retorna datos.
    """
    base_id = int(cliente_id) if (cliente_id and str(cliente_id).isdigit()) else 0
    return [
        Ruta(
            id=str(base_id + 1),
            cliente_id=str(cliente_id or "0"),
            sede_id=None,
            codigo="RT-001",
            nombre="Ruta Norte",
            origen="Origen A",
            destino="Destino B",
            distancia_km=12.5,
            activa=True,
            datos_adicionales={"dummy": True},
        ),
        Ruta(
            id=str(base_id + 2),
            cliente_id=str(cliente_id or "0"),
            sede_id=None,
            codigo="RT-002",
            nombre="Ruta Centro",
            origen="Origen C",
            destino="Destino D",
            distancia_km=8.0,
            activa=True,
            datos_adicionales={"dummy": True},
        ),
        Ruta(
            id=str(base_id + 3),
            cliente_id=str(cliente_id or "0"),
            sede_id=None,
            codigo="RT-003",
            nombre="Ruta Sur",
            origen="Origen E",
            destino="Destino F",
            distancia_km=20.0,
            activa=True,
            datos_adicionales={"dummy": True},
        ),
    ]


def _parse_location(loc: Any) -> str:
    """
    Extrae un nombre de ubicacion desde string o diccionario con 'name'.
    """
    if isinstance(loc, dict):
        return loc.get("name") or loc.get("code") or ""
    if loc is None:
        return ""
    return str(loc)


def _norm_txt(texto: str | None) -> str:
    """
    Normaliza texto a minusculas sin acentos para comparaciones de ciudad.
    """
    import unicodedata
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto).lower())
        if unicodedata.category(c) != "Mn"
    )


def _match_ciudad(ciudad_filtro: str, valor: str | None) -> bool:
    if not ciudad_filtro:
        return True
    cf = _norm_txt(ciudad_filtro)
    vt = _norm_txt(valor)
    # También probamos sin el texto entre paréntesis, ej: "Caloto (Cauca)" -> "Caloto"
    base = vt.split("(")[0].strip() if "(" in vt else vt
    return cf in vt or cf in base


VOWELS = set("AEIOUÁÉÍÓÚÜ")


def _abbr_candidates(texto: str | None, length: int = 3) -> list[str]:
    """
    Genera abreviaturas posibles priorizando consonantes (para casos como CHL)
    y luego las primeras letras simples como respaldo.
    """
    if not texto:
        return []
    chars = [c for c in texto.upper() if c.isalpha()]
    if not chars:
        return []

    simple = "".join(chars)[:length]
    consonants = "".join(c for c in chars if c not in VOWELS)[:length]

    opciones: list[str] = []
    for cand in (consonants, simple):
        cand = cand[:length]
        if cand and cand not in opciones:
            opciones.append(cand)
    return opciones


def _abbr(texto: str | None, length: int = 3) -> str:
    """
    Abreviatura base (usa la primera opción disponible).
    """
    opciones = _abbr_candidates(texto, length)
    return opciones[0] if opciones else ""


def _abbr_cliente(nombre: str | None, length: int = 3) -> str:
    """
    Usa la última palabra del nombre del cliente (ej: 'CCM CHILCO' -> 'CHILCO')
    y toma sus primeras letras para armar el prefijo.
    """
    if not nombre:
        return ""
    tokens = nombre.replace("-", " ").split()
    objetivo = tokens[-1] if tokens else nombre
    opciones = _abbr_candidates(objetivo, length)
    return opciones[0] if opciones else ""


def _route_prefix_from_filters(cliente_id: Optional[str], ciudad: Optional[str]) -> Optional[str]:
    """
    Construye prefijo de ruta: ABC-XYZ usando 3 letras del cliente y 3 de la ciudad.
    """
    if not ciudad:
        return None
    city_abbr = _abbr(ciudad, 3)
    client_abbr = ""
    if cliente_id and get_cliente:
        try:
            cli = get_cliente(cliente_id)
            client_abbr = _abbr_cliente(cli.get("name") or cli.get("nombre") or str(cliente_id), 3)
        except Exception:
            client_abbr = _abbr_cliente(str(cliente_id), 3)
    elif cliente_id:
        client_abbr = _abbr_cliente(str(cliente_id), 3)
    prefix = f"{client_abbr}-{city_abbr}" if client_abbr else city_abbr
    return prefix or None


def _route_code_from_filters(cliente_id: Optional[str], ciudad: Optional[str]) -> Optional[str]:
    """
    Construye codigo de ruta completo con sufijo VAR: ABC-XYZ-VAR (3 letras cliente + 3 letras ciudad).
    """
    candidates = _route_codes_candidates(cliente_id, ciudad)
    return candidates[0] if candidates else None


def _route_codes_candidates(
    cliente_id: Optional[str],
    ciudad: Optional[str],
    route_code: Optional[str] = None,
) -> list[str]:
    """
    Genera posibles códigos de ruta combinando abreviaturas de cliente/ciudad.
    Ej: ['CHL-YUM-VAR', 'CHI-YUM-VAR'] para cubrir variantes.
    """
    if route_code:
        return [route_code]
    if not ciudad:
        return []

    city_opts = _abbr_candidates(ciudad, 3)
    if not city_opts:
        return []

    client_opts: list[str] = []
    if cliente_id and get_cliente:
        try:
            cli = get_cliente(cliente_id)
            nombre_cli = cli.get("name") or cli.get("nombre") or str(cliente_id)
            client_opts = _abbr_candidates(nombre_cli, 3)
        except Exception:
            client_opts = _abbr_candidates(str(cliente_id), 3)
    elif cliente_id:
        client_opts = _abbr_candidates(str(cliente_id), 3)

    combos: list[str] = []
    for c_abbr in client_opts or [""]:
        for city_abbr in city_opts:
            prefix = f"{c_abbr}-{city_abbr}" if c_abbr else city_abbr
            combos.append(f"{prefix}-VAR")

    dedup: list[str] = []
    seen: set[str] = set()
    for code in combos:
        if code in seen:
            continue
        dedup.append(code)
        seen.add(code)
    return dedup


def _agregar_via(
    codigos: set[str],
    detalle: list[dict[str, Any]],
    code: Optional[str],
    name: Optional[str],
    raw: Optional[dict[str, Any]] = None,
) -> None:
    if not code and not name:
        return
    code_clean = str(code).strip() if code else ""
    name_clean = str(name).strip() if name else ""
    if code_clean:
        codigos.add(code_clean)
    detalle.append(
        {
            "code": code_clean or None,
            "name": name_clean or None,
            "raw": raw or {},
        }
    )


def _vias_desde_item(item: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]], Optional[str]]:
    """
    Extrae codigos y detalle de vias desde un item (route o travel).
    Retorna (codigos_unicos, detalle, via_codigo_principal)
    """
    codigos: set[str] = set()
    detalle: list[dict[str, Any]] = []
    principal: Optional[str] = None

    # Campos directos
    via_code = item.get("viaCode") or item.get("via_codigo") or item.get("via_code")
    via_name = item.get("viaName") or item.get("via_nombre")
    via_obj = item.get("via") or item.get("way") or item.get("viaObj")
    if isinstance(via_obj, dict):
        via_code = via_code or via_obj.get("code")
        via_name = via_name or via_obj.get("name")
        _agregar_via(codigos, detalle, via_obj.get("code"), via_obj.get("name"), raw=via_obj)

    # Listado de ways/vias
    ways = item.get("ways") or item.get("vias") or item.get("routesWays")
    if isinstance(ways, list):
        for w in ways:
            if not isinstance(w, dict):
                continue
            _agregar_via(codigos, detalle, w.get("code"), w.get("name"), raw=w)

    # Añadir por campos sueltos
    _agregar_via(codigos, detalle, via_code, via_name, raw=via_obj if isinstance(via_obj, dict) else None)

    if via_code:
        principal = str(via_code)
    elif codigos:
        principal = next(iter(codigos))

    return list(codigos), detalle, principal


def _vehicle_codes_para_rutas(ciudad: Optional[str], cliente_id: Optional[str]) -> list[str]:
    """
    Retorna codigos de vehiculo filtrados por ciudad/cliente para usar en travels.
    Se limita a TRAVELS_SAMPLE_VEHICLES para no exceder rate limit.
    """
    if not get_camiones:
        return []

    try:
        camiones = get_camiones() or []
    except Exception:
        return []

    ciudades_cliente = _ciudades_por_cliente(cliente_id)
    codes: list[str] = []

    for item in camiones:
        code = item.get("code") or item.get("placa")
        if not code:
            continue

        # Filtro ciudad
        city_obj = item.get("city")
        ubicacion = city_obj.get("name", "") if isinstance(city_obj, dict) else (city_obj or "")
        if ciudad and ubicacion and not _match_ciudad(ciudad, ubicacion):
            continue

        # Filtro cliente
        match_cliente = True
        if cliente_id:
            match_cliente = False
            if ciudades_cliente and ubicacion and ubicacion.lower() in ciudades_cliente:
                match_cliente = True
            customer_val = str(item.get("customerId", item.get("cliente_id", "")) or "")
            if customer_val and customer_val == str(cliente_id):
                match_cliente = True
            cost_center = item.get("costCenter")
            if cost_center:
                centro_id = str(cost_center.get("id") or cost_center.get("code") or "").strip()
                centro_nombre = (cost_center.get("name") or "").lower()
                cid = str(cliente_id).lower()
                if centro_id and cid in centro_id.lower():
                    match_cliente = True
                elif centro_nombre and cid in centro_nombre:
                    match_cliente = True
        if not match_cliente:
            continue

        codes.append(str(code))
        if TRAVELS_SAMPLE_VEHICLES and len(codes) >= TRAVELS_SAMPLE_VEHICLES:
            break

    # Si no encontramos codigos filtrando, usamos los primeros disponibles
    if not codes:
        for item in camiones[:TRAVELS_SAMPLE_VEHICLES] if TRAVELS_SAMPLE_VEHICLES else camiones:
            code = item.get("code") or item.get("placa")
            if code:
                codes.append(str(code))
    return codes


def _travels_para_rutas(
    cliente_id: Optional[str],
    ciudad: Optional[str],
    route_code: Optional[str],
    via_code: Optional[str] = None,
    route_codes: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """
    Obtiene viajes usando filtros válidos para la API (routeCode o vehicleCode).
    - Si se pasa route_code se intenta primero por ahí.
    - Luego se consulta por vehicleCode de una muestra de vehículos filtrados por ciudad/cliente.
    - Incluye un rango de fechas por defecto (últimos TRAVELS_RANGE_DAYS) en createdDate para cumplir con la API.
    """
    travels: list[dict[str, Any]] = []
    start_time = time.time()
    hoy = datetime.utcnow()
    desde = hoy - timedelta(days=TRAVELS_RANGE_DAYS)
    date_from = desde.isoformat(timespec="seconds") + "Z"
    date_to = hoy.isoformat(timespec="seconds") + "Z"

    candidate_route_codes = [rc for rc in (route_codes or [route_code]) if rc]

    # Intento directo por routeCode (probando variantes)
    for rc in candidate_route_codes:
        try:
            travels = get_travels(
                customer_id=str(cliente_id) if cliente_id else None,
                route_code=rc,
                via_code=via_code,
                created_from=date_from,
                created_to=date_to,
                max_pages=TRAVELS_MAX_PAGES,
            ) or []
            if travels:
                break
        except Exception:
            travels = []

    # Por vehicleCode
    if not travels:
        codes = _vehicle_codes_para_rutas(ciudad, cliente_id)
        if not codes:
            return []
        route_filter = candidate_route_codes[0] if candidate_route_codes else None
        for code in codes:
            if TRAVELS_FALLBACK_MAX_SECONDS and (time.time() - start_time) > TRAVELS_FALLBACK_MAX_SECONDS:
                break
            try:
                data = get_travels(
                    customer_id=str(cliente_id) if cliente_id else None,
                    vehicle_code=code,
                    route_code=route_filter,
                    via_code=via_code,
                    created_from=date_from,
                    created_to=date_to,
                    max_pages=TRAVELS_MAX_PAGES,
                ) or []
                travels.extend(data)
            except ValueError:
                # sin filtros válidos, continuar con el siguiente code
                continue
            except Exception:
                continue

    return travels


def _rutas_desde_travels(
    cliente_id: Optional[str],
    ciudad: Optional[str] = None,
    route_code: Optional[str] = None,
    route_codes: Optional[list[str]] = None,
    vehicle_codes: Optional[list[str]] = None,
    via_code: Optional[str] = None,
    route_prefix: Optional[str] = None,
) -> list[Ruta]:
    """
    Fallback para construir rutas a partir de los viajes (travels) cuando
    /routes no devuelve datos. Usa routeCode como codigo, y origin/destination.
    """
    if not get_travels:
        return []

    travels: list[dict[str, Any]] = _travels_para_rutas(
        cliente_id,
        ciudad,
        route_code,
        via_code=via_code,
        route_codes=route_codes,
    )

    rutas_map: dict[tuple[str, str, str], Ruta] = {}
    for t in travels or []:
        codigo = (
            t.get("routeCode")
            or t.get("code")
            or t.get("route", {}).get("code")
            or "SIN-COD"
        )
        nombre = t.get("route", {}).get("name") or codigo
        origen_val = _parse_location(t.get("origin"))
        destino_val = _parse_location(t.get("destination"))
        travel_city_obj = t.get("city")
        travel_city = travel_city_obj.get("name") if isinstance(travel_city_obj, dict) else travel_city_obj
        vias_codigos, vias_detalle, via_codigo = _vias_desde_item(t)

        # No filtramos por prefijo de ruta para no descartar coincidencias válidas

        # Filtrar por ciudad si se especifica (coincide en origen o destino)
        if ciudad:
            match_city = False
            if _match_ciudad(ciudad, origen_val) or _match_ciudad(ciudad, destino_val):
                match_city = True
            if not match_city and travel_city and _match_ciudad(ciudad, travel_city):
                match_city = True
            if not match_city:
                continue

        if via_code and via_codigo and via_code.lower() != str(via_codigo).lower():
            continue

        # evitar duplicar rutas por numero de viaje
        key = (codigo, origen_val, destino_val)
        existente = rutas_map.get(key)
        if existente:
            if via_codigo and via_codigo not in existente.vias:
                existente.vias.append(via_codigo)
            for vc in vias_codigos:
                if vc and vc not in existente.vias:
                    existente.vias.append(vc)
            if via_codigo and not existente.via_codigo:
                existente.via_codigo = via_codigo
            for vd in vias_detalle:
                code = vd.get("code")
                name = vd.get("name")
                dup = any(
                    (code and code == d.get("code"))
                    or (name and name == d.get("name"))
                    for d in existente.vias_detalle
                )
                if not dup:
                    existente.vias_detalle.append(vd)
            continue

        rutas_map[key] = Ruta(
            id=str(t.get("number") or "-".join(key)),
            cliente_id=str(cliente_id or t.get("customerId") or ""),
            sede_id=None,
            codigo=codigo,
            nombre=nombre,
            origen=origen_val,
            destino=destino_val,
            distancia_km=None,
            activa=not t.get("isFinished", False),
            via_codigo=via_codigo,
            vias=[c for c in vias_codigos if c] or ([via_codigo] if via_codigo else []),
            vias_detalle=vias_detalle,
            datos_adicionales=t,
        )
    return list(rutas_map.values())


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
    try:
        if not get_clientes:
            raise RuntimeError("CloudFleet API no configurada")

        data = get_clientes() or []
        clientes: list[Cliente] = []
        for item in data:
            clientes.append(Cliente(
                id=str(item.get("id", "")),
                nombre=item.get("name", item.get("nombre", "Sin nombre")),
                contacto=item.get("contact", item.get("contacto")),
                telefono=item.get("phone", item.get("telefono")),
                email=item.get("email"),
                datos_adicionales=item
            ))

        if clientes:
            return clientes

        clientes_fallback = _clientes_desde_camiones()
        if clientes_fallback:
            return clientes_fallback

        return clientes
    except Exception as e:
        clientes_fallback = _clientes_desde_camiones()
        if clientes_fallback:
            return clientes_fallback
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
            codigo = (
                item.get("code")
                or item.get("routeCode")
                or item.get("codigo")
                or "SIN-COD"
            )
            origen = _parse_location(item.get("origin", item.get("origen")))
            destino = _parse_location(item.get("destination", item.get("destino")))
            # Filtrar por ciudad de la sede si aplica
            if sede.ciudad:
                if not (_match_ciudad(sede.ciudad, origen) or _match_ciudad(sede.ciudad, destino)):
                    continue
            rutas.append(Ruta(
                id=str(item.get("id", "")),
                cliente_id=sede.cliente_id,
                sede_id=sede_id,
                codigo=codigo,
                nombre=item.get("name", item.get("nombre", codigo)),
                origen=origen,
                destino=destino,
                distancia_km=item.get("distance", item.get("distancia_km")),
                activa=item.get("active", item.get("activa", True)),
                datos_adicionales=item
            ))
        if not rutas and sede.ciudad:
            rutas = _rutas_desde_travels(sede.cliente_id, sede.ciudad, route_code=None)

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
def listar_rutas(
    cliente_id: Optional[str] = Query(None, description="ID del cliente para filtrar"),
    ciudad: Optional[str] = Query(None, description="Ciudad para filtrar por origen/destino"),
    route_code: Optional[str] = Query(None, description="Codigo de ruta para filtrar"),
    via_code: Optional[str] = Query(None, description="Codigo de via para filtrar"),
):
    """
    Obtiene rutas usando /routes y complementa con /travels.
    Filtra opcionalmente por cliente, ciudad y route_code.
    """
    try:
        rutas: list[Ruta] = []
        route_codes = _route_codes_candidates(cliente_id, ciudad, route_code)
        primary_route_code = route_codes[0] if route_codes else None

        # Intentar /routes si est? disponible
        if get_rutas:
            try:
                rutas_data = get_rutas(cliente_id) or []
                for item in rutas_data:
                    codigo = (
                        item.get("code")
                        or item.get("routeCode")
                        or item.get("codigo")
                        or "SIN-COD"
                    )
                    if primary_route_code and primary_route_code.lower() not in codigo.lower():
                        continue
                    origen = _parse_location(item.get("origin", item.get("origen")))
                    destino = _parse_location(item.get("destination", item.get("destino")))
                    if ciudad and not (_match_ciudad(ciudad, origen) or _match_ciudad(ciudad, destino)):
                        continue
                    vias_codigos, vias_detalle, via_codigo = _vias_desde_item(item)
                    rutas.append(Ruta(
                        id=str(item.get("id", "")),
                        cliente_id=str(item.get("customerId", item.get("cliente_id", ""))),
                        sede_id=str(item.get("locationId", item.get("sede_id", ""))),
                        codigo=codigo,
                        nombre=item.get("name", item.get("nombre", codigo)),
                        origen=origen,
                        destino=destino,
                        distancia_km=item.get("distance", item.get("distancia_km")),
                        activa=item.get("active", item.get("activa", True)),
                        via_codigo=via_codigo,
                        vias=vias_codigos,
                        vias_detalle=vias_detalle,
                        datos_adicionales=item
                    ))
            except Exception:
                pass

        # Complementar con travels (usa vehicleCode/routeCode que la API s? acepta)
        rutas_travels = _rutas_desde_travels(
            cliente_id,
            ciudad,
            route_code=primary_route_code,
            route_codes=route_codes,
            via_code=via_code,
        )
        rutas_map: dict[tuple[str, str, str], Ruta] = {(r.codigo, r.origen, r.destino): r for r in rutas}
        for r in rutas_travels:
            key = (r.codigo, r.origen, r.destino)
            existente = rutas_map.get(key)
            if existente:
                if r.via_codigo and not existente.via_codigo:
                    existente.via_codigo = r.via_codigo
                for vc in r.vias:
                    if vc and vc not in existente.vias:
                        existente.vias.append(vc)
                for vd in r.vias_detalle:
                    code = vd.get("code")
                    name = vd.get("name")
                    dup = any(
                        (code and code == d.get("code"))
                        or (name and name == d.get("name"))
                        for d in existente.vias_detalle
                    )
                    if not dup:
                        existente.vias_detalle.append(vd)
                continue
            rutas_map[key] = r

        return list(rutas_map.values())
    except Exception as e:
        logger.error("Error al obtener rutas: %s", e)
        # Evitar romper el front: devolver lista vacía
        return []
@app.get("/rutas/{ruta_id}", response_model=Ruta)
def obtener_ruta(ruta_id: str):
    """
    Obtiene una ruta especifica por ID
    """
    if not get_ruta:
        raise HTTPException(status_code=503, detail="CloudFleet API no configurada")
    
    try:
        item = get_ruta(ruta_id)
        codigo = (
            item.get("code")
            or item.get("routeCode")
            or item.get("codigo")
            or "SIN-COD"
        )
        origen = _parse_location(item.get("origin", item.get("origen")))
        destino = _parse_location(item.get("destination", item.get("destino")))
        return Ruta(
            id=str(item.get("id", ruta_id)),
            cliente_id=str(item.get("customerId", item.get("cliente_id", ""))),
            sede_id=str(item.get("locationId", item.get("sede_id", ""))),
            codigo=codigo,
            nombre=item.get("name", item.get("nombre", codigo)),
            origen=origen,
            destino=destino,
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
                # Si el vehiculo trae customerId, intentamos comparar directo
                if not match_cliente:
                    customer_val = str(item.get("customerId", item.get("cliente_id", "")) or "")
                    if customer_val:
                        match_cliente = customer_val == str(cliente_id)
                # Fallback: usar centro de costo como proxy de cliente
                if not match_cliente and cost_center:
                    centro_id = str(cost_center.get("id") or cost_center.get("code") or "").strip()
                    centro_nombre = (cost_center.get("name") or "").lower()
                    cid = str(cliente_id).lower()
                    if centro_id and cid in centro_id.lower():
                        match_cliente = True
                    elif centro_nombre and cid in centro_nombre:
                        match_cliente = True
                # Si no hay forma de saber, no descartamos
                if not match_cliente and not (ciudades_cliente or item.get("customerId") or cost_center):
                    match_cliente = True
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
        # Si hay filtros, limitamos paginas para reducir latencia
        max_pages = 0
        if ciudad or cliente_id or rol:
            max_pages = int(os.getenv("PERSONAL_MAX_PAGES_FILTER", "10"))
        if max_pages:
            # Volver a obtener con limite (requiere soporte de max_pages en cliente)
            try:
                personal_data = get_personas(max_pages=max_pages)  # type: ignore[arg-type]
            except TypeError:
                # Si la firma no acepta max_pages, continuamos con el resultado actual
                personal_data = personal_data
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
                # No hay customerId en personas; si no hay pistas, evitamos descartar todo
                if not match_cliente and not ciudades_cliente and not item.get("customerId"):
                    match_cliente = True
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
