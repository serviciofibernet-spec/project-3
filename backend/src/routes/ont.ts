import { Router } from 'express';
import { z } from 'zod';
import { reboot, setParameterValues, getDevice } from '../genieacs.js';

export const router = Router();

router.post('/:id/wifi', async (req, res) => {
  const schema = z.object({
    ssid24: z.string().min(1).optional(),
    key24: z.string().min(8).optional(),
    ssid5: z.string().min(1).optional(),
    key5: z.string().min(8).optional(),
  });
  const parse = schema.safeParse(req.body);
  if (!parse.success) return res.status(400).json(parse.error.flatten());
  const { ssid24, key24, ssid5, key5 } = parse.data;

  const params: Record<string, any> = {};
  if (ssid24) params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.SSID'] = ssid24;
  if (key24) params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.PreSharedKey.1.PreSharedKey'] = key24;
  if (ssid5) params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.SSID'] = ssid5;
  if (key5) params['InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.PreSharedKey.1.PreSharedKey'] = key5;

  try {
    const task = await setParameterValues(req.params.id, params);
    res.json({ task });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

router.post('/:id/reboot', async (req, res) => {
  try {
    const task = await reboot(req.params.id);
    res.json({ task });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

router.get('/:id/status', async (req, res) => {
  try {
    const device = await getDevice(req.params.id);
    // Example fields: optical power, connection status
    const rxPower = device?.parameters?.["InternetGatewayDevice.X_HW_OPTICAL.PowerRx"]?.value ?? null;
    const txPower = device?.parameters?.["InternetGatewayDevice.X_HW_OPTICAL.PowerTx"]?.value ?? null;
    const online = device?._lastInform != null;
    res.json({ rxPower, txPower, online, device });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});
