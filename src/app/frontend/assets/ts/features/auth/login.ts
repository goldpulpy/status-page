import { API } from "@/shared/lib/api";
import { handleApiError } from "@/shared/utils/errorHandler";

export function login(adminPath: string) {
  const api = new API(adminPath);

  return {
    username: null as string | null,
    password: null as string | null,
    isLoading: false,

    async submitForm() {
      this.isLoading = true;

      try {
        if (!this.username || !this.password) return;

        await api.login(this.username, this.password);
        window.location.replace(`/${adminPath}`);
      } catch (error) {
        handleApiError(error);
      } finally {
        this.isLoading = false;
      }
    },
  };
}
