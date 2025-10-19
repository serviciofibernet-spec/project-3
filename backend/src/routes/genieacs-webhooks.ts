import { Router } from 'express';
import { z } from 'zod';
import { query } from '../lib/db.js';

export const router = Router();

// GenieACS can call this via NBI scripts or external integration when a device first connects
const payloadSchema = z.object({
  _id: z.string(),
  DeviceID: z.object({ SerialNumber: z.string().optional(), ProductClass: z.string().optional() }).optional(),
});

router.post('/device-connected', async (req, res) => {
  try {
    const body = payloadSchema.parse(req.body);
    const acsId = body._id;
    const serial = body.DeviceID?.SerialNumber;
    const model = body.DeviceID?.ProductClass;

    const [rows] = await query('SELECT id FROM devices WHERE acs_id=?', [acsId]);
    if (rows.length === 0) {
      const [profiles] = await query('SELECT id FROM profiles WHERE model IS NULL OR model=? ORDER BY model IS NULL ASC LIMIT 1', [model ?? null]);
      const profileId = profiles?.[0]?.id ?? null;
      await query('INSERT INTO devices (acs_id, serial, model, profile_id) VALUES (?, ?, ?, ?)', [acsId, serial ?? null, model ?? null, profileId]);
    }

    res.json({ ok: true });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'invalid' });
  }
});
