export type WifiPayload = { ssid24?: string; pass24?: string; ssid5?: string; pass5?: string };

function isHuawei(model?: string | null): boolean {
  if (!model) return false;
  const m = model.toLowerCase();
  return m.includes('huawei') || m.startsWith('hg') || m.startsWith('hs');
}

export function buildWifiParams(model: string | undefined, payload: WifiPayload): Record<string, string> {
  const params: Record<string, string> = {};
  // Defaults use TR-098-ish indexes: 1 => 2.4GHz, 2 => 5GHz
  const w24Ssid = 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.SSID';
  const w24Psk  = 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.PreSharedKey.1.PreSharedKey';
  const w5Ssid  = 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.SSID';
  const w5Psk   = 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.PreSharedKey.1.PreSharedKey';

  // Huawei models typically align with above for many CPEs; override if needed per model
  if (payload.ssid24) params[w24Ssid] = payload.ssid24;
  if (payload.pass24) params[w24Psk] = payload.pass24;
  if (payload.ssid5) params[w5Ssid] = payload.ssid5;
  if (payload.pass5) params[w5Psk] = payload.pass5;
  return params;
}

export function buildVlanParams(model: string | undefined, vlanId: number): Record<string, string | number> {
  // Common Huawei extension params under PPP connection
  return {
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.X_HW_ServiceList': 'INTERNET',
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.X_HW_VLANIDMark': Number(vlanId),
  };
}

export function buildDnsParams(model: string | undefined, primary: string, secondary?: string): Record<string, string> {
  const dns = secondary ? `${primary},${secondary}` : primary;
  return {
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.DNSOverrideAllowed': '1',
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.DNSServers': dns,
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.DNSOverrideAllowed': '1',
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.DNSServers': dns,
  };
}

export function buildPortEnableParam(model: string | undefined, port: number, enable: boolean): Record<string, string> {
  return {
    [`InternetGatewayDevice.LANDevice.1.LANEthernetInterfaceConfig.${port}.Enable`]: enable ? '1' : '0',
  };
}

export function buildWifiRadioParam(model: string | undefined, band: '2.4'|'5', enable: boolean): Record<string, string> {
  const idx = band === '2.4' ? 1 : 2;
  return {
    [`InternetGatewayDevice.LANDevice.1.WLANConfiguration.${idx}.Enable`]: enable ? '1' : '0',
  };
}
