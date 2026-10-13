/**
 * TypeScript data models mirroring Python Pydantic schemas in src/workforce_agent/schemas/
 */

export type Priority = 'critical' | 'high' | 'medium' | 'low';

export type ExposureType =
  | 'outdoor_heat'
  | 'outdoor_storm'
  | 'height'
  | 'confined_space'
  | 'electrical'
  | 'indoor_controlled';

export type SiteHazard =
  | 'extreme_heat'
  | 'monsoon'
  | 'high_wind'
  | 'lightning'
  | 'height'
  | 'confined_space'
  | 'electrical'
  | 'chemical';

export type OperationalStatus = 'available' | 'in_use' | 'maintenance' | 'out_of_service';

export type HeatMetric = 'wet_bulb' | 'heat_index' | 'dry_bulb';

export type RuleAction = 'mandatory_break' | 'shorten_shift' | 'halt_work' | 'reschedule';

export type ScheduleDecision = 'scheduled' | 'delayed' | 'rescheduled' | 'cancelled';

export interface TimeWindow {
  start: string; // ISO 8601 with timezone
  end: string;
}

export interface OperatingHours {
  weekday: number; // 0 = Monday, 6 = Sunday
  start_local: string; // "HH:MM:SS"
  end_local: string;
}

export interface Certification {
  name: string;
  expires_at?: string | null;
}

export interface BreakRequirements {
  min_break_duration_minutes: number;
  max_continuous_work_minutes: number;
}

export interface Worker {
  worker_id: string;
  name: string;
  skills: string[];
  certifications: Certification[];
  availability_windows: TimeWindow[];
  break_requirements: BreakRequirements;
  max_shift_duration_minutes: number;
}

export interface Site {
  site_id: string;
  name: string;
  latitude: number;
  longitude: number;
  timezone: string;
  operating_hours: OperatingHours[];
  hazards: SiteHazard[];
}

export interface LocationCatalog {
  location_id: string;
  display_name: string;
  country: string;
  sites: Site[];
}

export interface WorkOrder {
  work_order_id: string;
  title: string;
  duration_minutes: number;
  priority: Priority;
  site_id: string;
  required_skills: string[];
  required_certifications: string[];
  min_crew_size: number;
  max_crew_size: number;
  depends_on?: string[];
  required_equipment_ids?: string[];
  planning_window: TimeWindow;
  deadline?: string | null;
  exposure_type: ExposureType;
  expected_exposure_duration_minutes: number;
  is_weather_exposed?: boolean;
}

export interface HourlyWeather {
  time: string; // ISO timestamp
  temperature_c: number | null;
  wet_bulb_temperature_c: number | null;
  heat_index_c: number | null;
  precipitation_mm: number | null;
  wind_speed_kmh: number | null;
  direct_normal_irradiance_wm2: number | null;
}

export interface DailyWeather {
  date: string; // YYYY-MM-DD
  max_temperature_c: number | null;
  min_temperature_c: number | null;
  max_wet_bulb_c: number | null;
  precipitation_hours: number | null;
}

export interface WeatherDataQuality {
  completeness_ratio: number;
  has_missing_intervals: boolean;
  is_stale: boolean;
  stale_threshold_hours: number;
}

export interface WeatherForecast {
  location_id: string;
  site_id: string;
  generated_at: string;
  latitude: number;
  longitude: number;
  timezone: string;
  hourly: HourlyWeather[];
  daily: DailyWeather[];
  data_quality?: WeatherDataQuality;
}

export interface CoolingBreak {
  start: string;
  duration_minutes: number;
  reason: string;
}

export interface ScheduleAssignment {
  assignment_id: string;
  work_order_id: string;
  worker_id: string;
  site_id: string;
  scheduled_start: string;
  scheduled_end: string;
  cooling_breaks?: CoolingBreak[];
  heat_risk_level?: 'low' | 'moderate' | 'high' | 'extreme';
}

export interface ScheduleProposal {
  proposal_id: string;
  site_id: string;
  generated_at: string;
  assignments: ScheduleAssignment[];
  unscheduled_work_order_ids: string[];
  notes?: string[];
}
