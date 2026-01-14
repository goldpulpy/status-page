import { API } from "@/shared/lib/api";
import { handleApiError } from "@/shared/utils/errorHandler";

export function logout(adminPath: string) {
  const api = new API(adminPath);

  return {
    async logout() {
      try {
        await api.logout();
        window.location.replace(`/${adminPath}/login`);
      } catch (error) {
        handleApiError(error);
      }
    },
  };
}
