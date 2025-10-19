const fs = require('fs').promises;
const path = require('path');
const mysql = require('mysql2/promise');
require('dotenv').config();

async function runMigration() {
    const config = {
        host: process.env.DB_HOST || 'localhost',
        user: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || '',
        port: process.env.DB_PORT || 3306,
        multipleStatements: true
    };

    let connection;
    
    try {
        // Connect to MySQL server
        connection = await mysql.createConnection(config);
        console.log('Connected to MySQL server');

        // Create database if it doesn't exist
        const dbName = process.env.DB_NAME || 'tr069_db';
        await connection.execute(`CREATE DATABASE IF NOT EXISTS \`${dbName}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`);
        console.log(`Database '${dbName}' created or already exists`);

        // Use the database
        await connection.execute(`USE \`${dbName}\``);

        // Read and execute schema
        const schemaPath = path.join(__dirname, 'schema.sql');
        const schema = await fs.readFile(schemaPath, 'utf8');
        
        // Split schema by semicolons and execute each statement
        const statements = schema.split(';').filter(stmt => stmt.trim().length > 0);
        
        for (const statement of statements) {
            if (statement.trim()) {
                await connection.execute(statement);
            }
        }

        console.log('Database migration completed successfully');
        
    } catch (error) {
        console.error('Migration failed:', error);
        process.exit(1);
    } finally {
        if (connection) {
            await connection.end();
        }
    }
}

// Run migration if this file is executed directly
if (require.main === module) {
    runMigration();
}

module.exports = runMigration;