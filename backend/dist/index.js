import express from 'express';
import cors from 'cors';
import { json } from 'express';
import { router as ontRouter } from './routes/ont.js';
import { router as adminRouter } from './routes/admin.js';
import { router as networkRouter } from './routes/network.js';
import { router as diagnosticsRouter } from './routes/diagnostics.js';
import { router as firmwareRouter } from './routes/firmware.js';
import { router as publicRouter } from './routes/public.js';
import { initDb } from './db.js';
import { startMonitoring } from './monitor.js';
const app = express();
app.use(cors());
app.use(json());
app.use('/api/ont', ontRouter);
app.use('/api/admin', adminRouter);
app.use('/api/network', networkRouter);
app.use('/api/diagnostics', diagnosticsRouter);
app.use('/api/firmware', firmwareRouter);
app.use('/public', publicRouter);
app.get('/health', (_req, res) => res.json({ ok: true }));
const port = process.env.PORT || 8080;
initDb()
    .then(() => {
    app.listen(port, () => console.log(`API listening on :${port}`));
    startMonitoring();
})
    .catch((err) => {
    console.error('DB connection failed', err);
    process.exit(1);
});
