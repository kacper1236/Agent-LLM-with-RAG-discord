import { ActionRowBuilder, ButtonBuilder, ButtonInteraction, StringSelectMenuBuilder } from "discord.js";
import { DataBase } from "../../db/db.module.js";
import { ButtonType } from "types/button.type.js";
import { llmAxios } from "llm/llm-axios.service.js";
import { ChatMetaData, LLMRequestData } from "llm/llm.service.js";

export const createNewTicketButton: ButtonType = {
  definition: new ButtonBuilder()
    .setCustomId('create-new-ticket')
  ,
  handler: async (interaction: ButtonInteraction) => {
    const button = interaction;
    //const dbService = DataBase.discord;

    if (!button?.guildId){
      await button.reply('This button is for servers only');
      return;
    }

    const selectMenu = new StringSelectMenuBuilder()
    .setCustomId('newTicket')
    .setPlaceholder('Choose one of problem')
    .addOptions([
      {
        label: 'Zgłoś użytkownika',
        description: 'Przygotuj ID użytkownika, kanału i ostatniej wiadomości',
        value: 'reportUser',
      },
      {
        label: 'Zgłoś problem',
        description: 'Jest problem? Opisz go tutaj',
        value: 'reportProblem',
      },
      {
        label: 'Daj propzycję',
        description: 'Chcesz coś zaproponować? Napisz tutaj',
        value: 'suggestion'
      },
      {
        label: 'Ranga "Zaufany futrzak"',
        description: 'Jeżeli wiesz, że możesz otrzymać tę rolę, napisz',
        value: 'trusted'
      },
      {
        label: 'Ogłoszenia artystyczne',
        description: 'Jeżeli jesteś artystą, to zgłoś się po rolę',
        value: 'artist'
      },
      {
        label: 'Inne',
        description: 'Inne problemy, pytania, uwagi',
        value: 'other'
      }
    ])

    const row = new ActionRowBuilder<StringSelectMenuBuilder>().addComponents(selectMenu);

    await interaction.reply({
      content: 'Wybierz opcję z listy',
      components: [row],
      ephemeral: true
    });

    // const x = await interaction.guild?.channels.create({
    //   name: 'ticket',
    // });

    // await x?.send({
    //   content: `Ticket Created for user <@${interaction.user.id}>`,
    // });

    // let requestData: LLMRequestData<ChatMetaData> = {
    //   query: '',
    //   model: 'none',
    //   ragType: 'none',
    //   namespace: 'none',
    //   prompt: 'none',

    //   meta : {
    //     userId: interaction.user.id,
    //     guildId: interaction.guildId,
    //     chat: [],
    //   },
    // };

    // const server = await dbService.getServerById(button.guildId);
    // if(!server) button.guildId = null;
    // else {
    //   requestData = {
    //     query: '',
    //     model: server.ragModel || 'mistral',
    //     ragType: server.ragType || 'none',
    //     namespace: server.ragNamespace || 'none',
    //     prompt: server.prompt || 'none',

    //     meta: requestData.meta,
    //   };
    // }

    // const chat = await dbService.getChatHistory(interaction.guildId || '', interaction.user.id, interaction.channelId || '');
    // if (chat) requestData.meta.chat = chat.chatLog.map(x => [x[0], x[1]]) || [];

    // try {
    //   const response = await llmAxios.post('/ticket', requestData, {responseType: 'json'});
    //   await x?.send({
    //     content: `query: ${response.data.message}`,
    //   });
    // } catch (err) {
    //   console.log(err);
    // }

    // await button.reply({
    //   content: 'Ticket Created',
    //   ephemeral: true,
    // });


  },
};
