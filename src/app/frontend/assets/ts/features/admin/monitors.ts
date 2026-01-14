import { API } from "@/shared/lib/api";
import { GroupForCRUD } from "@/shared/types/api";
import { createCrudStore } from "@/shared/utils/createCrudStore";
import { MonitorForm, EnrichedMonitor } from "@/shared/types/monitor";
import { EMPTY_MONITOR_FORM, NO_GROUP } from "@/shared/constants";
import { notyf } from "@/shared/lib/notyf";

export function monitors(adminPath: string) {
  const api = new API(adminPath);
  let _groups: GroupForCRUD[] = [];
  let _types: string[] = [];

  const crud = createCrudStore<EnrichedMonitor, MonitorForm>({
    fetch: async () => {
      _groups = await api.getGroups();
      _types = await api.getMonitorsTypes();
      const monitors = await api.getMonitors();

      return monitors.map((monitor) => {
        const group = _groups.find((g) => g.id === monitor.group_id);

        return {
          ...monitor,
          group_name: group?.name ?? NO_GROUP,
        };
      });
    },

    create: (data) => api.createMonitor(data as MonitorForm),
    update: (id, data) => api.updateMonitor(id, data as MonitorForm),
    delete: (id) => api.deleteMonitor(id),

    emptyForm: EMPTY_MONITOR_FORM,

    itemToForm: (monitor) => ({ ...monitor }),

    getId: (monitor) => monitor.id,

    modalTitles: {
      create: { title: "Create monitor", buttonText: "Create" },
      update: { title: "Update monitor", buttonText: "Update" },
      delete: { title: "Delete monitor", buttonText: "Delete" },
    },

    validate: (form, action) => {
      if (action === "delete") return true;
      if (!form.group_id) form.group_id = null;

      if (!form.name || !form.endpoint || !form.type) return false;

      const invalidJSON = (jsonString: string) => {
        try {
          JSON.parse(jsonString);
        } catch {
          notyf.error(
            `Invalid JSON in ${jsonString === form.headers ? "headers" : "error mapping"}`,
          );
          return true;
        }
        return false;
      };

      if (form.headers && form.type === "HTTP" && invalidJSON(form.headers))
        return false;
      if (form.error_mapping && invalidJSON(form.error_mapping)) return false;

      return Boolean(form.name && form.endpoint && form.type);
    },
  });

  return {
    ...crud,
    get groups() {
      return _groups;
    },
    get types() {
      return _types;
    },
  };
}
