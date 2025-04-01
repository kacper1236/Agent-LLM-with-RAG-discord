import { 
  AuditLogEvent,
  channelMention,
  Client,
  DMChannel,
  EmbedBuilder,
  Events,
  GatewayIntentBits,
  Guild,
  GuildBan,
  GuildChannel,
  GuildMember,
  IntentsBitField,
  Interaction,
  Invite,
  MessageFlagsBitField,
  ModalBuilder,
  PermissionsBitField,
  REST,
  roleMention,
  Routes,
  TextChannel,
  userMention,
  VoiceChannel,
  VoiceState,
  ModalSubmitInteraction,
  ThreadManager,
} from 'discord.js';
import { createHash } from 'node:crypto';
import type { DataBase } from '../db/db.module.js';
import { DiscordCommandsEntity } from '../db/entities/discord-commands.entity.js';
import type { CommandType } from '../types/command.type.js';
import { deepSortObject } from '../utils/deep-sort-object.util.js';
import { buttonsInSystem } from './buttons/index.js';
import { commandsInSystem } from './commands/index.js';
import { modalInSystem } from './modals/index.js';
import { llmAxios } from 'llm/llm-axios.service.js';
import { ModalType } from 'types/modal.type.js';

const token = process.env.DISCORD_TOKEN as string;
const tokenId = process.env.DISCORD_APP_ID as string;

const clientIntents = new IntentsBitField();
clientIntents.add(...[
  GatewayIntentBits.Guilds,
  GatewayIntentBits.DirectMessages,
  GatewayIntentBits.DirectMessageTyping,
  GatewayIntentBits.DirectMessageReactions,
  GatewayIntentBits.MessageContent,
  GatewayIntentBits.GuildMessages,
  GatewayIntentBits.GuildMessageTyping,
  GatewayIntentBits.GuildInvites,
  GatewayIntentBits.GuildMembers,
  GatewayIntentBits.GuildVoiceStates,
]);

const client = new Client({
  intents: clientIntents,
}) as Client<boolean> & { dbService: typeof DataBase };

client.on(Events.Debug, (msg) => {
  console.info(msg);
});

async function sendRulesToRAG() {
  try {
    const guilds = client.guilds.cache.map(guild => guild.id);
    for (let i = 0; i < guilds.length; i++){
      await llmAxios.post("/set_server_rules", {'serverId': guilds[i], 
        'rules': client.dbService.discord.getRules(guilds[i]),
        'namespace': 'abcd', //temporary
        'document': 'server_rules' //temporary or default idk
        })
    }
  } catch (err) {
    console.log(err);
  }
}

client.once(Events.ClientReady, async (cl) => {
  console.log(`Ready as: ${cl.user.tag}`);
  
  const commandsToSend: CommandType['definition'][] = [];
  const commandsToRemove: DiscordCommandsEntity[] = [];
  const dbCommands = await client.dbService.discord.getCommands();
  for (const [name, command] of commandsInSystem.entries()) {
    const dbCommand = dbCommands.find(x => x.name === name);
    if (!dbCommand) commandsToSend.push(command.definition);
    else {
      const hash = createHash('md5').update(JSON.stringify(deepSortObject(command.definition))).digest('hex');
      if (!dbCommand.discordId || dbCommand.definitionHash !== hash) {
        commandsToSend.push(command.definition);
        dbCommand.definitionHash = hash;
        dbCommand.displayName = command.definition.description;
      }
    }
  }
  for (const command of dbCommands) {
    if (!commandsInSystem.some(x => x.definition.name === command.name)) {
      if (command.discordId) commandsToRemove.push(command);
    }
  }
  
  if (commandsToRemove.length > 0) {
    const rest = new REST().setToken(token);
    
    console.log('sending commands <=', commandsToRemove.map(x => x.name));
    for (const command of commandsToRemove) {
      try {
        const response = await rest.delete(Routes.applicationCommand(tokenId, command.discordId as string));
        console.log(response);
      } catch (err) {
        console.log(err);
      }
    }
  }
  
  if (commandsToSend.length > 0) {
    const rest = new REST().setToken(token);
    
    console.log('sending commands =>', commandsToSend.map(x => x.name));
    const response = await rest.put(Routes.applicationCommands(tokenId), {
      body: commandsToSend,
    });
    
    console.log(response);
    if (Array.isArray(response)) {
      for (const saved of response) {
        const dbCommand = dbCommands.find(x => x.name === saved.name);
        const command = commandsInSystem.find(x => x.definition.name === saved.name) as CommandType;
        if (!dbCommand) {
          await client.dbService.discord.createCommand(command, saved.id);
        } else {
          dbCommand.discordId = saved.id;
          await dbCommand.save();
        }
      }
    }
  }


  
  console.log('Working...');
  client?.user?.setActivity('Waiting for Questions', {
    type: 4,
  });
});

