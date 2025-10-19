import axios from 'axios';

const NBI = process.env.GENIEACS_NBI_URL || 'http://localhost:7557';

export async function setParameterValues(deviceId: string, params: Record<string, any>) {
  const body = { name: 'setParameterValues', device: deviceId, parameterValues: Object.entries(params) };
  const { data } = await axios.post(`${NBI}/tasks`, body);
  return data;
}

export async function reboot(deviceId: string) {
  const { data } = await axios.post(`${NBI}/tasks`, { name: 'reboot', device: deviceId });
  return data;
}

export async function getDevice(deviceId: string) {
  const { data } = await axios.get(`${NBI}/devices/${encodeURIComponent(deviceId)}`);
  return data;
}

export async function searchDevices(query: any) {
  const { data } = await axios.post(`${NBI}/devices?query=true`, query);
  return data;
}

export async function downloadFirmware(deviceId: string, url: string, fileSize?: number, username?: string, password?: string) {
  const body: any = { name: 'download', device: deviceId, fileType: '1 Firmware Upgrade Image', url };
  if (fileSize) body.fileSize = fileSize;
  if (username) body.username = username;
  if (password) body.password = password;
  const { data } = await axios.post(`${NBI}/tasks`, body);
  return data;
}
