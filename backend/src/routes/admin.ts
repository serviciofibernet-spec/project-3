import { Router } from 'express';
import { z } from 'zod';
import { Ont } from '../models.js';

export const router = Router();

router.post('/assign', async (req, res) => {
  const schema = z.object({ device_id: z.string(), customer_id: z.number().int() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json(parsed.error.flatten());
  const { device_id, customer_id } = parsed.data;
  const [ont] = await Ont.findOrCreate({ where: { device_id }, defaults: { device_id, customer_id } });
  ont.customer_id = customer_id;
  await ont.save();
  res.json({ ok: true, ont });
});

router.post('/profile', async (req, res) => {
  // Placeholder for creating auto-provision profiles by model
  res.json({ ok: true });
});
