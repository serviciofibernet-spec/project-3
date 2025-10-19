#!/usr/bin/env python3
"""
Simple TR-069 test client to demonstrate server functionality
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime

class TR069TestClient:
    """Simple TR-069 test client"""
    
    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_soap_envelope(self, method_name: str, method_data: dict) -> str:
        """Create SOAP envelope for TR-069 method"""
        envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID>1</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:{method_name}>
"""
        
        for key, value in method_data.items():
            if isinstance(value, dict):
                envelope += f"            <{key}>\n"
                for sub_key, sub_value in value.items():
                    envelope += f"                <{sub_key}>{sub_value}</{sub_key}>\n"
                envelope += f"            </{key}>\n"
            else:
                envelope += f"            <{key}>{value}</{key}>\n"
        
        envelope += f"""        </cwmp:{method_name}>
    </soap:Body>
</soap:Envelope>"""
        return envelope
    
    async def send_inform(self, device_id: str = "TEST-DEVICE-001"):
        """Send Inform message to server"""
        inform_data = {
            "DeviceId": {
                "Manufacturer": "TestManufacturer",
                "ModelName": "TestModel",
                "SerialNumber": device_id
            },
            "Event": {
                "EventCode": "0 BOOTSTRAP",
                "CommandKey": ""
            },
            "MaxEnvelopes": "1",
            "CurrentTime": datetime.now().isoformat(),
            "RetryCount": "0",
            "ParameterList": {
                "ParameterValueStruct": [
                    {"Name": "Device.DeviceInfo.SoftwareVersion", "Value": "1.0.0"},
                    {"Name": "Device.DeviceInfo.HardwareVersion", "Value": "1.0"},
                    {"Name": "Device.ManagementServer.ConnectionRequestURL", "Value": "http://device.example.com:8080/connection"}
                ]
            }
        }
        
        soap_xml = self.create_soap_envelope("Inform", inform_data)
        
        async with self.session.post(
            f"{self.server_url}/tr069",
            data=soap_xml,
            headers={"Content-Type": "text/xml; charset=utf-8"}
        ) as response:
            return await response.text()
    
    async def send_get_parameter_values(self, device_id: str, parameter_names: list):
        """Send GetParameterValues request"""
        get_params_data = {
            "DeviceId": {
                "SerialNumber": device_id
            },
            "ParameterNames": {
                "string": parameter_names
            }
        }
        
        soap_xml = self.create_soap_envelope("GetParameterValues", get_params_data)
        
        async with self.session.post(
            f"{self.server_url}/tr069",
            data=soap_xml,
            headers={"Content-Type": "text/xml; charset=utf-8"}
        ) as response:
            return await response.text()
    
    async def send_set_parameter_values(self, device_id: str, parameters: dict):
        """Send SetParameterValues request"""
        param_list = []
        for name, value in parameters.items():
            param_list.append({"Name": name, "Value": value})
        
        set_params_data = {
            "DeviceId": {
                "SerialNumber": device_id
            },
            "ParameterList": {
                "ParameterValueStruct": param_list
            },
            "ParameterKey": "test-key-123"
        }
        
        soap_xml = self.create_soap_envelope("SetParameterValues", set_params_data)
        
        async with self.session.post(
            f"{self.server_url}/tr069",
            data=soap_xml,
            headers={"Content-Type": "text/xml; charset=utf-8"}
        ) as response:
            return await response.text()
    
    async def get_devices_rest(self):
        """Get devices via REST API"""
        async with self.session.get(f"{self.server_url}/devices") as response:
            return await response.json()

async def test_server():
    """Test the TR-069 server"""
    print("Testing TR-069 Server...")
    print("=" * 50)
    
    async with TR069TestClient() as client:
        # Test 1: Send Inform message
        print("1. Sending Inform message...")
        try:
            response = await client.send_inform("TEST-DEVICE-001")
            print("   ✓ Inform sent successfully")
            print(f"   Response: {response[:200]}...")
        except Exception as e:
            print(f"   ✗ Error sending Inform: {e}")
        
        print()
        
        # Test 2: Get devices via REST API
        print("2. Getting devices via REST API...")
        try:
            devices = await client.get_devices_rest()
            print(f"   ✓ Found {len(devices)} devices")
            for device in devices:
                print(f"   - {device['manufacturer']} {device['model']} ({device['serial_number']})")
        except Exception as e:
            print(f"   ✗ Error getting devices: {e}")
        
        print()
        
        # Test 3: Get parameter values
        print("3. Getting parameter values...")
        try:
            response = await client.send_get_parameter_values(
                "TEST-DEVICE-001",
                ["Device.DeviceInfo.Manufacturer", "Device.DeviceInfo.ModelName"]
            )
            print("   ✓ GetParameterValues sent successfully")
            print(f"   Response: {response[:200]}...")
        except Exception as e:
            print(f"   ✗ Error getting parameters: {e}")
        
        print()
        
        # Test 4: Set parameter values
        print("4. Setting parameter values...")
        try:
            response = await client.send_set_parameter_values(
                "TEST-DEVICE-001",
                {
                    "Device.WiFi.Radio.1.Enable": "true",
                    "Device.WiFi.Radio.1.SSID": "TestWiFi",
                    "Device.WiFi.Radio.1.Password": "testpass123"
                }
            )
            print("   ✓ SetParameterValues sent successfully")
            print(f"   Response: {response[:200]}...")
        except Exception as e:
            print(f"   ✗ Error setting parameters: {e}")
        
        print()
        print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_server())