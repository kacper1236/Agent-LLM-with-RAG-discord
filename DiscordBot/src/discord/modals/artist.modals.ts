import { 
    ModalBuilder, 
    TextInputBuilder, 
    TextInputStyle, 
    ActionRowBuilder, 
    ModalSubmitInteraction 
} from "discord.js";
import { ModalType } from "../../types/modal.type.js";

export const artist: ModalType = {
    definition: new ModalBuilder()
        .setCustomId('artist')
        .setTitle('Zgłoś bycie artystą')
        .addComponents(
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('howMany')
                    .setLabel('Od jakiego czasu przyjmujesz zamówienia?')
                    .setStyle(TextInputStyle.Short)
                    .setRequired(true)
            ),
            new ActionRowBuilder<TextInputBuilder>().addComponents(
                new TextInputBuilder()
                    .setCustomId('links')
                    .setLabel('Gdzie ogłaszasz swoje usługi artystyczne?')
                    .setStyle(TextInputStyle.Short)
                    .setRequired(true)
            )
        )
        ,

    handler: async (interaction: ModalSubmitInteraction) => {
        if (!interaction.isModalSubmit()) return;

        const howMany = interaction.fields.getTextInputValue('howMany');
        const links = interaction.fields.getTextInputValue('links');

        const x = await interaction.guild?.channels.create({
            name: `Ticket ${interaction.user.username}`
            //parent need to add (kategoria)
        });

        await x?.send({
            content: `✅ **Zgłoszenie przyjęte!**\n- **Od kiedy przyjmujesz zamówienia?**: ${howMany}\n- **Gdzie ogłaszasz swoje usługi artystyczne?**: ${links}`
        });

        await interaction.deferUpdate(); //w kazdym modalu to musi być bo inaczej modal się nie zamyka
    }
}