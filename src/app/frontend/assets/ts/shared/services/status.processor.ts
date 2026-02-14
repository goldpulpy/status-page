import { parseISO, startOfDay, endOfDay, subDays, isBefore } from "date-fns";
import type {
  IncidentForStatus,
  MonitorForStatus,
  StatusComponent,
} from "@/shared/types/api";
import type {
  Days,
  EnrichedIncident,
  EnrichedStatusComponent,
} from "@/shared/types/status";
import {
  INCIDENT_CONFIG,
  INCIDENT_PRIORITY_ORDER,
  OPERATIONAL_STATUS,
} from "@/shared/constants";
import { isGroup } from "@/shared/utils/status.utils";
import { BaseIncident, IncidentStatus } from "@/shared/types/incident";

const HISTORY_DAYS = 30;
const HISTORY_OFFSET = HISTORY_DAYS - 1;
const LOCALE = "en-US" as const;

const DATE_FORMAT_OPTIONS = {
  date: { month: "long", day: "numeric" } as const,
  time: { hour: "2-digit", minute: "2-digit" } as const,
} as const;

export class StatusProcessor {
  buildEnrichedIncidents(
    components: StatusComponent[],
  ): Map<string, EnrichedIncident[]> {
    const enrichedIncidentsByMonitor = new Map<string, EnrichedIncident[]>();

    const monitors = this.flattenMonitors(components);

    for (const monitor of monitors) {
      const enrichedIncidents = monitor.incidents.map((incident) =>
        this.buildEnrichedIncident(monitor, incident),
      );
      enrichedIncidentsByMonitor.set(monitor.id, enrichedIncidents);
    }

    return enrichedIncidentsByMonitor;
  }

  buildEnrichedStatusComponent(
    components: StatusComponent[],
    enrichedIncidentsByMonitor: Map<string, EnrichedIncident[]>,
  ): EnrichedStatusComponent[] {
    return components.map((component) => {
      if (isGroup(component)) {
        return this.enrichGroupComponent(component, enrichedIncidentsByMonitor);
      }
      return this.enrichMonitorComponent(component, enrichedIncidentsByMonitor);
    });
  }

  findActiveIncident<T extends BaseIncident>(
    incidents: T[],
  ): T | typeof OPERATIONAL_STATUS {
    const prioritizedIncidents = this.prioritizeIncidents(incidents);
    const activeIncident = prioritizedIncidents.find(
      (incident) => incident.status === IncidentStatus.OPEN,
    );

    return activeIncident ?? OPERATIONAL_STATUS;
  }

  private flattenMonitors(components: StatusComponent[]): MonitorForStatus[] {
    return components.flatMap((component) =>
      isGroup(component) ? component.monitors : [component],
    );
  }

  private enrichGroupComponent(
    component: StatusComponent & { monitors: MonitorForStatus[] },
    enrichedIncidentsByMonitor: Map<string, EnrichedIncident[]>,
  ): EnrichedStatusComponent {
    return {
      ...component,
      monitors: component.monitors.map((monitor) => ({
        ...monitor,
        currentIncident: this.findActiveIncident(
          enrichedIncidentsByMonitor.get(monitor.id) ?? [],
        ),
        history: this.buildHistoryForMonitors([monitor]),
      })),
    };
  }

  private enrichMonitorComponent(
    component: MonitorForStatus,
    enrichedIncidentsByMonitor: Map<string, EnrichedIncident[]>,
  ): EnrichedStatusComponent {
    return {
      ...component,
      currentIncident: this.findActiveIncident(
        enrichedIncidentsByMonitor.get(component.id) ?? [],
      ),
      history: this.buildHistoryForMonitors([component]),
    };
  }

  private prioritizeIncidents<T extends BaseIncident>(incidents: T[]): T[] {
    return [...incidents].sort(
      (a, b) =>
        INCIDENT_PRIORITY_ORDER.indexOf(a.type) -
        INCIDENT_PRIORITY_ORDER.indexOf(b.type),
    );
  }

  private sortIncidentsByDate(
    incidents: EnrichedIncident[],
  ): EnrichedIncident[] {
    return [...incidents].sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
  }

  private buildHistoryForMonitors(monitors: MonitorForStatus[]): Days[] {
    const now = new Date();

    return Array.from({ length: HISTORY_DAYS }, (_, dayIndex) => {
      const day = subDays(now, HISTORY_OFFSET - dayIndex);
      const dayStart = startOfDay(day);
      const dayEnd = endOfDay(day);

      const hasActiveMonitor = this.hasActiveMonitorOnDay(monitors, dayEnd);

      if (!hasActiveMonitor) {
        return { color: "bg-empty", index: dayIndex };
      }

      const dayIncidents = this.filterIncidentsByDateRange(
        monitors,
        dayStart,
        dayEnd,
      );

      if (dayIncidents.length === 0) {
        return {
          color: "bg-operational",
          index: dayIndex,
          incidents: [],
        };
      }

      const prioritizedIncidents = this.prioritizeIncidents(dayIncidents);

      return {
        index: dayIndex,
        color: prioritizedIncidents[0].color,
        incidents: this.sortIncidentsByDate(prioritizedIncidents),
      };
    });
  }

