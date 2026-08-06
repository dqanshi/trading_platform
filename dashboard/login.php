<?php
session_start();
if (isset($_SESSION['jwt_token'])) {
    header('Location: index.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Algo Trading Terminal - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #0f172a;
            color: #e2e8f0;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .card {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        }
        .form-control {
            background-color: #0f172a;
            border: 1px solid #334155;
            color: #f8fafc;
        }
        .form-control:focus {
            background-color: #0f172a;
            color: #f8fafc;
            border-color: #3b82f6;
            box-shadow: 0 0 0 0.25rem rgba(59, 130, 246, 0.25);
        }
    </style>
</head>
<body>
    <div class="container" style="max-width: 420px;">
        <div class="card p-4">
            <div class="text-center mb-4">
                <h3 class="fw-bold text-primary">QuantTerminal</h3>
                <p class="text-muted small">Algorithmic Execution Platform</p>
            </div>
            <div id="alertBox" class="alert alert-danger d-none" role="alert"></div>
            <form id="loginForm">
                <div class="mb-3">
                    <label for="username" class="form-label text-secondary small">Username</label>
                    <input type="text" class="form-control" id="username" required autocomplete="off">
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label text-secondary small">Password</label>
                    <input type="password" class="form-control" id="password" required>
                </div>
                <button type="submit" class="btn btn-primary w-100 py-2 mt-2 fw-semibold" id="loginBtn">Sign In</button>
            </form>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async function (e) {
            e.preventDefault();
            const btn = document.getElementById('loginBtn');
            const alertBox = document.getElementById('alertBox');
            btn.disabled = true;
            btn.innerText = 'Authenticating...';
            alertBox.classList.add('d-none');

            try {
                const response = await fetch('api.php?action=login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: document.getElementById('username').value,
                        password: document.getElementById('password').value
                    })
                });
                const data = await response.json();

                if (data.status) {
                    window.location.href = 'index.php';
                } else {
                    alertBox.innerText = data.detail || 'Invalid username or password';
                    alertBox.classList.remove('d-none');
                }
            } catch (err) {
                alertBox.innerText = 'Connection error to backend gateway.';
                alertBox.classList.remove('d-none');
            } finally {
                btn.disabled = false;
                btn.innerText = 'Sign In';
            }
        });
    </script>
</body>
</html>
