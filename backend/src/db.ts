import { Sequelize } from 'sequelize';

const host = process.env.MYSQL_HOST || 'localhost';
const database = process.env.MYSQL_DATABASE || 'acs';
const username = process.env.MYSQL_USER || 'acs';
const password = process.env.MYSQL_PASSWORD || 'acs';

export const sequelize = new Sequelize(database, username, password, {
  host,
  dialect: 'mysql',
  logging: false,
});

export async function initDb(): Promise<void> {
  await sequelize.authenticate();
}