client.on(Events.GuildCreate, async (guild: Guild) => {
  const server = await client.dbService.discord.getServerById(guild.id);
  if (!server) {
    await client.dbService.discord.createServer(guild.id, guild.name);
    // override all commands to server
    await client.dbService.discord.writeServerCommands(guild.id);
  }
});

client.on(Events.InteractionCreate, async (interaction: Interaction) => {
  
  if (interaction.isButton() || interaction.isChatInputCommand() || interaction.isModalSubmit() || interaction.isStringSelectMenu()) {
    ;
  } else return;
  
  const userBanned = await client.dbService.discord.isUserBanned(interaction.user.id);
  if (userBanned) {
    await interaction.reply({content: `Denied`, flags: MessageFlagsBitField.Flags.Ephemeral});
    console.log(`Banned user [${interaction.user.globalName}(#${interaction.user.username})] query: guild${interaction.guildId} chan${interaction.channelId} `)
    
    return interaction.deleteReply();
  }
  
  if (interaction.isButton()){
    const button = buttonsInSystem.get(interaction.customId);
    if (!button) {
      return interaction.reply({
        content: 'Button not found',
        flags: MessageFlagsBitField.Flags.Ephemeral,
      });
    }

    return await button.handler(interaction);
  }

  if (interaction.isModalSubmit()) {
    const modal = modalInSystem.get(interaction.customId);
    if (!modal) {
      return interaction.reply({
        content: 'Modal not found',
        flags: MessageFlagsBitField.Flags.Ephemeral,
      });
    }
    return await modal.handler(interaction);
  }

  if (interaction.isStringSelectMenu()) {
    if (!interaction.customId) return;
    
    const selectedValue = interaction.values;
    
    const modal = modalInSystem.get(selectedValue[0]);
    if (!modal){
      return await interaction.reply({
        content: 'Modal not found',
        ephemeral: true
      });
    }

    return await interaction.showModal(modal.definition);
  }
  
  const command = commandsInSystem.get(interaction.commandName);
  if (!command) {
    return interaction.reply({
      content: 'Command not found',
      flags: MessageFlagsBitField.Flags.Ephemeral,
    });
  }
  // /chat  chat:applies estim on two of the rings
  {
    const commandData = await client.dbService.discord.getCommand(interaction.commandName);
    if (commandData && commandData.status === 'disabled') {
      return interaction.reply({
        content: 'Command Disabled',
        flags: MessageFlagsBitField.Flags.Ephemeral,
      });
    }
    if (interaction.guildId) {
      const server = await client.dbService.discord.getServerById(interaction.guildId as string);
      if (!server) await client.dbService.discord.createServer(interaction.guildId, interaction?.guild?.name);
      
      const commandServerData = await client.dbService.discord.getServerCommand(interaction.guildId as string, interaction.commandName);
      if (commandServerData && commandServerData.status === 'disabled') {
        return interaction.reply({
          content: 'Command Server Disabled',
          flags: MessageFlagsBitField.Flags.Ephemeral,
        });
      }
      if (!commandServerData) {
        await client.dbService.discord.createServerCommand(interaction.guildId, command.definition.name, 'disabled');
        return interaction.reply({
          content: 'Command Server Disabled',
          flags: MessageFlagsBitField.Flags.Ephemeral,
        });
      }
      
      
      
      if (commandServerData && commandServerData.status === 'only-admins') {
        // TODO: check if current user is server admin
      }
    }
    
    // TODO: Validate other flags for command
    {
      
    }
  }
  
  await command.handler(interaction, client.dbService);
});

//logs

