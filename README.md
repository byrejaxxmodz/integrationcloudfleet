# CloudFleet Manager API

API completa para gestión de clientes, sedes, rutas, vehículos y personal integrada con CloudFleet.

## 🚀 Características

- **Gestión de Clientes**: Consulta clientes con todas sus sedes
- **Gestión de Sedes**: Obtén información detallada de cada sede incluyendo:
  - Vehículos asignados a la sede
  - Personal (conductores y auxiliares) en la sede
  - Rutas diarias asociadas
- **Gestión de Rutas**: Consulta rutas por cliente o sede
- **Gestión de Vehículos**: Filtra vehículos por sede o ciudad
- **Gestión de Personal**: Filtra personal por sede, ciudad o rol
- **Resumen Operacional**: Vista consolidada de toda la operación de un cliente

## 📋 Requisitos Previos

- Python 3.10 o superior
- MySQL 5.7 o superior (opcional, para base de datos local)
- Cuenta de CloudFleet con API Token

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Configuración de CloudFleet API
CLOUDFLEET_API_URL=https://fleet.cloudfleet.com/api/v1
CLOUDFLEET_API_TOKEN=tu_token_aqui

# Parámetros de negocio
MAX_DIAS_CONSECUTIVOS=6
FORCE_CLOUDFLEET=false
TARGET_PLACA=FKL 92H
TARGET_CONDUCTOR_DOC=1143865250

# Base de datos (opcional)
DB_HOST=mysql
DB_NAME=cloudfleet
DB_USER=mysql
DB_PASS=mysql
```

### 2. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### 3. Iniciar la API

```bash
# Desde la raíz del proyecto
python -m app.main

# O con uvicorn directamente
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación de Endpoints

### Página Principal

```
GET /
```

Devuelve información de la API y lista de endpoints disponibles.

---

### 👥 Clientes

#### Listar todos los clientes

```http
GET /clientes
```

**Respuesta:**
```json
[
  {
    "id": "123",
    "nombre": "Empresa XYZ",
    "contacto": "Juan Pérez",
    "telefono": "3001234567",
    "email": "contacto@empresa.com",
    "datos_adicionales": { ... }
  }
]
```

#### Obtener cliente completo con sedes

```http
GET /clientes/{cliente_id}
```

**Ejemplo:** `GET /clientes/123`

**Respuesta:**
```json
{
  "cliente": {
    "id": "123",
    "nombre": "Empresa XYZ",
    "contacto": "Juan Pérez",
    "telefono": "3001234567",
    "email": "contacto@empresa.com"
  },
  "sedes": [
    {
      "id": "456",
      "cliente_id": "123",
      "nombre": "Sede Bogotá",
      "ciudad": "Bogotá",
      "direccion": "Calle 123 #45-67",
      "telefono": "6012345678"
    }
  ],
  "total_sedes": 1
}
```

#### Resumen operacional de un cliente

```http
GET /clientes/{cliente_id}/resumen
```

**Ejemplo:** `GET /clientes/123/resumen`

**Respuesta:**
```json
{
  "cliente_id": "123",
  "cliente_nombre": "Empresa XYZ",
  "total_sedes": 3,
  "total_vehiculos": 15,
  "total_conductores": 12,
  "total_auxiliares": 18,
  "total_rutas": 25,
  "vehiculos_activos": 14,
  "personal_activo": 28
}
```

---

### 🏢 Sedes

#### Listar todas las sedes

```http
GET /sedes?cliente_id={cliente_id}
```

**Parámetros opcionales:**
- `cliente_id`: Filtrar sedes por cliente

**Ejemplo:** `GET /sedes?cliente_id=123`

**Respuesta:**
```json
[
  {
    "id": "456",
    "cliente_id": "123",
    "nombre": "Sede Bogotá",
    "ciudad": "Bogotá",
    "direccion": "Calle 123 #45-67",
    "telefono": "6012345678"
  }
]
```

#### Obtener sede completa con vehículos, personal y rutas

```http
GET /sedes/{sede_id}
```

**Ejemplo:** `GET /sedes/456`

**Respuesta:**
```json
{
  "sede": {
    "id": "456",
    "cliente_id": "123",
    "nombre": "Sede Bogotá",
    "ciudad": "Bogotá",
    "direccion": "Calle 123 #45-67"
  },
  "vehiculos": [
    {
      "id": "789",
      "sede_id": "456",
      "placa": "ABC123",
      "tipo": "Camión",
      "capacidad": 5000,
      "ubicacion_ciudad": "Bogotá",
      "activo": true
    }
  ],
  "personal": [
    {
      "id": "101",
      "sede_id": "456",
      "nombre": "Carlos López",
      "rol": "conductor",
      "documento": "1234567890",
      "telefono": "3001234567",
      "ubicacion_ciudad": "Bogotá",
      "activo": true
    }
  ],
  "rutas": [
    {
      "id": "111",
      "cliente_id": "123",
      "sede_id": "456",
      "codigo": "RG01",
      "nombre": "Ruta Norte",
      "origen": "Bogotá",
      "destino": "Chía",
      "distancia_km": 25.5,
      "activa": true
    }
  ],
  "total_vehiculos": 5,
  "total_personal": 8,
  "total_rutas": 12
}
```

---

### 🛣️ Rutas

#### Listar todas las rutas

```http
GET /rutas?cliente_id={cliente_id}
```

