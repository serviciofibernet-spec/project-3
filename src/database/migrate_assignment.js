const fs = require('fs').promises;
const path = require('path');
const mysql = require('mysql2/promise');
require('dotenv').config();

async function runAssignmentMigration() {
    const config = {
        host: process.env.DB_HOST || 'localhost',
        user: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || '',
        database: process.env.DB_NAME || 'tr069_db',
        port: process.env.DB_PORT || 3306,
        multipleStatements: true
    };

    let connection;
    
    try {
        // Connect to database
        connection = await mysql.createConnection(config);
        console.log('Connected to MySQL database');

        // Read and execute assignment tables schema
        const schemaPath = path.join(__dirname, 'assignment_tables.sql');
        const schema = await fs.readFile(schemaPath, 'utf8');
        
        // Split schema by semicolons and execute each statement
        const statements = schema.split(';').filter(stmt => stmt.trim().length > 0);
        
        for (const statement of statements) {
            if (statement.trim()) {
                await connection.execute(statement);
            }
        }

        console.log('Assignment tables migration completed successfully');
        
    } catch (error) {
        console.error('Assignment migration failed:', error);
        process.exit(1);
    } finally {
        if (connection) {
            await connection.end();
        }
    }
}

// Run migration if this file is executed directly
if (require.main === module) {
    runAssignmentMigration();
}

module.exports = runAssignmentMigration;