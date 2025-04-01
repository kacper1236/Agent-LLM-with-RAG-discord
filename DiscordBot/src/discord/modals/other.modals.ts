import { 
    ModalBuilder, 
    TextInputBuilder, 
    TextInputStyle, 
    ActionRowBuilder, 
    ModalSubmitInteraction 
} from "discord.js";
import { ModalType } from "../../types/modal.type.js";

export const other: ModalType = {
    definition: new ModalBuilder()
        .setCustomId('other')
        .setTitle('Zgłoś inny problem')
        .addComponents(
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('description')
                    .setLabel('Opisz problem')
                    .setStyle(TextInputStyle.Paragraph)
                    .setRequired(true)
            )
        ),
    
    handler: async (interaction: ModalSubmitInteraction) => {
        if (!interaction.isModalSubmit()) return;
        
        const description = interaction.fields.getTextInputValue('description');

        const x = await interaction.guild?.channels.create({
            name: `Ticket ${interaction.user.username}`
            //parent need to add (kategoria)
        });

        await x?.send({
            content: `✅ **Zgłoszenie przyjęte!**\n- **Opis problemu**: ${description}`
        });
        
        await interaction.deferUpdate(); //w kazdym modalu to musi być bo inaczej modal się nie zamyka
    }
}