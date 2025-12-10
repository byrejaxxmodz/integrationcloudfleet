import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

sys.path.append(os.getcwd())

from app.main import listar_clientes

def debug_app_clients():
    print("=== DEBUG APP CLIENTS (with fallback) ===")
    try:
        clientes = listar_clientes()
        print(f"Total clientes: {len(clientes)}")
        for c in clientes:
            print(f"ID: {c.id} | Nombre: {c.nombre} | Source: {'API' if '-' in c.id and len(c.id)>10 else 'FALLBACK/Vehicle'}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_app_clients()
