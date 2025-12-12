from datetime import datetime

# Estructura: (CLIENTE, SEDE) -> [Lun, Mar, Mie, Jue, Vie, Sab, Dom]
# 0 significa que no hay regla fija (o omitir)
QUOTA_MATRIX = {
    ("CCM LINDE", "BARRANQUILLA"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM LINDE", "BOGOTA"): [7, 7, 7, 7, 7, 7, 3],
    ("CCM LINDE", "CARTAGENA"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM LINDE", "IBAGUE"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM LINDE", "MEDELLIN"): [7, 7, 7, 7, 7, 7, 1],
    ("CCM LINDE", "PEREIRA"): [4, 4, 4, 4, 4, 4, 0],
    ("CCM LINDE", "POPAYAN"): [0, 0, 0, 0, 0, 0, 0],
    ("CCM LINDE", "SOGAMOSO"): [0, 0, 0, 0, 0, 0, 0],
    ("CCM LINDE", "TOCANCIPA"): [5, 5, 5, 5, 5, 5, 0],
    ("CCM LINDE", "YUMBO"): [5, 5, 5, 5, 5, 5, 0],

    # Alias CCM PRAXAIR -> CCM LINDE
    ("CCM PRAXAIR", "BARRANQUILLA"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM PRAXAIR", "BOGOTA"): [7, 7, 7, 7, 7, 7, 3],
    ("CCM PRAXAIR", "CARTAGENA"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM PRAXAIR", "IBAGUE"): [2, 2, 2, 2, 2, 2, 0],
    ("CCM PRAXAIR", "MEDELLIN"): [7, 7, 7, 7, 7, 7, 1],
    ("CCM PRAXAIR", "PEREIRA"): [4, 4, 4, 4, 4, 4, 0],
    ("CCM PRAXAIR", "POPAYAN"): [0, 0, 0, 0, 0, 0, 0],
    ("CCM PRAXAIR", "SOGAMOSO"): [0, 0, 0, 0, 0, 0, 0],
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
        
        # Normalizacion simple para busqueda
        c_key = cliente_nombre.upper().strip()
        s_key = sede_nombre.upper().strip()
        
        # Busqueda exacta primero
        rule = QUOTA_MATRIX.get((c_key, s_key))
        
        # Búsqueda parcial si no hay exacta (ej: "CCM LINDE SAS" -> "CCM LINDE")
        if not rule:
            for (k_cli, k_sede), v_rule in QUOTA_MATRIX.items():
                if k_cli in c_key and k_sede in s_key:
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
        
    c_key = cliente_nombre.upper().strip()
    sedes = set()
    
    # Busqueda exacta y parcial
    for (k_cli, k_sede) in QUOTA_MATRIX.keys():
        if k_cli in c_key:
            sedes.add(k_sede)
            
    return sorted(list(sedes))
