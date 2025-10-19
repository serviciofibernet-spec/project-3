<?php
namespace App;

use GuzzleHttp\\Client;

class GenieAcs {
    private Client $http;

    public function __construct() {
        $this->http = new Client(['base_uri' => Config::genieAcsNbi(), 'timeout' => 10]);
    }

    public function getDeviceBySerialOrId(string $id): ?array {
        $q = rawurlencode("_id:/$id/i OR DeviceID.SerialNumber:/$id/i");
        $res = $this->http->get('/devices', ['query' => ['query' => $q, 'limit' => 1]]);
        $data = json_decode($res->getBody()->getContents(), true);
        return $data[0] ?? null;
    }

    public function createTask(string $deviceId, string $name, array $body = []): array {
        $res = $this->http->post('/devices/' . rawurlencode($deviceId) . '/tasks', [
            'json' => array_merge(['name' => $name], $body),
        ]);
        return json_decode($res->getBody()->getContents(), true);
    }

    public function refreshObject(string $deviceId, string $object): array {
        return $this->createTask($deviceId, 'refreshObject', ['objectName' => $object]);
    }

    public function setParameterValues(string $deviceId, array $params): array {
        return $this->createTask($deviceId, 'setParameterValues', ['parameterValues' => $params]);
    }

    public function reboot(string $deviceId): array {
        return $this->createTask($deviceId, 'reboot');
    }

    public function downloadFirmware(string $deviceId, string $url, string $fileType = '1 Firmware Upgrade Image'): array {
        return $this->createTask($deviceId, 'download', ['file' => $url, 'fileType' => $fileType]);
    }
}
