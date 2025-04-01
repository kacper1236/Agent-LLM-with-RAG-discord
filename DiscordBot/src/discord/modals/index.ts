import { Collection } from "discord.js";
import { ModalType } from "types/modal.type.js";

import { reportUser } from "./report_user.modals.js";
import { reportProblem } from "./report_problem.modals.js";
import { suggestion } from "./suggestions.modals.js";
import { trusted } from "./trusted.modals.js";
import { artist } from "./artist.modals.js";
import { other } from "./other.modals.js";

const modalCollection = new Collection<string, ModalType>();

modalCollection.set((reportUser.definition.data as any).custom_id, reportUser);
modalCollection.set((reportProblem.definition.data as any).custom_id, reportProblem);
modalCollection.set((suggestion.definition.data as any).custom_id, suggestion);
modalCollection.set((trusted.definition.data as any).custom_id, trusted);
modalCollection.set((artist.definition.data as any).custom_id, artist);
modalCollection.set((other.definition.data as any).custom_id, other);

export { modalCollection as modalInSystem };
