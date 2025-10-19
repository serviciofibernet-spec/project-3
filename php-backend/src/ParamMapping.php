<?php
namespace App;

class ParamMapping {
    public static function wifiParams(?string $model, array $payload): array {
        $params = [];
        if (!empty($payload['ssid24'])) $params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.SSID'] = (string)$payload['ssid24'];
        if (!empty($payload['pass24'])) $params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.PreSharedKey.1.PreSharedKey'] = (string)$payload['pass24'];
        if (!empty($payload['ssid5']))  $params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.SSID'] = (string)$payload['ssid5'];
        if (!empty($payload['pass5']))  $params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.PreSharedKey.1.PreSharedKey'] = (string)$payload['pass5'];
        return $params;
    }

    public static function vlanParams(?string $model, int $vlanId): array {
        return [
            'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.X_HW_ServiceList' => 'INTERNET',
            'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.X_HW_VLANIDMark' => $vlanId,
        ];
    }

    public static function dnsParams(?string $model, string $primary, ?string $secondary = null): array {
        $dns = $secondary ? "$primary,$secondary" : $primary;
        return [
            'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.DNSOverrideAllowed' => '1',
            'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.DNSServers' => $dns,
            'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.DNSOverrideAllowed' => '1',
            'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.DNSServers' => $dns,
        ];
    }

    public static function portEnable(?string $model, int $port, bool $enable): array {
        return ["InternetGatewayDevice.LANDevice.1.LANEthernetInterfaceConfig.$port.Enable" => $enable ? '1' : '0'];
    }

    public static function wifiRadio(?string $model, string $band, bool $enable): array {
        $idx = $band === '2.4' ? 1 : 2;
        return ["InternetGatewayDevice.LANDevice.1.WLANConfiguration.$idx.Enable" => $enable ? '1' : '0'];
    }
}
