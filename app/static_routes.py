
# Definicion estatica de rutas y vias activas para cuando la API falla o faltan datos historicos
# Formato: { "CIUDAD_CLAVE": [ Lista de Rutas ] }

# Vias comunes para reutilizar
VIAS_PRUEBA = [
    {"code": "Directo", "name": "Directo", "distance": 10, "active": True},
    {"code": "AA00", "name": "AA00", "distance": 10, "active": True},
    {"code": "AA01", "name": "AA01", "distance": 23, "active": True},
    {"code": "RG01", "name": "RG01", "distance": 5, "active": True},
]

STATIC_ROUTES_DB = {
    "YUMBO": [
        {
            "code": "PRU-PRU",
            "name": "Ruta Prueba Estática",
            "origin": "YUMBO",
            "destination": "YUMBO",
            "distance": 10,
            "vias_detalle": VIAS_PRUEBA,
            "vias": ["Directo", "AA00", "AA01", "RG01"],
            "active": True
        }
    ],
    # Se pueden agregar mas ciudades aqui
}

def get_static_routes_by_city(city_name: str):
    if not city_name:
        return []
    
    city_key = city_name.upper()
    # Busqueda exacta o check parcial
    results = []
    
    # 1. Match directo
    if city_key in STATIC_ROUTES_DB:
        results.extend(STATIC_ROUTES_DB[city_key])
        
    return results
