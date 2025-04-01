import { Column, DataType, Model, Table } from 'sequelize-typescript';

export interface DiscordBannedUsersCreationAttributes {
  userId: string;
  isBanned: boolean;
}

export interface DiscordBannedUsersAttributes extends DiscordBannedUsersCreationAttributes {
  
}

@Table({
  tableName: 'discord-users',
})
export class DiscordUsersEntity extends Model<DiscordBannedUsersAttributes, DiscordBannedUsersCreationAttributes> {
  @Column({
    type: DataType.STRING,
    primaryKey: true,
  })
  declare userId: number;
  
  @Column(DataType.BOOLEAN)
  declare isBanned: boolean;
  
  @Column(DataType.BOOLEAN)
  declare isOwner: boolean;
}
