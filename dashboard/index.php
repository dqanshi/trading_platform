<?php
session_start();
if (!isset($_SESSION['jwt_token'])) {
    header('Location: login.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QuantTerminal - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        body {
            background-color: #0f172a;
            color: #f8fafc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .navbar {
            background-color: #1e293b;
            border-bottom: 1px solid #334155;
        }
        .card-custom {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
        }
        .text-accent-green { color: #10b981; }
        .text-accent-red { color: #ef4444; }
        .table-custom {
            color: #cbd5e1;
            margin-bottom: 0;
        }
        .table-custom th {
            background-color: #0f172a;
            border-color: #334155;
            color: #94a3b8;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        .table-custom td {
            border-color: #334155;
            vertical-align: middle;
            font-size: 0.9rem;
        }
        .badge-status {
            font-size: 0.75rem;
            padding: 0.35em 0.65em;
        }
        .log-box {
            background-color: #090d16;
            font-family: monospace;
            font-size: 0.85rem;
            max-height: 250px;
            overflow-y: auto;
            border-radius: 6px;
            padding: 10px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark px-4">
        <a class="navbar-brand fw-bold text-primary" href="#">
            <i class="bi bi-cpu me-2"></i>QuantTerminal
        </a>
        <div class="ms-auto d-flex align-items-center gap-3">
            <span class="badge bg-secondary" id="wsStatusBadge">
                <i class="bi bi-circle-fill me-1 small"></i> WebSocket DISCONNECTED
            </span>
            <span class="text-secondary small">User: <strong><?= htmlspecialchars($_SESSION['username']) ?></strong></span>
            <button class="btn btn-outline-danger btn-sm" id="logoutBtn">
                <i class="bi bi-box-arrow-right"></i> Logout
            </button>
        </div>
    </nav>

    <div class="container-fluid p-4">
        <!-- Control Bar & Key Metrics -->
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card card-custom p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-secondary small">Engine Status</div>
                            <h5 class="fw-bold mb-0 mt-1" id="engineStatusText">OFFLINE</h5>
                        </div>
                        <div>
                            <button class="btn btn-success btn-sm me-1" id="startBtn">Start</button>
                            <button class="btn btn-danger btn-sm" id="stopBtn" disabled>Stop</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-3">
                <div class="card card-custom p-3">
                    <div class="text-secondary small">Realized PnL (Today)</div>
                    <h4 class="fw-bold mb-0 mt-1" id="realizedPnl">₹ 0.00</h4>
                </div>
            </div>

            <div class="col-md-3">
                <div class="card card-custom p-3">
                    <div class="text-secondary small">Unrealized M2M</div>
                    <h4 class="fw-bold mb-0 mt-1" id="unrealizedPnl">₹ 0.00</h4>
                </div>
            </div>

            <div class="col-md-3">
                <div class="card card-custom p-3">
                    <div class="text-secondary small">Active Positions / Trades</div>
                    <h4 class="fw-bold mb-0 mt-1" id="activeStats">0 / 0</h4>
                </div>
            </div>
        </div>

        <!-- Main Content Area -->
        <div class="row g-3 mb-4">
            <!-- Active Positions -->
            <div class="col-lg-8">
                <div class="card card-custom">
                    <div class="card-header border-bottom border-secondary bg-transparent d-flex justify-content-between align-items-center py-3">
                        <h6 class="mb-0 fw-semibold"><i class="bi bi-layers me-2"></i>Active Open Positions</h6>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-custom align-middle">
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Product</th>
                                    <th>Qty</th>
                                    <th>Avg Price</th>
                                    <th>LTP</th>
                                    <th>M2M PnL</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody id="positionsTableBody">
                                <tr><td colspan="7" class="text-center text-muted py-3">No active positions.</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Orders Table -->
            <div class="col-lg-4">
                <div class="card card-custom">
                    <div class="card-header border-bottom border-secondary bg-transparent py-3">
                        <h6 class="mb-0 fw-semibold"><i class="bi bi-receipt me-2"></i>Today's Orders</h6>
                    </div>
                    <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
                        <table class="table table-custom">
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Type</th>
                                    <th>Qty</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="ordersTableBody">
                                <tr><td colspan="4" class="text-center text-muted py-3">No orders found today.</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Logs Box -->
        <div class="row">
            <div class="col-12">
                <div class="card card-custom p-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="fw-semibold small text-secondary"><i class="bi bi-terminal me-2"></i>Live System Stream Logs</span>
                        <span class="badge bg-dark text-muted">Auto-refresh (3s)</span>
                    </div>
                    <div class="log-box" id="logBox">
                        <div class="text-muted">[System] Waiting for logs...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function fetchStatus() {
            try {
                const res = await fetch('api.php?action=status');
                const data = await res.json();

                const engineStatusText = document.getElementById('engineStatusText');
                const startBtn = document.getElementById('startBtn');
                const stopBtn = document.getElementById('stopBtn');
                const wsBadge = document.getElementById('wsStatusBadge');

                if (data.is_running) {
                    engineStatusText.innerText = 'ACTIVE (' + (data.active_strategy || 'RUNNING') + ')';
                    engineStatusText.className = 'fw-bold mb-0 mt-1 text-accent-green';
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                } else {
                    engineStatusText.innerText = 'OFFLINE';
                    engineStatusText.className = 'fw-bold mb-0 mt-1 text-secondary';
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                }

                if (data.websocket_connected) {
                    wsBadge.className = 'badge bg-success';
                    wsBadge.innerHTML = '<i class="bi bi-circle-fill me-1 small"></i> WebSocket CONNECTED';
                } else {
                    wsBadge.className = 'badge bg-secondary';
                    wsBadge.innerHTML = '<i class="bi bi-circle-fill me-1 small"></i> WebSocket DISCONNECTED';
                }

                const realPnlEl = document.getElementById('realizedPnl');
                realPnlEl.innerText = '₹ ' + (data.realized_pnl_today || 0).toFixed(2);
                realPnlEl.className = 'fw-bold mb-0 mt-1 ' + (data.realized_pnl_today >= 0 ? 'text-accent-green' : 'text-accent-red');

                const unrealPnlEl = document.getElementById('unrealizedPnl');
                unrealPnlEl.innerText = '₹ ' + (data.unrealized_pnl_today || 0).toFixed(2);
                unrealPnlEl.className = 'fw-bold mb-0 mt-1 ' + (data.unrealized_pnl_today >= 0 ? 'text-accent-green' : 'text-accent-red');

                document.getElementById('activeStats').innerText = (data.open_positions_count || 0) + ' / ' + (data.total_trades_today || 0);

            } catch (err) {
                console.error("Status fetch error", err);
            }
        }

        async function fetchPositions() {
            try {
                const res = await fetch('api.php?action=positions');
                const positions = await res.json();
                const tbody = document.getElementById('positionsTableBody');

                if (!Array.isArray(positions) || positions.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">No active positions.</td></tr>';
                    return;
                }

                tbody.innerHTML = positions.map(p => `
                    <tr>
                        <td class="fw-bold">${p.symbol}</td>
                        <td><span class="badge bg-dark">${p.product}</span></td>
                        <td class="${p.quantity > 0 ? 'text-accent-green' : 'text-accent-red'} fw-bold">${p.quantity}</td>
                        <td>₹ ${p.average_price.toFixed(2)}</td>
                        <td>₹ ${(p.last_price || 0).toFixed(2)}</td>
                        <td class="${p.m2m >= 0 ? 'text-accent-green' : 'text-accent-red'} fw-bold">₹ ${p.m2m.toFixed(2)}</td>
                        <td>
                            <button class="btn btn-outline-danger btn-sm" onclick="squareOff('${p.symbol}')">Square Off</button>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error("Positions fetch error", err);
            }
        }

        async function fetchOrders() {
            try {
                const res = await fetch('api.php?action=orders');
                const orders = await res.json();
                const tbody = document.getElementById('ordersTableBody');

                if (!Array.isArray(orders) || orders.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">No orders found today.</td></tr>';
                    return;
                }

                tbody.innerHTML = orders.map(o => `
                    <tr>
                        <td class="fw-semibold">${o.symbol}</td>
                        <td><span class="badge ${o.transaction_type === 'BUY' ? 'bg-success' : 'bg-danger'}">${o.transaction_type}</span></td>
                        <td>${o.quantity}</td>
                        <td><span class="badge bg-secondary badge-status">${o.status}</span></td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error("Orders fetch error", err);
            }
        }

        async function fetchLogs() {
            try {
                const res = await fetch('api.php?action=logs');
                const logs = await res.json();
                const logBox = document.getElementById('logBox');

                if (!Array.isArray(logs) || logs.length === 0) {
                    return;
                }

                logBox.innerHTML = logs.map(l => {
                    let color = '#94a3b8';
                    if (l.level === 'ERROR') color = '#ef4444';
                    if (l.level === 'WARNING') color = '#f59e0b';
                    if (l.level === 'INFO') color = '#10b981';
                    return `<div style="color: ${color}">[${l.created_at}] [${l.level}] ${l.module}: ${l.message}</div>`;
                }).join('');
            } catch (err) {
                console.error("Logs fetch error", err);
            }
        }

        async function squareOff(symbol) {
            if (!confirm(`Are you sure you want to square off position for ${symbol}?`)) return;
            try {
                await fetch(`api.php?action=square_off&symbol=${symbol}`, { method: 'POST' });
                fetchPositions();
                fetchStatus();
            } catch (err) {
                alert('Square off action failed');
            }
        }

        document.getElementById('startBtn').addEventListener('click', async () => {
            await fetch('api.php?action=start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ strategy_name: 'ORB' })
            });
            fetchStatus();
        });

        document.getElementById('stopBtn').addEventListener('click', async () => {
            if (!confirm("Stop Trading Engine and square off all open positions?")) return;
            await fetch('api.php?action=stop', { method: 'POST' });
            fetchStatus();
        });

        document.getElementById('logoutBtn').addEventListener('click', async () => {
            await fetch('api.php?action=logout');
            window.location.href = 'login.php';
        });

        function refreshAll() {
            fetchStatus();
            fetchPositions();
            fetchOrders();
            fetchLogs();
        }

        refreshAll();
        setInterval(refreshAll, 3000);
    </script>
</body>
</html>
