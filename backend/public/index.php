<?php
declare(strict_types=1);

use Aurora\Http\JsonResponse;

try {
    $createApplication = require dirname(__DIR__) . '/bootstrap.php';
    $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    // Limita a leitura sem carregar um corpo inteiro acima do tamanho permitido.
    $raw = $method === 'POST' ? file_get_contents('php://input', false, null, 0, 2000001) : '';
    $response = $createApplication()->handle($method, $_GET, $raw === false ? '' : $raw);
    $response->send();
} catch (Throwable $error) {
    error_log('Fitness API bootstrap: ' . $error->getMessage());
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store, no-cache, must-revalidate');
    header('X-Content-Type-Options: nosniff');
    echo '{"ok":false,"error":"Falha ao acessar o banco Fitness"}';
}
