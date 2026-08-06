<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

function check_authenticated(): void {
    if (!isset($_SESSION['jwt_token'])) {
        header('Location: login.php');
        exit;
    }
}

function get_auth_token(): ?string {
    return $_SESSION['jwt_token'] ?? null;
}
?>
