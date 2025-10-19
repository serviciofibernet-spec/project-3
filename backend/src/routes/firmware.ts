import { Router } from 'express';
import { z } from 'zod';
import { downloadFirmware } from '../genieacs.js';

export const router = Router();

router.post('/:id/upgrade', async (req, res) => {
  const schema = z.object({ url: z.string().url(), fileSize: z.number().int().optional(), username: z.string().optional(), password: z.string().optional() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json(parsed.error.flatten());
  const { url, fileSize, username, password } = parsed.data;
  try {
    const task = await downloadFirmware(req.params.id, url, fileSize, username, password);
    res.json({ task });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});
