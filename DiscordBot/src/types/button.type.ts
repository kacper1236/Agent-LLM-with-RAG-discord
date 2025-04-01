import { ButtonBuilder, ButtonInteraction } from "discord.js";

export interface ButtonType {
    definition: ButtonBuilder;
    handler: (interaction: ButtonInteraction) => Promise<void>;
    displayName?: string;
}
