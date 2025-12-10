
import json
from app.cloudfleet import get_clientes

def list_clients():
    try:
        clientes = get_clientes() or []
        with open("clients_list.txt", "w", encoding="utf-8") as f:
            for c in clientes:
                line = f"ID: {c.get('id')} NAME: {c.get('nombre') or c.get('name')}\n"
                f.write(line)
        print("Clients written to clients_list.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_clients()
