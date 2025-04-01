import { AllowNull, Column, DataType, Default, Model, Table, Unique } from 'sequelize-typescript';
import { CommandStatus } from '../../types/command-status.type.js';

export interface DiscordCommandsCreationAttributes {
  name: string;
  displayName: string;
  description: string;
  status?: CommandStatus;
  definitionHash?: string;
  handlerHash?: string;
  discordId?: string;
}

export interface DiscordCommandsAttributes extends DiscordCommandsCreationAttributes {
 id: never;
 status: CommandStatus;
}

@Table({
  tableName: 'discord-commands',
  indexes: [
    {
      type: 'UNIQUE',
      fields: ['name'],
      name: 'index__discord-commands__name',
    },
    {
      type: 'UNIQUE',
      fields: ['displayName'],
      name: 'index__discord-commands__displayName',
    },
  ],
})
export class DiscordCommandsEntity extends Model<DiscordCommandsAttributes, DiscordCommandsCreationAttributes> {
  @Unique
  @Column(DataType.STRING)
  declare discordId: string | null;
  
  @AllowNull(false)
  @Column({
    type: DataType.STRING,
    primaryKey: true,
  })
  declare name: string;
  
  @AllowNull(false)
  @Column(DataType.STRING)
  declare displayName: string;
  
  @AllowNull(false)
  @Column(DataType.STRING)
  declare description: string;
  
  @AllowNull(false)
  @Default('devs' satisfies CommandStatus)
  @Column(DataType.STRING)
  declare status: CommandStatus;
  
  @Column(DataType.STRING)
  declare definitionHash: string;
}
