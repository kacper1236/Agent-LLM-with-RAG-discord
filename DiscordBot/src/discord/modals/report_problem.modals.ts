import { 
    ModalBuilder, 
    TextInputBuilder, 
    TextInputStyle, 
    ActionRowBuilder, 
    ModalSubmitInteraction 
} from "discord.js";
import { ModalType } from "../../types/modal.type.js";

export const reportProblem: ModalType = {
    definition: new ModalBuilder()
        .setCustomId('reportProblem')
        .setTitle('Zgłoś problem')
        .addComponents(
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('issue')
                    .setLabel('Opisz problem')
                    .setStyle(TextInputStyle.Paragraph)
                    .setRequired(true)
            ),
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('idChannel')
                    .setLabel('ID kanału (opcjonalnie)')
                    .setStyle(TextInputStyle.Short)
                    .setRequired(false)
            ),
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('idRank')
                    .setLabel('ID rangi (opcjonalnie)')
                    .setStyle(TextInputStyle.Short)
                    .setRequired(false)
            ),
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('case')
                    .setLabel('Opisz okoliczności')
                    .setStyle(TextInputStyle.Paragraph)
                    .setRequired(true)
            )
        ),
    handler: async (interaction: ModalSubmitInteraction) => {
        if (!interaction.isModalSubmit()) return;

        const issue = interaction.fields.getTextInputValue('issue');
        const idChannel = interaction.fields.getTextInputValue('idChannel') || 'Not get channel';
        const idRank = interaction.fields.getTextInputValue('idRank') || 'Not get rank';
        const caseIssue = interaction.fields.getTextInputValue('case');

        const x = await interaction.guild?.channels.create({
            name: `Ticket ${interaction.user.username}`
            //parent need to add (kategoria)
        });

        await x?.send({
            content: `✅ **Zgłoszenie przyjęte!**\n- **Problem**: ${issue}\n- **ID kanału**: ${idChannel}\n- **ID rangi**: ${idRank}\n- **Okoliczności**: ${caseIssue}`
        });

        await interaction.deferUpdate();
    }
}