import { Router } from 'express';
import { query } from '../lib/db.js';
import { z } from 'zod';

export const router = Router();

const payloadSchema = z.object({
  acsId: z.string(),
  serial: z.string().optional(),
  model: z.string().optional(),
});

router.post('/', async (req, res) => {
  const payload = payloadSchema.parse(req.body);
  const [rows] = await query('SELECT id FROM devices WHERE acs_id=?', [payload.acsId]);
  if (rows.length === 0) {
    // naive auto-assignment: match by serial to a customer if exists
    const [customers] = await query('SELECT id FROM customers WHERE doc_id=? OR phone=? OR email=? LIMIT 1', [payload.serial ?? null, null, null]);
    const customerId = customers?.[0]?.id ?? null;
    // match profile by model
    const [profiles] = await query('SELECT id FROM profiles WHERE model IS NULL OR model=? ORDER BY model IS NULL ASC LIMIT 1', [payload.model ?? null]);
    const profileId = profiles?.[0]?.id ?? null;

    await query('INSERT INTO devices (acs_id, serial, model, customer_id, profile_id) VALUES (?, ?, ?, ?, ?)',
      [payload.acsId, payload.serial ?? null, payload.model ?? null, customerId, profileId]);
  }
  res.json({ ok: true });
});
