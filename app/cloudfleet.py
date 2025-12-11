"""
Cliente base para consumir Cloudfleet.
Completa CLOUDFLEET_API_URL y CLOUDFLEET_API_TOKEN antes de usar.
Incluye manejo basico de 404 y 429 para no romper la UI.
"""
import os
import time
from typing import Any
from datetime import datetime, timedelta


import requests
from requests import HTTPError
from functools import lru_cache, wraps
from urllib.parse import quote

def ttl_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper(func):
        @lru_cache(maxsize=maxsize)
        def inner(__ttl, *args, **kwargs):
            # __ttl es solo para invalidar el cache cambiando el tiempo
            return func(*args, **kwargs)
        
        @wraps(func)
        def wrapped(*args, **kwargs):
            return inner(time.time() // seconds, *args, **kwargs)
        return wrapped
    return wrapper



BASE_URL = os.getenv("CLOUDFLEET_API_URL", "https://fleet.cloudfleet.com/api/v1").rstrip("/")
TOKEN = os.getenv("CLOUDFLEET_API_TOKEN", "")
TIMEOUT = 6
PAGE_SIZE = 50  # CloudFleet API limit
# 30 req/min -> ~2s; 0.8s es un buen compromiso
RATE_LIMIT_DELAY = float(os.getenv("CLOUDFLEET_RATE_LIMIT_DELAY", "0.8"))
# 0 = sin limite, >0 limita paginas por seguridad
MAX_PAGES = int(os.getenv("CLOUDFLEET_MAX_PAGES", "0"))
# 0 = sin limite, >0 corta por ventana de tiempo
MAX_TOTAL_SECONDS = float(os.getenv("CLOUDFLEET_MAX_TOTAL_SECONDS", "0"))
# Numero maximo de reintentos ante 429
MAX_RETRIES_429 = int(os.getenv("CLOUDFLEET_MAX_RETRIES_429", "10"))


def _check_config():
    if not BASE_URL or not TOKEN:
        raise RuntimeError("Faltan CLOUDFLEET_API_URL o CLOUDFLEET_API_TOKEN")


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
    }


def _get(path: str, default_on_404: Any = None) -> Any:
    """
    GET simple con manejo opcional de 404 devolviendo default_on_404.
    """
    _check_config()
    url = f"{BASE_URL}/{path.lstrip('/')}"
    resp = requests.get(url, headers=_headers(), timeout=TIMEOUT)
    try:
        resp.raise_for_status()
    except HTTPError as exc:
        if resp.status_code == 404 and default_on_404 is not None:
            return default_on_404
        raise exc
    time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
    return resp.json()


def _get_paginated(path: str, max_pages: int | None = None) -> list[dict[str, Any]]:
    """
    Obtiene todos los registros paginados de CloudFleet API.
    Maneja 404 devolviendo lo recopilado hasta el momento y 429 con reintentos.
    Soporta respuestas tipo lista o envueltas en un objeto con campo items/data/results.
    """
    _check_config()
    all_items: list[dict[str, Any]] = []
    page = 1
    retries_429 = 0
    start_time = time.time() if MAX_TOTAL_SECONDS else None
    max_pages_effective = max_pages if max_pages is not None else MAX_PAGES

    while True:
        separator = '&' if '?' in path else '?'
        paginated_path = f"{path}{separator}page={page}&pageSize={PAGE_SIZE}"
        url = f"{BASE_URL}/{paginated_path.lstrip('/')}"

        resp = requests.get(url, headers=_headers(), timeout=TIMEOUT)
        try:
            resp.raise_for_status()
            retries_429 = 0  # reset al tener respuesta ok
        except HTTPError as exc:
            status = resp.status_code
            if status == 404:
                return all_items
            if status == 429:
                retries_429 += 1
                if retries_429 > MAX_RETRIES_429:
                    raise
                # Backoff exponencial suave para salir del penalty box (1s, 2s, 4s, 8s...)
                wait_time = (1.5 ** retries_429) + 1
                logger.warning(f"Rate limit 429 hit. Waiting {wait_time:.2f}s (Retry {retries_429}/{MAX_RETRIES_429})")
                time.sleep(wait_time)
                continue
            raise exc

        data = resp.json()

        # Si viene envuelto en un objeto de paginacion
        if isinstance(data, dict):
            items = data.get("items") or data.get("data") or data.get("results")
            if items is None:
                # Si parece un solo objeto con ID, lo devolvemos como lista de 1
                if "id" in data:
                    data = [data]
                else:
                    return [] # Si no hay items y no parece objeto, devolvemos lista vacia
            elif not isinstance(items, list):
               return []
            else:
                data = items

        if not data:
            break

        all_items.extend(data)

        if len(data) < PAGE_SIZE:
            break
        if max_pages_effective and page >= max_pages_effective:
            break

        page += 1
        time.sleep(RATE_LIMIT_DELAY)  # Rate limiting between pages

        if MAX_TOTAL_SECONDS and start_time and (time.time() - start_time) > MAX_TOTAL_SECONDS:
            break

    return all_items


def get_camiones(code: str | None = None, customer_id: str | None = None, max_pages: int | None = None) -> list[dict[str, Any]]:
    """
    Obtiene listado completo de vehiculos con paginacion automatica.
    Para filtrar por codigo, usa code=ABC123.
    Endpoint base de Cloudfleet: /vehicles/?code={vehicle-code}
    """
    path = "vehicles/"
    params = []
    if code:
        params.append(f"code={code}")
    if customer_id:
        params.append(f"customerId={customer_id}")
    
    if params:
        path += "?" + "&".join(params)
        
    # Si buscamos por codigo especifico, retornamos todo (no deberia ser mucho).
    # Si es listado general, respetamos max_pages.
    return _get_paginated(path, max_pages=max_pages if not code else None)


