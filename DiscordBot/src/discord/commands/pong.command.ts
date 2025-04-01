import { SlashCommandBuilder } from '@discordjs/builders';
import { CommandInteraction, MessageCreateOptions, MessageFlagsBitField, MessageFlagsString } from 'discord.js';
import { llmAxios } from '../../llm/llm-axios.service.js';
import { CommandType } from '../../types/command.type.js';
import setTimeout = jest.setTimeout;

export const pongCommand: CommandType = {
  definition: new SlashCommandBuilder()
    .setName('pong')
    .setDescription('ping')
    .addStringOption(
      option => option
        .setName('query')
        .setDescription('query string for City of Cats')
    )
  ,
  handler: async (interaction: CommandInteraction) => {
    // console.log('Interaction', interaction);
    const start = Date.now();
    const query = interaction.options.get('query');
    await interaction.deferReply({
      ephemeral: false,
    });
    if (!query) {
      await interaction.deleteReply('Empty Query');
      return;
    }
    
    try {
      const response = await llmAxios.post('/query1', {
        query: query.value,
      }, {responseType: 'json'});
      
      const end = Date.now();
      await interaction.editReply({
        content: `query: ${query.value}\ndelay: ${end - start}\n\n${response.data.message}`,
      });
    } catch (err) {
      const end = Date.now();
      console.log(`delay: ${end - start}`)
      console.log(err);
      await interaction.deleteReply();
    }
  },
};
