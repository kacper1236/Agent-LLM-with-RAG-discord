import { ButtonBuilder } from "discord.js";
import { ButtonType } from "types/button.type.js";

export const cancelButton: ButtonType = {
    definition: new ButtonBuilder()
    .setCustomId('cancel')
    ,
    handler: async (interaction) => {
        const button = interaction;

        await button.reply({
            content: 'Cancelled action',
            ephemeral: true,
        });
    },
}