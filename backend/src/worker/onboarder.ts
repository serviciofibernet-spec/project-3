import axios from 'axios';
import { query } from '../lib/db.js';
import { setParameterValues } from '../lib/genieacs.js';
import { buildWifiParams, buildVlanParams } from '../lib/param-mapping.js';

const nbiUrl = process.env.GENIEACS_NBI_URL || 'http://localhost:7557';

async function fetchUnprovisionedDevices(limit = 50) {
  const queryStr = encodeURIComponent('NOT tags:provisioned');
  const { data } = await axios.get(`${nbiUrl}/devices`, { params: { query: queryStr, limit, sort: '-_lastInform' } });
  return Array.isArray(data) ? data : [];
}

async function markProvisioned(deviceId: string) {
  await axios.patch(`${nbiUrl}/devices/${encodeURIComponent(deviceId)}`, { $addToSet: { tags: 'provisioned' } });
}

async function applyProfile(device: any) {
  const acsId: string = device._id;
  const serial: string | undefined = device?.DeviceID?.SerialNumber;
  const model: string | undefined = device?.DeviceID?.ProductClass;

  const [devRows]: any = await query('SELECT id, profile_id FROM devices WHERE acs_id=?', [acsId]);
  let profileId: number | null = devRows?.[0]?.profile_id ?? null;
  if (!profileId) {
    const [p]: any = await query('SELECT id FROM profiles WHERE model IS NULL OR model=? ORDER BY model IS NULL ASC LIMIT 1', [model ?? null]);
    profileId = p?.[0]?.id ?? null;
    if (profileId) {
      await query('UPDATE devices SET profile_id=? WHERE acs_id=?', [profileId, acsId]);
    }
  }
  if (!profileId) return false;

  const [profRows]: any = await query('SELECT ssid24, pass24, ssid5, pass5, vlan_id FROM profiles WHERE id=?', [profileId]);
  const prof = profRows?.[0];
  if (!prof) return false;

  const wifiParams = buildWifiParams(model, { ssid24: prof.ssid24 ?? undefined, pass24: prof.pass24 ?? undefined, ssid5: prof.ssid5 ?? undefined, pass5: prof.pass5 ?? undefined });
  const vlanParams = prof.vlan_id ? buildVlanParams(model, Number(prof.vlan_id)) : {};
  const params: Record<string, string | number> = { ...wifiParams, ...vlanParams };

  if (Object.keys(params).length === 0) return true;

  await setParameterValues(acsId, params);
  return true;
}

export function startAutoOnboardingWorker() {
  const intervalMs = 30000;
  let running = false;
  setInterval(async () => {
    if (running) return;
    running = true;
    try {
      const devices = await fetchUnprovisionedDevices(50);
      for (const device of devices) {
        try {
          // ensure device exists in DB
          const [rows]: any = await query('SELECT id FROM devices WHERE acs_id=?', [device._id]);
          if (rows.length === 0) {
            await query('INSERT INTO devices (acs_id, serial, model) VALUES (?, ?, ?)', [device._id, device?.DeviceID?.SerialNumber ?? null, device?.DeviceID?.ProductClass ?? null]);
          }
          const applied = await applyProfile(device);
          if (applied) await markProvisioned(device._id);
        } catch (err) {
          // continue to next device
        }
      }
    } catch (e) {
      // ignore
    } finally {
      running = false;
    }
  }, intervalMs);
}
