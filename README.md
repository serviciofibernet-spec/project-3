## TR-069 ACS Stack (GenieACS + Backend + MySQL)

Servicios:
- GenieACS (CWMP 7547, NBI 7557, UI 3000)
- MongoDB, Redis
- Backend Node.js (API en :8080)
- MySQL (esquema básico clientes/ONTs)

Uso:
```bash
docker compose up -d --build
```

APIs principales:
- POST /api/ont/:id/wifi { ssid24, key24, ssid5, key5 }
- POST /api/ont/:id/reboot
- GET  /api/ont/:id/status
- POST /api/network/:id/pppoe { username, password }
- POST /api/network/:id/vlan { vlanId }
- POST /api/network/:id/dns { primary, secondary? }
- GET  /api/diagnostics/:id/clients
- POST /api/firmware/:id/upgrade { url }
- Public: GET /public/ont/:device_id, POST /public/ont/:device_id/wifi

Provisions:
- Colocar lógica en `genieacs/provisions/huawei.js`.
