import { handleApiError } from "@/shared/utils/errorHandler";
import { createModalState, resetModal } from "@/shared/types/modal";

export type CrudAction = "create" | "update" | "delete";

export function createCrudStore<TItem, TForm>(config: {
  fetch: () => Promise<TItem[]>;
  create: (data: TForm) => Promise<unknown>;
  update: (id: string, data: TForm) => Promise<unknown>;
  delete: (id: string) => Promise<void>;
  validate?: (data: TForm, action: CrudAction) => boolean;
  modalTitles: Record<CrudAction, { title: string; buttonText: string }>;
  emptyForm: TForm;
  itemToForm: (item: TItem) => TForm;
  getId: (item: TItem) => string;
}) {
  const state = {
    items: [] as TItem[],
    selectedId: null as string | null,
    form: { ...config.emptyForm } as TForm,
    action: null as CrudAction | null,
    modal: createModalState(),
  };

  return {
    state,

    async fetch() {
      this.state.items = await config.fetch();
    },

    openModal(action: CrudAction, item?: TItem) {
      const modalConfig = config.modalTitles[action];

      this.state.action = action;
      this.state.modal.title = modalConfig.title;
      this.state.modal.buttonText = modalConfig.buttonText;
      this.state.modal.isOpen = true;

      if (item) {
        this.state.selectedId = config.getId(item);
        this.state.form = config.itemToForm(item);
      }
    },

    cancel() {
      this.state.selectedId = null;
      this.state.form = { ...config.emptyForm };
      this.state.action = null;
      resetModal(this.state.modal);
    },

    async submit() {
      const action = this.state.action;
      if (!action) return;

      if (config.validate && !config.validate(this.state.form, action)) {
        return;
      }

      try {
        switch (action) {
          case "create":
            if (!this.state.form) throw new Error("No form");
            await config.create(this.state.form);
            break;

          case "update":
            if (!this.state.selectedId) throw new Error("No selectedId");
            await config.update(this.state.selectedId, this.state.form);
            break;

          case "delete":
            if (!this.state.selectedId) throw new Error("No selectedId");
            await config.delete(this.state.selectedId);
            break;

          default:
            throw new Error("Invalid action");
        }

        await this.fetch();
        this.cancel();
      } catch (error) {
        handleApiError(error);
      }
    },
  };
}
