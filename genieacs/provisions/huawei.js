/* Huawei provisioning tailored example. Adjust per exact models. */

// eslint-disable-next-line no-undef
const provision = async (device) => {
  const vendor = device?.device?.Manufacturer || '';
  if (!/Huawei/i.test(vendor)) return;

  const serial = device?.device?.SerialNumber || 'ONT';
  const model = device?.device?.ProductClass || '';

  const params = {};

  // Default WiFi (2.4/5G) — verify instance numbers per model
  params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.SSID'] = `ISP_${serial.slice(-6)}`;
  params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.PreSharedKey.1.PreSharedKey'] = `${serial.slice(-6)}2025`;
  params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.SSID'] = `ISP5_${serial.slice(-6)}`;
  params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.PreSharedKey.1.PreSharedKey'] = `${serial.slice(-6)}2025`;

  // Example WAN profile placeholders (model-specific)
  // params['InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Username'] = 'pppoe-user';
  // params['InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Password'] = 'pppoe-pass';
  // params['InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.X_HW_VLANIDMark'] = 10;

  // Ensure apply/write
  // eslint-disable-next-line no-undef
  return declare(params, { writable: true });
};

// eslint-disable-next-line no-undef
module.exports = provision;
