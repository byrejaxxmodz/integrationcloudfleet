<?php
// Pantalla simple para crear un viaje y disparar la programación básica
require_once __DIR__ . '/../includes/config.php';
require_once __DIR__ . '/../includes/db.php';
require_once __DIR__ . '/../services/scheduler_api.php';

$pdo = getPDO();
$mensaje = '';
$error = '';
$resultadoApi = [];

function obtenerClientes(PDO $pdo): array {
    $stmt = $pdo->query('SELECT id, nombre FROM clientes ORDER BY nombre');
    return $stmt->fetchAll();
}

function obtenerSedesPorCliente(PDO $pdo, int $clienteId): array {
    $stmt = $pdo->prepare('SELECT id, nombre FROM sedes WHERE cliente_id = ? ORDER BY nombre');
    $stmt->execute([$clienteId]);
    return $stmt->fetchAll();
}

try {
    $clientes = obtenerClientes($pdo);
    $clienteSeleccionado = isset($_POST['cliente_id']) ? (int)$_POST['cliente_id'] : ($clientes[0]['id'] ?? 0);
    $sedes = $clienteSeleccionado ? obtenerSedesPorCliente($pdo, $clienteSeleccionado) : [];

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $clienteId = (int)($_POST['cliente_id'] ?? 0);
        $sedeId = (int)($_POST['sede_id'] ?? 0);
        $fecha = trim($_POST['fecha'] ?? '');

        if (!$clienteId || !$sedeId || !$fecha) {
            throw new InvalidArgumentException('Debe indicar cliente, sede y fecha.');
        }

        $payload = [
            'cliente_id' => $clienteId,
            'sede_id' => $sedeId,
            'fecha' => $fecha,
        ];

        // Llamamos al microservicio para obtener asignaciones sugeridas
        $asignaciones = llamarScheduler($payload);
        $resultadoApi = $asignaciones; // Para mostrar en pantalla qué devolvió el scheduler

        $pdo->beginTransaction();
        $stmtViaje = $pdo->prepare('INSERT INTO viajes (cliente_id, sede_id, fecha, estado) VALUES (?, ?, ?, "borrador")');
        $stmtViaje->execute([$clienteId, $sedeId, $fecha]);
        $viajeId = (int)$pdo->lastInsertId();

        $stmtDetalle = $pdo->prepare(
            'INSERT INTO viaje_detalle (viaje_id, ruta_id, vehiculo_id, conductor_id, auxiliar_id, notas)
             VALUES (?, ?, ?, ?, ?, ?)'
        );

        foreach ($asignaciones as $a) {
            $stmtDetalle->execute([
                $viajeId,
                (int)$a['ruta_id'],
                (int)$a['vehiculo_id'],
                (int)$a['conductor_id'],
                (int)$a['auxiliar_id'],
                $a['notas'] ?? null,
            ]);
        }

        $pdo->commit();
        $mensaje = 'Viaje creado con éxito. ID: ' . $viajeId;
    }
} catch (Throwable $ex) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $error = $ex->getMessage();
}
?>
<!doctype html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Crear viaje</title>
</head>
<body>
    <h1>Crear viaje</h1>

    <?php if ($mensaje): ?>
        <p style="color:green;"><?= htmlspecialchars($mensaje) ?></p>
        <p><a href="viajes.php">Ver viajes</a></p>
    <?php endif; ?>

    <?php if ($error): ?>
        <p style="color:red;">Error: <?= htmlspecialchars($error) ?></p>
    <?php endif; ?>

    <?php if (!empty($resultadoApi)): ?>
        <h2>Respuesta del scheduler</h2>
        <table border="1" cellpadding="5" cellspacing="0">
            <thead>
                <tr>
                    <th>Ruta</th>
                    <th>Vehículo</th>
                    <th>Conductor</th>
                    <th>Auxiliar</th>
                    <th>Notas</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($resultadoApi as $a): ?>
                    <tr>
                        <td><?= htmlspecialchars($a['ruta_id'] ?? '') ?></td>
                        <td><?= htmlspecialchars($a['vehiculo_id'] ?? '') ?></td>
                        <td><?= htmlspecialchars($a['conductor_id'] ?? '') ?></td>
                        <td><?= htmlspecialchars($a['auxiliar_id'] ?? '') ?></td>
                        <td><?= htmlspecialchars($a['notas'] ?? '') ?></td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php endif; ?>

    <form method="post">
        <label>Cliente:</label><br>
        <select name="cliente_id" onchange="this.form.submit()">
            <option value="">Seleccione...</option>
            <?php foreach ($clientes as $c): ?>
                <option value="<?= $c['id'] ?>" <?= $c['id'] == $clienteSeleccionado ? 'selected' : '' ?>>
                    <?= htmlspecialchars($c['nombre']) ?>
                </option>
            <?php endforeach; ?>
        </select>
        <br><br>

        <label>Sede:</label><br>
        <select name="sede_id">
            <option value="">Seleccione...</option>
            <?php foreach ($sedes as $s): ?>
                <option value="<?= $s['id'] ?>" <?= isset($_POST['sede_id']) && $_POST['sede_id'] == $s['id'] ? 'selected' : '' ?>>
                    <?= htmlspecialchars($s['nombre']) ?>
                </option>
            <?php endforeach; ?>
        </select>
        <br><br>

        <label>Fecha:</label><br>
        <input type="date" name="fecha" value="<?= htmlspecialchars($_POST['fecha'] ?? '') ?>">
        <br><br>

        <button type="submit">Generar programación</button>
    </form>
</body>
</html>
