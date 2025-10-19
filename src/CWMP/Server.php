<?php
declare(strict_types=1);

namespace App\CWMP;

use App\Config;
use App\Database;
use App\Logger;
use DOMDocument;
use DOMXPath;
use PDO;

final class Server
{
    public function handleHttp(): void
    {
        // Optional Basic Auth
        if ((bool) (Config::get('auth.enabled', false))) {
            $user = (string) Config::get('auth.user', '');
            $pass = (string) Config::get('auth.pass', '');
            $reqUser = $_SERVER['PHP_AUTH_USER'] ?? null;
            $reqPass = $_SERVER['PHP_AUTH_PW'] ?? null;
            if ($user === '' || $pass === '' || $reqUser !== $user || $reqPass !== $pass) {
                header('WWW-Authenticate: Basic realm="ACS"');
                header('HTTP/1.1 401 Unauthorized');
                echo 'Authentication required';
                return;
            }
        }

        $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
        if ($method !== 'POST') {
            header('Content-Type: text/plain; charset=utf-8');
            echo "ACS endpoint. POST SOAP envelopes here.";
            return;
        }

        $raw = file_get_contents('php://input') ?: '';
        if (trim($raw) === '') {
            // Empty HTTP request: if ACS has no pending work, respond 204
            header('HTTP/1.1 204 No Content');
            return;
        }

        try {
            [$idHeader, $responseXml, $deviceInfo] = $this->handleSoap($raw);
        } catch (\Throwable $e) {
            Logger::error('SOAP handling failed', ['error' => $e->getMessage()]);
            header('HTTP/1.1 500 Internal Server Error');
            header('Content-Type: text/plain; charset=utf-8');
            echo 'Internal error';
            return;
        }

        // Return InformResponse (and no more tasks for now)
        header('Content-Type: text/xml; charset=utf-8');
        echo $responseXml;
    }

    /**
     * @return array{0:string|null,1:string,2:array<string,mixed>}
     */
    private function handleSoap(string $xml): array
    {
        $doc = new DOMDocument();
        $doc->preserveWhiteSpace = false;
        $doc->formatOutput = false;
        if (!@$doc->loadXML($xml)) {
            throw new \RuntimeException('Invalid XML');
        }
        $xp = new DOMXPath($doc);
        // Accept any prefixes by using local-name()
        $idNode = $xp->query('/*[local-name()="Envelope"]/*[local-name()="Header"]/*[local-name()="ID"]')->item(0);
        $id = $idNode ? trim($idNode->textContent) : null;

        $body = $xp->query('/*[local-name()="Envelope"]/*[local-name()="Body"]')->item(0);
        if (!$body) {
            throw new \RuntimeException('No SOAP Body');
        }

        // Determine cwmp namespace URI from any cwmp element in body
        $cwmpUri = 'urn:dslforum-org:cwmp-1-0';
        $cwmpEl = $xp->query('.//*[starts-with(namespace-uri(), "urn:dslforum-org:cwmp-")]', $body)->item(0);
        if ($cwmpEl && $cwmpEl->namespaceURI) {
            $cwmpUri = $cwmpEl->namespaceURI;
        }

        $isInform = $xp->query('./*[local-name()="Inform"]', $body)->length > 0
            || $xp->query('.//*[local-name()="Inform"][ancestor::*[local-name()="Body"]]')->length > 0;

        if ($isInform) {
            $device = $this->parseInform($xp, $body);
            $this->upsertDevice($device);
            $response = $this->buildInformResponse($id, $cwmpUri);
            return [$id, $response, $device];
        }

        // If unknown RPC, respond with 204 as we have nothing else to send
        Logger::info('Unknown RPC received', ['raw' => substr($xml, 0, 1024)]);
        header('HTTP/1.1 204 No Content');
        return [$id, '', []];
    }

