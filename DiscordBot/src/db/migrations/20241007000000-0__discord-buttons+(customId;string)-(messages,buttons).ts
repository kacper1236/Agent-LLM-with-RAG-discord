import { DataTypes, QueryInterface } from 'sequelize';
import { Sequelize } from 'sequelize-typescript';
import { MigrationBaseType, MigrationHelperClass } from '../classes/migration-helper.class.js';

const TABLE_NAME = 'discord-buttons';


export const migration: MigrationBaseType = {
  up: async ({context}): Promise<void> => {
    const {sequelize, queryInterface} = context;
    const helper = await MigrationHelperClass.from(queryInterface);
    await helper.prepare(TABLE_NAME);
    
    return queryInterface.sequelize.transaction(async (transaction) => {
        if (helper.tableExists(TABLE_NAME)) {
          if (!helper.columnExists(TABLE_NAME, 'customId')) {
            await queryInterface.addColumn(TABLE_NAME, 'customId', {
              type: DataTypes.STRING,
              allowNull: false,
            }, { transaction });
          }
          if (helper.columnExists(TABLE_NAME, 'messages')) {
            await queryInterface.removeColumn(TABLE_NAME, 'messages', { transaction });
          }
          if (helper.columnExists(TABLE_NAME, 'buttons')) {
            await queryInterface.removeColumn(TABLE_NAME, 'buttons', { transaction });
          }
        }
    });
  },
  down: async ({context}): Promise<void> => {
    const {sequelize, queryInterface} = context;
    
    return queryInterface.sequelize.transaction(
      async (transaction) => {
        // here go all migration undo changes
      },
    );
  },
};

export const up = migration.up;
export const down = migration.down;
