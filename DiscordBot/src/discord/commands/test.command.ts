import { SlashCommandBuilder } from '@discordjs/builders';
import Axios from 'axios';
import { CommandInteraction, EmbedBuilder, MessageCreateOptions, MessageFlagsBitField, MessageFlagsString } from 'discord.js';
import { CommandType } from '../../types/command.type.js';


export const testCommand: CommandType = {
  definition: new SlashCommandBuilder()
    .setName('test')
    .setDescription('test')
    .addStringOption(
      option => option
      .setName('echo')
      .setDescription('Echoes Data')
      .setRequired(true)
    )
  ,
  
    handler: async (interaction: CommandInteraction) => {
      console.log('Interaction', interaction);
      const query = interaction.options.get('echo');
      if (!query) {
        await interaction.reply('No parameters found');
        
        return;
      }
      
      await interaction.deferReply({
        ephemeral: false,
      });
      await interaction.editReply({
        content: `query: ${query.value}}`,
        // embeds: [
        //   new EmbedBuilder()
        //     .setColor('#10A080')
        //     .setTitle('ECHO')
        //     .setTimestamp()
        //     .setDescription('ECHO ANSWER')
        //   ,
        // ],
      });
      // interaction.channel?.send('a');
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
