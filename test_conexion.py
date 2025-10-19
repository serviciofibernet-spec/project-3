#!/usr/bin/env python3
"""
Script de prueba para verificar conexión al servidor TR-069
"""

import http.client
import base64

def test_server_connection(host='localhost', port=7547, username='admin', password='admin123'):
    """
    Prueba la conexión al servidor TR-069
    """
    print("="*60)
    print("Test de Conexión al Servidor TR-069")
    print("="*60)
    print(f"\nServidor: {host}:{port}")
    print(f"Usuario: {username}")
    print()
    
    try:
        # Crear conexión
        conn = http.client.HTTPConnection(host, port, timeout=10)
        
        # Test 1: GET request (panel web)
        print("Test 1: Verificando panel web (GET /)...")
        conn.request("GET", "/")
        response = conn.getresponse()
        print(f"✓ Respuesta: {response.status} {response.reason}")
        
        if response.status == 200:
            print("✓ Panel web accesible")
        
        # Test 2: POST con autenticación
        print("\nTest 2: Verificando autenticación...")
        
        # Crear credenciales Basic Auth
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        }
        
        # SOAP envelope simple para test
        soap_body = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">TEST123</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:GetRPCMethods/>
    </soap:Body>
</soap:Envelope>"""
        
        conn = http.client.HTTPConnection(host, port, timeout=10)
        conn.request("POST", "/", body=soap_body, headers=headers)
        response = conn.getresponse()
        
        print(f"✓ Respuesta: {response.status} {response.reason}")
        
        if response.status == 200:
            print("✓ Autenticación exitosa")
            response_data = response.read().decode('utf-8')
            if 'GetRPCMethodsResponse' in response_data:
                print("✓ Servidor procesando mensajes CWMP correctamente")
        elif response.status == 401:
            print("⚠ Autenticación fallida - verifica usuario/contraseña")
        
        conn.close()
        
        print("\n" + "="*60)
        print("✓ TESTS COMPLETADOS EXITOSAMENTE")
        print("="*60)
        print("\n🌐 Accede al panel web: http://{}:{}".format(host, port))
        
        return True
        
    except ConnectionRefusedError:
        print("❌ ERROR: No se pudo conectar al servidor")
        print("   Verifica que el servidor esté ejecutándose")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Función principal"""
    print("\n")
    
    # Puedes modificar estos valores para probar con diferentes configuraciones
    HOST = 'localhost'
    PORT = 7547
    USERNAME = 'admin'
    PASSWORD = 'admin123'
    
    success = test_server_connection(HOST, PORT, USERNAME, PASSWORD)
    
    if not success:
        print("\n📝 Sugerencias:")
        print("   1. Asegúrate de que el servidor esté ejecutándose")
        print("   2. Ejecuta: python tr069_server.py")
        print("   3. Verifica el puerto en tr069_config.json")
        print("   4. Verifica las credenciales en tr069_config.json")
    
    print()
    input("Presiona Enter para salir...")


if __name__ == '__main__':
    main()
