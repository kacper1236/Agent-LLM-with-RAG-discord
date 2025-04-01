import { GuildMemberRoleManager, MessageFlagsBitField, PermissionsBitField, SlashCommandBuilder } from "discord.js";
import { CommandType } from "../../types/command.type.js";
import { CommandInteraction } from "discord.js";
import { DataBase } from "db/db.module.js";
import { ServerKick } from "db/entities/discord-servers-kicks.entity.js";

export const kickCommand: CommandType = {
    definition: new SlashCommandBuilder()
    .setName('kick')
    .setDescription('Kick a user')
    .addStringOption(
        option => option
        .setName('user')
        .setDescription('User to kick')
        .setRequired(true)
    )
    .addStringOption(
        option => option
        .setName('reason')
        .setDescription('Give reason')
    ),
    handler: async (interaction: CommandInteraction, db: typeof DataBase) => {

        const permission = interaction.member?.permissions as PermissionsBitField;
        if (!permission.has(PermissionsBitField.Flags.KickMembers)) {
            await interaction.reply({
                content: 'You do not have permission to kick users',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }
        else if (!interaction.guild) {
            await interaction.reply({
                content: 'This command must be used in a server',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }
        const user = interaction.options.get('user')?.value || '';
        const reason = interaction.options.get('reason')?.value || 'No reason given';
        
        const member = interaction.guild.members.cache.find(member => member.user.id === user || `<@${member.user.id}>` === user);

        if (!member) {
            await interaction.reply({
                content: 'User not found',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }
        else if (!member.kickable) {
            await interaction.reply({
                content: 'User cannot be kicked',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }
        else if (interaction.user.id === member.user.id) {
            await interaction.reply({
                content: 'You cannot kick yourself',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }

        const creatorCommand = interaction.member?.roles as GuildMemberRoleManager;
        if(member.roles.highest.position >= creatorCommand.highest.position) {
            await interaction.reply({
                content: 'This user has a higher or equal role than you',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
        }
        
        await member.kick(reason.toString());

        const kicks: ServerKick[] = [{
            reason: reason.toString(),
            createdAt: new Date(Date.now()),
            createdBy: interaction.user.id,
        },];
        db.discord.addKicks(member.id, interaction.guild?.id, kicks);

        await interaction.reply({
            content: `User ${user} has been kicked`,
        });
    }
};
