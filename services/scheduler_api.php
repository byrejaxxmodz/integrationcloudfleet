<?php
// Cliente simple para consumir el microservicio de programación
function llamarScheduler(array $payload): array {
    $ch = curl_init(SCHEDULER_API_URL . '/schedule');
    $jsonPayload = json_encode($payload);

    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Accept: application/json'
        ],
        CURLOPT_POSTFIELDS => $jsonPayload,
    ]);

    $response = curl_exec($ch);
    $errno = curl_errno($ch);
    $error = curl_error($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno) {
        throw new RuntimeException('Error de cURL al llamar al scheduler: ' . $error);
    }

    if ($httpCode >= 400) {
        throw new RuntimeException('El scheduler devolvió HTTP ' . $httpCode . ': ' . $response);
    }

    $decoded = json_decode($response, true);
    if ($decoded === null && json_last_error() !== JSON_ERROR_NONE) {
        throw new RuntimeException('No se pudo decodificar la respuesta JSON del scheduler.');
    }

    return $decoded;
}
