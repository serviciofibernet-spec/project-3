const { nanoid } = require('nanoid');

class DeviceStore {
  constructor() {
    this.devices = new Map(); // key: deviceKey (OUI-Serial), value: device info
    this.queues = new Map(); // key: deviceKey, value: array of pending SOAP envelopes
    this.lastSeen = new Map(); // deviceKey -> timestamp
    this.sessions = new Map(); // sessionId -> { deviceKey, lastActivity }
  }

  deviceKeyFrom({ oui, serialNumber }) {
    return `${oui || 'UNK'}-${serialNumber || nanoid(6)}`;
  }

  upsertDevice(info) {
    const key = this.deviceKeyFrom(info);
    const existing = this.devices.get(key) || {};
    const merged = { ...existing, ...info };
    this.devices.set(key, merged);
    this.lastSeen.set(key, Date.now());
    if (!this.queues.has(key)) this.queues.set(key, []);
    return { key, device: merged };
  }

  enqueueCommand(deviceKey, soapXml, meta = {}) {
    const q = this.queues.get(deviceKey) || [];
    q.push({ xml: soapXml, meta, enqueuedAt: Date.now() });
    this.queues.set(deviceKey, q);
    return q.length;
  }

  peekNext(deviceKey) {
    const q = this.queues.get(deviceKey) || [];
    return q[0] || null;
  }

  dequeue(deviceKey) {
    const q = this.queues.get(deviceKey) || [];
    const item = q.shift();
    this.queues.set(deviceKey, q);
    return item || null;
  }

  listDevices() {
    const list = [];
    for (const [key, device] of this.devices.entries()) {
      list.push({ key, ...device, lastSeen: this.lastSeen.get(key) });
    }
    return list;
  }
}

module.exports = { DeviceStore };
