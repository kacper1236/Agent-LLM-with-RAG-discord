export const CommandStatuses = ['enabled', 'disabled', 'only-admins', 'devs'] as const;
export type CommandStatus = typeof CommandStatuses[number];
export type CommonCommandStatus = Exclude<CommandStatus, 'devs'>; 
