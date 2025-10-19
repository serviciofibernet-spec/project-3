import { DataTypes, Model, Optional } from 'sequelize';
import { sequelize } from './db.js';

export interface CustomerAttributes {
  id: number;
  name: string;
  email?: string;
  created_at?: Date;
}

export interface OntAttributes {
  id: number;
  device_id: string;
  model?: string;
  serial?: string;
  customer_id?: number;
  ssid?: string;
  wifi_key?: string;
  vlan_id?: number;
  pppoe_user?: string;
  pppoe_pass?: string;
  created_at?: Date;
}

type CustomerCreation = Optional<CustomerAttributes, 'id'>;
export class Customer extends Model<CustomerAttributes, CustomerCreation> implements CustomerAttributes {
  declare id: number;
  declare name: string;
  declare email?: string;
  declare created_at?: Date;
}

Customer.init(
  {
    id: { type: DataTypes.BIGINT, autoIncrement: true, primaryKey: true },
    name: { type: DataTypes.STRING(128), allowNull: false },
    email: { type: DataTypes.STRING(128), allowNull: true, unique: true },
    created_at: { type: DataTypes.DATE, allowNull: true },
  },
  { sequelize, tableName: 'customers', timestamps: false }
);

type OntCreation = Optional<OntAttributes, 'id'>;
export class Ont extends Model<OntAttributes, OntCreation> implements OntAttributes {
  declare id: number;
  declare device_id: string;
  declare model?: string;
  declare serial?: string;
  declare customer_id?: number;
  declare ssid?: string;
  declare wifi_key?: string;
  declare vlan_id?: number;
  declare pppoe_user?: string;
  declare pppoe_pass?: string;
  declare created_at?: Date;
}

Ont.init(
  {
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
  },
  { sequelize, tableName: 'onts', timestamps: false }
);

Customer.hasMany(Ont, { foreignKey: 'customer_id' });
Ont.belongsTo(Customer, { foreignKey: 'customer_id' });
