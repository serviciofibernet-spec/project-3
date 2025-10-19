"""
Connection Request - Initiate connection to CPE
"""
import requests
from requests.auth import HTTPDigestAuth
from lxml import etree
from tr069.soap_handler import SOAP_NS, CWMP_NS

def send_connection_request(device):
    """
    Send connection request to device to initiate CWMP session
    This is used to trigger the device to connect to ACS immediately
    """
    try:
        if not device.connection_request_url:
            print(f"No connection request URL for device {device.serial_number}")
            return False
        
        # Create empty connection request (HTTP GET or POST)
        # Some devices expect POST with empty body, others GET
        
        auth = None
        if device.connection_request_username and device.connection_request_password:
            auth = HTTPDigestAuth(
                device.connection_request_username,
                device.connection_request_password
            )
        
        # Try POST first
        try:
            response = requests.post(
                device.connection_request_url,
                auth=auth,
                timeout=10,
                verify=False  # Many ONTs use self-signed certificates
            )
            
            if response.status_code in [200, 204]:
                print(f"Connection request sent to {device.serial_number}")
                return True
                
        except Exception as e:
            print(f"POST failed, trying GET: {e}")
        
        # Try GET as fallback
        try:
            response = requests.get(
                device.connection_request_url,
                auth=auth,
                timeout=10,
                verify=False
            )
            
            if response.status_code in [200, 204]:
                print(f"Connection request sent to {device.serial_number}")
                return True
                
        except Exception as e:
            print(f"GET also failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"Error sending connection request: {e}")
        return False

def trigger_device_connection(device_id):
    """
    Trigger a device to connect to ACS
    Useful for immediate configuration changes
    """
    from database.models import Device
    
    device = Device.query.get(device_id)
    if not device:
        return False
    
    return send_connection_request(device)
