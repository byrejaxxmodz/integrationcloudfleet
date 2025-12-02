"""
Cliente base para consumir Cloudfleet.
Completa CLOUDFLEET_API_URL y CLOUDFLEET_API_TOKEN antes de usar.
"""
import os
import time
from typing import Any
import requests


BASE_URL = os.getenv("CLOUDFLEET_API_URL", "https://fleet.cloudfleet.com/api/v1").rstrip("/")
TOKEN = os.getenv("CLOUDFLEET_API_TOKEN", "")
TIMEOUT = 10
PAGE_SIZE = 50  # CloudFleet API limit
RATE_LIMIT_DELAY = 2.0  # Seconds between requests to stay under 30 req/min


def _check_config():
    if not BASE_URL or not TOKEN:
        raise RuntimeError("Faltan CLOUDFLEET_API_URL o CLOUDFLEET_API_TOKEN")


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
    }


def _get(path: str) -> Any:
    _check_config()
    url = f"{BASE_URL}/{path.lstrip('/')}"
    resp = requests.get(url, headers=_headers(), timeout=TIMEOUT)
    resp.raise_for_status()
    time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
    return resp.json()


def _get_paginated(path: str) -> list[dict[str, Any]]:
    """
    Obtiene todos los registros paginados de CloudFleet API.
    La API retorna máximo 50 items por página.
    """
    _check_config()
    all_items = []
    page = 1
    
    while True:
        separator = '&' if '?' in path else '?'
        paginated_path = f"{path}{separator}page={page}&pageSize={PAGE_SIZE}"
        
        url = f"{BASE_URL}/{paginated_path.lstrip('/')}"
        resp = requests.get(url, headers=_headers(), timeout=TIMEOUT)
        resp.raise_for_status()
        
        data = resp.json()
        
        # Si no es una lista, retornar como está
        if not isinstance(data, list):
            return data
        
        # Si no hay más datos, terminar
        if not data or len(data) == 0:
            break
            
        all_items.extend(data)
        
        # Si recibimos menos de PAGE_SIZE, es la última página
        if len(data) < PAGE_SIZE:
            break
            
        page += 1
        time.sleep(RATE_LIMIT_DELAY)  # Rate limiting entre páginas
    
    return all_items


def get_camiones(code: str | None = None) -> list[dict[str, Any]]:
    """
    Obtiene listado completo de vehiculos con paginación automática.
    Para filtrar por codigo, usa code=ABC123.
    Endpoint base de Cloudfleet: /vehicles/?code={vehicle-code}
    """
    path = "vehicles/"
    if code:
        path += f"?code={code}"
        return _get(path)  # Si busca por código específico, no paginar
    return _get_paginated(path)


def get_camion_por_codigo(code: str) -> dict[str, Any]:
    """Atajo para un solo vehiculo por codigo."""
    data = get_camiones(code)
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
    return _get("customers/")


def get_cliente(customer_id: str) -> dict[str, Any]:
    """
    Obtiene un cliente específico por ID.
    Endpoint: /customers/{customerId}
    """
    return _get(f"customers/{customer_id}")


def get_sedes(customer_id: str | None = None) -> list[dict[str, Any]]:
    """
    Obtiene listado de sedes/ubicaciones.
    Si se proporciona customer_id, filtra por cliente.
    Endpoint: /locations/ o /locations/?customerId={customerId}
    """
    path = "locations/"
    if customer_id:
        path += f"?customerId={customer_id}"
    return _get(path)


def get_sede(location_id: str) -> dict[str, Any]:
    """
    Obtiene una sede específica por ID.
    Endpoint: /locations/{locationId}
    """
    return _get(f"locations/{location_id}")


def get_rutas(customer_id: str | None = None) -> list[dict[str, Any]]:
    """
    Obtiene listado de rutas.
    Si se proporciona customer_id, filtra por cliente.
    Endpoint: /routes/ o /routes/?customerId={customerId}
    """
    path = "routes/"
    if customer_id:
        path += f"?customerId={customer_id}"
    return _get(path)


def get_ruta(route_id: str) -> dict[str, Any]:
    """
    Obtiene una ruta específica por ID.
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
    end_date: str | None = None
) -> list[dict[str, Any]]:
    """
    Obtiene listado de viajes.
    Puede filtrar por cliente y rango de fechas.
    Endpoint: /travels/?customerId={customerId}&startDate={startDate}&endDate={endDate}
    """
    path = "travels/"
    params = []
    if customer_id:
        params.append(f"customerId={customer_id}")
    if start_date:
        params.append(f"startDate={start_date}")
    if end_date:
        params.append(f"endDate={end_date}")
    if params:
        path += "?" + "&".join(params)
    return _get(path)


def get_personas() -> list[dict[str, Any]]:
    """
    Obtiene listado completo de personas con paginación automática.
    Endpoint: /people/
    """
    return _get_paginated("people/")


def get_persona(person_id: str) -> dict[str, Any]:
    """
    Obtiene una persona específica por ID.
    Endpoint: /people/{personId}
    """
    return _get(f"people/{person_id}")
