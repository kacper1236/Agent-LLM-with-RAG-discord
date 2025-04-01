import { ActionRowBuilder, MessageActionRowComponentBuilder, SlashCommandBuilder } from "discord.js";
import { ButtonBuilder, ButtonStyle } from "discord.js";
import { CommandType } from "types/command.type.js";
import { DataBase } from "db/db.module.js";

export const createNewTicketCommand: CommandType = {
    definition: new SlashCommandBuilder()
    .setName('create_new_ticket')
    .setDescription('Create a new ticket')
    ,
    handler: async (interaction) => {

        const confirm = new ButtonBuilder()
        .setStyle(ButtonStyle.Primary)
        .setCustomId('create-new-ticket')
        .setLabel('Confirm')

        const cancel = new ButtonBuilder()
        .setStyle(ButtonStyle.Danger)
        .setCustomId('cancel')
        .setLabel('Cancel')
        
        const row = new ActionRowBuilder<MessageActionRowComponentBuilder>()
        .addComponents(confirm, cancel);
        
        await interaction.reply({
            content: 'Are you sure you want to create a new ticket?',
            components: [row],
        });
    },
};
