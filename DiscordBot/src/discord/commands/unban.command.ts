import { DataBase } from "db/db.module.js";
import { CommandInteraction, GuildBan, MessageFlagsBitField, PermissionsBitField, SlashCommandBuilder, User } from "discord.js";
import { CommandType } from "types/command.type.js";

export const unbanCommand: CommandType = {
    definition: new SlashCommandBuilder()
        .setName('unban')
        .setDescription('Unban a user')
        .addStringOption(
            option => option
            .setName('user')
            .setDescription('User to unban, example: 123456789012345678')
            .setRequired(true)
        )
    ,
    handler: async (interaction: CommandInteraction, db: typeof DataBase) => {
        if (!interaction.guild) {
            await interaction.reply({
                content: 'This command must be used in a server',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        };

        const permission = interaction.member?.permissions as PermissionsBitField;
        if (!permission.has(PermissionsBitField.Flags.BanMembers)) {
            await interaction.reply({
                content: 'You do not have permission to ban users',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }

        const user = interaction.options.get('user')?.value as string || '';
        let userToUnban: GuildBan | null;

        try {
            userToUnban = await interaction.guild?.bans.fetch(user) || null;
        }
        catch (error) {
            await interaction.reply({
                content: 'User not found',
            });
            return;
        }

        try {
            await interaction.guild.bans.remove(userToUnban.user.id);
        }
        catch (error) {
            await interaction.reply({
                content: `User ${userToUnban.user.username} is already unbanned`,
            });
            return;
        }

        db.discord.deleteBan(userToUnban.user.id, interaction.guild.id);

        await interaction.reply({
            content: `Unbanned ${userToUnban.user.username}`,
        });
    },
}