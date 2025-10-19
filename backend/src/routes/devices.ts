import { Router } from 'express';
import { z } from 'zod';
import axios from 'axios';
import { getDeviceBySerialOrId, reboot, setParameterValues, refreshObject, downloadFirmware } from '../lib/genieacs.js';
import { buildWifiParams, buildVlanParams, buildDnsParams, buildPortEnableParam, buildWifiRadioParam } from '../lib/param-mapping.js';
import { query as dbQuery } from '../lib/db.js';

export const router = Router();

const idSchema = z.object({ id: z.string().min(1) });

const nbiUrl = process.env.GENIEACS_NBI_URL || 'http://localhost:7557';

router.get('/', async (_req, res) => {
  const [rows] = await dbQuery(
    `SELECT d.id, d.acs_id as acsId, d.serial, d.model, c.name as customerName, d.profile_id as profileId
     FROM devices d
     LEFT JOIN customers c ON c.id = d.customer_id
     ORDER BY d.id DESC`
  );
  res.json(rows);
});

router.get('/search', async (req, res) => {
  const q = (req.query.q as string) || '';
  const queryStr = q ? encodeURIComponent(q) : encodeURIComponent('*');
  const { data } = await axios.get(`${nbiUrl}/devices`, { params: { query: queryStr, limit: 50, sort: '-_lastInform' } });
  res.json(Array.isArray(data) ? data : []);
});

router.get('/:id', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });
    res.json(device);
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

const wifiSchema = z.object({
  ssid24: z.string().optional(),
  pass24: z.string().optional(),
  ssid5: z.string().optional(),
  pass5: z.string().optional(),
});

router.post('/:id/wifi', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const body = wifiSchema.parse(req.body);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });

    const params = buildWifiParams(device?.DeviceID?.ProductClass, body);

    const result = await setParameterValues(device._id, params);
    res.json({ ok: true, task: result });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

const pppoeSchema = z.object({ user: z.string(), pass: z.string() });
router.post('/:id/pppoe', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const { user, pass } = pppoeSchema.parse(req.body);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });

    const params: Record<string, string> = {
      'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Username': user,
      'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Password': pass,
      'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.NATEnabled': '1',
    };
    const result = await setParameterValues(device._id, params);
    res.json({ ok: true, task: result });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

const vlanSchema = z.object({ vlanId: z.number().int().min(1).max(4094) });
router.post('/:id/vlan', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const { vlanId } = vlanSchema.parse(req.body);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });

    const params = buildVlanParams(device?.DeviceID?.ProductClass, vlanId);
    const result = await setParameterValues(device._id, params);
    res.json({ ok: true, task: result });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

router.post('/:id/reboot', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });
    const task = await reboot(device._id);
    res.json({ ok: true, task });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

const fwSchema = z.object({ url: z.string().url(), fileType: z.string().optional() });
router.post('/:id/firmware', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const { url, fileType } = fwSchema.parse(req.body);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });
    const task = await downloadFirmware(device._id, url, fileType);
    res.json({ ok: true, task });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

router.post('/:id/refresh', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });
    const task = await refreshObject(device._id, 'InternetGatewayDevice');
    res.json({ ok: true, task });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

// Set DNS servers; try both PPP and IP connection contexts
const dnsSchema = z.object({ primary: z.string().ip(), secondary: z.string().ip().optional() });
router.post('/:id/dns', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const { primary, secondary } = dnsSchema.parse(req.body);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });
    const params = buildDnsParams(device?.DeviceID?.ProductClass, primary, secondary);
    const result = await setParameterValues(device._id, params);
    res.json({ ok: true, task: result });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

// Enable/disable LAN ethernet port by index
const portSchema = z.object({ port: z.number().int().min(1).max(8), enable: z.boolean() });
router.post('/:id/port', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const { port, enable } = portSchema.parse(req.body);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });
    const params = buildPortEnableParam(device?.DeviceID?.ProductClass, port, enable);
    const result = await setParameterValues(device._id, params);
    res.json({ ok: true, task: result });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

// Toggle WiFi radio by band 2.4/5
const radioSchema = z.object({ band: z.enum(['2.4','5']), enable: z.boolean() });
router.post('/:id/wifi-radio', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const { band, enable } = radioSchema.parse(req.body);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });
    const params = buildWifiRadioParam(device?.DeviceID?.ProductClass, band, enable);
    const result = await setParameterValues(device._id, params);
    res.json({ ok: true, task: result });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});

// Generic parameter setter
const paramsSchema = z.object({ parameters: z.record(z.union([z.string(), z.number(), z.boolean()])) });
router.post('/:id/params', async (req, res) => {
  try {
    const { id } = idSchema.parse(req.params);
    const { parameters } = paramsSchema.parse(req.body);
    const device = await getDeviceBySerialOrId(id);
    if (!device) return res.status(404).json({ error: 'Device not found' });
    const task = await setParameterValues(device._id, parameters as Record<string, any>);
    res.json({ ok: true, task });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});
