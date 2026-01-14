import type {
  GroupForCRUD,
  MonitorForCRUD,
  StatusComponent,
} from "@/shared/types/api";
import type { MonitorForm } from "@/shared/types/monitor";

export class APIError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "APIError";
  }
}

export class API {
  constructor(
    private adminPath: string | null = null,
    private baseUrl: string = "/api/v1",
  ) {}
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        credentials: "include",
      });

      if (response.status === 204) {
        return undefined as T;
      }

      const text = await response.text();

      if (!response.ok) {
        const errorData = text ? JSON.parse(text) : {};
        if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
          throw new APIError(response.status, errorData.detail[0].msg);
        } else if (errorData.detail) {
          throw new APIError(response.status, errorData.detail);
        } else {
          throw new APIError(response.status, `HTTP ${response.status}`);
        }
      }

      return text ? JSON.parse(text) : (undefined as T);
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new Error("Network error");
    }
  }

  private serializeMonitor(monitor: MonitorForm) {
    return {
      ...monitor,
      headers: monitor.headers ? JSON.parse(monitor.headers) : null,
      error_mapping: monitor.error_mapping
        ? JSON.parse(monitor.error_mapping)
        : null,
    };
  }

  private deserializeMonitor(monitor: MonitorForCRUD): MonitorForCRUD {
    return {
      ...monitor,
      headers: monitor.headers ? JSON.stringify(monitor.headers) : null,
      error_mapping: monitor.error_mapping
        ? JSON.stringify(monitor.error_mapping)
        : null,
    };
  }

  async getStatus(): Promise<StatusComponent[]> {
    return this.request<{ components: StatusComponent[] }>("/status", {
      method: "GET",
    }).then((response) => response.components);
  }

  async login(username: string, password: string): Promise<void> {
    return this.request(`/${this.adminPath}/login`, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  }

  async logout(): Promise<void> {
    return this.request(`/${this.adminPath}/logout`, {
      method: "POST",
    });
  }

  async getGroups(): Promise<GroupForCRUD[]> {
    return this.request<{ groups: GroupForCRUD[] }>(
      `/${this.adminPath}/groups`,
    ).then((response) => response.groups);
  }

  async createGroup(name: string): Promise<GroupForCRUD> {
    return this.request<GroupForCRUD>(`/${this.adminPath}/groups`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  }

  async updateGroup(id: string, name: string): Promise<GroupForCRUD> {
    return this.request<GroupForCRUD>(`/${this.adminPath}/groups/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name }),
    });
  }

  async deleteGroup(id: string): Promise<void> {
    return this.request<void>(`/${this.adminPath}/groups/${id}`, {
      method: "DELETE",
    });
  }

  async getMonitors(): Promise<MonitorForCRUD[]> {
    const { monitors } = await this.request<{ monitors: MonitorForCRUD[] }>(
      `/${this.adminPath}/monitors`,
    );

    return monitors.map((m) => this.deserializeMonitor(m));
  }

  async getMonitorsTypes(): Promise<string[]> {
    return this.request<{ types: string[] }>(
      `/${this.adminPath}/monitors/types`,
    ).then((response) => response.types);
  }

  async createMonitor(monitor: MonitorForm): Promise<MonitorForCRUD> {
    return this.request<MonitorForCRUD>(`/${this.adminPath}/monitors`, {
      method: "POST",
      body: JSON.stringify(this.serializeMonitor(monitor)),
    });
  }

  async updateMonitor(
    id: string,
    monitor: MonitorForm,
  ): Promise<MonitorForCRUD> {
    return this.request<MonitorForCRUD>(`/${this.adminPath}/monitors/${id}`, {
      method: "PUT",
      body: JSON.stringify(this.serializeMonitor(monitor)),
    });
  }

  async deleteMonitor(id: string): Promise<void> {
    return this.request<void>(`/${this.adminPath}/monitors/${id}`, {
      method: "DELETE",
    });
  }
}
