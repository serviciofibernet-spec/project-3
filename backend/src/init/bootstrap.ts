import fs from 'fs/promises';
import path from 'path';
import { query } from '../lib/db.js';

export async function bootstrapMySQL() {
  const sqlPath = path.join(process.cwd(), 'src', 'init', 'mysql.sql');
  const content = await fs.readFile(sqlPath, 'utf8');
  const statements = content.split(/;\s*\n/).map(s => s.trim()).filter(Boolean);
  for (const stmt of statements) {
    await query(stmt);
  }
}
