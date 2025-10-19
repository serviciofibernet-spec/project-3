import { Router } from 'express';
import axios from 'axios';

export const router = Router();

const nbiUrl = process.env.GENIEACS_NBI_URL || 'http://localhost:7557';

router.get('/device/:id/summary', async (req, res) => {
  try {
    const id = req.params.id;
    const query = encodeURIComponent(`_id:/${id}/i OR DeviceID.SerialNumber:/${id}/i`);
    const { data } = await axios.get(`${nbiUrl}/devices`, { params: { query, limit: 1 } });
    if (!data?.[0]) return res.status(404).json({ error: 'Device not found' });
    const device = data[0];

    // Attempt to read Huawei common telemetry fields
    const opticalDbm = device["InternetGatewayDevice"]["X_HW_DEBUG"]["OpticalInfo"]["OpticalSignalLevel"] ??
                       device["Device"]["Optical"]["Power"];

    const wlan24 = device?.InternetGatewayDevice?.LANDevice?.["1"]?.WLANConfiguration?.["1"];
    const wlan5  = device?.InternetGatewayDevice?.LANDevice?.["1"]?.WLANConfiguration?.["2"];

    const clients24 = Number(wlan24?.AssociatedDeviceNumberOfEntries ?? 0);
    const clients5  = Number(wlan5?.AssociatedDeviceNumberOfEntries ?? 0);

    const linkStatus = device?.InternetGatewayDevice?.WANDevice?.["1"]?.WANConnectionDevice?.["1"]?.WANPPPConnection?.["1"]?.ConnectionStatus
      || device?.InternetGatewayDevice?.WANDevice?.["1"]?.WANConnectionDevice?.["1"]?.WANIPConnection?.["1"]?.ConnectionStatus;

    res.json({
      id: device._id,
      serial: device.DeviceID?.SerialNumber,
      model: device.DeviceID?.ProductClass,
      opticalDbm,
      linkStatus,
      wifi: {
        clients24,
        clients5,
      }
    });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Invalid request' });
  }
});
