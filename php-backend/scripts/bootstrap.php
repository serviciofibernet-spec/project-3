<?php
use App\Db;

$path = __DIR__ . '/../sql/mysql.sql';
if (file_exists($path)) {
    $sql = file_get_contents($path);
    $stmts = preg_split('/;\s*\n/', $sql);
    foreach ($stmts as $s) {
        $s = trim($s);
        if ($s) {
            try { Db::query($s); } catch (Throwable $e) { /* ignore */ }
        }
    }
}
