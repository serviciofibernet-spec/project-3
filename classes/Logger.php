<?php
/**
 * Simple Logger Class for TR-069 ACS
 */
class Logger {
    private $logFile;
    
    public function __construct($logFile = 'logs/acs.log') {
        $this->logFile = $logFile;
        
        // Create logs directory if it doesn't exist
        $logDir = dirname($logFile);
        if (!is_dir($logDir)) {
            mkdir($logDir, 0755, true);
        }
    }
    
    private function writeLog($level, $message) {
        $timestamp = date('Y-m-d H:i:s');
        $logEntry = "[$timestamp] [$level] $message" . PHP_EOL;
        file_put_contents($this->logFile, $logEntry, FILE_APPEND | LOCK_EX);
    }
    
    public function info($message) {
        $this->writeLog('INFO', $message);
    }
    
    public function warning($message) {
        $this->writeLog('WARNING', $message);
    }
    
    public function error($message) {
        $this->writeLog('ERROR', $message);
    }
    
    public function debug($message) {
        $this->writeLog('DEBUG', $message);
    }
}
?>