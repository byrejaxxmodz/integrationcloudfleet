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
  activo TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE rutas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  nombre VARCHAR(150) NOT NULL,
  origen VARCHAR(150),
  destino VARCHAR(150),
  distancia_km DECIMAL(8,2),
  notas TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_rutas_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id)
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
