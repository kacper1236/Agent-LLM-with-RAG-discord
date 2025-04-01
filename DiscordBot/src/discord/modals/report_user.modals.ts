import { 
    ModalBuilder, 
    TextInputBuilder, 
    TextInputStyle, 
    ActionRowBuilder, 
    ModalSubmitInteraction,
    TextChannel,
    Message,
    EmbedBuilder,
    GuildMember
} from "discord.js";
import { ModalType } from "../../types/modal.type.js";
import { llmAxios } from "llm/llm-axios.service.js";

export const reportUser: ModalType = {
    definition: new ModalBuilder()
        .setCustomId('reportUser')
        .setTitle('Zgłoś użytkownika')
        .addComponents(
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('idUser')
                    .setLabel('Podaj ID użytkownika')
                    .setStyle(TextInputStyle.Short)
                    .setRequired(true)
            ),
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('idChannel')
                    .setLabel('Podaj ID kanału')
                    .setStyle(TextInputStyle.Short)
                    .setRequired(true)
            ),
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('idMessage')
                    .setLabel('Podaj ID ostatniej wiadomości (dla kontekstu)')
                    .setStyle(TextInputStyle.Short)
                    .setRequired(true)
            ),
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('reason')
                    .setLabel('Podaj powód zgłoszenia')
                    .setStyle(TextInputStyle.Paragraph)
                    .setRequired(true)
            )
        ),
    
    handler: async (interaction: ModalSubmitInteraction) => {
        if (!interaction.isModalSubmit()) return;
        
        await interaction.deferUpdate(); // Ensure the modal closes

        const userId = interaction.fields.getTextInputValue('idUser');
        const channelId = interaction.fields.getTextInputValue('idChannel');
        const lastMessageId = interaction.fields.getTextInputValue('idMessage');
        const reportReason = interaction.fields.getTextInputValue('reason');

        const x = await interaction.guild?.channels.create({
            name: `Ticket ${interaction.user.username}`
            //parent need to add (kategoria)
        });

        await x?.send({
            content: `✅ **Zgłoszenie przyjęte!**\n- **Użytkownik ID**: ${userId}\n- **Kanał ID**: ${channelId}\n- **ID wiadomości**: ${lastMessageId}\n- **Powód**: ${reportReason}`
        });

        const channel = interaction.guild?.channels.cache.get(channelId) as TextChannel;

        let messages: Message[] = [];

        await channel.messages.fetch({ limit: 100, before: lastMessageId }).then(messagePage => {
            messagePage.forEach(msg => messages.push(msg));
        });
        
        // Join messages into a single string for context
        const context = messages.map(m => `${m.author.username}: ${m.content}`).join("\n");

        const response = await llmAxios.post('/report_user', {
            'model': 'mistral',
            'context': context, // Use the joined string here directly
            'reason': reportReason,
            'reportedUser': (await interaction.guild?.members.fetch(userId) as GuildMember).user.username,
            'affectedUser': interaction.user.username,
        });

        try {
            const embed = new EmbedBuilder()
            .setTitle('Odpowiedź AI')
            .setColor('Blue')
            .setAuthor({name: 'Mistral'})
            .setDescription('Odpowiedź AI na zgłoszenie użytkownika')
            .addFields({
                name: 'Osoba do ukarania',
                value: response.data.personToPunishment,
            }, {
                name: 'Powód',
                value: response.data.reason,
            }, {
                name: 'Kara',
                value: response.data.punishment,
            }, {
                name: 'Czas',
                value: response.data.time,
            }, {
                name: 'Komentarz',
                value: response.data.summary,
            }
            );

            await x?.send({embeds: [embed]});
        } catch (err) {
            await x?.send(response.data);
        }

        
    }
};