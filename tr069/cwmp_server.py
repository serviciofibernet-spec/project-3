"""
CWMP Server - Handles TR-069 protocol communication
"""
from flask import Blueprint, request, Response
from tr069.soap_handler import SOAPHandler
from tr069.device_manager import DeviceManager
from database.models import db, Device
from datetime import datetime
import uuid

cwmp_bp = Blueprint('cwmp', __name__)

# Store active sessions
active_sessions = {}

@cwmp_bp.route('/cwmp', methods=['POST'])
def cwmp_handler():
    """Main CWMP endpoint for device communication"""
    try:
        # Get request data
        xml_data = request.data
        
        # Parse SOAP message
        method_name, parameters = SOAPHandler.parse_soap_message(xml_data)
        
        if not method_name:
            return Response("Invalid SOAP message", status=400)
        
        print(f"Received CWMP method: {method_name}")
        
        # Handle different CWMP methods
        if method_name == 'Inform':
            return handle_inform(parameters)
        elif method_name == 'TransferCompleteResponse':
            return handle_transfer_complete(parameters)
        elif method_name == 'GetParameterValuesResponse':
            return handle_get_parameter_values_response(parameters)
        elif method_name == 'SetParameterValuesResponse':
            return handle_set_parameter_values_response(parameters)
        elif method_name == 'RebootResponse':
            return handle_reboot_response(parameters)
        elif method_name == 'GetRPCMethodsResponse':
            return handle_get_rpc_methods_response(parameters)
        else:
            print(f"Unhandled method: {method_name}")
            return Response(SOAPHandler.create_empty_response(), 
                          mimetype='text/xml', 
                          status=200)
            
    except Exception as e:
        print(f"Error in CWMP handler: {e}")
        return Response("Internal server error", status=500)

def handle_inform(parameters):
    """Handle Inform message from device"""
    try:
        # Extract device info
        device_info = parameters.get('DeviceId', {})
        event_list = parameters.get('Event', [])
        param_list = parameters.get('ParameterList', [])
        
        # Convert parameter list to dictionary
        param_dict = {}
        if isinstance(param_list, list):
            for param in param_list:
                if isinstance(param, dict):
                    name = param.get('Name', '')
                    value = param.get('Value', '')
                    param_dict[name] = value
        
        # Register or update device
        device = DeviceManager.register_device(device_info, param_dict)
        
        if not device:
            return Response("Failed to register device", status=500)
        
        # Create session
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            'device_id': device.id,
            'started_at': datetime.utcnow(),
            'task_queue': []
        }
        
        # Get pending tasks for this device
        pending_tasks = DeviceManager.get_pending_tasks(device.id)
        
        # Send InformResponse
        response_xml = SOAPHandler.create_inform_response()
        
        # If there are pending tasks, we'll handle them in the next exchange
        if pending_tasks:
            session = active_sessions[session_id]
            session['task_queue'] = pending_tasks
            session['current_task_index'] = 0
            
            # Process first task
            task = pending_tasks[0]
            DeviceManager.update_task_status(task.id, 'in_progress')
            response_xml = create_task_request(task)
        
        return Response(response_xml, 
                       mimetype='text/xml',
                       status=200,
                       headers={'Set-Cookie': f'sessionid={session_id}'})
        
    except Exception as e:
        print(f"Error handling Inform: {e}")
        return Response(SOAPHandler.create_inform_response(), 
                       mimetype='text/xml', 
                       status=200)

def handle_set_parameter_values_response(parameters):
    """Handle SetParameterValues response"""
    try:
        status = parameters.get('Status', '1')
        
        # Get session
        session_id = request.cookies.get('sessionid')
        session = active_sessions.get(session_id)
        
        if session and session.get('task_queue'):
            task_queue = session['task_queue']
            current_index = session.get('current_task_index', 0)
            
            if current_index < len(task_queue):
                current_task = task_queue[current_index]
                
                # Update task status
                if status == '0':
                    DeviceManager.update_task_status(current_task.id, 'completed')
                else:
                    DeviceManager.update_task_status(current_task.id, 'failed', 
                                                    f'Status code: {status}')
                
                # Move to next task
                current_index += 1
                session['current_task_index'] = current_index
                
                if current_index < len(task_queue):
                    # Process next task
                    next_task = task_queue[current_index]
                    DeviceManager.update_task_status(next_task.id, 'in_progress')
                    response_xml = create_task_request(next_task)
                    return Response(response_xml, mimetype='text/xml', status=200)
        
        # No more tasks
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)
        
    except Exception as e:
        print(f"Error handling SetParameterValues response: {e}")
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)

