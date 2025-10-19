import { Router } from 'express';
import { getDevice } from '../genieacs.js';

export const router = Router();

router.get('/:id/clients', async (req, res) => {
  try {
    const device = await getDevice(req.params.id);
    const clients24 = device?.parameters?.['InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.AssociatedDeviceNumberOfEntries']?.value ?? null;
    const clients5 = device?.parameters?.['InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.AssociatedDeviceNumberOfEntries']?.value ?? null;
    res.json({ clients24, clients5 });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});
