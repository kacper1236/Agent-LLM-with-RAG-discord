import { AllowNull, BelongsTo, Column, DataType, Default, ForeignKey, Model, PrimaryKey, Table } from 'sequelize-typescript';
import { CommandStatus, CommonCommandStatus } from '../../types/command-status.type.js';
import { DiscordCommandsEntity } from './discord-commands.entity.js';
import { DiscordServersEntity } from './discord-servers.entity.js';

@Table({
  tableName: 'discord-servers-commands',
  indexes: [
    {
      type: 'UNIQUE',
      name: 'index__discord-servers-commands__commandId_serverId_channelId',
      fields: ['serverId', 'commandId', 'channelId'],
    },
  ],
})
export class DiscordServersCommandsEntity extends Model {
  @AllowNull(false)
  @ForeignKey(() => DiscordCommandsEntity)
  @Column(DataType.INTEGER)
  declare commandId: number;
  
  @BelongsTo(() => DiscordCommandsEntity)
  declare command: DiscordCommandsEntity;
  
  @AllowNull(false)
  @ForeignKey(() => DiscordServersEntity)
  @Column(DataType.STRING)
  declare serverId: string;
  
  @AllowNull(true)
  @Column(DataType.STRING)
  declare channelId: string;
  
  @BelongsTo(() => DiscordServersEntity)
  declare server: DiscordServersEntity;
  
  @AllowNull(false)
  @Default('disabled' satisfies CommandStatus)
  @Column(DataType.STRING)
  declare status: CommonCommandStatus;
}
