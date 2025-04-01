import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';

import type { Dialect } from 'sequelize';
import { Sequelize } from 'sequelize-typescript';
import { ModelCtor } from 'sequelize-typescript/dist/model/model/model.js';
import { Umzug, SequelizeStorage } from 'umzug';
import { MigrationModuleType } from './classes/migration-helper.class.js';
import { DiscordChatsEntity } from './entities/discord-chats.entity.js';
import { DiscordUsersEntity } from './entities/discord-users.entity.js';
import { DiscordCommandsEntity } from './entities/discord-commands.entity.js';
import { DiscordServersCommandsEntity } from './entities/discord-servers-commands.entity.js';
import { DiscordServersEntity } from './entities/discord-servers.entity.js';
import { DiscordDbServiceClass } from './services/discord.db-service.js';
import { DiscordServersWarningEntity } from './entities/discord-servers-warnings.entity.js';
import { DiscordButtonsEntity } from './entities/discord-buttons.entity.js';
import { DiscordServersBanEntity } from './entities/discord-servers-bans.entity.js';
import { DiscordServersKickEntity } from './entities/discord-servers-kicks.entity.js';

const MODELS: ModelCtor[] = [
  DiscordCommandsEntity,
  
  DiscordServersEntity,
  DiscordServersCommandsEntity,
  
  DiscordUsersEntity,
  DiscordServersWarningEntity,
  
  DiscordChatsEntity,

  DiscordButtonsEntity,
  
  DiscordServersBanEntity,
  DiscordServersKickEntity,
  DiscordLastAcceptedMessageEntity,

  DiscordRulesEntity,
];


const sequelize = new Sequelize({
  dialect: process.env.DB_DIALECT as Dialect || 'sqlite',
  
  username: process.env.DB_USERNAME || 'username',
  password: process.env.DB_PASSWORD || 'password',
  
  database: process.env.DB_NAME || 'db_name',
  host: process.env.DB_HOST || 'db.sqlite',
  port: Number.parseInt(process.env.DB_PORT || '0'),
  logging: process.env.DB_LOGGING ? console.log : undefined,
});


sequelize.addModels(MODELS);

export const migrationsLanguageSpecificHelp = {
  '.ts': "TypeScript files can be required by adding `ts-node` as a dependency and calling `require('ts-node/register')` at the program entrypoint before running migrations.",
  '.sql': 'Try writing a resolver which reads file content and executes it as a sql query.',
};


const __filename = fileURLToPath(import.meta.url);

const __dirname = dirname(__filename);
import { createRequire } from "module";
import { DirectoryChannel } from 'discord.js';
import { DiscordLastAcceptedMessageEntity } from './entities/discord-last-accepted-message.entity.js';
import { DiscordRulesEntity } from './entities/discord-rules.entity.js';

const require = createRequire(import.meta.url);

export const init = async () => {
  // auto create new entities (when they do not exist)
  await sequelize.sync();
  
  console.log(join(__dirname, 'migrations'));
  const umzug = new Umzug({
    migrations: {
      glob: ['*.{t,j}s', { cwd: join(__dirname, 'migrations'), ignore: ['*.d.ts'] }],
      resolve: (params) => {
        if (params.path?.endsWith('.mjs') || params.path?.endsWith('.js')) {
          const getModule = () => import(`file:///${params.path?.replace(/\\/g, '/')}`)
          return {
            name: params.name,
            path: params.path,
            up: async upParams => (await getModule()).up(upParams),
            down: async downParams => (await getModule()).down(downParams),
          }
        }
        return {
          name: params.name,
          path: params.path,
          ...(require(params.path as string)),
        }
      }
    },
    context: () => ({sequelize, queryInterface: sequelize.getQueryInterface()}), 
    storage: new SequelizeStorage({ sequelize }),
    logger: console,
  });
  
  // umzug.debug.enabled = true;
  umzug.on('migrating', ev => console.log({ name: ev.name, path: ev.path }));
  
  // run migrations
  await umzug.up();
};

const DiscordDbServiceInstance = new DiscordDbServiceClass(DiscordServersEntity, DiscordCommandsEntity, DiscordServersCommandsEntity);


export { DiscordDbServiceInstance as DiscordDbService };

export const DataBase = {
  discord: DiscordDbServiceInstance,
}
export { sequelize };

export const disconnect = async () => {
  return sequelize.close();
};