    /**
     * @param DOMXPath $xp
     * @param \DOMNode $body
     * @return array<string,mixed>
     */
    private function parseInform(DOMXPath $xp, \DOMNode $body): array
    {
        $node = $xp->query('.//*[local-name()="Inform"]', $body)->item(0);
        if (!$node) {
            throw new \RuntimeException('Inform missing');
        }

        $get = function (string $path) use ($xp, $node): ?string {
            $n = $xp->query($path, $node)->item(0);
            return $n ? trim($n->textContent) : null;
        };

        $manufacturer = $get('.//*[local-name()="DeviceId"]/*[local-name()="Manufacturer"]') ?? '';
        $oui = $get('.//*[local-name()="DeviceId"]/*[local-name()="OUI"]') ?? '';
        $productClass = $get('.//*[local-name()="DeviceId"]/*[local-name()="ProductClass"]') ?? '';
        $serialNumber = $get('.//*[local-name()="DeviceId"]/*[local-name()="SerialNumber"]') ?? '';

        $eventCodes = [];
        foreach ($xp->query('.//*[local-name()="Event"]//*[local-name()="EventCode"]', $node) as $ev) {
            $eventCodes[] = trim($ev->textContent);
        }

        $parameters = [];
        foreach ($xp->query('.//*[local-name()="ParameterList"]//*[local-name()="ParameterValueStruct"]', $node) as $pvs) {
            $name = trim(($xp->query('./*[local-name()="Name"]', $pvs)->item(0)?->textContent) ?? '');
            $valueNode = $xp->query('./*[local-name()="Value"]', $pvs)->item(0);
            if ($name === '' || !$valueNode) {
                continue;
            }
            $type = '';
            if ($valueNode->attributes && $valueNode->attributes->getNamedItemNS('http://www.w3.org/2001/XMLSchema-instance', 'type')) {
                $type = $valueNode->attributes->getNamedItemNS('http://www.w3.org/2001/XMLSchema-instance', 'type')->nodeValue ?? '';
            }
            $parameters[$name] = [
                'value' => trim($valueNode->textContent),
                'type' => $type,
            ];
        }

        $ip = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '';

        $connReqUrl = $parameters['ManagementServer.ConnectionRequestURL']['value'] ?? null;
        $swVersion = $parameters['DeviceInfo.SoftwareVersion']['value'] ?? null;
        $hwVersion = $parameters['DeviceInfo.HardwareVersion']['value'] ?? null;
        $maxEnvStr = $get('.//*[local-name()="MaxEnvelopes"]');
        $maxEnvelopes = $maxEnvStr !== null ? (int) $maxEnvStr : 1;

        return [
            'manufacturer' => $manufacturer,
            'oui' => $oui,
            'productClass' => $productClass,
            'serialNumber' => $serialNumber,
            'eventCodes' => $eventCodes,
            'parameters' => $parameters,
            'ip' => $ip,
            'connectionRequestUrl' => $connReqUrl,
            'softwareVersion' => $swVersion,
            'hardwareVersion' => $hwVersion,
            'maxEnvelopes' => $maxEnvelopes,
        ];
    }

