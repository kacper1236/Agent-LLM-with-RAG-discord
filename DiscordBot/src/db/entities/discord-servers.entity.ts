import { AllowNull, Column, DataType, HasMany, Model, Table } from 'sequelize-typescript';

type PromptConfiguration = any;

export interface DiscordServerCreationAttributes {
  id: string;
  name?: string;
}

export interface DiscordServerAttributes extends DiscordServerCreationAttributes {
  ragSize: number | null;
  prompt: PromptConfiguration | null;
}

@Table({
  tableName: 'discord-servers',
})
export class DiscordServersEntity extends Model<DiscordServerAttributes, DiscordServerCreationAttributes> {
  @Column({
    type: DataType.STRING,
    primaryKey: true,
    autoIncrement: false,
  })
  declare id: string;
  
  @AllowNull(true)
  @Column(DataType.STRING)
  declare name?: string;
  
  @AllowNull(true)
  @Column(DataType.STRING)
  declare ragModel?: string;
  
  @AllowNull(true)
  @Column(DataType.STRING)
  declare ragType?: string;
  
  @AllowNull(true)
  @Column(DataType.STRING)
  declare ragNamespace?: string;
  
  @AllowNull(true)
  @Column(DataType.INTEGER)
  declare ragSize?: number;
  
  @AllowNull(true)
  @Column(DataType.JSONB)
  declare prompt: PromptConfiguration;
}
