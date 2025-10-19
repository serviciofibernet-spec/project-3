import { Router } from 'express';
import { z } from 'zod';
import { query } from '../lib/db.js';

export const router = Router();

router.get('/customers', async (_req, res) => {
  const [rows] = await query('SELECT * FROM customers ORDER BY id DESC');
  res.json(rows);
});

const upsertCustomer = z.object({ id: z.number().int().optional(), name: z.string(), doc_id: z.string().optional(), phone: z.string().optional(), email: z.string().email().optional() });
router.post('/customers', async (req, res) => {
  const c = upsertCustomer.parse(req.body);
  if (c.id) {
    await query('UPDATE customers SET name=?, doc_id=?, phone=?, email=? WHERE id=?', [c.name, c.doc_id ?? null, c.phone ?? null, c.email ?? null, c.id]);
    res.json({ ok: true, id: c.id });
  } else {
    const [r]: any = await query('INSERT INTO customers (name, doc_id, phone, email) VALUES (?, ?, ?, ?)', [c.name, c.doc_id ?? null, c.phone ?? null, c.email ?? null]);
    res.json({ ok: true, id: r.insertId });
  }
});

router.get('/devices', async (_req, res) => {
  const [rows] = await query(
    `SELECT d.*, c.name AS customer_name, p.name AS profile_name
     FROM devices d
     LEFT JOIN customers c ON c.id = d.customer_id
     LEFT JOIN profiles p ON p.id = d.profile_id
     ORDER BY d.id DESC`
  );
  res.json(rows);
});

const assignSchema = z.object({ deviceId: z.number().int(), customerId: z.number().int().nullable(), profileId: z.number().int().nullable() });
router.post('/assign', async (req, res) => {
  const { deviceId, customerId, profileId } = assignSchema.parse(req.body);
  await query('UPDATE devices SET customer_id=?, profile_id=? WHERE id=?', [customerId, profileId, deviceId]);
  res.json({ ok: true });
});