**Parámetros opcionales:**
- `cliente_id`: Filtrar rutas por cliente

**Ejemplo:** `GET /rutas?cliente_id=123`

**Respuesta:**
```json
[
  {
    "id": "111",
    "cliente_id": "123",
    "sede_id": "456",
    "codigo": "RG01",
    "nombre": "Ruta Norte",
    "origen": "Bogotá",
    "destino": "Chía",
    "distancia_km": 25.5,
    "activa": true
  }
]
```

#### Obtener una ruta específica

```http
GET /rutas/{ruta_id}
```

**Ejemplo:** `GET /rutas/111`

---

### 🚚 Vehículos

#### Listar todos los vehículos

```http
GET /vehiculos?sede_id={sede_id}&ciudad={ciudad}
```

**Parámetros opcionales:**
- `sede_id`: Filtrar vehículos por sede
- `ciudad`: Filtrar vehículos por ciudad

**Ejemplo:** `GET /vehiculos?ciudad=Bogotá`

**Respuesta:**
```json
[
  {
    "id": "789",
    "sede_id": "456",
    "placa": "ABC123",
    "tipo": "Camión",
    "capacidad": 5000,
    "ubicacion_ciudad": "Bogotá",
    "activo": true,
    "datos_adicionales": { ... }
  }
]
```

---

### 👷 Personal

#### Listar todo el personal

```http
GET /personal?sede_id={sede_id}&ciudad={ciudad}&rol={rol}
```

**Parámetros opcionales:**
- `sede_id`: Filtrar personal por sede
- `ciudad`: Filtrar personal por ciudad
- `rol`: Filtrar por rol (`conductor` o `auxiliar`)

**Ejemplo:** `GET /personal?ciudad=Bogotá&rol=conductor`

**Respuesta:**
```json
[
  {
    "id": "101",
    "sede_id": "456",
    "nombre": "Carlos López",
    "rol": "conductor",
    "documento": "1234567890",
    "telefono": "3001234567",
    "ubicacion_ciudad": "Bogotá",
    "activo": true,
    "datos_adicionales": { ... }
  }
]
```

---

### 📅 Programación de Viajes (Legacy)

#### Programar asignaciones

```http
POST /schedule
```

**Body:**
```json
{
  "fecha": "2025-12-03",
  "cliente_id": 123,
  "sede_id": 456
}
```

**Respuesta:**
```json
[
  {
    "ruta_id": 1,
    "vehiculo_id": 789,
    "conductor_id": 101,
    "auxiliar_id": 102,
    "notas": "Asignación automática 2025-12-03"
  }
]
```

---

## 📖 Documentación Interactiva

Una vez iniciada la API, puedes acceder a la documentación interactiva en:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 Estructura del Proyecto

```
CLOUDFLEET/
├── app/
│   ├── __init__.py
│   ├── cloudfleet.py       # Cliente para API de CloudFleet
│   └── main.py             # API FastAPI principal
├── includes/
│   ├── config.php
│   └── db.php
├── public/
│   ├── crear_viaje.php
│   └── viajes.php
├── services/
│   └── scheduler_api.php
├── schema.sql              # Esquema de base de datos
├── requirements.txt        # Dependencias Python
├── Dockerfile
└── README.md              # Este archivo
```

## 🎯 Casos de Uso Comunes

### 1. Obtener todos los datos de un cliente

```bash
# 1. Obtener cliente con sus sedes
curl http://localhost:8000/clientes/123

# 2. Obtener el resumen operacional
curl http://localhost:8000/clientes/123/resumen
```

### 2. Consultar información de una sede específica

```bash
# Obtener sede completa con vehículos, personal y rutas
curl http://localhost:8000/sedes/456
```

### 3. Filtrar vehículos por ciudad

```bash
# Obtener vehículos en Bogotá
curl http://localhost:8000/vehiculos?ciudad=Bogotá
```

### 4. Obtener conductores de una ciudad

```bash
# Obtener solo conductores en Medellín
curl http://localhost:8000/personal?ciudad=Medellín&rol=conductor
```

## 🐛 Solución de Problemas

### Error: "CloudFleet API no configurada"

**Solución:** Verifica que hayas configurado las variables de entorno `CLOUDFLEET_API_URL` y `CLOUDFLEET_API_TOKEN`.

### Error: "Faltan CLOUDFLEET_API_URL o CLOUDFLEET_API_TOKEN"

**Solución:** Asegúrate de que tu archivo `.env` esté en la raíz del proyecto o que las variables estén exportadas en tu sistema.

### Los vehículos/personal no aparecen en la sede

**Solución:** La API filtra por ciudad. Verifica que la ciudad de la sede coincida con la ubicación de los vehículos/personal en CloudFleet.

## 📝 Notas Importantes

1. **Filtrado por ubicación**: Los vehículos y personal se asignan a sedes basándose en la coincidencia de ciudades.

2. **Datos adicionales**: Cada modelo incluye un campo `datos_adicionales` con toda la respuesta original de CloudFleet.

3. **IDs como strings**: Todos los IDs se manejan como strings para compatibilidad con diferentes sistemas.

4. **Endpoints de documentación**: Visita `/docs` para ver la documentación interactiva completa con Swagger UI.

## 🤝 Contribuir

Para contribuir al proyecto:

1. Realiza un fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y está bajo la licencia de la organización.

## 📧 Contacto

Para soporte o consultas, contacta al equipo de desarrollo.
