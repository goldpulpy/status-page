import { GroupForCRUD } from "@/shared/types/api";
import { API } from "@/shared/lib/api";
import { createCrudStore } from "@/shared/utils/createCrudStore";

export function groups(adminPath: string) {
  const api = new API(adminPath);

  const crud = createCrudStore<GroupForCRUD, { name: string | null }>({
    fetch: () => api.getGroups(),
    create: (data) => api.createGroup(data.name!),
    update: (id, data) => api.updateGroup(id, data.name!),
    delete: (id) => api.deleteGroup(id),

    emptyForm: {
      name: null,
    },

    itemToForm: (group) => ({ name: group.name }),

    getId: (group) => group.id,

    modalTitles: {
      create: { title: "Create group", buttonText: "Create" },
      update: { title: "Update group", buttonText: "Update" },
      delete: { title: "Delete group", buttonText: "Delete" },
    },

    validate: (form, action) => {
      if (action === "delete") return true;
      return Boolean(form.name);
    },
  });

  return {
    ...crud,
  };
}
