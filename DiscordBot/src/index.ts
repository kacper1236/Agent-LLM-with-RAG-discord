import { DataBase, init } from './db/db.module.js';
import { connect } from './discord/discord.module.js';

await init();
await connect(DataBase);
