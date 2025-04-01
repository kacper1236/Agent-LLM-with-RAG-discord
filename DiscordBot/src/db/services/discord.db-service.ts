import { CacheType, CacheTypeReducer, ClientEvents, Events } from 'discord.js';
import { createHash, UUID } from 'node:crypto';
import { Includeable, WhereOptions } from 'sequelize/lib/model';
import { CommandStatus, CommonCommandStatus } from '../../types/command-status.type.js';
import { CommandType } from '../../types/command.type.js';
import { deepSortObject } from '../../utils/deep-sort-object.util.js';
import { DiscordChatsEntity, RAGChatRow } from '../entities/discord-chats.entity.js';
import { DiscordUsersEntity } from '../entities/discord-users.entity.js';
import { DiscordCommandsEntity } from '../entities/discord-commands.entity.js';
import { DiscordServersCommandsEntity } from '../entities/discord-servers-commands.entity.js';
import { DiscordServersEntity } from '../entities/discord-servers.entity.js';
import { DiscordButtonsEntity } from '../entities/discord-buttons.entity.js';
import { DiscordServersBanEntity, ServerBan } from '../entities/discord-servers-bans.entity.js';
import { DiscordServersKickEntity, ServerKick } from 'db/entities/discord-servers-kicks.entity.js';
import { DiscordServersWarningEntity, ServerWarning } from 'db/entities/discord-servers-warnings.entity.js';
import { DiscordLastAcceptedMessageEntity } from 'db/entities/discord-last-accepted-message.entity.js';
import { DiscordRulesEntity, DiscordRulesMessage } from 'db/entities/discord-rules.entity.js';
import { channel } from 'node:diagnostics_channel';

export class DiscordDbServiceClass {
  constructor(
    protected readonly servers: typeof DiscordServersEntity = DiscordServersEntity,
    protected readonly commands: typeof DiscordCommandsEntity = DiscordCommandsEntity,
    protected readonly serverCommands: typeof DiscordServersCommandsEntity = DiscordServersCommandsEntity,
    protected readonly users: typeof DiscordUsersEntity = DiscordUsersEntity,
    protected readonly chats: typeof DiscordChatsEntity = DiscordChatsEntity,
    protected readonly buttons: typeof DiscordButtonsEntity = DiscordButtonsEntity,
    protected readonly bans: typeof DiscordServersBanEntity = DiscordServersBanEntity,
    protected readonly kicks: typeof DiscordServersKickEntity = DiscordServersKickEntity,
    protected readonly warns: typeof DiscordServersWarningEntity = DiscordServersWarningEntity,
    protected readonly lastAcceptedMessage: typeof DiscordLastAcceptedMessageEntity = DiscordLastAcceptedMessageEntity,
    protected readonly rules: typeof DiscordRulesEntity = DiscordRulesEntity,
  ) {}
  
  async getServerById(id: string) {
    return this.servers.findByPk(id);
  }
  
  async getCommands() {
    return this.commands.findAll();
  }
  async getCommand(commandName: string) {
    return this.commands.findByPk(commandName);
  }
  
  async getServerCommand(serverId: string, commandName: string, options?: { includeServer?: boolean; includeCommands?: boolean }) {
    const include: Includeable[] = [];
    if (options?.includeCommands) include.push(DiscordCommandsEntity);
    if (options?.includeServer) include.push(DiscordServersEntity);
    
    const where: WhereOptions<DiscordServersCommandsEntity> = {
      serverId,
      commandId: commandName,
    };
    
    return this.serverCommands.findOne({
      where,
      include,
    });
  }  
  async getServerCommands(serverId: string) {
    return this.serverCommands.findAll({
      where: {
        serverId,
      },
    });
  }
  
  async createServer(id: string, name?: string) {
    const entity = await this.getServerById(id);
    if (!entity) {
      const server = await this.servers.create({
        id, name,
      });
      
      const commands = await this.getCommands();
      for (const command of commands) {
        await this.serverCommands.create({
          serverId: server.id,
          commandId: command.name,
          
          status: 'disabled',
        });
      }
    }
  }
  
  async writeServerCommands(serverId: string) {
    const commands = await this.getCommands();
    const serverCommands = await this.getServerCommands(serverId);
    for (const command of commands) {
      if (serverCommands.some(x => x.commandId === command.id)) continue;
      
      await this.serverCommands.create({
        commandId: command.id,
        serverId,
      });
    }
  }
  
  async changeServerCommand(serverId: number, commandId: number, newState: CommonCommandStatus) {
    let entity = await this.serverCommands.findOne({
      where: {
        serverId,
        commandId,
      },
      paranoid: false,
    });
    if (!entity) {
      entity = await this.serverCommands.create({
        serverId,
        commandId,
        
        status: newState,
      });
    } {
      entity.status = newState;
      await entity.save();
    }
    
    return entity;
  }
  
  async createCommand(command: CommandType, id?: string, hash?: string) {
    await this.commands.create({
      discordId: id,
      name: command.definition.name,
      description: command.definition.description,
      displayName: command.displayName || `Command: ${command.definition.name}`,
      
      definitionHash: hash || createHash('md5').update(JSON.stringify(deepSortObject(command))).digest('hex'),
    });
  }
  
