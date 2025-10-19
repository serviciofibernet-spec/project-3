const express = require('express');
const morgan = require('morgan');
const bodyParser = require('body-parser');
const { DeviceStore } = require('./store');
const {
  parseSoap,
  getCwmpMethodName,
  buildInformResponse,
  extractInformData,
  buildGetParameterValues,
  buildReboot,
} = require('./cwmp');

const app = express();
const store = new DeviceStore();

// Raw XML parser for SOAP
app.use('/cwmp', bodyParser.text({ type: ['text/xml', 'application/xml', 'application/soap+xml', '*/*'], limit: '5mb' }));
app.use(morgan('dev'));

app.post('/cwmp', async (req, res) => {
  const xml = req.body || '';
  let envelope;
  try {
    envelope = parseSoap(xml);
  } catch (e) {
    console.error('SOAP parse error', e);
    return res.status(400).send('Invalid SOAP');
  }

  const method = getCwmpMethodName(envelope);
  // Handle Inform
  if (method && /Inform$/i.test(method)) {
    const info = extractInformData(envelope) || {};
    const { key } = store.upsertDevice(info);

    // After Inform, CPE expects InformResponse and then may send empty GetRPCMethods or we push pending commands
    const responseXml = buildInformResponse({ maxEnvelopes: 1, idHeader: undefined });
    res.set('Content-Type', 'text/xml; charset="utf-8"');
    return res.status(200).send(responseXml);
  }

  // After InformResponse, CPE often sends an empty HTTP POST with no SOAP body to pull next command
  // Detect empty body
  if (!method) {
    // Find device by last seen heuristic is unreliable; in production use session cookies or src IP mapping
    // For MVP, just pick the most recently seen device
    const devices = store.listDevices().sort((a, b) => (b.lastSeen || 0) - (a.lastSeen || 0));
    const device = devices[0];
    if (!device) {
      return res.status(204).send('');
    }
    const next = store.dequeue(device.key);
    if (!next) {
      return res.status(204).send('');
    }
    res.set('Content-Type', 'text/xml; charset="utf-8"');
    return res.status(200).send(next.xml);
  }

  // Default: acknowledge other RPCs with 204
  return res.status(204).send('');
});

// Admin API
app.use(express.json());

app.get('/api/devices', (req, res) => {
  return res.json({ devices: store.listDevices() });
});

app.post('/api/devices/:key/get', (req, res) => {
  const { key } = req.params;
  const { names } = req.body || {};
  if (!Array.isArray(names) || names.length === 0) {
    return res.status(400).json({ error: 'names array required' });
  }
  const { xml } = buildGetParameterValues({ parameterNames: names });
  const length = store.enqueueCommand(key, xml, { type: 'GetParameterValues', names });
  return res.json({ queued: true, queueLength: length });
});

app.post('/api/devices/:key/reboot', (req, res) => {
  const { key } = req.params;
  const { commandKey } = req.body || {};
  const { xml } = buildReboot({ commandKey });
  const length = store.enqueueCommand(key, xml, { type: 'Reboot', commandKey });
  return res.json({ queued: true, queueLength: length });
});

const PORT = process.env.PORT || 7547;
app.listen(PORT, () => {
  console.log(`ACS TR-069 listening on port ${PORT}`);
});