def handle_get_parameter_values_response(parameters):
    """Handle GetParameterValues response"""
    try:
        param_list = parameters.get('ParameterList', [])
        
        # Get session
        session_id = request.cookies.get('sessionid')
        session = active_sessions.get(session_id)
        
        if session:
            device_id = session['device_id']
            
            # Store parameters
            param_dict = {}
            if isinstance(param_list, list):
                for param in param_list:
                    if isinstance(param, dict):
                        name = param.get('Name', '')
                        value = param.get('Value', '')
                        param_dict[name] = value
            
            DeviceManager.update_device_parameters(device_id, param_dict)
            
            # Check for more tasks
            if session.get('task_queue'):
                task_queue = session['task_queue']
                current_index = session.get('current_task_index', 0)
                
                if current_index < len(task_queue):
                    current_task = task_queue[current_index]
                    DeviceManager.update_task_status(current_task.id, 'completed')
                    
                    # Move to next task
                    current_index += 1
                    session['current_task_index'] = current_index
                    
                    if current_index < len(task_queue):
                        next_task = task_queue[current_index]
                        DeviceManager.update_task_status(next_task.id, 'in_progress')
                        response_xml = create_task_request(next_task)
                        return Response(response_xml, mimetype='text/xml', status=200)
        
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)
        
    except Exception as e:
        print(f"Error handling GetParameterValues response: {e}")
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)

def handle_reboot_response(parameters):
    """Handle Reboot response"""
    try:
        session_id = request.cookies.get('sessionid')
        session = active_sessions.get(session_id)
        
        if session and session.get('task_queue'):
            task_queue = session['task_queue']
            current_index = session.get('current_task_index', 0)
            
            if current_index < len(task_queue):
                current_task = task_queue[current_index]
                DeviceManager.update_task_status(current_task.id, 'completed')
        
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)
        
    except Exception as e:
        print(f"Error handling Reboot response: {e}")
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)

def handle_transfer_complete(parameters):
    """Handle TransferComplete (firmware upgrade completion)"""
    try:
        command_key = parameters.get('CommandKey', '')
        fault_struct = parameters.get('FaultStruct', {})
        
        session_id = request.cookies.get('sessionid')
        session = active_sessions.get(session_id)
        
        if session and session.get('task_queue'):
            task_queue = session['task_queue']
            current_index = session.get('current_task_index', 0)
            
            if current_index < len(task_queue):
                current_task = task_queue[current_index]
                
                if fault_struct and fault_struct.get('FaultCode') != '0':
                    DeviceManager.update_task_status(current_task.id, 'failed',
                                                    fault_struct.get('FaultString', 'Unknown error'))
                else:
                    DeviceManager.update_task_status(current_task.id, 'completed')
        
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)
        
    except Exception as e:
        print(f"Error handling TransferComplete: {e}")
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)

def handle_get_rpc_methods_response(parameters):
    """Handle GetRPCMethods response"""
    try:
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)
    except Exception as e:
        print(f"Error handling GetRPCMethods response: {e}")
        return Response(SOAPHandler.create_empty_response(), 
                       mimetype='text/xml', 
                       status=200)

def create_task_request(task):
    """Create SOAP request based on task type"""
    try:
        if task.task_type == 'set_parameters':
            parameters = task.parameters.get('parameters', {})
            return SOAPHandler.create_set_parameter_values(parameters)
        
        elif task.task_type == 'get_parameters':
            parameters = task.parameters.get('parameters', [])
            return SOAPHandler.create_get_parameter_values(parameters)
        
        elif task.task_type == 'reboot':
            return SOAPHandler.create_reboot()
        
        elif task.task_type == 'firmware_upgrade':
            url = task.parameters.get('url', '')
            file_size = task.parameters.get('file_size', 0)
            return SOAPHandler.create_download(url, file_size=file_size)
        
        elif task.task_type == 'factory_reset':
            return SOAPHandler.create_factory_reset()
        
        else:
            return SOAPHandler.create_empty_response()
            
    except Exception as e:
        print(f"Error creating task request: {e}")
        return SOAPHandler.create_empty_response()
