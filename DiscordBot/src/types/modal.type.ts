import { ModalBuilder, ModalSubmitInteraction } from "discord.js";

export interface ModalType {
    definition: ModalBuilder;
    handler: (interaction: ModalSubmitInteraction) => Promise<void>;
    displayName?: string;
}