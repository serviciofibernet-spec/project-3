import { Router } from 'express';
import { z } from 'zod';
import { Ont } from '../models.js';
import { setParameterValues } from '../genieacs.js';
export const router = Router();
router.get('/ont/:device_id', async (req, res) => {
    const ont = await Ont.findOne({ where: { device_id: req.params.device_id } });
    if (!ont)
        return res.status(404).json({ error: 'ONT not found' });
    res.json({ ont });
});
router.post('/ont/:device_id/wifi', async (req, res) => {
    const schema = z.object({ ssid: z.string().min(1), key: z.string().min(8) });
    const parsed = schema.safeParse(req.body);
    if (!parsed.success)
        return res.status(400).json(parsed.error.flatten());
    const { ssid, key } = parsed.data;
    const ont = await Ont.findOne({ where: { device_id: req.params.device_id } });
    if (!ont)
        return res.status(404).json({ error: 'ONT not found' });
    const params = {
        'InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.SSID': ssid,
        'InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.PreSharedKey.1.PreSharedKey': key,
    };
    try {
        await setParameterValues(req.params.device_id, params);
        ont.ssid = ssid;
        ont.wifi_key = key;
        await ont.save();
        res.json({ ok: true });
    }
    catch (e) {
        res.status(500).json({ error: e.message });
    }
});
