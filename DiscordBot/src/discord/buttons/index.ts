import { Collection } from "discord.js";
import type { ButtonType } from "types/button.type.js";

import { createNewTicketButton } from "./create-new-ticket.button.js";
import { cancelButton } from "./cancel.button.js";

const collection = new Collection<string, ButtonType>();
//błąd w bibliotece, powinno być customId a nie custom_id
//Dlatego też jest as any
if ((createNewTicketButton.definition.data as any).custom_id) {
  collection.set((createNewTicketButton.definition.data as any).custom_id, createNewTicketButton);
}
if ((cancelButton.definition.data as any).custom_id) {
  collection.set((cancelButton.definition.data as any).custom_id, cancelButton);
}

export { collection as buttonsInSystem }
