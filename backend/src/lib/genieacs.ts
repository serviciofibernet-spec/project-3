import axios from 'axios';

const nbiUrl = process.env.GENIEACS_NBI_URL || 'http://localhost:7557';

export type TaskBody = Record<string, unknown>;

export async function createTask(deviceId: string, name: string, body: TaskBody) {
  const url = `${nbiUrl}/devices/${encodeURIComponent(deviceId)}/tasks`;
  const { data } = await axios.post(url, { name, ...body });
  return data;
}

export async function getDeviceBySerialOrId(identifier: string) {
  const url = `${nbiUrl}/devices`;
  const query = encodeURIComponent(`_id:/${identifier}/i OR DeviceID.SerialNumber:/${identifier}/i`);
  const { data } = await axios.get(url, { params: { query, limit: 1 } });
  return data?.[0] ?? null;
}

export async function refreshObject(deviceId: string, objectName: string) {
  return createTask(deviceId, 'refreshObject', { objectName });
}

export async function setParameterValues(deviceId: string, parameters: Record<string, string | number | boolean>) {
  return createTask(deviceId, 'setParameterValues', { parameterValues: parameters });
}

export async function reboot(deviceId: string) {
  return createTask(deviceId, 'reboot', {});
}

export async function downloadFirmware(deviceId: string, url: string, fileType = '1 Firmware Upgrade Image') {
  return createTask(deviceId, 'download', { file: url, fileType });
}
