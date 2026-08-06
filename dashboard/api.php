<?php
session_start();

define('FASTAPI_BASE_URL', 'http://127.0.0.1:8000/api/v1');

function call_fastapi(string $endpoint, string $method = 'GET', array $data = [], ?string $token = null): array
{
    $url = FASTAPI_BASE_URL . $endpoint;
    $ch = curl_init($url);

    $headers = [
        'Content-Type: application/json',
        'Accept: application/json'
    ];

    if ($token) {
        $headers[] = 'Authorization: Bearer ' . $token;
    }

    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);

    if (in_array($method, ['POST', 'PUT', 'PATCH']) && !empty($data)) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    }

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) {
        return ['status' => false, 'code' => 500, 'data' => ['detail' => 'cURL Error: ' . $error]];
    }

    $decoded = json_decode($response, true);
    return [
        'status' => ($httpCode >= 200 && $httpCode < 300),
        'code' => $httpCode,
        'data' => $decoded ?? []
    ];
}

if (isset($_GET['action'])) {
    header('Content-Type: application/json');

    if (!isset($_SESSION['jwt_token']) && $_GET['action'] !== 'login') {
        echo json_encode(['status' => false, 'detail' => 'Unauthorized']);
        exit;
    }

    $token = $_SESSION['jwt_token'] ?? null;
    $action = $_GET['action'];

    switch ($action) {
        case 'login':
            $input = json_decode(file_get_contents('php://input'), true);
            $postData = http_build_query([
                'username' => $input['username'] ?? '',
                'password' => $input['password'] ?? ''
            ]);

            $ch = curl_init(FASTAPI_BASE_URL . '/auth/login');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
            curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/x-www-form-urlencoded']);
            $res = curl_exec($ch);
            $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);

            $data = json_decode($res, true);
            if ($code === 200 && isset($data['access_token'])) {
                $_SESSION['jwt_token'] = $data['access_token'];
                $_SESSION['username'] = $input['username'];
                echo json_encode(['status' => true, 'message' => 'Login successful']);
            } else {
                echo json_encode(['status' => false, 'detail' => $data['detail'] ?? 'Login failed']);
            }
            exit;

        case 'status':
            $res = call_fastapi('/trading/status', 'GET', [], $token);
            echo json_encode($res['data']);
            exit;

        case 'start':
            $input = json_decode(file_get_contents('php://input'), true) ?? [];
            $res = call_fastapi('/trading/start', 'POST', $input, $token);
            echo json_encode($res['data']);
            exit;

        case 'stop':
            $res = call_fastapi('/trading/stop', 'POST', [], $token);
            echo json_encode($res['data']);
            exit;

        case 'positions':
            $res = call_fastapi('/trading/positions', 'GET', [], $token);
            echo json_encode($res['data']);
            exit;

        case 'orders':
            $res = call_fastapi('/trading/orders', 'GET', [], $token);
            echo json_encode($res['data']);
            exit;

        case 'trades':
            $res = call_fastapi('/trading/trades', 'GET', [], $token);
            echo json_encode($res['data']);
            exit;

        case 'square_off':
            $symbol = $_GET['symbol'] ?? '';
            $res = call_fastapi("/trading/square-off/{$symbol}", 'POST', [], $token);
            echo json_encode($res['data']);
            exit;

        case 'logs':
            $res = call_fastapi('/logs?limit=50', 'GET', [], $token);
            echo json_encode($res['data']);
            exit;

        case 'logout':
            session_destroy();
            echo json_encode(['status' => true]);
            exit;

        default:
            echo json_encode(['status' => false, 'detail' => 'Invalid action']);
            exit;
    }
}
