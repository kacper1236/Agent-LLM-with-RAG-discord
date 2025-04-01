import { AllowNull, Column, DataType, Default, ForeignKey, Index, Model, Table } from 'sequelize-typescript';
import { DiscordUsersEntity } from './discord-users.entity.js';
import { DiscordServersEntity } from './discord-servers.entity.js';

export interface ServerKick {
    reason: string;
    createdAt: Date;
    createdBy: string;
}

export interface DiscordServersKickCreationAttributes {
    userId: string;
    serverId: string;
    kicks: ServerKick[];
}

export interface DiscordServersKickAttributes extends DiscordServersKickCreationAttributes {
    id: never;
}

@Table({
    tableName: 'discord-servers-kicks',
})
export class DiscordServersKickEntity extends Model<DiscordServersKickAttributes, DiscordServersKickCreationAttributes> {
    @Index('index__discord-servers-kicks__userId_serverId')
    @ForeignKey(() => DiscordUsersEntity)
    @Column({
        type: DataType.STRING,
        primaryKey: true,
    })
    declare userId: string;

    @Index('index__discord-servers-kicks__userId_serverId')
    @ForeignKey(() => DiscordServersEntity)
    @Column({
        type: DataType.STRING,
        primaryKey: true,
    })
    declare serverId: string;

    @AllowNull(false)
    @Default([])
    @Column(DataType.JSONB)
    declare kicks: ServerKick[];
}
