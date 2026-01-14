import { API } from "@/shared/lib/api";
import type {
  Days,
  EnrichedIncident,
  EnrichedStatusComponent,
  Tooltip,
} from "../shared/types/status";
import { OPERATIONAL_STATUS, REFRESH_INTERVAL_MS } from "@/shared/constants";
import { StatusProcessor } from "@/shared/services/status.processor";
import { notyf } from "@/shared/lib/notyf";

export class StatusService {
  private readonly api: API;
  private readonly statusProcessor: StatusProcessor;
  private started = false;
  private abortController: AbortController | null = null;

  public tooltip: Tooltip = {
    isActive: false,
    style: "",
  };
  public components: EnrichedStatusComponent[] = [];
  public incidents: EnrichedIncident[] = [];
  public currentIncident: EnrichedIncident | typeof OPERATIONAL_STATUS | null =
    null;

  constructor(api?: API) {
    this.api = api ?? new API();
    this.statusProcessor = new StatusProcessor();
  }

  public async refresh(): Promise<void> {
    const components = await this.api.getStatus();
    const incidentsMap =
      this.statusProcessor.buildEnrichedIncidents(components);
    this.incidents = Array.from(incidentsMap.values()).flat();
    this.currentIncident = this.statusProcessor.findActiveIncident(
      this.incidents,
    );
    this.components = this.statusProcessor.buildEnrichedStatusComponent(
      components,
      incidentsMap,
    );
  }

  public async start(): Promise<void> {
    if (this.started) {
      throw new Error("StatusService is already running");
    }

    this.started = true;
    this.abortController = new AbortController();

    try {
      await this.runRefreshLoop();
    } finally {
      this.started = false;
      this.abortController = null;
    }
  }
  public setTooltip(day?: Days, event?: MouseEvent): void {
    if (!day || !event) {
      this.tooltip = {
        isActive: false,
        style: "",
        incidents: undefined,
      };
      return;
    }

    const x = event.clientX;
    const y = event.clientY + 15;

    let style = "";

    if (x > window.innerWidth / 2) {
      style = `top: ${y}px; right: ${window.innerWidth - x}px;`;
    } else {
      style = `top: ${y}px; left: ${x}px;`;
    }

    this.tooltip = {
      isActive: true,
      incidents: day?.incidents,
      style: style,
    };
  }
  public stop(): void {
    this.abortController?.abort();
  }
  public handleHistoryHover(event: MouseEvent, history: Days[]): void {
    try {
      const target = event.target as HTMLElement;
      const index = target.dataset.index;

      if (!index) {
        this.setTooltip();
        return;
      }

      const day = history[parseInt(index)];
      this.setTooltip(day, event);
    } catch {
      notyf.error("Something went wrong");
    }
  }

  private async runRefreshLoop(): Promise<void> {
    while (!this.abortController?.signal.aborted) {
      try {
        await this.refresh();
      } catch {
        notyf.error("Something went wrong");
      }
      await this.sleepInterruptible(REFRESH_INTERVAL_MS);
    }
  }

  private async sleepInterruptible(ms: number): Promise<void> {
    return new Promise((resolve) => {
      const timeout = setTimeout(resolve, ms);
      this.abortController?.signal.addEventListener("abort", () => {
        clearTimeout(timeout);
        resolve();
      });
    });
  }
}

let statusInstance: StatusService | null = null;

export function status(): StatusService {
  if (!statusInstance) {
    statusInstance = new StatusService();
  }
  return statusInstance;
}
