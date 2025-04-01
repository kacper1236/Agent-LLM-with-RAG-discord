import { SlashCommandBuilder } from '@discordjs/builders';
import { CommandInteraction, EmbedBuilder, MessageCreateOptions, MessageFlagsBitField, MessageFlagsString } from 'discord.js';
import { DataBase } from '../../db/db.module.js';
import { llmAxios } from '../../llm/llm-axios.service.js';
import { CommandType } from '../../types/command.type.js';

export const queryCommand: CommandType = {
  definition: new SlashCommandBuilder()
  .setName('query')
  .setDescription('Query LLM [RAG] MODEL')
  .addStringOption(
    option => option
    .setName('query')
    .setDescription('Question for model')
  )
  ,
  handler: async (interaction: CommandInteraction, dbService: typeof DataBase) => {
    // console.log('Interaction', interaction);
    const start = Date.now();
    const query = interaction.options.get('query');
    await interaction.deferReply({
      ephemeral: false,
    });
   
    let requestData: {query: string; model: string; ragType: string; namespace: string; prompt: string; meta: Record<string, string | number | boolean | undefined | null>;} = {
      query: '',
      model: 'none',
      ragType: 'none',
      namespace: 'none',
      prompt: 'none',
      
      meta: {
        userId: interaction.user.id,
        guildId: interaction.guildId,
      },
    };
  
    
    if (interaction.guildId) {
      const server = await dbService.discord.getServerById(interaction.guildId);
      if (!server) interaction.guildId = null;
      else {
        requestData = {
          query: (query?.value || '').toString(),
          model: server.ragModel || 'none',
          ragType: server.ragType || 'none',
          namespace: server.ragNamespace || 'none',
          prompt: server.prompt || 'none',
          
          meta: requestData.meta,
        };
      }
    }
    if (!interaction.guildId) {
      // const user = await dbService.discord.getUser(interaction.user.id);
      const user: any = {};
      
      requestData = {
        query: (query?.value || '').toString(),
        model: user?.ragModel || 'none',
        ragType: user?.ragType || 'none',
        namespace: user?.ragNamespace || 'none',
        prompt: user?.prompt || 'none',
        
        meta: requestData.meta,
      };
    }
    
    
    try {
      const response = await llmAxios.post('/query', requestData, {responseType: 'json'});
      const end = Date.now();
      await interaction.editReply({
        content: `query: ${query?.value}\n\ndelay: ${end - start}\n\n${response.data.message}`,
      });
    } catch (err) {
      const end = Date.now();
      console.log(`delay: ${end - start}`)
      console.log(err);
      await interaction.deleteReply();
    }
  },
};
