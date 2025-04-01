import { AllowNull, Column, DataType, Default, ForeignKey, Index, Model, Table } from 'sequelize-typescript';
import { DiscordUsersEntity } from './discord-users.entity.js';

export interface DiscordLastAcceptedMessageCreationAttributes {
    userId: string;
    channelId: string;
    messageId: string;
    isAccepted: boolean;
}

export interface DiscordLastAcceptedMessageAttributes extends DiscordLastAcceptedMessageCreationAttributes {
    id: never;
}

@Table({
    tableName : 'discord-last-accepted-message',
})
export class DiscordLastAcceptedMessageEntity extends Model<DiscordLastAcceptedMessageAttributes, DiscordLastAcceptedMessageCreationAttributes> {
    @Index('index__discord-last-accepted-message__userId_channelId')
    @ForeignKey(() => DiscordUsersEntity)
    @Column({
        type : DataType.STRING,
        primaryKey : true,
    })
    declare userId : string;

    @Index('index__discord-last-accepted-message__userId_channelId')
    @Column({
        type : DataType.STRING,
        primaryKey : true,
    })
    declare channelId : string;

    @AllowNull(false)
    @Default('')
    @Column(DataType.STRING)
    declare messageId : string;

    @AllowNull(false)
    @Column({
        type: DataType.BOOLEAN,
        defaultValue: false,
    })
    declare isAccepted : boolean;
}