client.on(Events.MessageCreate, (message) => {
  if (message.author.bot) return;
  //console.log(message.content);
});
// if patch is added
// client.on(Events.PrivateMessageCreate, async (message: OmitPartialGroupDMChannel<Message>) => {
//   // this is only message, nothing to do here sadly
// });

client.on(Events.MessageUpdate, (oldMessage, newMessage) => {
  if (oldMessage.author?.bot) return;
  
  const embed = new EmbedBuilder()
    .setTitle('Edited message')
    .setColor('Blue')
    .setAuthor({name : oldMessage.author?.username ?? 'Unknown author', iconURL: oldMessage.author?.avatarURL() ?? undefined})
    .setDescription(`Message edited in channel ${channelMention((oldMessage.channel?.id) as string || 'Unknown channel')} by ${userMention((oldMessage.author?.id) as string) || 'Unknown author'} [Jump here](${oldMessage.url})`)
    .addFields(
      { name: 'Old message', value: oldMessage.content ?? 'Not available content' },
      { name: 'New message', value: newMessage.content ?? 'Not available content' },
    )
    .setTimestamp();

  const channel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (channel) {
    channel.send({ embeds: [embed] });
  }
});

client.on(Events.MessageDelete, (message) => {
  if (message.author?.bot) return;

  const embed = new EmbedBuilder()
    .setTitle('Deleted message')
    .setColor('Red')
    .setAuthor({name : message.author?.username ?? 'Unknown author', iconURL: message.author?.avatarURL() ?? undefined})
    .setDescription(`Message deleted in channel ${channelMention((message.channel?.id) as string || 'Unknown channel')} by ${userMention((message.author?.id) as string) || 'Unknown author'}`)
    .addFields(
      { name: 'Message', value: message.content ?? 'Not available content' },
    )
    .setTimestamp();
  const channel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (channel) {
    channel.send({ embeds: [embed] });
  }
});

