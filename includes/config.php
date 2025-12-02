<?php
// Configuración básica: credenciales de BD y URL del microservicio de programación
define('DB_HOST', '127.0.0.1');
define('DB_NAME', 'cloufleet');
define('DB_USER', 'root');
define('DB_PASS', 'password');

// URL base del microservicio de FastAPI (sin slash final)
define('SCHEDULER_API_URL', 'http://localhost:8000');
