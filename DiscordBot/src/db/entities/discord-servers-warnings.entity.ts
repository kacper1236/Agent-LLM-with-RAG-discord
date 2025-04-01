import { AllowNull, Column, DataType, Default, ForeignKey, Index, Model, Table } from 'sequelize-typescript';
import { DiscordServersEntity } from './discord-servers.entity.js';
import { DiscordUsersEntity } from './discord-users.entity.js';
import { UUID } from 'node:crypto';

export interface ServerWarning {
    id: UUID;
    text: string;
    createdAt: Date;
    createdBy: string;
    expiresAt: Date | string;
}

export interface DiscordServersWarningCreationAttributes {
    userId: string;
    serverId: string;
    count?: number;
    last?: string;
    warnings?: ServerWarning[];
    expiresAt?: Date | string;
}

export interface DiscordServersWarningAttributes extends DiscordServersWarningCreationAttributes {
    id: never;
    count: number;
    warnings: ServerWarning[];
}

@Table({
    tableName: 'discord-servers-warnings',
})
export class DiscordServersWarningEntity extends Model<DiscordServersWarningAttributes, DiscordServersWarningCreationAttributes> {
    @Index('index__discord-servers-warnings__userId_serverId_count')
    @ForeignKey(() => DiscordUsersEntity)
    @Column({
        type: DataType.STRING,
        primaryKey: true,
    })
    declare userId: string;

    @Index('index__discord-servers-warnings__userId_serverId_count')
    @ForeignKey(() => DiscordServersEntity)
    @Column({
        type: DataType.STRING,
        primaryKey: true,
    })
    declare serverId: string;

    @AllowNull(false)
    @Default(0)
    @Column(DataType.INTEGER({unsigned: true}))
    declare count: number;

    @Column(DataType.STRING)
    declare last?: string;

    @Index('index__discord-servers-warnings__userId_serverId_count')
    @AllowNull(false)
    @Default([])
    @Column(DataType.JSONB)
    declare warnings: ServerWarning[];

    @Index('index__discord-servers-warnings__expiresAt')
    @Column(DataType.DATE)
    declare expiresAt?: Date | string;
}