    private function upsertDevice(array $d): void
    {
        $pdo = Database::connection();
        $pdo->beginTransaction();
        try {
            $stmt = $pdo->prepare('SELECT id, first_inform_at FROM devices WHERE oui = ? AND product_class = ? AND serial_number = ?');
            $stmt->execute([$d['oui'], $d['productClass'], $d['serialNumber']]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);

            if ($row) {
                $deviceId = (int) $row['id'];
                $stmt = $pdo->prepare('UPDATE devices SET manufacturer = ?, software_version = ?, hardware_version = ?, connection_request_url = ?, ip_address = ?, max_envelopes = ?, last_inform_at = NOW(), updated_at = NOW() WHERE id = ?');
                $stmt->execute([
                    $d['manufacturer'],
                    $d['softwareVersion'],
                    $d['hardwareVersion'],
                    $d['connectionRequestUrl'],
                    $d['ip'],
                    (int) $d['maxEnvelopes'],
                    $deviceId,
                ]);
            } else {
                $stmt = $pdo->prepare('INSERT INTO devices (oui, product_class, serial_number, manufacturer, software_version, hardware_version, connection_request_url, ip_address, max_envelopes, last_inform_at, first_inform_at) VALUES (?,?,?,?,?,?,?,?,?,NOW(),NOW())');
                $stmt->execute([
                    $d['oui'],
                    $d['productClass'],
                    $d['serialNumber'],
                    $d['manufacturer'],
                    $d['softwareVersion'],
                    $d['hardwareVersion'],
                    $d['connectionRequestUrl'],
                    $d['ip'],
                    (int) $d['maxEnvelopes'],
                ]);
                $deviceId = (int) $pdo->lastInsertId();
            }

            // Events
            if (!empty($d['eventCodes'])) {
                $stmt = $pdo->prepare('INSERT INTO device_events (device_id, event_code, command_key) VALUES (?,?,?)');
                foreach ($d['eventCodes'] as $code) {
                    $stmt->execute([$deviceId, $code, null]);
                }
            }

            // Parameters upsert
            if (!empty($d['parameters'])) {
                $sel = $pdo->prepare('SELECT id FROM device_parameters WHERE device_id = ? AND name = ?');
                $ins = $pdo->prepare('INSERT INTO device_parameters (device_id, name, value, type, writable) VALUES (?,?,?,?,0)');
                $upd = $pdo->prepare('UPDATE device_parameters SET value = ?, type = ?, updated_at = NOW() WHERE id = ?');
                foreach ($d['parameters'] as $name => $pv) {
                    $sel->execute([$deviceId, $name]);
                    $existing = $sel->fetch(PDO::FETCH_ASSOC);
                    if ($existing) {
                        $upd->execute([$pv['value'], $pv['type'], $existing['id']]);
                    } else {
                        $ins->execute([$deviceId, $name, $pv['value'], $pv['type']]);
                    }
                }
            }

            $pdo->commit();
        } catch (\Throwable $e) {
            $pdo->rollBack();
            Logger::error('Device upsert failed', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    private function buildInformResponse(?string $id, string $cwmpUri): string
    {
        $soapEnv = 'http://schemas.xmlsoap.org/soap/envelope/';
        $xsd = 'http://www.w3.org/2001/XMLSchema';
        $xsi = 'http://www.w3.org/2001/XMLSchema-instance';

        $doc = new DOMDocument('1.0', 'UTF-8');
        $doc->formatOutput = false;

        $env = $doc->createElementNS($soapEnv, 'SOAP-ENV:Envelope');
        $env->setAttributeNS('http://www.w3.org/2000/xmlns/', 'xmlns:cwmp', $cwmpUri);
        $env->setAttributeNS('http://www.w3.org/2000/xmlns/', 'xmlns:xsd', $xsd);
        $env->setAttributeNS('http://www.w3.org/2000/xmlns/', 'xmlns:xsi', $xsi);
        $doc->appendChild($env);

        $hdr = $doc->createElementNS($soapEnv, 'SOAP-ENV:Header');
        if ($id !== null) {
            $idEl = $doc->createElementNS($cwmpUri, 'cwmp:ID');
            $idEl->setAttributeNS($soapEnv, 'SOAP-ENV:mustUnderstand', '1');
            $idEl->nodeValue = $id;
            $hdr->appendChild($idEl);
        }
        $env->appendChild($hdr);

        $body = $doc->createElementNS($soapEnv, 'SOAP-ENV:Body');
        $resp = $doc->createElementNS($cwmpUri, 'cwmp:InformResponse');
        $max = $doc->createElement('MaxEnvelopes');
        $max->setAttributeNS($xsi, 'xsi:type', 'xsd:unsignedInt');
        $max->nodeValue = (string) 1;
        $resp->appendChild($max);
        $body->appendChild($resp);
        $env->appendChild($body);

        return $doc->saveXML() ?: '';
    }
}
