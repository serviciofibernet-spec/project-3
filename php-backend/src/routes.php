<?php
use Slim\App;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Db;
use App\GenieAcs;
use App\ParamMapping;
use GuzzleHttp\Client;

return function (App $app) {
    $app->get('/api/devices/{id}', function(Request $req, Response $res, $args){
        $acs = new GenieAcs();
        $dev = $acs->getDeviceBySerialOrId($args['id']);
        if (!$dev) {
            $res->getBody()->write(json_encode(['error' => 'Device not found']));
            return $res->withStatus(404)->withHeader('Content-Type','application/json');
        }
        $res->getBody()->write(json_encode($dev));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/devices/{id}/wifi', function(Request $req, Response $res, $args){
        $body = (array) $req->getParsedBody();
        $acs = new GenieAcs();
        $dev = $acs->getDeviceBySerialOrId($args['id']);
        if (!$dev) return $res->withStatus(404);
        $params = ParamMapping::wifiParams($dev['DeviceID']['ProductClass'] ?? null, $body);
        $task = $acs->setParameterValues($dev['_id'], $params);
        $res->getBody()->write(json_encode(['ok'=>true,'task'=>$task]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/devices/{id}/pppoe', function(Request $req, Response $res, $args){
        $b = (array) $req->getParsedBody();
        $user = $b['user'] ?? '';
        $pass = $b['pass'] ?? '';
        if (!$user || !$pass) return $res->withStatus(400);
        $acs = new GenieAcs();
        $dev = $acs->getDeviceBySerialOrId($args['id']);
        if (!$dev) return $res->withStatus(404);
        $params = [
          'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Username' => $user,
          'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Password' => $pass,
          'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.NATEnabled' => '1',
        ];
        $task = $acs->setParameterValues($dev['_id'], $params);
        $res->getBody()->write(json_encode(['ok'=>true,'task'=>$task]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/devices/{id}/vlan', function(Request $req, Response $res, $args){
        $b = (array) $req->getParsedBody();
        $vlanId = (int)($b['vlanId'] ?? 0);
        if ($vlanId < 1 || $vlanId > 4094) return $res->withStatus(400);
        $acs = new GenieAcs();
        $dev = $acs->getDeviceBySerialOrId($args['id']);
        if (!$dev) return $res->withStatus(404);
        $params = ParamMapping::vlanParams($dev['DeviceID']['ProductClass'] ?? null, $vlanId);
        $task = $acs->setParameterValues($dev['_id'], $params);
        $res->getBody()->write(json_encode(['ok'=>true,'task'=>$task]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/devices/{id}/dns', function(Request $req, Response $res, $args){
        $b = (array) $req->getParsedBody();
        $primary = $b['primary'] ?? '';
        $secondary = $b['secondary'] ?? null;
        if (!filter_var($primary, FILTER_VALIDATE_IP)) return $res->withStatus(400);
        if ($secondary && !filter_var($secondary, FILTER_VALIDATE_IP)) return $res->withStatus(400);
        $acs = new GenieAcs();
        $dev = $acs->getDeviceBySerialOrId($args['id']);
        if (!$dev) return $res->withStatus(404);
        $params = ParamMapping::dnsParams($dev['DeviceID']['ProductClass'] ?? null, $primary, $secondary);
        $task = $acs->setParameterValues($dev['_id'], $params);
        $res->getBody()->write(json_encode(['ok'=>true,'task'=>$task]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/devices/{id}/port', function(Request $req, Response $res, $args){
        $b = (array) $req->getParsedBody();
        $port = (int)($b['port'] ?? 0);
        $enable = (bool)($b['enable'] ?? false);
        if ($port < 1 || $port > 8) return $res->withStatus(400);
        $acs = new GenieAcs();
        $dev = $acs->getDeviceBySerialOrId($args['id']);
        if (!$dev) return $res->withStatus(404);
        $params = ParamMapping::portEnable($dev['DeviceID']['ProductClass'] ?? null, $port, $enable);
        $task = $acs->setParameterValues($dev['_id'], $params);
        $res->getBody()->write(json_encode(['ok'=>true,'task'=>$task]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/devices/{id}/wifi-radio', function(Request $req, Response $res, $args){
        $b = (array) $req->getParsedBody();
        $band = $b['band'] ?? '';
        $enable = (bool)($b['enable'] ?? false);
        if (!in_array($band, ['2.4','5'], true)) return $res->withStatus(400);
        $acs = new GenieAcs();
        $dev = $acs->getDeviceBySerialOrId($args['id']);
        if (!$dev) return $res->withStatus(404);
        $params = ParamMapping::wifiRadio($dev['DeviceID']['ProductClass'] ?? null, $band, $enable);
        $task = $acs->setParameterValues($dev['_id'], $params);
        $res->getBody()->write(json_encode(['ok'=>true,'task'=>$task]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/devices/{id}/firmware', function(Request $req, Response $res, $args){
        $b = (array) $req->getParsedBody();
        $url = $b['url'] ?? '';
        $fileType = $b['fileType'] ?? '1 Firmware Upgrade Image';
        if (!filter_var($url, FILTER_VALIDATE_URL)) return $res->withStatus(400);
        $acs = new GenieAcs();
        $dev = $acs->getDeviceBySerialOrId($args['id']);
        if (!$dev) return $res->withStatus(404);
        $task = $acs->downloadFirmware($dev['_id'], $url, $fileType);
        $res->getBody()->write(json_encode(['ok'=>true,'task'=>$task]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/devices/{id}/refresh', function(Request $req, Response $res, $args){
        $acs = new GenieAcs();
        $dev = $acs->getDeviceBySerialOrId($args['id']);
        if (!$dev) return $res->withStatus(404);
        $task = $acs->refreshObject($dev['_id'], 'InternetGatewayDevice');
        $res->getBody()->write(json_encode(['ok'=>true,'task'=>$task]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->get('/api/profiles', function(Request $req, Response $res){
        $rows = Db::query('SELECT id, name, model, ssid24, pass24, ssid5, pass5, vlan_id AS vlanId FROM profiles ORDER BY id DESC');
        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/profiles', function(Request $req, Response $res){
        $b = (array) $req->getParsedBody();
        $id = isset($b['id']) ? (int)$b['id'] : null;
        $vals = [
            $b['name'] ?? '', $b['model'] ?? null, $b['ssid24'] ?? null, $b['pass24'] ?? null,
            $b['ssid5'] ?? null, $b['pass5'] ?? null, isset($b['vlanId']) ? (int)$b['vlanId'] : null
        ];
        if ($id) {
            Db::query('UPDATE profiles SET name=?, model=?, ssid24=?, pass24=?, ssid5=?, pass5=?, vlan_id=? WHERE id=?', array_merge($vals, [$id]));
            $res->getBody()->write(json_encode(['ok'=>true,'id'=>$id]));
        } else {
            $r = Db::query('INSERT INTO profiles (name, model, ssid24, pass24, ssid5, pass5, vlan_id) VALUES (?, ?, ?, ?, ?, ?, ?)', $vals);
            $res->getBody()->write(json_encode(['ok'=>true,'id'=>$r['lastInsertId']]));
        }
        return $res->withHeader('Content-Type','application/json');
    });

    $app->get('/api/monitoring/device/{id}/summary', function(Request $req, Response $res, $args){
        $acsUrl = App\Config::genieAcsNbi();
        $client = new Client(['base_uri' => $acsUrl]);
        $q = rawurlencode("_id:/{$args['id']}/i OR DeviceID.SerialNumber:/{$args['id']}/i");
        $resp = $client->get('/devices', ['query' => ['query' => $q, 'limit' => 1]]);
        $data = json_decode($resp->getBody()->getContents(), true);
        if (!($data[0] ?? null)) return $res->withStatus(404);
        $d = $data[0];
        $optical = $d['InternetGatewayDevice']['X_HW_DEBUG']['OpticalInfo']['OpticalSignalLevel'] ?? ($d['Device']['Optical']['Power'] ?? null);
        $w24 = $d['InternetGatewayDevice']['LANDevice']['1']['WLANConfiguration']['1'] ?? [];
        $w5  = $d['InternetGatewayDevice']['LANDevice']['1']['WLANConfiguration']['2'] ?? [];
        $link = $d['InternetGatewayDevice']['WANDevice']['1']['WANConnectionDevice']['1']['WANPPPConnection']['1']['ConnectionStatus']
             ?? $d['InternetGatewayDevice']['WANDevice']['1']['WANConnectionDevice']['1']['WANIPConnection']['1']['ConnectionStatus']
             ?? null;
        $out = [
            'id' => $d['_id'] ?? null,
            'serial' => $d['DeviceID']['SerialNumber'] ?? null,
            'model' => $d['DeviceID']['ProductClass'] ?? null,
            'opticalDbm' => $optical,
            'linkStatus' => $link,
            'wifi' => [
                'clients24' => (int)($w24['AssociatedDeviceNumberOfEntries'] ?? 0),
                'clients5' => (int)($w5['AssociatedDeviceNumberOfEntries'] ?? 0),
            ],
        ];
        $res->getBody()->write(json_encode($out));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/onboarding', function(Request $req, Response $res){
        $b = (array) $req->getParsedBody();
        $acsId = $b['acsId'] ?? '';
        $serial = $b['serial'] ?? null;
        $model = $b['model'] ?? null;
        if (!$acsId) return $res->withStatus(400);
        $rows = Db::query('SELECT id FROM devices WHERE acs_id=?', [$acsId]);
        if (count($rows) === 0) {
            $prof = Db::query('SELECT id FROM profiles WHERE model IS NULL OR model=? ORDER BY model IS NULL ASC LIMIT 1', [$model]);
            $profileId = $prof[0]['id'] ?? null;
            Db::query('INSERT INTO devices (acs_id, serial, model, profile_id) VALUES (?, ?, ?, ?)', [$acsId, $serial, $model, $profileId]);
        }
        $res->getBody()->write(json_encode(['ok'=>true]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/hooks/device-connected', function(Request $req, Response $res){
        $b = (array) $req->getParsedBody();
        $acsId = $b['_id'] ?? '';
        $serial = $b['DeviceID']['SerialNumber'] ?? null;
        $model = $b['DeviceID']['ProductClass'] ?? null;
        if (!$acsId) return $res->withStatus(400);
        $rows = Db::query('SELECT id FROM devices WHERE acs_id=?', [$acsId]);
        if (count($rows) === 0) {
            $prof = Db::query('SELECT id FROM profiles WHERE model IS NULL OR model=? ORDER BY model IS NULL ASC LIMIT 1', [$model]);
            $profileId = $prof[0]['id'] ?? null;
            Db::query('INSERT INTO devices (acs_id, serial, model, profile_id) VALUES (?, ?, ?, ?)', [$acsId, $serial, $model, $profileId]);
        }
        $res->getBody()->write(json_encode(['ok'=>true]));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->get('/api/admin/customers', function(Request $req, Response $res){
        $rows = Db::query('SELECT * FROM customers ORDER BY id DESC');
        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/admin/customers', function(Request $req, Response $res){
        $b = (array) $req->getParsedBody();
        $id = isset($b['id']) ? (int)$b['id'] : null;
        if ($id) {
            Db::query('UPDATE customers SET name=?, doc_id=?, phone=?, email=? WHERE id=?', [
                $b['name'] ?? '', $b['doc_id'] ?? null, $b['phone'] ?? null, $b['email'] ?? null, $id
            ]);
            $res->getBody()->write(json_encode(['ok'=>true,'id'=>$id]));
        } else {
            $r = Db::query('INSERT INTO customers (name, doc_id, phone, email) VALUES (?, ?, ?, ?)', [
                $b['name'] ?? '', $b['doc_id'] ?? null, $b['phone'] ?? null, $b['email'] ?? null
            ]);
            $res->getBody()->write(json_encode(['ok'=>true,'id'=>$r['lastInsertId']]));
        }
        return $res->withHeader('Content-Type','application/json');
    });

    $app->get('/api/admin/devices', function(Request $req, Response $res){
        $rows = Db::query('SELECT d.*, c.name AS customer_name, p.name AS profile_name FROM devices d LEFT JOIN customers c ON c.id=d.customer_id LEFT JOIN profiles p ON p.id=d.profile_id ORDER BY d.id DESC');
        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type','application/json');
    });

    $app->post('/api/admin/assign', function(Request $req, Response $res){
        $b = (array) $req->getParsedBody();
        $deviceId = (int)($b['deviceId'] ?? 0);
        $customerId = array_key_exists('customerId', $b) ? ($b['customerId'] === null ? null : (int)$b['customerId']) : null;
        $profileId = array_key_exists('profileId', $b) ? ($b['profileId'] === null ? null : (int)$b['profileId']) : null;
        if (!$deviceId) return $res->withStatus(400);
        Db::query('UPDATE devices SET customer_id=?, profile_id=? WHERE id=?', [$customerId, $profileId, $deviceId]);
        $res->getBody()->write(json_encode(['ok'=>true]));
        return $res->withHeader('Content-Type','application/json');
    });
};