def get_camion_por_codigo(code: str) -> dict[str, Any]:
    """Atajo para un solo vehiculo por codigo."""
    data = get_camiones(code=code)
    if isinstance(data, list) and data:
        return data[0]
    return data


def get_conductores() -> list[dict[str, Any]]:
    """Alias para obtener personas y filtrar rol si corresponde."""
    return get_personas()


def get_clientes() -> list[dict[str, Any]]:
    """
    Obtiene listado de clientes.
    Endpoint: /customers/
    """
    return _get_paginated("customers")


@ttl_lru_cache(seconds=300)
def get_cliente(cliente_id: str) -> dict[str, Any]:
    """
    Obtiene un cliente especifico por ID.
    Endpoint: /customers/{customerId}
    """
    return _get(f"customers/{cliente_id}")


@ttl_lru_cache(seconds=300)
def get_sedes(cliente_id: str | None = None) -> list[dict[str, Any]]:
    """
    Obtiene listado de sedes/ubicaciones.
    Si se proporciona customer_id, filtra por cliente.
    Endpoint: /locations/ o /locations/?customerId={customerId}
    """
    path = f"locations?customerId={quote(str(cliente_id))}" if cliente_id else "locations"
    # Si no hay cliente_id, locations puede devolver 404 si no es superuser o similar,
    # manejamos devolviendo vacio
    try:
        return _get_paginated(path)
    except Exception as e:
        # Si falla (404, 400, etc), devolvemos lista vacia para no romper flujo
        return []


@ttl_lru_cache(seconds=300)
def get_sede(sede_id: str) -> dict[str, Any]:
    """
    Obtiene una sede especifica por ID.
    Endpoint: /locations/{locationId}
    """
    return _get(f"locations/{sede_id}")


@ttl_lru_cache(seconds=300)
def get_rutas() -> list[dict[str, Any]]:
    """
    Obtiene listado de rutas.
    Si se proporciona customer_id, filtra por cliente.
    Endpoint: /routes or /routes?customerId={customerId}
    """
    return _get_paginated("routes")


@ttl_lru_cache(seconds=300)
def get_ruta(ruta_id: str) -> dict[str, Any]:
    """
    Obtiene una ruta especifica por ID.
    Endpoint: /routes/{routeId}
    """
    return _get(f"routes/{route_id}")


def get_travel(travel_number: str) -> dict[str, Any]:
    """
    Obtiene un viaje por numero de viaje.
    Endpoint: /travels/{travelNumber}
    """
    return _get(f"travels/{travel_number}")


def get_travels(
    customer_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    departure_from: str | None = None,
    departure_to: str | None = None,
    finished_from: str | None = None,
    finished_to: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    system_finished_from: str | None = None,
    system_finished_to: str | None = None,
    vehicle_code: str | None = None,
    route_code: str | None = None,
    via_code: str | None = None,
    travel_number: str | None = None,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    """
    Obtiene listado de viajes.
    CloudFleet exige al menos un filtro y rango de fechas no mayor a 2 meses.
    """
    if not (travel_number or vehicle_code or route_code or customer_id or start_date or end_date or departure_from or departure_to or finished_from or finished_to or created_from or created_to or system_finished_from or system_finished_to):
        raise ValueError("CloudFleet /travels requiere al menos un filtro")

    # Validar rango max de 62 días en departure/finished/system_finished/created si se proveen
    def _check_range(fro: str | None, to: str | None, label: str):
        if not fro or not to:
            return
        try:
            df_dt = datetime.fromisoformat(fro.replace("Z", "+00:00"))
            dt_dt = datetime.fromisoformat(to.replace("Z", "+00:00"))
            if (dt_dt - df_dt) > timedelta(days=62):
                raise ValueError(f"El rango {label} no debe superar 2 meses")
        except Exception:
            # si formato invalido, dejamos que la API responda
            return

    _check_range(departure_from or start_date, departure_to or end_date, "departure")
    _check_range(finished_from, finished_to, "finished")
    _check_range(created_from, created_to, "created")
    _check_range(system_finished_from, system_finished_to, "systemFinished")

    path = "travels/"
    params = []
    if customer_id:
        params.append(f"customerId={customer_id}")
    if start_date:
        params.append(f"startDate={start_date}")
    if end_date:
        params.append(f"endDate={end_date}")
    if departure_from:
        params.append(f"departureDateFrom={departure_from}")
    if departure_to:
        params.append(f"departureDateTo={departure_to}")
    if finished_from:
        params.append(f"finishedDateFrom={finished_from}")
    if finished_to:
        params.append(f"finishedDateTo={finished_to}")
    if created_from:
        params.append(f"createdDateFrom={created_from}")
    if created_to:
        params.append(f"createdDateTo={created_to}")
    if system_finished_from:
        params.append(f"systemFinishedDateFrom={system_finished_from}")
    if system_finished_to:
        params.append(f"systemFinishedDateTo={system_finished_to}")
    if vehicle_code:
        params.append(f"vehicleCode={vehicle_code}")
    if route_code:
        params.append(f"routeCode={route_code}")
    if via_code:
        params.append(f"viaCode={via_code}")
    if travel_number:
        params.append(f"number={travel_number}")
    if params:
        path += "?" + "&".join(params)
    return _get_paginated(path, max_pages=max_pages)


def get_personas(max_pages: int | None = None) -> list[dict[str, Any]]:
    """
    Obtiene listado completo de personas con paginacion automatica.
    Endpoint: /people/
    """
    return _get_paginated("people/", max_pages=max_pages)


def get_persona(person_id: str) -> dict[str, Any]:
    """
    Obtiene una persona especifica por ID.
    Endpoint: /people/{personId}
    """
    return _get(f"people/{person_id}")
