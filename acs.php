<?php
declare(strict_types=1);

require __DIR__ . '/src/Config.php';
require __DIR__ . '/src/Database.php';

use TR069\Config;
use TR069\Database;

$config = Config::load();

// Optional HTTP Basic auth
if (!empty($config['acs']['username'])) {
    $expectedUser = (string)$config['acs']['username'];
    $expectedPass = (string)($config['acs']['password'] ?? '');
    $user = $_SERVER['PHP_AUTH_USER'] ?? null;
    $pass = $_SERVER['PHP_AUTH_PW'] ?? null;
    $ok = $user !== null && $pass !== null
        && hash_equals($expectedUser, (string)$user)
        && hash_equals($expectedPass, (string)$pass);
    if (!$ok) {
        header('WWW-Authenticate: Basic realm="TR-069 ACS"');
        header('HTTP/1.1 401 Unauthorized');
        echo 'Unauthorized';
        exit;
    }
}

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'GET') {
    header('Content-Type: text/plain; charset=utf-8');
    echo "ACS endpoint is running. POST SOAP to this URL.\n";
    exit;
}

$raw = file_get_contents('php://input') ?: '';
if (trim($raw) === '') {
    http_response_code(204);
    header('Content-Length: 0');
    exit;
}

$soap = @simplexml_load_string($raw);
if ($soap === false) {
    http_response_code(400);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Invalid SOAP payload';
    exit;
}

// Extract cwmp:ID from Header to echo back
$idNodes = $soap->xpath('/*[local-name()="Envelope"]/*[local-name()="Header"]//*[local-name()="ID"]');
$idValue = ($idNodes && isset($idNodes[0])) ? trim((string)$idNodes[0]) : bin2hex(random_bytes(4));

$bodyNodes = $soap->xpath('/*[local-name()="Envelope"]/*[local-name()="Body"]');
if (!$bodyNodes || !isset($bodyNodes[0])) {
    http_response_code(400);
    echo 'No SOAP Body';
    exit;
}
$body = $bodyNodes[0];
$rpc = null;
foreach ($body->children() as $child) {
    $rpc = $child;
    break;
}
if ($rpc === null) {
    http_response_code(204);
    exit;
}
$rpcName = dom_import_simplexml($rpc)->localName ?? null;

