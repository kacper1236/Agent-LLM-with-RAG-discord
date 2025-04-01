import { SlashCommandBuilder } from '@discordjs/builders';
import { CommandInteraction, EmbedBuilder, MessageCreateOptions, MessageFlagsBitField, MessageFlagsString } from 'discord.js';
import { DataBase } from '../../db/db.module.js';
import { RAGChatRow } from '../../db/entities/discord-chats.entity.js';
import { llmAxios } from '../../llm/llm-axios.service.js';
import { ChatMetaData, LLMRequestData, llmService } from '../../llm/llm.service.js';
import { CommandType } from '../../types/command.type.js';


export const chatCommand: CommandType = {
  definition: new SlashCommandBuilder()
  .setName('chat')
  .setDescription('Chat with LLM Model')
  .addStringOption(
    option => option
    .setName('chat')
    .setDescription('Question for model (empty means create new chat)')
  )
  ,
  handler: async (interaction: CommandInteraction, dbService: typeof DataBase) => {
    // console.log('Interaction', interaction);
    const start = Date.now();
    const query = interaction.options.get('chat');
    await interaction.deferReply({
      ephemeral: false,
    });
    
//    console.log(query?.value === '', !query , !query?.value)
    if (query?.value === '' || !query?.value) {
      await dbService.discord.archiveChatHistory(interaction.guildId || '', interaction.user.id, interaction.channelId || '');
      
      await interaction.editReply({
        content: `Chat closed.`,
      });
      return;
    }
    
   
    let requestData: LLMRequestData<ChatMetaData> = {
      query: '',
      model: 'none',
      ragType: 'none',
      namespace: 'none',
      prompt: 'none',
      
      meta: {
        userId: interaction.user.id,
        guildId: interaction.guildId,
        chat: [],
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
    
    const chat = await dbService.discord.getChatHistory(interaction.guildId || '', interaction.user.id, interaction.channelId || '');
    if (chat) {
      requestData.meta.chat = chat.chatLog.map(x => [x[0], x[1]]) || [];
    }
    
    try {
      // const response = await llmAxios.post('/query', requestData, {responseType: 'json'});
      const response = await llmService.chat(requestData);
      console.log('res', response);
      const end = Date.now();
      await interaction.editReply({
        content: `query: ${query?.value}\n\ndelay: ${end - start}\n\n${response.message}`,
      });
      
      const newChat: RAGChatRow[] = [
        ['human', requestData.query, new Date()],
        ['assistant', response.message, new Date(), end-start],
      ]
      
      await dbService.discord.addChatHistory(interaction.guildId || '', interaction.user.id, interaction.channelId || '', newChat);
    } catch (err) {
      const end = Date.now();
      console.log(`delay: ${end - start}`)
      console.log(err);
      await interaction.deleteReply();
    }
  },
};
