import { SlashCommandBuilder } from '@discordjs/builders';
import Axios from 'axios';
import { CommandInteraction, EmbedBuilder, MessageCreateOptions, MessageFlagsBitField, MessageFlagsString } from 'discord.js';
import { llmAxios } from '../../llm/llm-axios.service.js';
import { CommandType } from '../../types/command.type.js';

export const pingCommand: CommandType = {
  definition: new SlashCommandBuilder()
    .setName('ping')
    .setDescription('pong')
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
        const response = await llmAxios.post('/query2', {
          query: query.value,
        }, {responseType: 'json'});
        
        
        console.log(query);
        const end = Date.now();
        await interaction.editReply({
          content: `query: ${query.value}\ndelay: ${end - start}\n\n${response.data.message}`,
          embeds: [
            new EmbedBuilder()
              .setColor('#10A080')
              .setTitle('PING')
              .setTimestamp()
              .setDescription('desc?')
            ,
          ],
        });
      } catch (err) {
        const end = Date.now();
        console.log(`delay: ${end - start}`)
        console.log(err);
        await interaction.deleteReply();
      }
    },
  // handler: async (interaction: CommandInteraction) => {
  //   console.log('Interaction', interaction);
  //  
  //   await interaction.deferReply({
  //     ephemeral: false,
  //   });
  //  
  //   try {
  //     const response = await axios.post('/chat', {
  //       "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q8_0",
  //       "messages": [
  //         {
  //           "role": "system",
  //           "content": "Odpowiadasz po Polsku, kwieciście i epicko jak z horroru Lovecrafta. Odpowiedź powinna być krótka."
  //         },
  //         {
  //           "role": "user",
  //           "content": "Opowiedz coś o sobie"
  //         }
  //       ],
  //       options: {
  //         num_predict: 400,
  //       },
  //       "stream": false
  //       // "format": "json"
  //     }, {responseType: 'json'});
  //    
  //    
  //     await interaction.editReply({
  //       content: response.data.message.content,
  //     });
  //   } catch (err) {
  //     console.dir(err);
  //   }
  // },
};
