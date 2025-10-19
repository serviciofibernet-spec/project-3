import express from 'express';
import { json } from 'express';
import { router as devicesRouter } from './routes/devices.js';
import { router as profilesRouter } from './routes/profiles.js';
import { router as monitoringRouter } from './routes/monitoring.js';
import { router as onboardingRouter } from './routes/onboarding.js';
import { router as genieacsWebhooksRouter } from './routes/genieacs-webhooks.js';
import { router as adminRouter } from './routes/admin.js';
import { bootstrapMySQL } from './init/bootstrap.js';
import { ensurePresets } from './lib/genieacs-bootstrap.js';
import { startAutoOnboardingWorker } from './worker/onboarder.js';

const app = express();
app.use(json());
app.use(express.static('src/public'));

app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

app.use('/api/devices', devicesRouter);
app.use('/api/profiles', profilesRouter);
app.use('/api/monitoring', monitoringRouter);
app.use('/api/onboarding', onboardingRouter);
app.use('/api/hooks', genieacsWebhooksRouter);
app.use('/api/admin', adminRouter);

const port = process.env.PORT ? Number(process.env.PORT) : 8080;

async function start() {
  await bootstrapMySQL();
  try { await ensurePresets(); } catch {}
  startAutoOnboardingWorker();
  app.listen(port, () => {
    console.log(`API listening on ${port}`);
  });
}

start().catch((err) => {
  console.error('Failed to start service', err);
  process.exit(1);
});