if ($rpcName === 'Inform') {
    $oui = '';
    $productClass = null;
    $serialNumber = '';

    $deviceIdNode = $rpc->xpath('./*[local-name()="DeviceId"]');
    if ($deviceIdNode && isset($deviceIdNode[0])) {
        $ouiNode = $deviceIdNode[0]->xpath('./*[local-name()="OUI"]');
        $prodNode = $deviceIdNode[0]->xpath('./*[local-name()="ProductClass"]');
        $snNode = $deviceIdNode[0]->xpath('./*[local-name()="SerialNumber"]');
        $oui = isset($ouiNode[0]) ? trim((string)$ouiNode[0]) : '';
        $productClass = isset($prodNode[0]) ? trim((string)$prodNode[0]) : null;
        $serialNumber = isset($snNode[0]) ? trim((string)$snNode[0]) : '';
    }

    // Events
    $eventCodes = [];
    $eventNodes = $rpc->xpath('./*[local-name()="Event"]/*[local-name()="EventStruct"]/*[local-name()="EventCode"]');
    if ($eventNodes) {
        foreach ($eventNodes as $e) {
            $code = trim((string)$e);
            if ($code !== '') {
                $eventCodes[] = $code;
            }
        }
    }

    // Parameters
    $paramMap = [];
    $paramStructs = $rpc->xpath('./*[local-name()="ParameterList"]/*[local-name()="ParameterValueStruct"]');
    if ($paramStructs) {
        foreach ($paramStructs as $p) {
            $nameNode = $p->xpath('./*[local-name()="Name"]');
            $valueNode = $p->xpath('./*[local-name()="Value"]');
            $name = isset($nameNode[0]) ? trim((string)$nameNode[0]) : null;
            $value = isset($valueNode[0]) ? (string)$valueNode[0] : null;
            if ($name !== null && $name !== '') {
                $paramMap[$name] = $value;
            }
        }
    }

    $softwareVersion = $paramMap['Device.DeviceInfo.SoftwareVersion'] ?? null;
    $hardwareVersion = $paramMap['Device.DeviceInfo.HardwareVersion'] ?? null;

    // Persist
    try {
        $pdo = Database::getConnection();
        $pdo->beginTransaction();

        $stmt = $pdo->prepare(
            'INSERT INTO devices (oui, product_class, serial_number, username, ip_address, sw_version, hw_version, first_inform, last_inform)
             VALUES (:oui, :product_class, :serial, :username, :ip, :sw, :hw, NOW(), NOW())
             ON DUPLICATE KEY UPDATE username=VALUES(username), ip_address=VALUES(ip), sw_version=VALUES(sw), hw_version=VALUES(hw), last_inform=VALUES(last_inform), id=LAST_INSERT_ID(id)'
        );
        $stmt->execute([
            ':oui' => $oui,
            ':product_class' => $productClass,
            ':serial' => $serialNumber,
            ':username' => $_SERVER['PHP_AUTH_USER'] ?? null,
            ':ip' => $_SERVER['REMOTE_ADDR'] ?? null,
            ':sw' => $softwareVersion,
            ':hw' => $hardwareVersion,
        ]);
        $deviceId = (int)$pdo->lastInsertId();

        if (!empty($eventCodes)) {
            $evStmt = $pdo->prepare('INSERT INTO events (device_id, event_code, created_at) VALUES (:device_id, :event_code, NOW())');
            foreach ($eventCodes as $code) {
                $evStmt->execute([':device_id' => $deviceId, ':event_code' => $code]);
            }
        }

        if (!empty($paramMap)) {
            $parStmt = $pdo->prepare(
                'INSERT INTO parameters (device_id, name, value, updated_at)
                 VALUES (:device_id, :name, :value, NOW())
                 ON DUPLICATE KEY UPDATE value=VALUES(value), updated_at=VALUES(updated_at)'
            );
            foreach ($paramMap as $pname => $pvalue) {
                $parStmt->execute([':device_id' => $deviceId, ':name' => $pname, ':value' => $pvalue]);
            }
        }

        $pdo->commit();
    } catch (\Throwable $t) {
        if (isset($pdo) && $pdo->inTransaction()) {
            $pdo->rollBack();
        }
        // We still respond to the CPE to keep the session alive, but log error
        error_log('ACS persist error: ' . $t->getMessage());
    }

    // Build InformResponse
    $envelopeNs = 'http://schemas.xmlsoap.org/soap/envelope/';
    $cwmpNs = 'urn:dslforum-org:cwmp-1-0';
    $xml = '<?xml version="1.0" encoding="UTF-8"?>'
        . '<SOAP-ENV:Envelope xmlns:SOAP-ENV="' . $envelopeNs . '" xmlns:cwmp="' . $cwmpNs . '">'
        . '<SOAP-ENV:Header>'
        . '<cwmp:ID SOAP-ENV:mustUnderstand="1">' . htmlspecialchars($idValue, ENT_XML1 | ENT_COMPAT, 'UTF-8') . '</cwmp:ID>'
        . '</SOAP-ENV:Header>'
        . '<SOAP-ENV:Body>'
        . '<cwmp:InformResponse>'
        . '<MaxEnvelopes>1</MaxEnvelopes>'
        . '</cwmp:InformResponse>'
        . '</SOAP-ENV:Body>'
        . '</SOAP-ENV:Envelope>';

    header('Content-Type: text/xml; charset=utf-8');
    header('Content-Length: ' . strlen($xml));
    echo $xml;
    exit;
}

// For any other RPC, reply with 204 (no commands queued)
http_response_code(204);
header('Content-Length: 0');
