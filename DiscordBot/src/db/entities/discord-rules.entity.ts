import { AllowNull, Column, DataType, Default, Model, Table } from 'sequelize-typescript';

export interface DiscordRulesMessage {
    text: string;
    idText: string;
    createdAt: Date;
}

export interface DiscordRuleMessageAttributes extends DiscordRulesMessage {
  id: never;
}

@Table({
  tableName: 'discord-rules',
})
export class DiscordRulesEntity extends Model {
  @AllowNull(false)
  @Column(DataType.STRING)
  declare serverId: string;

  @AllowNull(false)
  @Column(DataType.STRING)
  declare channelId: string;

  @Default([])
  @Column(DataType.JSONB)
  declare message: DiscordRulesMessage[];

}
