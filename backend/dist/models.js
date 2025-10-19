import { DataTypes, Model } from 'sequelize';
import { sequelize } from './db.js';
export class Customer extends Model {
}
Customer.init({
    id: { type: DataTypes.BIGINT, autoIncrement: true, primaryKey: true },
    name: { type: DataTypes.STRING(128), allowNull: false },
    email: { type: DataTypes.STRING(128), allowNull: true, unique: true },
    created_at: { type: DataTypes.DATE, allowNull: true },
}, { sequelize, tableName: 'customers', timestamps: false });
export class Ont extends Model {
}
Ont.init({
    id: { type: DataTypes.BIGINT, autoIncrement: true, primaryKey: true },
    device_id: { type: DataTypes.STRING(256), allowNull: false, unique: true },
    model: { type: DataTypes.STRING(128), allowNull: true },
    serial: { type: DataTypes.STRING(128), allowNull: true },
    customer_id: { type: DataTypes.BIGINT, allowNull: true },
    ssid: { type: DataTypes.STRING(64), allowNull: true },
    wifi_key: { type: DataTypes.STRING(128), allowNull: true },
    vlan_id: { type: DataTypes.INTEGER, allowNull: true },
    pppoe_user: { type: DataTypes.STRING(128), allowNull: true },
    pppoe_pass: { type: DataTypes.STRING(128), allowNull: true },
    created_at: { type: DataTypes.DATE, allowNull: true },
}, { sequelize, tableName: 'onts', timestamps: false });
Customer.hasMany(Ont, { foreignKey: 'customer_id' });
Ont.belongsTo(Customer, { foreignKey: 'customer_id' });
