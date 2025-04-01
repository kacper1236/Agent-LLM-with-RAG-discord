import { SlashCommandBuilder } from "discord.js";
import { CommandInteraction } from "discord.js";
import { EmbedBuilder } from "discord.js";
import { CommandType } from '../../types/command.type.js';

export const tttCommand: CommandType = {
    definition: new SlashCommandBuilder()
        .setName('ttt')
        .setDescription('ssshelp command')
    ,
    handler: async (interaction: CommandInteraction) => {
        const embed = new EmbedBuilder()
            .setColor(0x2475f0)
            .setTitle('Help')
            .setTimestamp()
            .setDescription('This is a help command')
            .addFields(
                { name: 'Command 1', value: 'Description 1' },
                { name: 'Command 2', value: 'Description 2' },
                { name: 'Command 3', value: 'Description 3' },
            )
        await interaction.reply({ embeds: [embed] });
    },
};
