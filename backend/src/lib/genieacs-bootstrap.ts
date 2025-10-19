import axios from 'axios';

const nbiUrl = process.env.GENIEACS_NBI_URL || 'http://localhost:7557';

export async function ensurePresets() {
  const presets = [
    {
      name: 'Initial Provision',
      weight: 0,
      precondition: "!tags.includes('provisioned')",
      config: {
        refresh: { InternetGatewayDevice: { _object: { _w: true } } },
      },
    },
  ];

  const { data: existing } = await axios.get(`${nbiUrl}/presets`);
  const names = new Set((existing || []).map((p: any) => p.name));
  for (const p of presets) {
    if (!names.has(p.name)) {
      await axios.post(`${nbiUrl}/presets`, p);
    }
  }
}
