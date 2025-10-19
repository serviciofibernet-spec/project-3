import { Router } from 'express';
import { z } from 'zod';
import { query } from '../lib/db.js';

export const router = Router();

router.get('/', async (_req, res) => {
  const [rows] = await query('SELECT id, name, model, ssid24, pass24, ssid5, pass5, vlan_id AS vlanId FROM profiles ORDER BY id DESC');
  res.json(rows);
});

const upsertSchema = z.object({
  id: z.number().int().optional(),
  name: z.string(),
  model: z.string().optional(),
  ssid24: z.string().optional(),
  pass24: z.string().optional(),
  ssid5: z.string().optional(),
  pass5: z.string().optional(),
  vlanId: z.number().int().min(1).max(4094).optional(),
});

router.post('/', async (req, res) => {
  const body = upsertSchema.parse(req.body);
  if (body.id) {
    await query(
      'UPDATE profiles SET name=?, model=?, ssid24=?, pass24=?, ssid5=?, pass5=?, vlan_id=? WHERE id=?',
      [body.name, body.model ?? null, body.ssid24 ?? null, body.pass24 ?? null, body.ssid5 ?? null, body.pass5 ?? null, body.vlanId ?? null, body.id]
    );
    res.json({ ok: true, id: body.id });
  } else {
    const [result]: any = await query(
      'INSERT INTO profiles (name, model, ssid24, pass24, ssid5, pass5, vlan_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [body.name, body.model ?? null, body.ssid24 ?? null, body.pass24 ?? null, body.ssid5 ?? null, body.pass5 ?? null, body.vlanId ?? null]
    );
    res.json({ ok: true, id: result.insertId });
  }
});
