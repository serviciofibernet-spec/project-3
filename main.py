#!/usr/bin/env python3
"""
TR069 ACS Server - Main Application
"""

import sys
import os
import threading
import signal
import argparse
import logging
from tr069_server.server import TR069Server
from tr069_server.api import run_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('config', exist_ok=True)
os.makedirs('data/devices', exist_ok=True)

class TR069Application:
    """Main application controller"""
    
    def __init__(self):
        self.tr069_server = None
        self.api_thread = None
        self.running = False
    
    def start(self, tr069_host='0.0.0.0', tr069_port=7547, 
             api_host='0.0.0.0', api_port=8080, api_enabled=True):
        """Start the TR069 server and API"""
        
        logger.info("=" * 60)
        logger.info("TR069/CWMP ACS Server v1.0.0")
        logger.info("=" * 60)
        
        # Start API server in background thread if enabled
        if api_enabled:
            self.api_thread = threading.Thread(
                target=run_api,
                args=(api_host, api_port, False),
                daemon=True
            )
            self.api_thread.start()
            logger.info(f"API server started on http://{api_host}:{api_port}")
            logger.info(f"Default credentials: admin/admin")
        
        # Start TR069 server (blocks)
        self.tr069_server = TR069Server(host=tr069_host, port=tr069_port)
        self.running = True
        
        try:
            self.tr069_server.start()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"Application error: {e}")
            self.stop()
    
    def stop(self):
        """Stop the application"""
        logger.info("Shutting down application...")
        self.running = False
        
        if self.tr069_server:
            self.tr069_server.stop()
        
        logger.info("Application stopped")
        sys.exit(0)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='TR069/CWMP ACS Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Start with default settings
  python main.py
  
  # Start TR069 on custom port
  python main.py --tr069-port 8080
  
  # Start without API server
  python main.py --no-api
  
  # Enable debug logging
  python main.py --debug
        '''
    )
    
    parser.add_argument('--tr069-host', default='0.0.0.0',
                       help='TR069 server host (default: 0.0.0.0)')
    parser.add_argument('--tr069-port', type=int, default=7547,
                       help='TR069 server port (default: 7547)')
    parser.add_argument('--api-host', default='0.0.0.0',
                       help='API server host (default: 0.0.0.0)')
    parser.add_argument('--api-port', type=int, default=8080,
                       help='API server port (default: 8080)')
    parser.add_argument('--no-api', action='store_true',
                       help='Disable API server')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start application
    app = TR069Application()
    
    # Handle signals
    def signal_handler(sig, frame):
        logger.info("Signal received, shutting down...")
        app.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start application
    app.start(
        tr069_host=args.tr069_host,
        tr069_port=args.tr069_port,
        api_host=args.api_host,
        api_port=args.api_port,
        api_enabled=not args.no_api
    )

if __name__ == '__main__':
    main()