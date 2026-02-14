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

type IncidentType = keyof typeof INCIDENT_CONFIG;

interface DateProvider {
  now(): Date;
}

class DefaultDateProvider implements DateProvider {
  now(): Date {
    return new Date();
  }
}

export class StatusProcessor {
  private dateProvider: DateProvider;

  constructor(dateProvider: DateProvider = new DefaultDateProvider()) {
    this.dateProvider = dateProvider;
  }

  buildEnrichedIncidents(
    components: StatusComponent[],
  ): Map<string, EnrichedIncident[]> {
    const enrichedIncidentsByMonitor = new Map<string, EnrichedIncident[]>();

    const monitors = this.flattenMonitors(components);

    for (const monitor of monitors) {
      const enrichedIncidents = monitor.incidents
        .map((incident) => this.buildEnrichedIncident(monitor, incident))
        .filter((incident): incident is EnrichedIncident => incident !== null);

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
    const prioritizedIncidents = this.prioritizeIncidents(incidents, false);
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

  private prioritizeIncidents<T extends BaseIncident>(
    incidents: T[],
    immutable = true,
  ): T[] {
    const arr = immutable ? [...incidents] : incidents;
    return arr.sort(
      (a, b) =>
        INCIDENT_PRIORITY_ORDER.indexOf(a.type) -
        INCIDENT_PRIORITY_ORDER.indexOf(b.type),
    );
  }

  private sortIncidentsByLatest(
    incidents: EnrichedIncident[],
    immutable = true,
  ): EnrichedIncident[] {
    const arr = immutable ? [...incidents] : incidents;

    const OPEN_PRIORITY = 0;
    const CLOSED_PRIORITY = 1;

    return arr.sort((a, b) => {
      const statusDiff =
        (a.status === IncidentStatus.OPEN ? OPEN_PRIORITY : CLOSED_PRIORITY) -
        (b.status === IncidentStatus.OPEN ? OPEN_PRIORITY : CLOSED_PRIORITY);

      if (statusDiff !== 0) return statusDiff;

      return (
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    });
  }

  private buildHistoryForMonitors(monitors: MonitorForStatus[]): Days[] {
    const now = this.dateProvider.now();

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

      const prioritizedIncidents = this.prioritizeIncidents(
        dayIncidents,
        false,
      );

      return {
        index: dayIndex,
        color: prioritizedIncidents[0].color,
        incidents: this.sortIncidentsByLatest(prioritizedIncidents, false),
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
        .filter((i) => this.isIncidentInDateRange(i, dayStart, dayEnd))
        .map((i) =>
          this.enrichIncident(monitor, i, { start: dayStart, end: dayEnd }),
        )
        .filter((e): e is EnrichedIncident => e !== null),
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

  private enrichIncident(
    monitor: MonitorForStatus,
    incident: IncidentForStatus,
    dateRange?: { start: Date; end: Date },
  ): EnrichedIncident | null {
    const incidentStartDate = this.parseDateSafe(incident.created_at);
    if (!incidentStartDate) {
      return null;
    }

    const incidentEndDate = incident.ended_at
      ? this.parseDateSafe(incident.ended_at)
      : null;

    let actualStart = incidentStartDate;
    let actualEnd = incidentEndDate;

    if (dateRange) {
      actualStart =
        incidentStartDate > dateRange.start
          ? incidentStartDate
          : dateRange.start;
      actualEnd =
        incidentEndDate && incidentEndDate < dateRange.end
          ? incidentEndDate
          : dateRange.end;
    }

    const config = this.getIncidentConfig(incident.type);
    if (!config) {
      return null;
    }

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
  ): EnrichedIncident | null {
    return this.enrichIncident(monitor, incident);
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

    return `${monitor.name} is currently affected. Issue started on ${formattedDate} at ${formattedTime}`;
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
    if (!(type in INCIDENT_CONFIG)) return null;
    return INCIDENT_CONFIG[type as IncidentType];
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
