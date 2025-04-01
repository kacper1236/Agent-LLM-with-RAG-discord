import { CommandInteraction, SlashCommandBuilder, SlashCommandOptionsOnlyBuilder } from 'discord.js';
import { DataBase } from '../db/db.module.js';

export interface CommandType {
  definition: SlashCommandBuilder | SlashCommandOptionsOnlyBuilder;
  handler: (interaction: CommandInteraction, dbService: typeof DataBase) => Promise<void>;
  displayName?: string;
}
