<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= isset($page_title) ? $page_title . ' - ' : '' ?>TR-069 ACS</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 0 20px;
        }
        
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 60px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: 600;
            color: #667eea;
        }
        
        .nav {
            display: flex;
            gap: 30px;
        }
        
        .nav a {
            text-decoration: none;
            color: #666;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav a:hover, .nav a.active {
            color: #667eea;
        }
        
        .user-menu {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .user-info {
            color: #666;
            font-size: 14px;
        }
        
        .btn {
            background: #667eea;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.3s;
            display: inline-block;
        }
        
        .btn:hover {
            background: #5a67d8;
        }
        
        .btn-small {
            padding: 6px 12px;
            font-size: 12px;
        }
        
        .btn-secondary {
            background: #e2e8f0;
            color: #4a5568;
        }
        
        .btn-secondary:hover {
            background: #cbd5e0;
        }
        
        .main-content {
            max-width: 1200px;
            margin: 20px auto;
            padding: 0 20px;
        }
        
        .page-header {
            margin-bottom: 30px;
        }
        
        .page-title {
            font-size: 32px;
            font-weight: 300;
            margin-bottom: 10px;
        }
        
        .page-subtitle {
            color: #666;
            font-size: 16px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .stat-icon {
            font-size: 24px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f7fafc;
        }
        
        .stat-card.online .stat-icon {
            background: #f0fff4;
        }
        
        .stat-card.pending .stat-icon {
            background: #fffbeb;
        }
        
        .stat-card.events .stat-icon {
            background: #f0f9ff;
        }
        
        .stat-content h3 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .stat-content p {
            color: #666;
            font-size: 14px;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        .dashboard-section {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .section-header {
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .section-header h2 {
            font-size: 18px;
            font-weight: 600;
        }
        
        .device-list, .event-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .device-item {
            padding: 15px 20px;
            border-bottom: 1px solid #f7fafc;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .device-item:last-child {
            border-bottom: none;
        }
        
        .device-status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #cbd5e0;
        }
        
        .device-status.online {
            background: #48bb78;
        }
        
        .device-status.recent {
            background: #ed8936;
        }
        
        .device-status.offline {
            background: #e53e3e;
        }
        
        .device-info {
            flex: 1;
        }
        
        .device-details {
            color: #666;
            font-size: 14px;
        }
        
        .device-meta {
            color: #999;
            font-size: 12px;
            margin-top: 5px;
        }
        
        .event-item {
            padding: 12px 20px;
            border-bottom: 1px solid #f7fafc;
            display: flex;
            gap: 15px;
        }
        
        .event-item:last-child {
            border-bottom: none;
        }
        
        .event-time {
            color: #666;
            font-size: 12px;
            min-width: 40px;
        }
        
        .event-content {
            flex: 1;
        }
        
        .event-type {
            font-weight: 500;
            font-size: 14px;
        }
        
        .event-device {
            color: #666;
            font-size: 12px;
        }
        
        .event-message {
            color: #999;
            font-size: 12px;
            margin-top: 2px;
        }
        
        .severity-error {
            border-left: 3px solid #e53e3e;
        }
        
        .severity-warning {
            border-left: 3px solid #ed8936;
        }
        
        .severity-info {
            border-left: 3px solid #3182ce;
        }
        
        .empty-state {
            padding: 40px 20px;
            text-align: center;
            color: #666;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .table th {
            background: #f7fafc;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .table td {
            padding: 12px;
            border-bottom: 1px solid #f7fafc;
        }
        
        .table tr:last-child td {
            border-bottom: none;
        }
        
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .badge-online {
            background: #f0fff4;
            color: #38a169;
        }
        
        .badge-offline {
            background: #fed7d7;
            color: #e53e3e;
        }
        
        .badge-pending {
            background: #fffbeb;
            color: #d69e2e;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .nav {
                display: none;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo">TR-069 ACS</div>
            
            <nav class="nav">
                <a href="index.php" class="<?= basename($_SERVER['PHP_SELF']) == 'index.php' ? 'active' : '' ?>">Dashboard</a>
                <a href="devices.php" class="<?= basename($_SERVER['PHP_SELF']) == 'devices.php' ? 'active' : '' ?>">Dispositivos</a>
                <a href="tasks.php" class="<?= basename($_SERVER['PHP_SELF']) == 'tasks.php' ? 'active' : '' ?>">Tareas</a>
                <a href="events.php" class="<?= basename($_SERVER['PHP_SELF']) == 'events.php' ? 'active' : '' ?>">Eventos</a>
                <a href="presets.php" class="<?= basename($_SERVER['PHP_SELF']) == 'presets.php' ? 'active' : '' ?>">Presets</a>
            </nav>
            
            <div class="user-menu">
                <span class="user-info">Bienvenido, <?= htmlspecialchars($_SESSION['username']) ?></span>
                <a href="?logout=1" class="btn btn-small btn-secondary">Salir</a>
            </div>
        </div>
    </header>
    
    <main class="main-content">