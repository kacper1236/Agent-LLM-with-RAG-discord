import { 
    ModalBuilder, 
    TextInputBuilder, 
    TextInputStyle, 
    ActionRowBuilder, 
    ModalSubmitInteraction 
} from "discord.js";
import { ModalType } from "../../types/modal.type.js";

export const trusted: ModalType = {
    definition: new ModalBuilder()
        .setCustomId('trusted')
        .setTitle('Ranga "Zaufany futrzak"')
        .addComponents(
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('reason')
                    .setLabel('Opisz dlaczego masz dostać tę rolę')
                    .setStyle(TextInputStyle.Paragraph)
                    .setRequired(true)
            )
        )
    ,
    
    handler: async (interaction: ModalSubmitInteraction) => {
        if (!interaction.isModalSubmit()) return;

        const reason = interaction.fields.getTextInputValue('reason');

        const x = await interaction.guild?.channels.create({
            name: `Ticket ${interaction.user.username}`
            //parent need to add (kategoria)
        });

        await x?.send({
            content: `✅ **Propozycja przyjęta!**\n- **Opis**: ${reason}`
        });

        await interaction.deferUpdate(); //w kazdym modalu to musi być bo inaczej modal się nie zamyka

    }
}