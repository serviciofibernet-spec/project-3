#!/usr/bin/env python3
"""
TR069 Data Model Implementation
Defines the parameter tree structure and data types
"""

import json
import os
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ParameterNode:
    """Represents a node in the parameter tree"""
    
    def __init__(self, name: str, writable: bool = True, value: Any = None, node_type: str = "object"):
        self.name = name
        self.writable = writable
        self.value = value
        self.node_type = node_type  # object, string, int, boolean, dateTime
        self.children = {}
        self.attributes = {}
    
    def add_child(self, name: str, node: 'ParameterNode'):
        """Add a child node"""
        self.children[name] = node
    
    def get_child(self, name: str) -> Optional['ParameterNode']:
        """Get a child node"""
        return self.children.get(name)
    
    def get_path(self, path: str) -> Optional['ParameterNode']:
        """Get node by path (e.g., 'Device.DeviceInfo.SerialNumber')"""
        parts = path.split('.')
        current = self
        
        for part in parts:
            if part in current.children:
                current = current.children[part]
            else:
                return None
        
        return current
    
    def set_value(self, value: Any):
        """Set node value"""
        if self.writable:
            self.value = value
            return True
        return False
    
    def to_dict(self) -> Dict:
        """Convert node to dictionary"""
        result = {
            'name': self.name,
            'type': self.node_type,
            'writable': self.writable,
            'value': self.value,
            'attributes': self.attributes
        }
        
        if self.children:
            result['children'] = {
                name: child.to_dict() for name, child in self.children.items()
            }
        
        return result

