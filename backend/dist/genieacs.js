import axios from 'axios';
const NBI = process.env.GENIEACS_NBI_URL || 'http://localhost:7557';
export async function setParameterValues(deviceId, params) {
    const body = { name: 'setParameterValues', device: deviceId, parameterValues: Object.entries(params) };
    const { data } = await axios.post(`${NBI}/tasks`, body);
    return data;
}
export async function reboot(deviceId) {
    const { data } = await axios.post(`${NBI}/tasks`, { name: 'reboot', device: deviceId });
    return data;
}
export async function getDevice(deviceId) {
    const { data } = await axios.get(`${NBI}/devices/${encodeURIComponent(deviceId)}`);
    return data;
}
export async function searchDevices(query) {
    const { data } = await axios.post(`${NBI}/devices?query=true`, query);
    return data;
}
export async function downloadFirmware(deviceId, url, fileSize, username, password) {
    const body = { name: 'download', device: deviceId, fileType: '1 Firmware Upgrade Image', url };
    if (fileSize)
        body.fileSize = fileSize;
    if (username)
        body.username = username;
    if (password)
        body.password = password;
    const { data } = await axios.post(`${NBI}/tasks`, body);
    return data;
}
