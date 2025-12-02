<?php
// Listado simple de viajes y detalle al seleccionar uno
require_once __DIR__ . '/../includes/config.php';
require_once __DIR__ . '/../includes/db.php';

$pdo = getPDO();
$viajes = $pdo->query(
    'SELECT v.id, v.fecha, v.estado, c.nombre AS cliente, s.nombre AS sede
     FROM viajes v
     JOIN clientes c ON c.id = v.cliente_id
     JOIN sedes s ON s.id = v.sede_id
     ORDER BY v.fecha DESC, v.id DESC'
)->fetchAll();

$detalle = [];
$viajeIdDetalle = isset($_GET['viaje_id']) ? (int)$_GET['viaje_id'] : 0;

if ($viajeIdDetalle) {
    $stmt = $pdo->prepare(
        'SELECT vd.id, r.nombre AS ruta, veh.placa AS vehiculo, cond.nombre AS conductor, aux.nombre AS auxiliar, vd.notas
         FROM viaje_detalle vd
         JOIN rutas r ON r.id = vd.ruta_id
         JOIN vehiculos veh ON veh.id = vd.vehiculo_id
         JOIN personas cond ON cond.id = vd.conductor_id
         JOIN personas aux ON aux.id = vd.auxiliar_id
         WHERE vd.viaje_id = ?
         ORDER BY vd.id'
    );
    $stmt->execute([$viajeIdDetalle]);
    $detalle = $stmt->fetchAll();
}
?>
<!doctype html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Viajes</title>
</head>
<body>
    <h1>Viajes</h1>
    <p><a href="crear_viaje.php">Crear nuevo viaje</a></p>

    <table border="1" cellpadding="5" cellspacing="0">
        <thead>
            <tr>
                <th>ID</th>
                <th>Fecha</th>
                <th>Cliente</th>
                <th>Sede</th>
                <th>Estado</th>
                <th>Detalle</th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($viajes as $v): ?>
                <tr>
                    <td><?= $v['id'] ?></td>
                    <td><?= htmlspecialchars($v['fecha']) ?></td>
                    <td><?= htmlspecialchars($v['cliente']) ?></td>
                    <td><?= htmlspecialchars($v['sede']) ?></td>
                    <td><?= htmlspecialchars($v['estado']) ?></td>
                    <td><a href="viajes.php?viaje_id=<?= $v['id'] ?>">Ver</a></td>
                </tr>
            <?php endforeach; ?>
        </tbody>
    </table>

    <?php if ($viajeIdDetalle): ?>
        <h2>Detalle del viaje <?= $viajeIdDetalle ?></h2>
        <?php if (empty($detalle)): ?>
            <p>No hay asignaciones.</p>
        <?php else: ?>
            <table border="1" cellpadding="5" cellspacing="0">
                <thead>
                    <tr>
                        <th>ID Detalle</th>
                        <th>Ruta</th>
                        <th>Vehículo</th>
                        <th>Conductor</th>
                        <th>Auxiliar</th>
                        <th>Notas</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($detalle as $d): ?>
                        <tr>
                            <td><?= $d['id'] ?></td>
                            <td><?= htmlspecialchars($d['ruta']) ?></td>
                            <td><?= htmlspecialchars($d['vehiculo']) ?></td>
                            <td><?= htmlspecialchars($d['conductor']) ?></td>
                            <td><?= htmlspecialchars($d['auxiliar']) ?></td>
                            <td><?= htmlspecialchars($d['notas'] ?? '') ?></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php endif; ?>
    <?php endif; ?>
</body>
</html>