class TR069DataModel:
    """TR069 Data Model following TR-181 specification"""
    
    def __init__(self):
        self.root = ParameterNode("", node_type="object")
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize the standard TR069 data model"""
        
        # Create Device root
        device = ParameterNode("Device", writable=False, node_type="object")
        self.root.add_child("Device", device)
        
        # Device.DeviceInfo
        device_info = ParameterNode("DeviceInfo", writable=False, node_type="object")
        device.add_child("DeviceInfo", device_info)
        
        # Basic device information parameters
        device_info.add_child("Manufacturer", ParameterNode("Manufacturer", False, "Generic", "string"))
        device_info.add_child("ManufacturerOUI", ParameterNode("ManufacturerOUI", False, "000000", "string"))
        device_info.add_child("ModelName", ParameterNode("ModelName", False, "TR069Device", "string"))
        device_info.add_child("Description", ParameterNode("Description", False, "TR069 Compatible Device", "string"))
        device_info.add_child("SerialNumber", ParameterNode("SerialNumber", False, "000000000001", "string"))
        device_info.add_child("HardwareVersion", ParameterNode("HardwareVersion", False, "1.0", "string"))
        device_info.add_child("SoftwareVersion", ParameterNode("SoftwareVersion", False, "1.0.0", "string"))
        device_info.add_child("UpTime", ParameterNode("UpTime", False, 0, "unsignedInt"))
        device_info.add_child("FirstUseDate", ParameterNode("FirstUseDate", False, datetime.now().isoformat(), "dateTime"))
        
        # Device.ManagementServer
        mgmt_server = ParameterNode("ManagementServer", writable=False, node_type="object")
        device.add_child("ManagementServer", mgmt_server)
        
        mgmt_server.add_child("URL", ParameterNode("URL", True, "http://localhost:7547", "string"))
        mgmt_server.add_child("Username", ParameterNode("Username", True, "", "string"))
        mgmt_server.add_child("Password", ParameterNode("Password", True, "", "string"))
        mgmt_server.add_child("PeriodicInformEnable", ParameterNode("PeriodicInformEnable", True, True, "boolean"))
        mgmt_server.add_child("PeriodicInformInterval", ParameterNode("PeriodicInformInterval", True, 3600, "unsignedInt"))
        mgmt_server.add_child("PeriodicInformTime", ParameterNode("PeriodicInformTime", True, datetime.now().isoformat(), "dateTime"))
        mgmt_server.add_child("ParameterKey", ParameterNode("ParameterKey", False, "", "string"))
        mgmt_server.add_child("ConnectionRequestURL", ParameterNode("ConnectionRequestURL", False, "", "string"))
        mgmt_server.add_child("ConnectionRequestUsername", ParameterNode("ConnectionRequestUsername", True, "", "string"))
        mgmt_server.add_child("ConnectionRequestPassword", ParameterNode("ConnectionRequestPassword", True, "", "string"))
        
        # Device.LAN
        lan = ParameterNode("LAN", writable=False, node_type="object")
        device.add_child("LAN", lan)
        
        # Device.LAN.IPInterface
        ip_interface = ParameterNode("IPInterface", writable=False, node_type="object")
        lan.add_child("IPInterface", ip_interface)
        
        # Device.LAN.IPInterface.1
        ip_interface_1 = ParameterNode("1", writable=False, node_type="object")
        ip_interface.add_child("1", ip_interface_1)
        
        ip_interface_1.add_child("Enable", ParameterNode("Enable", True, True, "boolean"))
        ip_interface_1.add_child("IPAddress", ParameterNode("IPAddress", True, "192.168.1.1", "string"))
        ip_interface_1.add_child("SubnetMask", ParameterNode("SubnetMask", True, "255.255.255.0", "string"))
        ip_interface_1.add_child("AddressingType", ParameterNode("AddressingType", True, "Static", "string"))
        
        # Device.WiFi
        wifi = ParameterNode("WiFi", writable=False, node_type="object")
        device.add_child("WiFi", wifi)
        
        # Device.WiFi.Radio
        radio = ParameterNode("Radio", writable=False, node_type="object")
        wifi.add_child("Radio", radio)
        
        # Device.WiFi.Radio.1
        radio_1 = ParameterNode("1", writable=False, node_type="object")
        radio.add_child("1", radio_1)
        
        radio_1.add_child("Enable", ParameterNode("Enable", True, True, "boolean"))
        radio_1.add_child("Status", ParameterNode("Status", False, "Up", "string"))
        radio_1.add_child("Channel", ParameterNode("Channel", True, 6, "unsignedInt"))
        radio_1.add_child("AutoChannelEnable", ParameterNode("AutoChannelEnable", True, True, "boolean"))
        radio_1.add_child("OperatingFrequencyBand", ParameterNode("OperatingFrequencyBand", True, "2.4GHz", "string"))
        
        # Device.WiFi.SSID
        ssid = ParameterNode("SSID", writable=False, node_type="object")
        wifi.add_child("SSID", ssid)
        
        # Device.WiFi.SSID.1
        ssid_1 = ParameterNode("1", writable=False, node_type="object")
        ssid.add_child("1", ssid_1)
        
        ssid_1.add_child("Enable", ParameterNode("Enable", True, True, "boolean"))
        ssid_1.add_child("Status", ParameterNode("Status", False, "Up", "string"))
        ssid_1.add_child("SSID", ParameterNode("SSID", True, "TR069_Network", "string"))
        ssid_1.add_child("BSSID", ParameterNode("BSSID", False, "00:00:00:00:00:00", "string"))
        
        # Device.WiFi.AccessPoint
        ap = ParameterNode("AccessPoint", writable=False, node_type="object")
        wifi.add_child("AccessPoint", ap)
        
        # Device.WiFi.AccessPoint.1
        ap_1 = ParameterNode("1", writable=False, node_type="object")
        ap.add_child("1", ap_1)
        
        ap_1.add_child("Enable", ParameterNode("Enable", True, True, "boolean"))
        ap_1.add_child("Status", ParameterNode("Status", False, "Enabled", "string"))
        
        # Device.WiFi.AccessPoint.1.Security
        security = ParameterNode("Security", writable=False, node_type="object")
        ap_1.add_child("Security", security)
        
        security.add_child("ModesSupported", ParameterNode("ModesSupported", False, "None,WPA2-Personal,WPA3-Personal", "string"))
        security.add_child("ModeEnabled", ParameterNode("ModeEnabled", True, "WPA2-Personal", "string"))
        security.add_child("PreSharedKey", ParameterNode("PreSharedKey", True, "", "string"))
        security.add_child("KeyPassphrase", ParameterNode("KeyPassphrase", True, "", "string"))
        
        # Device.Time
        time = ParameterNode("Time", writable=False, node_type="object")
        device.add_child("Time", time)
        
        time.add_child("NTPServer1", ParameterNode("NTPServer1", True, "pool.ntp.org", "string"))
        time.add_child("NTPServer2", ParameterNode("NTPServer2", True, "time.google.com", "string"))
        time.add_child("CurrentLocalTime", ParameterNode("CurrentLocalTime", False, datetime.now().isoformat(), "dateTime"))
        time.add_child("LocalTimeZone", ParameterNode("LocalTimeZone", True, "UTC", "string"))
        
        logger.info("Data model initialized")
    
    def get_parameter_value(self, path: str) -> Optional[Any]:
        """Get parameter value by path"""
        node = self.root.get_path(path)
        if node:
            return node.value
        return None
    
    def set_parameter_value(self, path: str, value: Any) -> bool:
        """Set parameter value by path"""
        node = self.root.get_path(path)
        if node and node.writable:
            # Type conversion based on node type
            if node.node_type == "boolean":
                value = str(value).lower() in ("true", "1", "yes")
            elif node.node_type in ("int", "unsignedInt"):
                value = int(value)
            elif node.node_type == "string":
                value = str(value)
            
            return node.set_value(value)
        return False
    
    def get_parameter_names(self, path: str = "", next_level: bool = False) -> List[Dict]:
        """Get parameter names starting from path"""
        if not path:
            node = self.root
        else:
            node = self.root.get_path(path)
        
        if not node:
            return []
        
        results = []
        
        def traverse(current_node, current_path):
            full_path = f"{current_path}.{current_node.name}" if current_path else current_node.name
            
            if current_node.name:  # Skip root node
                results.append({
                    'name': full_path,
                    'writable': current_node.writable
                })
            
            if not next_level or current_path == path:
                for child_name, child_node in current_node.children.items():
                    traverse(child_node, full_path)
        
        traverse(node, path)
        return results
    
    def add_object(self, path: str, name: str) -> bool:
        """Add a new object instance"""
        parent = self.root.get_path(path)
        if parent and parent.node_type == "object":
            # Find next available index
            index = 1
            while str(index) in parent.children:
                index += 1
            
            new_object = ParameterNode(str(index), writable=False, node_type="object")
            parent.add_child(str(index), new_object)
            return True
        return False
    
    def delete_object(self, path: str) -> bool:
        """Delete an object instance"""
        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            parent_path, obj_name = parts
            parent = self.root.get_path(parent_path)
            if parent and obj_name in parent.children:
                del parent.children[obj_name]
                return True
        return False
    
    def export_to_json(self, filepath: str):
        """Export data model to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.root.to_dict(), f, indent=2)
            logger.info(f"Data model exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting data model: {e}")
    
    def import_from_json(self, filepath: str):
        """Import data model from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # TODO: Implement JSON to model conversion
            logger.info(f"Data model imported from {filepath}")
        except Exception as e:
            logger.error(f"Error importing data model: {e}")