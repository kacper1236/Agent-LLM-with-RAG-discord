import { AllowNull, Column, DataType, Table, Model, ForeignKey, Default } from "sequelize-typescript";

export interface LLMMessages {
    role: 'user' | 'assistant';
    content: string;
}

export interface DiscordLLMChatCreationAttributes {
    serverId: string;
    userId: string;
    messages?: LLMMessages[];
}

export interface DiscordLLMChatAttributes extends DiscordLLMChatCreationAttributes {
    id: never;
}

@Table({
    tableName: 'discord-llm-chats',
})
export class DiscordLLMChatEntity extends Model<DiscordLLMChatAttributes, DiscordLLMChatCreationAttributes> {
    @AllowNull(false)
    @ForeignKey(() => DiscordLLMChatEntity)
    @Column({
        type: DataType.STRING,
        primaryKey: true,
    })
    declare serverId: string;

    @AllowNull(false)
    @ForeignKey(() => DiscordLLMChatEntity)
    @Column({
        type: DataType.STRING,
        primaryKey: true,
    })
    declare userId: string;

    @AllowNull(false)
    @Column(DataType.JSONB)
    @Default([])
    declare messages: LLMMessages[];
}