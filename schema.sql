-- Esquema inicial de tablas para el sistema de programación de viajes
CREATE TABLE clientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  contacto VARCHAR(120),
  telefono VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE sedes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  ciudad VARCHAR(120),
  direccion VARCHAR(200),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_sedes_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id)
) ENGINE=InnoDB;

CREATE TABLE vehiculos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sede_id INT NOT NULL,
  placa VARCHAR(20) NOT NULL UNIQUE,
  tipo VARCHAR(60),
  capacidad INT,
  ubicacion_ciudad VARCHAR(120),
  activo TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_vehiculos_sede FOREIGN KEY (sede_id) REFERENCES sedes(id)
) ENGINE=InnoDB;

CREATE TABLE personas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  rol ENUM('conductor','auxiliar') NOT NULL,
  documento VARCHAR(30) UNIQUE,
  telefono VARCHAR(50),
  ubicacion_ciudad VARCHAR(120),
  activo TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE rutas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  codigo VARCHAR(50),
  nombre VARCHAR(150) NOT NULL,
  origen VARCHAR(150),
  destino VARCHAR(150),
  distancia_km DECIMAL(8,2),
  notas TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  sede_id INT NULL,
  CONSTRAINT fk_rutas_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
  CONSTRAINT fk_rutas_sede FOREIGN KEY (sede_id) REFERENCES sedes(id),
  CONSTRAINT uq_ruta_cliente_codigo UNIQUE (cliente_id, codigo)
) ENGINE=InnoDB;

CREATE TABLE vias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ruta_id INT NOT NULL,
  nombre VARCHAR(150) NOT NULL,
  tipo VARCHAR(60),
  kilometro_inicio DECIMAL(8,2),
  kilometro_fin DECIMAL(8,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_vias_ruta FOREIGN KEY (ruta_id) REFERENCES rutas(id)
) ENGINE=InnoDB;

CREATE TABLE viajes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  sede_id INT NOT NULL,
  fecha DATE NOT NULL,
  estado ENUM('borrador','confirmado','cancelado') DEFAULT 'borrador',
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_viajes_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
  CONSTRAINT fk_viajes_sede FOREIGN KEY (sede_id) REFERENCES sedes(id)
) ENGINE=InnoDB;

CREATE TABLE viaje_detalle (
  id INT AUTO_INCREMENT PRIMARY KEY,
  viaje_id INT NOT NULL,
  ruta_id INT NOT NULL,
  vehiculo_id INT NOT NULL,
  conductor_id INT NOT NULL,
  auxiliar_id INT NOT NULL,
  notas TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_detalle_viaje FOREIGN KEY (viaje_id) REFERENCES viajes(id),
  CONSTRAINT fk_detalle_ruta FOREIGN KEY (ruta_id) REFERENCES rutas(id),
  CONSTRAINT fk_detalle_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
  CONSTRAINT fk_detalle_conductor FOREIGN KEY (conductor_id) REFERENCES personas(id),
  CONSTRAINT fk_detalle_auxiliar FOREIGN KEY (auxiliar_id) REFERENCES personas(id)
) ENGINE=InnoDB;

-- Mapeo manual cliente-sede para suplir ausencia de relacion directa en Cloudfleet
CREATE TABLE cliente_sede_map (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  sede_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_map_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
  CONSTRAINT fk_map_sede FOREIGN KEY (sede_id) REFERENCES sedes(id),
  CONSTRAINT uq_cliente_sede UNIQUE (cliente_id, sede_id)
) ENGINE=InnoDB;

-- Rutas internas por cliente (RG01, RG02, etc.)
CREATE TABLE cliente_rutas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  sede_id INT NULL,
  codigo VARCHAR(50) NOT NULL,
  nombre VARCHAR(150) NOT NULL,
  activo TINYINT(1) DEFAULT 1,
  notas TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cliente_rutas_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
  CONSTRAINT fk_cliente_rutas_sede FOREIGN KEY (sede_id) REFERENCES sedes(id),
  CONSTRAINT uq_cliente_ruta_codigo UNIQUE (cliente_id, codigo)
) ENGINE=InnoDB;

-- Asignacion de personal a cliente (no solo por ciudad)
CREATE TABLE cliente_persona (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  persona_id INT NOT NULL,
  rol ENUM('conductor','auxiliar') NOT NULL,
  activo TINYINT(1) DEFAULT 1,
  ultima_asignacion DATE NULL,
  dias_consecutivos INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cliente_persona_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
  CONSTRAINT fk_cliente_persona_persona FOREIGN KEY (persona_id) REFERENCES personas(id),
  CONSTRAINT uq_cliente_persona UNIQUE (cliente_id, persona_id)
) ENGINE=InnoDB;

-- Permisos especiales por persona
CREATE TABLE persona_permiso (
  id INT AUTO_INCREMENT PRIMARY KEY,
  persona_id INT NOT NULL,
  permiso_codigo VARCHAR(80) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_permiso_persona FOREIGN KEY (persona_id) REFERENCES personas(id),
  CONSTRAINT uq_persona_permiso UNIQUE (persona_id, permiso_codigo)
) ENGINE=InnoDB;

-- Permisos requeridos por ruta
CREATE TABLE ruta_permiso (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ruta_id INT NOT NULL,
  permiso_codigo VARCHAR(80) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_permiso_ruta FOREIGN KEY (ruta_id) REFERENCES rutas(id),
  CONSTRAINT uq_ruta_permiso UNIQUE (ruta_id, permiso_codigo)
) ENGINE=InnoDB;

-- Datos adicionales de vehiculos
CREATE TABLE vehiculo_meta (
  vehiculo_id INT PRIMARY KEY,
  km_actual DECIMAL(10,1) NULL,
  anticipo_base DECIMAL(10,2) NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_meta_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
) ENGINE=InnoDB;

-- Historial de reprogramaciones y cambios
CREATE TABLE programacion_historial (
  id INT AUTO_INCREMENT PRIMARY KEY,
  viaje_id INT NOT NULL,
  cambio TEXT,
  motivo TEXT,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_hist_viaje FOREIGN KEY (viaje_id) REFERENCES viajes(id)
) ENGINE=InnoDB;