  async createServerCommand(serverId: string, commandId: string, status: CommonCommandStatus) {
      await this.serverCommands.create({
        serverId,
        commandId,
        
        status,
      });
  }
  
  async isUserBanned(userId: string) { //ban for bot
    return this.users.findOne({
      where: {
        userId,
        isBanned: true,
      },
    });
  }
  
  async getChatHistoryById(id: number) {
    return this.chats.findByPk(id);
  }
  
  async addChatHistory(guildId: string, userId: string, channelId: string, logs: RAGChatRow[]) {
    const chat = await this.getChatHistory(guildId, userId, channelId);
    if (!chat) return this.chats.create({
      serverId: guildId,
      userId,
      channelId,
      chatLog: logs,
      isCurrent: true,
    });
    
    chat.chatLog.push(...logs);
    chat.changed('chatLog', true);
    await chat.save();
    await chat.increment('count', {by: 1});
  }
  async archiveChatHistory(guildId: string, userId: string, channelId: string) {
    const chat = await this.getChatHistory(guildId, userId, channelId);
    if (!chat) return;
      
    chat.isCurrent = null;
    await chat.save();
  }
  async getChatHistory(guildId: string, userId: string, channelId: string) {
    return this.chats.findOne({
      where: {
        serverId: guildId,
        userId,
        channelId,
        isCurrent: true,
      },
    });
  }

  async archiveButtonInteraction(guildId: string, channelId: string, customId: string) {
    const interaction = await this.getButtonInteraction(guildId, channelId, customId);  
    if (!interaction) return;

    await interaction.save();
  }
  
  async getButtonInteraction(guildId: string, channelId: string, customId: string) {
    return this.buttons.findOne({
      where: {
        guildId,
        channelId,
        customId,
      },
    });
  }

  async getBan(userId: string, serverId: string) { //ban for server
    return this.bans.findOne({
      where: {
        userId,
        serverId,
      },
    });
  } 

  async addBan(userId: string, serverId: string, bans: ServerBan[], expiresAt?: Date) {
    const user = await this.getBan(userId, serverId);
    if (!user) {
      return this.bans.create({
        userId,
        serverId,
        bans,
        expiresAt,
        isBanned: true,
      })
    }
    user.bans.push(...bans);
    user.changed('bans', true);
    await user.save();
  }

  async deleteBan(userId: string, serverId: string) {
    return this.bans.destroy({
      where: {
        userId,
        serverId,
      },
    });
  }

  async getKick(userId: string, serverId: string) {
    return this.kicks.findOne({
      where: {
        userId,
        serverId,
      },
    });
  }

  async addKicks(userId: string, serverId: string, kicks: ServerKick[]) {
    const user = await this.getKick(userId, serverId);
    if (!user) {
      return this.kicks.create({
        userId,
        serverId,
        kicks,
      })
    }
    user.kicks.push(...kicks);
    user.changed('kicks', true);
    await user.save();
  }

  async getWarn(userId: string, serverId: string){
    return this.warns.findOne({
      where: {
        userId,
        serverId,
      },
    });
  }

  async getWarns(userId: string, serverId: string) {
    return this.warns.findAll({
      where: {
        userId,
        serverId,
      },
    });
  }

  async deleteWarns(userId: string, serverId: string) {
    return this.warns.destroy({
      where: {
        userId,
        serverId,
      },
    });
  }

  async deleteWarn(userId: string, serverId: string, warnId: UUID) {
    const warn = await this.getWarn(userId, serverId);
    if (!warn) return false;
    
    const orginalCount = warn.warnings.length;
    warn.warnings = warn.warnings.filter(x => x.id !== warnId);
    if (orginalCount === warn.warnings.length) return false;

    warn.changed('warnings', true);
    await warn.save();
    return true;
  }

  async addWarn(userId: string, serverId: string, warns: ServerWarning[], expiresAt?: Date | string) {
    const warn = await this.getWarn(userId, serverId);
    if (!warn) {
      return this.warns.create({
        userId,
        serverId,
        warnings: warns,
        expiresAt,
      });
    }
    warn.warnings.push(...warns);
    warn.changed('warnings', true);
    await warn.save();
  }

  async getLastAcceptedMessage(messageId: string) {
    return this.lastAcceptedMessage.findOne({
      where: {
        messageId,
      },
    });
  }

  async replaceLastAcceptedMessage(userId: string, channelId: string, newMessageId: string) {
    const message = await this.getLastAcceptedMessage(newMessageId);
    if (!message) {
      return this.lastAcceptedMessage.create({
        userId: userId,
        channelId: channelId,
        messageId: newMessageId,
        isAccepted: true,
      });
    }
    message.userId = userId;
    message.channelId = channelId;
    message.isAccepted = true;
    await message.save();
  }

  async getRules(serverId: string){
    return this.rules.findOne({
      where: {
        serverId
      }
    })
  }

  async setRules(serverId: string, channelId: string, message: DiscordRulesMessage[]) {
    const rule = await this.getRules(serverId);
    if (!rule) {
      return this.rules.create({
        serverId: serverId,
        channelId: channelId,
        message: message,
      });
    }
    rule.channelId = channelId;
    rule.message = message;
    await rule.save();
  }

}

