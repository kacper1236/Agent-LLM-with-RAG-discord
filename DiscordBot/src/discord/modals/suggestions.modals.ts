import { 
    ModalBuilder, 
    TextInputBuilder, 
    TextInputStyle, 
    ActionRowBuilder, 
    ModalSubmitInteraction 
} from "discord.js";
import { ModalType } from "../../types/modal.type.js";

export const suggestion: ModalType = {
    definition: new ModalBuilder()
        .setCustomId('suggestion')
        .setTitle('Daj propozycję')
        .addComponents(
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('suggestion')
                    .setLabel('Podaj swoją propozycję')
                    .setStyle(TextInputStyle.Short)
                    .setRequired(true)
            ),
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('reason')
                    .setLabel('Opisz propozycję')
                    .setStyle(TextInputStyle.Paragraph)
                    .setRequired(true)
            )
        )
    ,
    handler: async(interaction: ModalSubmitInteraction) => {
        if (!interaction.isModalSubmit()) return; 
        
        const suggestion = interaction.fields.getTextInputValue('suggestion');
        const reason = interaction.fields.getTextInputValue('reason');

        const x = await interaction.guild?.channels.create({
            name: `Ticket ${interaction.user.username}`
            //parent need to add (kategoria)
        });

        await x?.send({
            content: `✅ **Propozycja przyjęta!**\n- **Propozycja**: ${suggestion}\n- **Opis**: ${reason}`
        });

        await interaction.deferUpdate(); //w kazdym modalu to musi być bo inaczej modal się nie zamyka

    }
}