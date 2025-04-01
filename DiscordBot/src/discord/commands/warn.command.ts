import { CommandInteraction, GuildMember, GuildMemberRoleManager, MessageFlagsBitField, PermissionsBitField, SlashCommandBuilder } from "discord.js";
import { ServerWarning } from "db/entities/discord-servers-warnings.entity.js"
import { CommandType } from "types/command.type.js";
import { DataBase } from "db/db.module.js";
import { userMention } from "discord.js";
import { uuidv7 } from "uuidv7";
import { UUID } from "node:crypto";

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

export const warnCommand: CommandType = {
    definition: new SlashCommandBuilder()
    .setName("warn")
    .setDescription("warn a member")
    .addUserOption(
        option => option
        .setName("user")
        .setDescription("Member to warn")
        .setRequired(true)
    )
    .addStringOption(
        option => option
        .setName("reason")
        .setDescription("Reason to warn member")
    )
    .addStringOption(
        option => option
        .setName("expires")
        .setDescription("Warn expiration date")
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
                content: 'You do not have permission to warn users',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }
        const user = interaction.options.get('user')?.value || "";
        const reason = interaction.options.get('reason')?.value || "No reason given";
        const expires = interaction.options.get('expires')?.value || "never";
        const date = convertToDate(expires.toString())

        const warns: ServerWarning[] = [{
            id: (await uuidv7()) as UUID,
            text: reason.toString(),
            createdAt: new Date(),
            createdBy: interaction.user.id,
            expiresAt: expires ? date : 'never',
        }];
        db.discord.addWarn(interaction.guild.id, user.toString(), warns, expires ? date : 'never');
        
        await interaction.reply({
            content: `Warned ${userMention(user.toString())} for ${reason}`,
        });

    },
}