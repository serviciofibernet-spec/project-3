import mysql from 'mysql2/promise';

const pool = mysql.createPool({
  host: process.env.MYSQL_HOST || 'localhost',
  port: process.env.MYSQL_PORT ? Number(process.env.MYSQL_PORT) : 3306,
  user: process.env.MYSQL_USER || 'root',
  password: process.env.MYSQL_PASSWORD || '',
  database: process.env.MYSQL_DB || 'acs',
  connectionLimit: 10,
});

export async function query<T = any>(sql: string, params: any[] = []): Promise<[T[], any]> {
  const [rows, fields] = await pool.query(sql, params);
  return [rows as T[], fields];
}

export default pool;
