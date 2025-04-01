import { Collection } from 'discord.js';
import type { CommandType } from '../../types/command.type.js';
import { chatCommand } from './chat.command.js';
import { helpCommand } from './help.command.js';
import { pingCommand } from './ping.command.js';
import { pongCommand } from './pong.command.js';
import { queryCommand } from './query.command.js';
import { testCommand } from './test.command.js';
import { tttCommand } from './ttt.command.js';
import { createNewTicketCommand } from './create_new_ticket.command.js';
import { banCommand } from './ban.command.js';
import { kickCommand } from './kick.command.js';
import { warnCommand } from './warn.command.js';
import { warningsCommand } from './warnings.module.js';
import { delwarnCommand } from './delwarn.command.js';
import { unbanCommand } from './unban.command.js';

const collection = new Collection<string, CommandType>();
collection.set(pingCommand.definition.name, pingCommand);
collection.set(pongCommand.definition.name, pongCommand);
collection.set(testCommand.definition.name, testCommand);
collection.set(helpCommand.definition.name, helpCommand);
collection.set(queryCommand.definition.name, queryCommand)
collection.set(chatCommand.definition.name, chatCommand);
collection.set(createNewTicketCommand.definition.name, createNewTicketCommand);
collection.set(banCommand.definition.name, banCommand);
collection.set(kickCommand.definition.name, kickCommand);
collection.set(warnCommand.definition.name, warnCommand);
collection.set(warningsCommand.definition.name, warningsCommand);
collection.set(delwarnCommand.definition.name, delwarnCommand);
collection.set(unbanCommand.definition.name, unbanCommand);
// collection.set(tttCommand.definition.name, tttCommand);

export { collection as commandsInSystem };
