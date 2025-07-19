import { DataBase } from "db/db.module.js";
import { LLMMessages } from "db/entities/discord-llm-chat.entity.js";
import { CommandInteraction, SlashCommandBuilder } from "discord.js";
import { llmAxios } from "llm/llm-axios.service.js";
import { CommandType } from "types/command.type.js";

export const chatCommand: CommandType = {
    definition: new SlashCommandBuilder()
        .setName('chat')
        .setDescription('Chat with the bot')
        .addStringOption(option =>
            option.setName('message')
                .setDescription('The message to send')
                .setRequired(true)
                )
        ,
    handler: async (interaction: CommandInteraction, db: typeof DataBase) => {
        const message = interaction.options.get('message');

        if (message?.value === '' || !message?.value) {
            await db.discord.deleteLLMChat(interaction.guild?.id as string, interaction.user.id);
            await interaction.reply({
                content: 'Chat has been closed.',
                ephemeral: true,
            });
            return;
        }

        const userMessage: LLMMessages[] = [{
            role: 'user',
            content: message?.value as string,
        }];
        db.discord.addLLMChat(interaction.guild?.id as string, interaction.user.id, userMessage);

        const response = await llmAxios.post('/chat', {
            message: message?.value,
        }, {responseType: 'json'});
        await interaction.reply({
            content: `Chat response: ${response.data.message}`,
        });

        const agentMessage: LLMMessages[] = [{
            role: 'assistant',
            content: response.data.message,
        }];
        db.discord.addLLMChat(interaction.guild?.id as string, interaction.user.id, agentMessage);
    },
};