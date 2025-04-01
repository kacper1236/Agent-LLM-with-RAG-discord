import { AllowNull, Column, DataType, Default, Model, Table, Unique } from 'sequelize-typescript';

export type RAGChatRow = ['assistant' | 'human', string, Date, number?];

export interface DiscordChatsCreationAttributes {
  serverId: string;
  userId: string;
  channelId: string;
  isCurrent?: true | null;
  chatLog?: RAGChatRow[];
  count?: number;
}
export interface DiscordChatsAttributes extends DiscordChatsCreationAttributes {
  isCurrent: true | null;
  chatLog: RAGChatRow[];
  count: number;
}

@Table({
  tableName: 'discord-chats',
  indexes: [
    {
      type: 'UNIQUE',
      name: 'discord-chats--UNIQUE--serverId-userId-channelId-isCurrent',
      fields: ['serverId', 'userId', 'channelId', 'isCurrent'],
    },
  ],
})
export class DiscordChatsEntity extends Model<DiscordChatsAttributes, DiscordChatsCreationAttributes> {
  @AllowNull(false)
  @Column(DataType.STRING)
  declare serverId: string;
  
  @AllowNull(false)
  @Column(DataType.STRING)
  declare userId: string;
  
  @AllowNull(false)
  @Column(DataType.STRING)
  declare channelId: string;
  
  @AllowNull(true)
  @Column(DataType.BOOLEAN)
  declare isCurrent: true | null;
  
  @Default([])
  @Column(DataType.JSONB)
  declare chatLog: RAGChatRow[];
  
  @Default(1)
  @AllowNull(false)
  @Column(DataType.INTEGER)
  declare count: number;
}
