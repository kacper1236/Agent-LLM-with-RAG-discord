import { DataBase } from "db/db.module.js";
import { CommandInteraction, EmbedBuilder, MessageFlagsBitField, PermissionsBitField, SlashCommandBuilder, userMention } from "discord.js";
import { CommandType } from "types/command.type.js";

export const warningsCommand: CommandType = {
    definition: new SlashCommandBuilder()
        .setName('warnings')
        .setDescription('get warnings for a user')
        .addUserOption(
            option => option
            .setName('user')
            .setDescription('User to get warnings for')
            .setRequired(true)
        )
    ,
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
                content: 'You do not have permission to ban users',
                flags: MessageFlagsBitField.Flags.Ephemeral,
            });
            return;
        }
        const user = interaction.options.get('user')?.value || "";
        const warns = (await db.discord.getWarns(interaction.guild.id, user.toString())).map(warn => warn.dataValues.warnings);
        console.log(warns.map(warn => warn.map(w => w.text)));

        const embed = new EmbedBuilder()
            .setTitle(`Warnings for user ${(await interaction.client.users.fetch(user.toString())).username}`)
            .setColor('Purple')
            .setTimestamp()
        
        for (const warn of warns) {
            for (const w of warn) {
                const creatorWarn = (await interaction.client.users.fetch(w.createdBy)).username;
                embed.addFields({
                    name: `Warned by ${creatorWarn} \nID: ${w.id}`,
                    value: w.text,
                });
            }
        }
        await interaction.reply({ embeds: [embed] });
    },
};