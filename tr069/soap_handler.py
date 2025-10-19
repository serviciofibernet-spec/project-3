"""
SOAP/XML Handler for TR-069/CWMP Protocol
"""
from lxml import etree
import uuid

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
CWMP_NS = "urn:dslforum-org:cwmp-1-0"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

NSMAP = {
    'soap': SOAP_NS,
    'cwmp': CWMP_NS,
    'xsd': XSD_NS,
    'xsi': XSI_NS
}

class SOAPHandler:
    @staticmethod
    def parse_soap_message(xml_data):
        """Parse SOAP message and extract CWMP method and parameters"""
        try:
            root = etree.fromstring(xml_data.encode('utf-8') if isinstance(xml_data, str) else xml_data)
            body = root.find('.//{%s}Body' % SOAP_NS)
            
            if body is None:
                return None, None
            
            # Get the first child of Body (the actual CWMP method)
            method = body[0] if len(body) > 0 else None
            
            if method is None:
                return None, None
            
            method_name = method.tag.replace('{%s}' % CWMP_NS, '')
            
            # Extract parameters
            parameters = {}
            for child in method:
                param_name = child.tag.replace('{%s}' % CWMP_NS, '')
                param_value = SOAPHandler._extract_value(child)
                parameters[param_name] = param_value
            
            return method_name, parameters
        except Exception as e:
            print(f"Error parsing SOAP message: {e}")
            return None, None
    
    @staticmethod
    def _extract_value(element):
        """Extract value from XML element, handling arrays and structures"""
        # Check if it's an array
        array_type = element.get('{%s}arrayType' % SOAP_NS)
        if array_type or element.tag.endswith('List'):
            items = []
            for child in element:
                items.append(SOAPHandler._extract_value(child))
            return items
        
        # Check if it has children (structure)
        if len(element) > 0:
            result = {}
            for child in element:
                child_name = child.tag.replace('{%s}' % CWMP_NS, '')
                result[child_name] = SOAPHandler._extract_value(child)
            return result
        
        # Simple value
        return element.text
    
    @staticmethod
    def create_inform_response(max_envelopes=1):
        """Create InformResponse message"""
        root = etree.Element('{%s}Envelope' % SOAP_NS, nsmap=NSMAP)
        body = etree.SubElement(root, '{%s}Body' % SOAP_NS)
        inform_response = etree.SubElement(body, '{%s}InformResponse' % CWMP_NS)
        max_env = etree.SubElement(inform_response, 'MaxEnvelopes')
        max_env.text = str(max_envelopes)
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    @staticmethod
    def create_get_parameter_values(parameters):
        """Create GetParameterValues request"""
        root = etree.Element('{%s}Envelope' % SOAP_NS, nsmap=NSMAP)
        header = etree.SubElement(root, '{%s}Header' % SOAP_NS)
        header_id = etree.SubElement(header, '{%s}ID' % CWMP_NS, attrib={'mustUnderstand': '1'})
        header_id.text = str(uuid.uuid4())
        
        body = etree.SubElement(root, '{%s}Body' % SOAP_NS)
        gpv = etree.SubElement(body, '{%s}GetParameterValues' % CWMP_NS)
        param_names = etree.SubElement(gpv, 'ParameterNames', attrib={'{%s}arrayType' % SOAP_NS: f'xsd:string[{len(parameters)}]'})
        
        for param in parameters:
            string_elem = etree.SubElement(param_names, 'string')
            string_elem.text = param
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    @staticmethod
    def create_set_parameter_values(parameters):
        """Create SetParameterValues request"""
        root = etree.Element('{%s}Envelope' % SOAP_NS, nsmap=NSMAP)
        header = etree.SubElement(root, '{%s}Header' % SOAP_NS)
        header_id = etree.SubElement(header, '{%s}ID' % CWMP_NS, attrib={'mustUnderstand': '1'})
        header_id.text = str(uuid.uuid4())
        
        body = etree.SubElement(root, '{%s}Body' % SOAP_NS)
        spv = etree.SubElement(body, '{%s}SetParameterValues' % CWMP_NS)
        
        param_list = etree.SubElement(spv, 'ParameterList', attrib={'{%s}arrayType' % SOAP_NS: f'cwmp:ParameterValueStruct[{len(parameters)}]'})
        
        for param_name, param_value in parameters.items():
            param_struct = etree.SubElement(param_list, 'ParameterValueStruct')
            name_elem = etree.SubElement(param_struct, 'Name')
            name_elem.text = param_name
            value_elem = etree.SubElement(param_struct, 'Value', attrib={'{%s}type' % XSI_NS: 'xsd:string'})
            value_elem.text = str(param_value)
        
        param_key = etree.SubElement(spv, 'ParameterKey')
        param_key.text = str(uuid.uuid4())
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    @staticmethod
    def create_reboot():
        """Create Reboot request"""
        root = etree.Element('{%s}Envelope' % SOAP_NS, nsmap=NSMAP)
        header = etree.SubElement(root, '{%s}Header' % SOAP_NS)
        header_id = etree.SubElement(header, '{%s}ID' % CWMP_NS, attrib={'mustUnderstand': '1'})
        header_id.text = str(uuid.uuid4())
        
        body = etree.SubElement(root, '{%s}Body' % SOAP_NS)
        reboot = etree.SubElement(body, '{%s}Reboot' % CWMP_NS)
        command_key = etree.SubElement(reboot, 'CommandKey')
        command_key.text = f'Reboot_{uuid.uuid4()}'
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    @staticmethod
    def create_download(url, file_type='1 Firmware Upgrade Image', file_size=0, username='', password=''):
        """Create Download (Firmware Upgrade) request"""
        root = etree.Element('{%s}Envelope' % SOAP_NS, nsmap=NSMAP)
        header = etree.SubElement(root, '{%s}Header' % SOAP_NS)
        header_id = etree.SubElement(header, '{%s}ID' % CWMP_NS, attrib={'mustUnderstand': '1'})
        header_id.text = str(uuid.uuid4())
        
        body = etree.SubElement(root, '{%s}Body' % SOAP_NS)
        download = etree.SubElement(body, '{%s}Download' % CWMP_NS)
        
        command_key = etree.SubElement(download, 'CommandKey')
        command_key.text = f'Download_{uuid.uuid4()}'
        
        file_type_elem = etree.SubElement(download, 'FileType')
        file_type_elem.text = file_type
        
        url_elem = etree.SubElement(download, 'URL')
        url_elem.text = url
        
        username_elem = etree.SubElement(download, 'Username')
        username_elem.text = username
        
        password_elem = etree.SubElement(download, 'Password')
        password_elem.text = password
        
        file_size_elem = etree.SubElement(download, 'FileSize')
        file_size_elem.text = str(file_size)
        
        target_filename = etree.SubElement(download, 'TargetFileName')
        target_filename.text = ''
        
        delay_seconds = etree.SubElement(download, 'DelaySeconds')
        delay_seconds.text = '0'
        
        success_url = etree.SubElement(download, 'SuccessURL')
        success_url.text = ''
        
        failure_url = etree.SubElement(download, 'FailureURL')
        failure_url.text = ''
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    @staticmethod
    def create_factory_reset():
        """Create FactoryReset request"""
        root = etree.Element('{%s}Envelope' % SOAP_NS, nsmap=NSMAP)
        header = etree.SubElement(root, '{%s}Header' % SOAP_NS)
        header_id = etree.SubElement(header, '{%s}ID' % CWMP_NS, attrib={'mustUnderstand': '1'})
        header_id.text = str(uuid.uuid4())
        
        body = etree.SubElement(root, '{%s}Body' % SOAP_NS)
        factory_reset = etree.SubElement(body, '{%s}FactoryReset' % CWMP_NS)
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    @staticmethod
    def create_empty_response():
        """Create empty SOAP response (no more requests)"""
        root = etree.Element('{%s}Envelope' % SOAP_NS, nsmap=NSMAP)
        body = etree.SubElement(root, '{%s}Body' % SOAP_NS)
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    @staticmethod
    def create_get_rpc_methods():
        """Create GetRPCMethods request"""
        root = etree.Element('{%s}Envelope' % SOAP_NS, nsmap=NSMAP)
        header = etree.SubElement(root, '{%s}Header' % SOAP_NS)
        header_id = etree.SubElement(header, '{%s}ID' % CWMP_NS, attrib={'mustUnderstand': '1'})
        header_id.text = str(uuid.uuid4())
        
        body = etree.SubElement(root, '{%s}Body' % SOAP_NS)
        get_rpc = etree.SubElement(body, '{%s}GetRPCMethods' % CWMP_NS)
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