  private hasActiveMonitorOnDay(
    monitors: MonitorForStatus[],
    dayEnd: Date,
  ): boolean {
    return monitors.some((monitor) => {
      const componentCreated = this.parseDateSafe(monitor.created_at);
      return componentCreated && !isBefore(dayEnd, componentCreated);
    });
  }

  private filterIncidentsByDateRange(
    monitors: MonitorForStatus[],
    dayStart: Date,
    dayEnd: Date,
  ): EnrichedIncident[] {
    return monitors.flatMap((monitor) =>
      monitor.incidents
        .filter((incident) =>
          this.isIncidentInDateRange(incident, dayStart, dayEnd),
        )
        .map((incident) =>
          this.buildDaySpecificIncident(monitor, incident, dayStart, dayEnd),
        ),
    );
  }

  private isIncidentInDateRange(
    incident: IncidentForStatus,
    dayStart: Date,
    dayEnd: Date,
  ): boolean {
    const incidentStartDate = this.parseDateSafe(incident.created_at);
    if (!incidentStartDate) return false;

    const incidentEndDate = incident.ended_at
      ? this.parseDateSafe(incident.ended_at)
      : null;

    const startedBeforeOrDuringDay = incidentStartDate <= dayEnd;
    const endedAfterDay = !incidentEndDate || incidentEndDate >= dayStart;

    return startedBeforeOrDuringDay && endedAfterDay;
  }

  private buildDaySpecificIncident(
    monitor: MonitorForStatus,
    incident: IncidentForStatus,
    dayStart: Date,
    dayEnd: Date,
  ): EnrichedIncident {
    const incidentStartDate = this.parseDateSafe(incident.created_at)!;
    const incidentEndDate = incident.ended_at
      ? this.parseDateSafe(incident.ended_at)
      : null;

    const actualStart =
      incidentStartDate > dayStart ? incidentStartDate : dayStart;
    const actualEnd =
      incidentEndDate && incidentEndDate < dayEnd ? incidentEndDate : dayEnd;

    const config = this.getIncidentConfig(incident.type);
    const message = this.buildIncidentMessage(monitor, incidentStartDate);

    const tooltip = this.buildTooltip(
      incident.message,
      actualStart,
      actualEnd,
      incident.ended_at !== null,
    );

    return {
      ...incident,
      ...config,
      message,
      tooltip,
    };
  }

  private buildEnrichedIncident(
    monitor: MonitorForStatus,
    incident: IncidentForStatus,
  ): EnrichedIncident {
    const startedDateTime = this.parseDateSafe(incident.created_at);
    if (!startedDateTime) {
      throw new Error(`Invalid created_at date for incident: ${incident.id}`);
    }

    const config = this.getIncidentConfig(incident.type);
    const message = this.buildIncidentMessage(monitor, startedDateTime);

    const endedDateTime = incident.ended_at
      ? this.parseDateSafe(incident.ended_at)
      : null;

    const tooltip = this.buildTooltip(
      incident.message,
      startedDateTime,
      endedDateTime,
      incident.ended_at !== null,
    );

    return {
      ...incident,
      ...config,
      message,
      tooltip,
    };
  }

  private buildIncidentMessage(
    monitor: MonitorForStatus,
    startedDateTime: Date,
  ): string {
    const formattedDate = startedDateTime.toLocaleDateString(
      LOCALE,
      DATE_FORMAT_OPTIONS.date,
    );
    const formattedTime = startedDateTime.toLocaleTimeString(
      LOCALE,
      DATE_FORMAT_OPTIONS.time,
    );

    const message = `${monitor.name} is currently affected. Issue started on ${formattedDate} at ${formattedTime}`;

    return message;
  }

  private buildTooltip(
    incidentMessage: string,
    startTime: Date,
    endTime: Date | null,
    isEnded: boolean,
  ): string {
    const startFormatted = startTime.toLocaleTimeString(
      LOCALE,
      DATE_FORMAT_OPTIONS.time,
    );

    if (!isEnded) {
      return `${incidentMessage} (started at ${startFormatted})`;
    }

    const endFormatted = endTime
      ? endTime.toLocaleTimeString(LOCALE, DATE_FORMAT_OPTIONS.time)
      : startFormatted;

    return `${incidentMessage} (${startFormatted} - ${endFormatted})`;
  }

  private getIncidentConfig(type: string) {
    const config = INCIDENT_CONFIG[type as keyof typeof INCIDENT_CONFIG];
    if (!config) {
      throw new Error(`Unknown incident type: ${type}`);
    }
    return config;
  }

  private parseDateSafe(dateString: string): Date | null {
    try {
      const date = parseISO(dateString);
      return isNaN(date.getTime()) ? null : date;
    } catch {
      return null;
    }
  }
}
