from datetime import datetime
import unicodedata

def normalize_key(s):
    if not s: return ""
    # Normalize to NFD, strip accents, convert to uppercase
    return ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn').upper().strip()

# Estructura: (CLIENTE, SEDE) -> [Lun, Mar, Mie, Jue, Vie, Sab, Dom]
# 0 significa que no hay regla fija (o omitir)
QUOTA_MATRIX = {
    ("CCM LINDE", "BARRANQUILLA"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM LINDE", "BOGOTA"): [7, 7, 7, 7, 7, 7, 3],
    ("CCM LINDE", "CARTAGENA"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM LINDE", "IBAGUE"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM LINDE", "MEDELLIN"): [7, 7, 7, 7, 7, 7, 1],
    ("CCM LINDE", "PEREIRA"): [4, 4, 4, 4, 4, 4, 0],
    ("CCM LINDE", "POPAYAN"): [1, 0, 0, 0, 0, 0, 0], # Updated from Excel
    ("CCM LINDE", "SOGAMOSO"): [2, 0, 0, 0, 0, 0, 0], # Updated from Excel
    ("CCM LINDE", "TOCANCIPA"): [5, 5, 5, 5, 5, 5, 0],
    ("CCM LINDE", "YUMBO"): [5, 5, 5, 5, 5, 5, 0],

    # Alias CCM PRAXAIR -> CCM LINDE (Explicit copy to be safe, though dynamic alias handles it)
    ("CCM PRAXAIR", "BARRANQUILLA"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM PRAXAIR", "BOGOTA"): [7, 7, 7, 7, 7, 7, 3],
    ("CCM PRAXAIR", "CARTAGENA"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM PRAXAIR", "IBAGUE"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM PRAXAIR", "MEDELLIN"): [7, 7, 7, 7, 7, 7, 1],
    ("CCM PRAXAIR", "PEREIRA"): [4, 4, 4, 4, 4, 4, 0],
    ("CCM PRAXAIR", "POPAYAN"): [1, 0, 0, 0, 0, 0, 0],
    ("CCM PRAXAIR", "SOGAMOSO"): [2, 0, 0, 0, 0, 0, 0],
    ("CCM PRAXAIR", "TOCANCIPA"): [5, 5, 5, 5, 5, 5, 0],
    ("CCM PRAXAIR", "YUMBO"): [5, 5, 5, 5, 5, 5, 0],
    
    # CCM CHILCO - Asumimos 2 2 2 2 2 2 2 para Cazuca y Florencia
    ("CCM CHILCO", "CAZUCA"): [2, 2, 2, 2, 2, 2, 2],
    ("CCM CHILCO", "FLORENCIA"): [2, 2, 2, 2, 2, 2, 2],
    ("CCM CHILCO", "GIRARDOT"): [1, 1, 1, 1, 1, 1, 1],
    ("CCM CHILCO", "HISPANIA"): [1, 1, 1, 1, 1, 1, 1],
    ("CCM CHILCO", "MADRID"): [1, 1, 1, 1, 1, 1, 1],
    ("CCM CHILCO", "MARINILLA"): [2, 2, 2, 2, 2, 2, 2],
    ("CCM CHILCO", "NEIVA"): [3, 3, 3, 3, 3, 3, 3],
    ("CCM CHILCO", "YUMBO"): [1, 1, 1, 1, 1, 1, 1],

    # Alias CHILCO (nombre corto) -> CCM CHILCO
    ("CHILCO", "CAZUCA"): [2, 2, 2, 2, 2, 2, 2],
    ("CHILCO", "FLORENCIA"): [2, 2, 2, 2, 2, 2, 2],
    ("CHILCO", "GIRARDOT"): [1, 1, 1, 1, 1, 1, 1],
    ("CHILCO", "HISPANIA"): [1, 1, 1, 1, 1, 1, 1],
    ("CHILCO", "MADRID"): [1, 1, 1, 1, 1, 1, 1],
    ("CHILCO", "MARINILLA"): [2, 2, 2, 2, 2, 2, 2],
    ("CHILCO", "NEIVA"): [3, 3, 3, 3, 3, 3, 3],
    ("CHILCO", "YUMBO"): [1, 1, 1, 1, 1, 1, 1],
}

def get_quota_for_date(cliente_nombre: str, sede_nombre: str, fecha_str: str) -> int:
    """
    Retorna el cupo sugerido para un cliente, sede y fecha dados.
    Si no encuentra regla, retorna 0 (para dejar manual).
    fecha_str debe ser YYYY-MM-DD.
    """
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        day_of_week = dt.weekday() # 0=Lun, 6=Dom
        
        # Normalizacion ROBUSTA para busqueda
        c_key = normalize_key(cliente_nombre)
        s_key = normalize_key(sede_nombre)
        
        # AGGRESSIVE ALIAS: PRAXAIR IS LINDE
        if "PRAXAIR" in c_key:
            c_key = "CCM LINDE"
            
        # Busqueda exacta primero
        rule = QUOTA_MATRIX.get((c_key, s_key))
        
        # Búsqueda parcial si no hay exacta
        if not rule:
            for (k_cli, k_sede), v_rule in QUOTA_MATRIX.items():
                # Normalize matrix keys just in case (though they are upper/unaccented)
                k_c_norm = normalize_key(k_cli)
                k_s_norm = normalize_key(k_sede)

                # Check exact or partial containment
                match_c = k_c_norm in c_key or (c_key in k_c_norm)
                match_s = k_s_norm in s_key or (s_key in k_s_norm)
                
                if match_c and match_s:
                    rule = v_rule
                    break
        
        if rule:
            return rule[day_of_week]
            
    except Exception:
        pass
        
    return 0


def get_expected_sedes(cliente_nombre: str) -> list[str]:
    """
    Retorna la lista de nombres de sedes configuradas en la matriz para un cliente dado.
    """
    if not cliente_nombre:
        return []
        
    c_key = normalize_key(cliente_nombre)
    sedes = set()
    
    # Tratamiento especial alias
    if "PRAXAIR" in c_key:
        c_key = "CCM LINDE"

    # Busqueda Unidireccional:
    # Solo si el nombre del API contiene la clave (ej: "CCM LINDE SAS" contiene "CCM LINDE")
    # Para casos cortos como "CHILCO", usamos el alias explicito en la matriz.
    for (k_cli, k_sede) in QUOTA_MATRIX.keys():
        k_c_norm = normalize_key(k_cli)
        if k_c_norm in c_key or c_key in k_c_norm:
            sedes.add(k_sede)
            
    return sorted(list(sedes))
