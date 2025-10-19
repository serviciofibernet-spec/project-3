-- Script de inicialización de la base de datos MySQL para TR-069
-- Este archivo se ejecuta automáticamente al crear el contenedor MySQL

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS `tr069_onts` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE `tr069_onts`;

-- Crear usuario si no existe
CREATE USER IF NOT EXISTS 'tr069'@'%' IDENTIFIED BY 'tr069pass';
GRANT ALL PRIVILEGES ON `tr069_onts`.* TO 'tr069'@'%';
FLUSH PRIVILEGES;

-- Configuraciones adicionales para optimizar el rendimiento
SET GLOBAL innodb_buffer_pool_size = 256M;
SET GLOBAL max_connections = 200;
SET GLOBAL query_cache_size = 32M;
SET GLOBAL query_cache_type = 1;