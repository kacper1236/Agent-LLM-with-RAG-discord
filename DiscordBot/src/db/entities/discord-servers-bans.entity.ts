import { AllowNull, Column, DataType, Default, ForeignKey, Index, Model, Table } from 'sequelize-typescript';
import { DiscordServersEntity } from './discord-servers.entity.js';
import { DiscordUsersEntity } from './discord-users.entity.js';

export interface ServerBan {
    text: string;
    createdAt: Date;
    createdBy: string;
    expiresAt: Date | string;
    isPerm: boolean;
    isFinal: boolean;
    finalizedBy?: string; // after appeal
    finalizedAt?: Date;
}

export interface DiscordServersBanCreationAttributes {
    userId: string;
    serverId: string;
    bans: ServerBan[];
    expiresAt?: Date | string;
    isBanned?: boolean;
} 

export interface DiscordServersBanAttributes extends DiscordServersBanCreationAttributes {
    id: never;
}

@Table({
    tableName: 'discord-servers-bans',
})
export class DiscordServersBanEntity extends Model<DiscordServersBanAttributes, DiscordServersBanCreationAttributes> {
    @Index('index__discord-servers-bans__userId_serverId')
    @ForeignKey(() => DiscordUsersEntity)
    @Column({
        type: DataType.STRING,
        primaryKey: true,
    })
    declare userId: string;

    @Index('index__discord-servers-bans__userId_serverId')
    @ForeignKey(() => DiscordServersEntity)
    @Column({
        type: DataType.STRING,
        primaryKey: true,
    })
    declare serverId: string;

    @Index('index__discord-servers-bans__userId_serverId')
    @AllowNull(false)
    @Default([])
    @Column(DataType.JSONB)
    declare bans: ServerBan[];

    @Index('index__discord-servers-bans__expiresAt')
    @Column(DataType.DATE)
    declare expiresAt?: Date;
}
