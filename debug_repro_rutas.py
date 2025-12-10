import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Ajustar path para importar app
sys.path.append(os.getcwd())

from app.cloudfleet import get_clientes, get_rutas, get_travels
from app.main import _match_ciudad, _parse_location, listar_rutas_v2

def run_debug():
    print("=== DEBUG RUTAS FIX VERIFICATION ===")
    
    # Force Client ID "1" (CCM PRAXAIR fallback)
    client_id = "1" 
    print(f"Usando Cliente ID Fijo: {client_id} (CCM PRAXAIR)")

    # Call the ACTUAL app function to test the fix in main.py
    print(f"\n--- Probando listar_rutas_v2(cliente_id={client_id}) ---")
    try:
        # Simulate request filters: Client=1, City=BOGOTA (example) or TOCANCIPA
        rutas_app = listar_rutas_v2(
            cliente_id=client_id,
            ciudad="TOCANCIPA"
        )
        print(f"Total rutas retornadas por APP: {len(rutas_app)}")
        
        matches = 0
        for r in rutas_app:
            print(f"  [RESULT] {r.codigo} | {r.nombre} | Origen: {r.origen} | Destino: {r.destino}")
            matches += 1
            if matches >= 5:
                print("  ... (mas rutas omitidas)")
                break
                
    except Exception as e:
        print(f"ERROR APP: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        run_debug()
    except Exception as e:
        print(f"CRASH: {e}")
