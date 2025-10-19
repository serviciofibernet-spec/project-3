import { Ont } from './models.js';
import { searchDevices } from './genieacs.js';
export async function pollAndSync() {
    // Discover ONTs from GenieACS and sync basic info
    const query = { _limit: 100, _sort: [['_lastInform', -1]] };
    const devices = await searchDevices(query);
    for (const d of devices) {
        const device_id = d?._id;
        const serial = d?.device?.SerialNumber;
        const model = d?.device?.ProductClass;
        const [ont] = await Ont.findOrCreate({ where: { device_id }, defaults: { device_id, serial, model } });
        if (ont.serial !== serial || ont.model !== model) {
            ont.serial = serial;
            ont.model = model;
            await ont.save();
        }
    }
}
export function startMonitoring() {
    const intervalMs = Number(process.env.MONITOR_INTERVAL_MS || '60000');
    setInterval(() => {
        pollAndSync().catch((e) => console.error('monitor error', e.message));
    }, intervalMs);
}
