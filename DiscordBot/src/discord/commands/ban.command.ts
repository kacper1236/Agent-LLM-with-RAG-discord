import { GuildMember, GuildMemberRoleManager, MessageFlagsBitField, PermissionsBitField, SlashCommandBuilder, userMention } from "discord.js";
import { CommandType } from "../../types/command.type.js";
import { CommandInteraction } from "discord.js";
import { DataBase } from "db/db.module.js";
import { ServerBan } from "db/entities/discord-servers-bans.entity.js";

function convertToDate(date: string): Date {
    if (date === 'never') return new Date(0);
    const dateArr = date.split(' ');
    
    let finalDate = new Date(Date.now());

    for (let i = 0; i < dateArr.length; i++) {
        const dateContent = dateArr[i] as string;
        dateArr[i] = dateArr[i].slice(0, -1);
        switch(dateContent[dateContent.length - 1]) {
            case 'Y':
                finalDate = new Date(finalDate.getTime() + parseInt(dateArr[i]) * 1000 * 60 * 60 * 24 * 365);
                break;
            case 'M':
                finalDate = new Date(finalDate.getTime() + parseInt(dateArr[i]) * 1000 * 60 * 60 * 24 * 30);
                break;
            case 'D':
                finalDate = new Date(finalDate.getTime() + parseInt(dateArr[i]) * 1000 * 60 * 60 * 24);
                break;
            case 'h':
                finalDate = new Date(finalDate.getTime() + parseInt(dateArr[i]) * 1000 * 60 * 60);
                break;
            case 'm':
                finalDate = new Date(finalDate.getTime() + parseInt(dateArr[i]) * 1000 * 60);
                break;
            case 's':
                finalDate = new Date(finalDate.getTime() + parseInt(dateArr[i]) * 1000);
                break;
            default:
                console.log(`Invalid date format ${dateArr[i]}`);
                break;
        }
    }
    return finalDate;
}

export const banCommand: CommandType = {
    definition: new SlashCommandBuilder()
    .setName('ban')
    .setDescription('Ban a user')
    .addStringOption(
        option => option
        .setName('user')
        .setDescription('User to ban')
        .setRequired(true)
    )
    .addStringOption(
        option => option
        .setName('reason')
        .setDescription('Reason for ban')
    )
    .addStringOption(
        option => option
        .setName('expires')
        .setDescription('Ban expiration date')
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
        const reason = interaction.options.get('reason')?.value || 'No reason given';
        const expires = interaction.options.get('expires') ?.value || 'never';
        const date = convertToDate(expires.toString());

        const userToBan = interaction.guild?.members.cache.find(member => `<@${member.user.id}>` === user || member.user.id === user) || 
            await interaction.client.users.fetch(user.replace("<@", "").replace(">", ""));

        if (userToBan.id === interaction.user.id) {
            await interaction.reply({
                content: 'You cannot ban yourself',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }

        else if (!userToBan) {
            await interaction.reply({
                content: 'User not found',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }
        const creatorCommand = interaction.member?.roles as GuildMemberRoleManager;
        if(userToBan instanceof GuildMember && userToBan.roles.highest.position >= creatorCommand.highest.position) {
            await interaction.reply({
                content: 'This user has a higher or equal role than you',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
        }
        else if (userToBan instanceof GuildMember && !userToBan.bannable) {
            await interaction.reply({
                content: 'User cannot be banned',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }

        await interaction.guild?.members.ban(userToBan, {reason: reason.toString()});
        
        const bans: ServerBan[] = [{
            text: reason.toString(),
            createdAt: new Date(),
            createdBy: interaction.user.id,
            expiresAt: expires ? date : 'never',
            isPerm: 'never' === expires? true : false,
            isFinal: false,
        },];
        db.discord.addBan(userToBan.id,interaction.guildId as string, bans, expires ? new Date(expires.toString()) : undefined);
        
        await interaction.reply({
            content: `User ${userMention(user)} has been banned for ${reason}`,
        });
    },
};
