import { Router } from 'express';
import { z } from 'zod';
import { setParameterValues } from '../genieacs.js';

export const router = Router();

router.post('/:id/pppoe', async (req, res) => {
  const schema = z.object({ username: z.string(), password: z.string() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json(parsed.error.flatten());
  const { username, password } = parsed.data;
  const params: Record<string, any> = {
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Username': username,
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Password': password,
  };
  try {
    const task = await setParameterValues(req.params.id, params);
    res.json({ task });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

router.post('/:id/vlan', async (req, res) => {
  const schema = z.object({ vlanId: z.number().int().min(1).max(4094) });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json(parsed.error.flatten());
  const { vlanId } = parsed.data;
  const params: Record<string, any> = {
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.X_HW_VLANIDMark': vlanId,
  };
  try {
    const task = await setParameterValues(req.params.id, params);
    res.json({ task });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

router.post('/:id/dns', async (req, res) => {
  const schema = z.object({ primary: z.string(), secondary: z.string().optional() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json(parsed.error.flatten());
  const { primary, secondary } = parsed.data;
  const params: Record<string, any> = {
    'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.DNSServers': secondary ? `${primary},${secondary}` : primary,
  };
  try {
    const task = await setParameterValues(req.params.id, params);
    res.json({ task });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});
