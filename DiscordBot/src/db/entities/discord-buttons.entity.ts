import { AllowNull, Column, DataType, Default, Model, Table, Unique } from 'sequelize-typescript';

export interface DiscordButtonsCreationAttributes {
    guildId: string;
    channelId: string;
    customId: string;
}

export interface DiscordButtonsAttributes extends DiscordButtonsCreationAttributes {
    id: never;
}

@Table({
    tableName: 'discord-buttons',
    indexes: [
        {
            type: 'UNIQUE',
            fields: ['customId'],
            name: 'index__discord-buttons__customId',
        },
    ],
})

export class DiscordButtonsEntity extends Model<DiscordButtonsCreationAttributes> {

    @AllowNull(false)
    @Column(DataType.STRING)
    declare guildId: string;

    @AllowNull(false)
    @Column(DataType.STRING)
    declare channelId: string;

    @AllowNull(false)
    @Column(DataType.STRING)
    declare customId: string;
}
