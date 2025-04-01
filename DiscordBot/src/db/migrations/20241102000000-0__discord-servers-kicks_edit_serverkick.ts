import { DataTypes, QueryInterface } from 'sequelize';
import { Sequelize } from 'sequelize-typescript';
import { MigrationBaseType, MigrationHelperClass } from '../classes/migration-helper.class.js';

const TABLE_NAME = 'discord-servers-kicks';

export const migration: MigrationBaseType = {
    up: async ({context}): Promise<void> => {
        const {sequelize, queryInterface} = context;
        const helper = await MigrationHelperClass.from(queryInterface);
        await helper.prepare(TABLE_NAME);
        
        return queryInterface.sequelize.transaction(async (transaction) => {
            if (helper.tableExists(TABLE_NAME)) {
                if (!helper.columnExists(TABLE_NAME, 'kicks')) {
                    await queryInterface.addColumn(TABLE_NAME, 'kicks', {
                        type: DataTypes.JSONB,
                        allowNull: false,
                        defaultValue: [],
                    }, { transaction });
                }
            }
        });
    },
    down: async ({context}): Promise<void> => {
        const {sequelize, queryInterface} = context;
        
        return queryInterface.sequelize.transaction(
            async (transaction) => {
                await queryInterface.removeColumn(TABLE_NAME, 'kicks', { transaction });
            },
        );
    },
}

export const up = migration.up;
export const down = migration.down;