import { DataBase } from "db/db.module.js";
import { CommandInteraction, MessageFlagsBitField, PermissionsBitField, SlashCommandBuilder, userMention } from "discord.js";
import { UUID } from "node:crypto";
import { CommandType } from "types/command.type.js";

export const delwarnCommand: CommandType = {
    definition: new SlashCommandBuilder()
        .setName('delwarn')
        .setDescription('delete a warning')
        .addUserOption(
            option => option
            .setName('user')
            .setDescription('User to delete warning for')
            .setRequired(true)
        )
        .addStringOption(
            option => option
            .setName('warnid')
            .setDescription('Warning to delete')
            .setRequired(true)
        ),
    handler: async (interaction: CommandInteraction, db: typeof DataBase) => {
        if (!interaction.guild){
            await interaction.reply({
                content: 'This command must be used in a server',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }
        const permission = interaction.member?.permissions as PermissionsBitField;
        if (!permission.has(PermissionsBitField.Flags.BanMembers) || !permission.has(PermissionsBitField.Flags.KickMembers)) {
            await interaction.reply({
                content: 'You do not have permission to delete warn users',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }
        const user = interaction.options.get('user')?.value || "";
        const warnid = interaction.options.get('warnid')?.value || "";

        if (user === "" || warnid === "") {
            await interaction.reply({
                content: 'Please provide a user or warnid',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }

        const deleteFromDatabase = await db.discord.deleteWarn(interaction.guild.id, user.toString(), warnid as UUID);
        if (deleteFromDatabase === true) {
            await interaction.reply({
                content: `Deleted warning for ${userMention(user.toString())}`,
            });
        }
    }
}