client.on(Events.ChannelCreate, async (channel: GuildChannel) => {
  if (!channel.guild) return;

  let target = null;

  try{
    const fetchLogs = await channel.guild.fetchAuditLogs({
        type: AuditLogEvent.ChannelCreate,
        limit: 1,
    });

    target = fetchLogs.entries.first()?.executor;
    if (!target) return;
  }
  catch (err){
    console.log(`ChannelCreate has occurr: ${err}`);
  }

  const embed = new EmbedBuilder()
    .setTitle('Channel created')
    .setColor('Green')
    .setDescription(`Channel created: ${channelMention(channel.id)}`)
    .addFields({
      name: 'Created by',
      value: userMention(target?.id as string) || 'Unknown user',
    })
    .setTimestamp();
  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.ChannelDelete, async (channel) => {
  if (!channel.isTextBased() || channel instanceof DMChannel|| !channel.guild) return;

  let target = null;

  try {
    const fetchLogs = await channel.guild.fetchAuditLogs({
        type: AuditLogEvent.ChannelDelete,
        limit: 1,
    });

    target = fetchLogs.entries.first()?.executor;
    if (!target) console.log("Target for ChannelDelete is null");
  }
  catch (err) {
    console.log(`ChannelDelete has occurr: ${err}`);
  }

  const embed = new EmbedBuilder()
    .setTitle('Channel deleted')
    .setColor('Red')
    .setDescription(`Channel deleted: ${channelMention(channel.id)}`)
    .addFields({
      name: 'Deleted by',
      value: userMention(target?.id as string) || 'Unknown user',
    })
    .setTimestamp();
  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.ChannelUpdate, async (oldChannel, newChannel) => {
  if (!oldChannel.isTextBased() || oldChannel instanceof DMChannel || !oldChannel.guild) return;
  if (!newChannel.isTextBased() || newChannel instanceof DMChannel || !newChannel.guild) return;
  let target = null;

  try {
    const fetchLogs = await oldChannel.guild.fetchAuditLogs({
        type: AuditLogEvent.ChannelUpdate,
        limit: 1,
    });

    target = fetchLogs.entries.first()?.executor || null;
    if (target === null) console.log('Target for Channel Update is null'); //must be changed for smth
  }
  catch (err) {
    console.log(`ChannelUpdate has occurr: ${err}`);
  }

  const embed = new EmbedBuilder()
    .setTitle('Channel updated')
    .setColor('Yellow')
    .setDescription(`Channel updated in ${channelMention(oldChannel.id)}`)
    .addFields({
      name: 'Updated by',
      value: userMention(target?.id as string) || 'Unknown user',
    }
    )
    .setTimestamp();

  const allPermissions = Object.entries(PermissionsBitField.Flags);
  const oldAllowPermissions = oldChannel.permissionOverwrites.cache.get(oldChannel.guild.id)?.allow;
  const newAllowPermissions = newChannel.permissionOverwrites.cache.get(newChannel.guild.id)?.allow;
  const oldDenyPermissions = oldChannel.permissionOverwrites.cache.get(oldChannel.guild.id)?.deny;
  const newDenyPermissions = newChannel.permissionOverwrites.cache.get(newChannel.guild.id)?.deny;

  if (oldChannel.name !== newChannel.name) {
    embed.addFields({
      name: 'Old name',
      value: oldChannel.name,
    }, {
      name: 'New name',
      value: newChannel.name,
    });
  }
  if (!(oldChannel instanceof VoiceChannel) && !(newChannel instanceof VoiceChannel) && oldChannel.topic !== newChannel.topic) {
    embed.addFields({
      name: 'Old topic',
      value: oldChannel.topic || 'Not available or empty',
    }, {
      name: 'New topic',
      value: newChannel.topic || 'Not available or empty',
    })
  }
  if (oldChannel.nsfw !== newChannel.nsfw) {
    embed.addFields({
      name: 'Old nsfw',
      value: oldChannel.nsfw ? 'Yes' : 'No',
    }, {
      name: 'New nsfw',
      value: newChannel.nsfw ? 'Yes' : 'No',
    });
  }
  if (oldChannel.permissionOverwrites.cache.size !== newChannel.permissionOverwrites.cache.size) { //dodawanie i usuwanie konkretnej roli dla kanału
    embed.addFields({
      name: 'Old permission overwrites',
      value: oldChannel.permissionOverwrites.cache.size.toString(),
    }, {
      name: 'New permission overwrites',
      value: newChannel.permissionOverwrites.cache.size.toString(),
    });
  }
  if (oldAllowPermissions !== newAllowPermissions) { //dodawnia permisji na konkretny kanał dla konkretnej roli
    const hasOldPermissions = allPermissions.filter(([name, bit]) => oldAllowPermissions?.has(BigInt(bit))).map(([name]) => name) || ['No permissions']; 
    const hasNewPermissions = allPermissions.filter(([name, bit]) => newAllowPermissions?.has(BigInt(bit))).map(([name]) => name) || ['No permissions'];
    //console.log(hasOldPermissions);
    embed.addFields({
      name: 'For role',
      value: `${roleMention(oldChannel.permissionOverwrites.cache.get(oldChannel.guild.id)?.id as string) || 'Unknown role'}`,
    },{
      name: 'Old permissions',
      value: `${hasOldPermissions.join(', ') || 'No permissions'}`,
    }, {
      name: 'New add permissions',
      value: hasNewPermissions.join(', ') || 'No permissions',
    }); // do poprawy, żeby niektórych nie dublował i żeby pokazywał tylko zmiany
  }
  if (oldDenyPermissions !== newDenyPermissions) { //usuwanie permisji na konkretny kanał dla konkretnej roli 
    const hasOldPermissions = allPermissions.filter(([name, bit]) => oldDenyPermissions?.has(BigInt(bit))).map(([name]) => name) || ['No permissions'];
    const hasNewPermissions = allPermissions.filter(([name, bit]) => newDenyPermissions?.has(BigInt(bit))).map(([name]) => name) || ['No permissions'];
    embed.addFields({
      name: 'For role',
      value: `${roleMention(oldChannel.permissionOverwrites.cache.get(oldChannel.guild.id)?.id as string) || 'Unknown role'}`,
    },{
      name: 'Old permissions',
      value: `${hasOldPermissions.join(', ') || 'No permissions'}`,
    }, {
      name: 'New deny permissions',
      value: hasNewPermissions.join(', ') || 'No permissions',
    }); // do poprawy, żeby niektórych nie dublował i żeby pokazywał tylko zmiany
  }

  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.InviteCreate, async (invite) => {
  console.log([invite.expiresTimestamp, invite.createdTimestamp, invite.maxUses, invite.maxAge]);
  const embed = new EmbedBuilder()
    .setTitle('Invite created')
    .setColor('Green')
    .setDescription(`Invite created by ${invite.inviter || 'Unknown user'}`)
    .addFields({
      name: 'Link',
      value: invite.url,
    })
    .setTimestamp();

  if (invite.channelId !== null) {
    embed.addFields({
      name: 'From channel',
      value: channelMention(invite.channelId as string),
    })
  }
  if (invite.targetUser !== null) { // zaproszenie z VC dokładniej: the user whose stream to display for this voice channel stream invite
    embed.addFields({
      name: 'Target user',
      value: `${invite.targetUser}`,
    })
  } 
  if (invite.expiresTimestamp !== null) { //wymaga wymiany na inny format
    console.log("Siema");
    embed.addFields({
      name: 'Expires at',
      value: `${new Date(invite.expiresTimestamp).toISOString()}`,
    })
  }
  if (invite.createdTimestamp !== null) { //wymaga wymiany na inny format
    
    embed.addFields({
      name: 'Created at',
      value: `${new Date(invite.createdTimestamp)}`,
    })
  }
  if (invite.maxUses !== null) {
    if (invite.maxUses > 0) {
      embed.addFields({
        name: "Max uses",
        value: `${invite.maxUses}`,
      })
    }
    else if (invite.maxUses == 0) {
      embed.addFields({
        name: "Max uses",
        value: 'Unlimited',
      })
    }
    else {
      embed.addFields({
        name: "Max uses",
        value: 'Something went wrong',
      })
    }
  }
  if (invite.maxAge !== null) { //w sekundach
    if (invite.maxAge > 0) {
      embed.addFields({
        name: 'Will expire on',
        value: new Date(Date.now() + invite.maxAge * 1000).toISOString(), 
      })
    }
    else if (invite.maxAge == 0) {
      embed.addFields({
        name: 'Will expire on',
        value: 'Never',
      })
    }
    else {
      embed.addFields({
        name: 'Will expire on',
        value: 'Something went wrong',
      })
    }
  }

  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.InviteDelete, async (invite: Invite) => {
  let target = null;
  try {
    const guild = invite.guild as Guild;
    const fetchLogs = await guild.fetchAuditLogs({
        type: AuditLogEvent.InviteDelete,
        limit: 1,
    });

    target = fetchLogs.entries.first()?.executor;
    if (!target) console.log('Target for InviteDelete is null'); 
  }
  catch (err) {
    console.log(`InviteDelete has occurr: ${err}`); 
  }

  const embed = new EmbedBuilder()
    .setTitle('Invite deleted')
    .setColor('Red')
    .setTimestamp()
    .setDescription(`Invite deleted by ${userMention(target?.id as string) || 'Unknown user'}`)
    .addFields({
      name: 'Link',
      value: invite.url,
    })

  if (invite.channelId !== null) {
    embed.addFields({
      name: 'From channel',
      value: channelMention(invite.channelId as string),
    })
  }

  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.ThreadCreate, (thread) => { // view embed must be changed
  const embed = new EmbedBuilder()
    .setTitle('Thread created')
    .setColor('Green')
    .setTimestamp()
    .setDescription(`Thread created by ${userMention(thread.ownerId as string)} in ${thread.parent}`) // parent, czyli kanał na którym jest thread
    .addFields({
      name: 'link',
      value: thread.url,
    }, {
      name: 'Name',
      value: thread.name,
    }, {
      name: 'Is joinable',
      value: `${thread.joinable}`,
    }, {
      name: 'Is managable',
      value: `${thread.manageable}`,
    }, {
      name: 'Is editable',
      value: `${thread.editable}`,
    }, {
      name: 'Is viewable',
      value: `${thread.viewable}`,
    }, {
      name: 'Is sendable',
      value: `${thread.sendable}`
    }, {
      name: 'Is locked',
      value: `${thread.locked}`
    }
  )
  
  if (thread.createdAt !== null) {
    embed.addFields({
      name: 'Created at',
      value: `${thread.createdAt}`,
    })
  }
  
  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.ThreadDelete, async (thread) => { // view embed must be changed
  let target = null;
  try {
    const guild = thread.guild as Guild;
    const fetchLogs = await guild.fetchAuditLogs({
        type: AuditLogEvent.ThreadDelete,
        limit: 1,
    });

    target = fetchLogs.entries.first()?.executor;
    if (!target) console.log('Target for ThreadDelete is null'); 
  }
  catch (err) {
    console.log(`ThreadDelete has occurr: ${err}`); 
  }

  const embed = new EmbedBuilder()
    .setTitle('Thread deleted')
    .setColor('Red')
    .setTimestamp()
    .setDescription(`Thread deleted by ${userMention(target?.id as string) || 'unknown user'} in ${thread.parent}`) // parent, czyli kanał na którym jest thread
    .addFields({
      name: 'Author',
      value: userMention(thread.ownerId as string),
    } ,{
      name: 'link',
      value: thread.url,
    }, {
      name: 'Name',
      value: thread.name,
    }, {
      name: 'Is joinable',
      value: `${thread.joinable}`,
    }, {
      name: 'Is managable',
      value: `${thread.manageable}`,
    }, {
      name: 'Is editable',
      value: `${thread.editable}`,
    }, {
      name: 'Is viewable',
      value: `${thread.viewable}`,
    }, {
      name: 'Is sendable',
      value: `${thread.sendable}`
    }, {
      name: 'Is locked',
      value: `${thread.locked}`
    })

  if (thread.createdAt !== null) {
    embed.addFields({
      name: 'Created at',
      value: `${thread.createdAt}`,
    })
  }

  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.GuildBanAdd, async (ban: GuildBan) => {
  let target = null;
  try {
    const guild = ban.guild as Guild;
    const fetchLogs = await guild.fetchAuditLogs({
        type: AuditLogEvent.MemberBanAdd,
        limit: 1,
    });

    target = fetchLogs.entries.first()?.executor;
    if (!target) console.log('Target for MemberBanAdd is null'); 
  }
  catch (err) {
    console.log(`TargetBanAdd has occurr: ${err}`); 
  }

  const embed = new EmbedBuilder()
    .setTitle('User banned')
    .setColor('Red')
    .setTimestamp()
    .setDescription(`User banned in ${ban.guild.name} by ${userMention(target?.id as string) || 'unknown user'}`)
    .addFields({
      name: 'User',
      value: ban.user.username,
    },{
      name: 'Reason',
      value: ban.reason || 'No reason given',
    })
  
  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.GuildBanRemove, async (ban: GuildBan) => { // need to verify
  let target = null;
  try {
    const guild = ban.guild as Guild;
    const fetchLogs = await guild.fetchAuditLogs({
        type: AuditLogEvent.MemberBanRemove,
        limit: 1,
    });

    target = fetchLogs.entries.first()?.executor;
    if (!target) console.log('Target for MemberBanRemove is null'); 
  }
  catch (err) {
    console.log(`TargetBanRemove has occurr: ${err}`);
  }

  const embed = new EmbedBuilder()
    .setTitle('User unbanned')
    .setColor('Green')
    .setTimestamp()
    .setDescription(`User unbanned in ${ban.guild.name} by ${userMention(target?.id as string) || 'unknown user'}`)
    .addFields({
      name: 'User',
      value: ban.user.username,
    },{
      name: 'Reason',
      value: ban.reason || 'No reason given',
    })
  
  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.GuildMemberAdd, async (member: GuildMember) => { //need to verify
  const embed = new EmbedBuilder()
    .setTitle('Member joined')
    .setColor('Green')
    .setTimestamp()
    .setDescription(`Member joined ${member.guild.name}`)
    .addFields({
      name: 'User',
      value: member.user.username,
    }, {
      name: 'Joined at',
      value: `${member.joinedAt}`,
    }, {
      name: 'Created at',
      value: `${member.user.createdAt}`,
    })
  
  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.GuildMemberRemove, async (member) => { // need to verify!!

  try {
      const fetchLogs = await member.guild.fetchAuditLogs({
          type: AuditLogEvent.MemberBanAdd,
          limit: 1,
      });

      const target = fetchLogs.entries.first()?.executor;
      if (!target) return; //return ponieważ wywołał się GuildBanAdd

      if (target.username !== member.user.username) return; //dodawć warunek różnicy czasów między banem a usunięciem
      //jest błąd taktyczny
  }
  catch (err) {
    console.log(`GuildMemberRemove has occurr on MemberBanAdd: ${err}`);
  }
  let target = null;
  try {
      const fetchLogs = await member.guild.fetchAuditLogs({
          type: AuditLogEvent.MemberKick,
          limit: 1,
      });

      target = fetchLogs.entries.first()?.executor;
      if (!target) console.log("Target for MemberKick is null"); //na cokoklwiek innego?

      if (target?.username !== member.user.username) return;
  }
  catch (err) {
    console.log(`GuildMemberRemove has occurr on MemberKick: ${err}`);
  }

  const embed = new EmbedBuilder()
    .setTitle('Member left')
    .setColor('Red')
    .setTimestamp()
    .setDescription(`Member left ${member.guild.id}`)
    .addFields({
      name: 'User',
      value: member.user.username,
    }, {
      name: 'Joined at',
      value: `${member.joinedAt}`,
    }, {
      name: 'Created at',
      value: `${member.user.createdAt}`,
    })
  
  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.GuildMemberUpdate, async (oldMember, newMember) => { // need to verify
  const embed = new EmbedBuilder()
    .setTitle('Member updated')
    .setColor('Yellow')
    .setTimestamp()
    .setDescription(`Member updated in ${oldMember.guild.name}`)
    .addFields({
      name: 'User',
      value: oldMember.user.username,
    })
  
  if (oldMember.nickname !== newMember.nickname) {
    embed.addFields({
      name: 'Old nickname',
      value: oldMember.nickname || 'No nickname',
    }, {
      name: 'New nickname',
      value: newMember.nickname || 'No nickname',
    });
  }
  if (oldMember.roles.cache.size !== newMember.roles.cache.size) {
    const oldRoles = oldMember.roles.cache.map(role => role.name).join(', ') || 'No roles';
    const newRoles = newMember.roles.cache.map(role => role.name).join(', ') || 'No roles';
    embed.addFields({
      name: 'Old roles',
      value: oldRoles,
    }, {
      name: 'New roles',
      value: newRoles,
    }); // do poprawy, żeby niektórych nie dublował i żeby pokazywał tylko zmiany
  }
  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

client.on(Events.VoiceStateUpdate, async (oldState: VoiceState, newState: VoiceState) => { // need to verify

  if (oldState.channelId === newState.channelId) return; // Można dodać self_mute, self_deaf, mute i deaf
  //supress jest dla osób na podium jako pozwolenie na mówienie

  const embed = new EmbedBuilder()
    .setTitle('Voice state updated')
    .setColor('Yellow')
    .setTimestamp()
    .setDescription(`Voice state updated in ${oldState.guild.name}`)
    .addFields({
      name: 'User',
      value: userMention(oldState.member?.id as string) || 'Unknown user',
    })
  
  if (oldState.channelId !== newState.channelId && oldState.channelId !== null && newState.channelId !== null) {
    embed.addFields({
      name: 'Move from',
      value: oldState.channel?.name || 'No channel',
    }, {
      name: 'Move to',
      value: newState.channel?.name || 'No channel',
    });
  }
  if (oldState.channelId !== null && newState.channelId === null) {
    embed.addFields({
      name: 'Leave from',
      value: oldState.channel?.name || 'No channel',
    });
  }
  if (oldState.channelId === null && newState.channelId !== null) {
    embed.addFields({
      name: 'Join to',
      value: newState.channel?.name || 'No channel',
    });
  }

  const logChannel = client?.channels.cache.get("1319715211971657811") as TextChannel;
  if (logChannel) {
    logChannel.send({ embeds: [embed] });
  }
});

export const connect = async (service: typeof DataBase) => {
  try {
    client.dbService = service;
    await client.login(token);
  } catch (error) {
    console.error('Could not take bot account', error);
    
    throw error;
  }
};

export const disconnect = async () => {
  try {
    await client.destroy();
  } catch (error) {
    console.log('Could not destroy bot connection', error);
    
    throw error;
  }
};

export const isReady = () => {
  return client.isReady();
};
