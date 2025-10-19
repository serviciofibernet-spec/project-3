"""
Background scheduler for automated tasks
"""
import schedule
import time
from datetime import datetime, timedelta
from database.models import db, Device, DeviceDiagnostics, ConfigurationTask
from tr069.device_manager import DeviceManager

def check_device_status():
    """Check and update device online/offline status"""
    try:
        threshold = datetime.utcnow() - timedelta(minutes=10)
        
        # Mark devices as offline if no inform in last 10 minutes
        offline_devices = Device.query.filter(
            Device.last_inform < threshold,
            Device.status == 'online'
        ).all()
        
        for device in offline_devices:
            device.status = 'offline'
            print(f"Device {device.serial_number} marked as offline")
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Error checking device status: {e}")

def collect_diagnostics():
    """Schedule diagnostics collection for all online devices"""
    try:
        online_devices = Device.query.filter_by(status='online').all()
        
        diagnostic_params = [
            DeviceManager.HUAWEI_PARAMS['optical_power_rx'],
            DeviceManager.HUAWEI_PARAMS['optical_power_tx'],
            DeviceManager.HUAWEI_PARAMS['temperature'],
            DeviceManager.HUAWEI_PARAMS['uptime'],
            DeviceManager.HUAWEI_PARAMS['wan_ip'],
            DeviceManager.HUAWEI_PARAMS['hosts_count'],
        ]
        
        for device in online_devices:
            # Check if there's already a pending diagnostic task
            existing_task = ConfigurationTask.query.filter_by(
                device_id=device.id,
                task_type='get_parameters',
                status='pending'
            ).first()
            
            if not existing_task:
                task = ConfigurationTask(
                    device_id=device.id,
                    task_type='get_parameters',
                    parameters={'parameters': diagnostic_params},
                    status='pending'
                )
                db.session.add(task)
        
        db.session.commit()
        print(f"Scheduled diagnostics collection for {len(online_devices)} devices")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error scheduling diagnostics: {e}")

def cleanup_old_data():
    """Clean up old diagnostic and event data"""
    try:
        # Remove diagnostics older than 30 days
        threshold = datetime.utcnow() - timedelta(days=30)
        
        deleted_diag = DeviceDiagnostics.query.filter(
            DeviceDiagnostics.collected_at < threshold
        ).delete()
        
        # Remove completed tasks older than 7 days
        task_threshold = datetime.utcnow() - timedelta(days=7)
        deleted_tasks = ConfigurationTask.query.filter(
            ConfigurationTask.completed_at < task_threshold,
            ConfigurationTask.status.in_(['completed', 'failed'])
        ).delete()
        
        db.session.commit()
        print(f"Cleaned up {deleted_diag} old diagnostics and {deleted_tasks} old tasks")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error cleaning up old data: {e}")

def retry_failed_tasks():
    """Retry failed configuration tasks"""
    try:
        failed_tasks = ConfigurationTask.query.filter(
            ConfigurationTask.status == 'failed',
            ConfigurationTask.retry_count < ConfigurationTask.max_retries
        ).all()
        
        for task in failed_tasks:
            task.status = 'pending'
            task.retry_count += 1
            task.error_message = None
        
        db.session.commit()
        print(f"Retrying {len(failed_tasks)} failed tasks")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error retrying failed tasks: {e}")

def run_scheduler(app):
    """Run the background scheduler"""
    with app.app_context():
        # Schedule tasks
        schedule.every(5).minutes.do(lambda: check_device_status())
        schedule.every(15).minutes.do(lambda: collect_diagnostics())
        schedule.every().day.at("03:00").do(lambda: cleanup_old_data())
        schedule.every(30).minutes.do(lambda: retry_failed_tasks())
        
        print("Scheduler started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    run_scheduler(app)
