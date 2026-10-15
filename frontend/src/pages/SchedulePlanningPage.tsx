import React, { useMemo, useState } from 'react';
import { apiRequest } from '../services/api';

type ExposureType = 'outdoor_heat' | 'outdoor_storm' | 'height';
type Scenario = 'normal' | 'caution' | 'high_heat' | 'extreme_heat' | 'storm' | 'missing';
type Decision = 'proceed' | 'extra_breaks' | 'reschedule' | 'blocked';

interface AssessmentResult {
  decision: Decision;
  reasons: string[];
  requires_review: boolean;
  cooling_break_minutes: number;
  proposed_window: { start: string; end: string };
  forecast_id: string;
  forecast_issued_at: string;
}

const scenarioLabels: Record<Scenario, string> = {
  normal: 'Normal conditions',
  caution: 'Caution heat',
  high_heat: 'High heat',
  extreme_heat: 'Extreme heat',
  storm: 'Thunderstorm',
  missing: 'Missing weather data',
};

const decisionLabels: Record<Decision, string> = {
  proceed: 'OK to proceed',
  extra_breaks: 'Extra breaks required',
  reschedule: 'Reschedule this task',
  blocked: 'Do not clear this task',
};

function localDateTimeValue(date: Date): string {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function toIso(value: string): string {
  return new Date(value).toISOString();
}

export const SchedulePlanningPage: React.FC = () => {
  const [scenario, setScenario] = useState<Scenario>('normal');
  const [taskName, setTaskName] = useState('Outdoor equipment inspection');
  const [siteId, setSiteId] = useState('VAD-PLANT-01');
  const [exposure, setExposure] = useState<ExposureType>('outdoor_heat');
  const [duration, setDuration] = useState(60);
  const [start, setStart] = useState(() => localDateTimeValue(new Date(Date.now() + 60 * 60_000)));
  const [temperature, setTemperature] = useState(27);
  const [humidity, setHumidity] = useState(55);
  const [apparentTemperature, setApparentTemperature] = useState(29);
  const [windSpeed, setWindSpeed] = useState(3);
  const [precipitation, setPrecipitation] = useState(0);
  const [weatherCode, setWeatherCode] = useState(0);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const proposedEnd = useMemo(() => {
    if (!start) return '';
    return new Date(new Date(start).getTime() + duration * 60_000).toLocaleString();
  }, [start, duration]);

  const applyScenario = (next: Scenario) => {
    setScenario(next);
    setResult(null);
    setError('');
    const values: Record<Scenario, { temp: number; humidity: number; apparent: number; wind: number; rain: number; code: number }> = {
      normal: { temp: 27, humidity: 55, apparent: 29, wind: 3, rain: 0, code: 0 },
      caution: { temp: 32, humidity: 65, apparent: 35, wind: 3, rain: 0, code: 0 },
      high_heat: { temp: 36, humidity: 70, apparent: 40, wind: 3, rain: 0, code: 0 },
      extreme_heat: { temp: 42, humidity: 50, apparent: 45, wind: 2, rain: 0, code: 0 },
      storm: { temp: 28, humidity: 85, apparent: 30, wind: 15, rain: 12, code: 95 },
      missing: { temp: 27, humidity: 55, apparent: 29, wind: 3, rain: 0, code: 0 },
    };
    const selected = values[next];
    setTemperature(selected.temp);
    setHumidity(selected.humidity);
    setApparentTemperature(selected.apparent);
    setWindSpeed(selected.wind);
    setPrecipitation(selected.rain);
    setWeatherCode(selected.code);
  };

  const runAssessment = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    const startAt = new Date(start);
    const endAt = new Date(startAt.getTime() + duration * 60_000);
    const slots = Math.max(1, Math.ceil(duration / 60));
    const missing = scenario === 'missing';
    const hourly = Array.from({ length: slots }, (_, index) => ({
      valid_at: new Date(startAt.getTime() + index * 60 * 60_000).toISOString(),
      temperature_c: missing ? null : temperature,
      relative_humidity_pct: missing ? null : humidity,
      apparent_temperature_c: missing ? null : apparentTemperature,
      dew_point_c: null,
      wet_bulb_temperature_c: null,
      precipitation_mm: missing ? null : precipitation,
      precipitation_probability_pct: null,
      weather_code: missing ? null : weatherCode,
      wind_speed_ms: missing ? null : windSpeed,
      wind_gusts_ms: null,
      shortwave_radiation_wm2: null,
    }));

    const payload = {
      work_order: {
        work_order_id: 'DEMO-WO-001',
        title: taskName,
        duration_minutes: duration,
        priority: 'medium',
        site_id: siteId,
        required_skills: ['general_maintenance'],
        required_certifications: [],
        min_crew_size: 1,
        max_crew_size: 1,
        depends_on: [],
        required_equipment_ids: [],
        planning_window: { start: toIso(start), end: toIso(endAt.toISOString()) },
        deadline: null,
        exposure_type: exposure,
        expected_exposure_duration_minutes: duration,
        is_weather_exposed: true,
      },
      policy: {
        policy_id: 'demo-climate-policy',
        name: 'Demo climate policy',
        version: '1.0',
        applies_to_exposure_types: [exposure],
        heat_thresholds: [{ metric: 'temperature_c', caution_c: 30, high_c: 35, prohibitive_c: 40 }],
        work_rest_rules: [{
          metric: 'temperature_c',
          min_c: 30,
          max_c: 35,
          work_minutes: 45,
          rest_minutes: 15,
          cooling_required: true,
          severity: 'warning',
          required_action: 'extra_breaks',
        }],
        rules: [],
        operational_constraints: [],
        max_wind_speed_ms: 12.5,
        max_precipitation_mm: 8,
        lightning_prohibits_work: true,
        prohibited_weather_codes: [95, 96, 99],
        missing_weather_action: 'require_review',
      },
      forecast: {
        forecast_id: `ui-demo-${scenario}`,
        site_id: siteId,
        issued_at: new Date().toISOString(),
        source: 'interactive-ui-demo',
        valid_from: startAt.toISOString(),
        valid_until: endAt.toISOString(),
        hourly,
        daily: [],
        quality: {
          is_complete: !missing,
          is_stale: false,
          covers_requested_window: true,
          missing_variables: missing ? ['temperature_2m', 'relative_humidity_2m'] : [],
          incomplete_hour_count: missing ? slots : 0,
          past_hour_count: 0,
          notes: missing ? ['Simulated missing forecast values'] : [],
        },
      },
      proposed_start: toIso(start),
    };

    const response = await apiRequest<AssessmentResult>('/api/safety/assessments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setLoading(false);
    if (response.error || !response.data) {
      setError(response.error ?? 'The backend did not return an assessment.');
      return;
    }
    setResult(response.data);
  };

  const resultTone = result?.decision === 'proceed'
    ? 'safe'
    : result?.decision === 'extra_breaks'
      ? 'caution'
      : 'risk';

  return (
    <div id="safety-page">
      <div className="safety-page-heading">
        <div>
          <div className="eyebrow">Interactive policy check</div>
          <h1>Safety Check</h1>
          <p>Try a task against a clear climate scenario and see the policy result in plain language.</p>
        </div>
        <span className="demo-tag">DEMO POLICY · NOT SITE APPROVAL</span>
      </div>

      <div className="safety-layout">
        <form className="card safety-form" onSubmit={runAssessment}>
          <div className="card-header">
            <h2 className="card-title"><span>🧪</span> Set up a check</h2>
            <span className="step-label">1 · TASK & CONDITIONS</span>
          </div>

          <label className="safety-field">
            <span>Scenario</span>
            <select value={scenario} onChange={(event) => applyScenario(event.target.value as Scenario)}>
              {Object.entries(scenarioLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
            <small>Presets fill in sample weather values. You can adjust them below.</small>
          </label>

          <div className="safety-field-grid">
            <label className="safety-field">
              <span>Task name</span>
              <input value={taskName} onChange={(event) => setTaskName(event.target.value)} required />
            </label>
            <label className="safety-field">
              <span>Site ID</span>
              <input value={siteId} onChange={(event) => setSiteId(event.target.value)} required />
            </label>
            <label className="safety-field">
              <span>Work type</span>
              <select value={exposure} onChange={(event) => setExposure(event.target.value as ExposureType)}>
                <option value="outdoor_heat">Outdoor heat exposure</option>
                <option value="outdoor_storm">Outdoor storm exposure</option>
                <option value="height">Working at height</option>
              </select>
            </label>
            <label className="safety-field">
              <span>Task duration</span>
              <select value={duration} onChange={(event) => setDuration(Number(event.target.value))}>
                <option value={60}>1 hour</option>
                <option value={120}>2 hours</option>
                <option value={180}>3 hours</option>
              </select>
            </label>
            <label className="safety-field">
              <span>Proposed start</span>
              <input type="datetime-local" value={start} onChange={(event) => setStart(event.target.value)} required />
            </label>
            <div className="safety-field safety-window-preview">
              <span>Proposed end</span>
              <strong>{proposedEnd || 'Choose a start time'}</strong>
            </div>
          </div>

          <div className="safety-weather-heading">
            <div>
              <h3>Sample weather</h3>
              <p>These values are sent to the backend policy engine as a demo forecast.</p>
            </div>
            <span className="sample-label">SIMULATED INPUT</span>
          </div>
          <div className="safety-field-grid weather-grid">
            <label className="safety-field">
              <span>Air temperature (°C)</span>
              <input type="number" value={temperature} onChange={(event) => setTemperature(Number(event.target.value))} />
            </label>
            <label className="safety-field">
              <span>Feels-like temperature (°C)</span>
              <input type="number" value={apparentTemperature} onChange={(event) => setApparentTemperature(Number(event.target.value))} />
            </label>
            <label className="safety-field">
              <span>Humidity (%)</span>
              <input type="number" min="0" max="100" value={humidity} onChange={(event) => setHumidity(Number(event.target.value))} />
            </label>
            <label className="safety-field">
              <span>Wind speed (m/s)</span>
              <input type="number" min="0" step="0.5" value={windSpeed} onChange={(event) => setWindSpeed(Number(event.target.value))} />
            </label>
            <label className="safety-field">
              <span>Precipitation (mm/hour)</span>
              <input type="number" min="0" step="0.5" value={precipitation} onChange={(event) => setPrecipitation(Number(event.target.value))} />
            </label>
            <label className="safety-field">
              <span>Weather condition</span>
              <select value={weatherCode} onChange={(event) => setWeatherCode(Number(event.target.value))}>
                <option value={0}>Clear</option>
                <option value={61}>Rain</option>
                <option value={95}>Thunderstorm</option>
              </select>
            </label>
          </div>

          <div className="safety-form-footer">
            <p>Demo thresholds: caution at 30°C, reschedule at 35°C, block at 40°C.</p>
            <button className="btn btn-primary" type="submit" disabled={loading || !start || !taskName || !siteId}>
              {loading ? 'Checking…' : 'Check safety'} <span aria-hidden="true">→</span>
            </button>
          </div>
          {error && <div className="safety-error" role="alert"><strong>Couldn’t run the check</strong><span>{error}. Make sure the backend is running.</span></div>}
        </form>

        <aside className="safety-side-column">
          {result ? (
            <section className={`card safety-result ${resultTone}`} aria-live="polite">
              <div className="card-header">
                <h2 className="card-title"><span>📋</span> Assessment result</h2>
                <span className={`result-indicator ${resultTone}`} />
              </div>
              <div className="result-decision">{decisionLabels[result.decision]}</div>
              <div className="result-task">{taskName} · {siteId}</div>
              {result.requires_review && <div className="review-callout">Manager review required before this task can be cleared.</div>}
              {result.cooling_break_minutes > 0 && (
                <div className="break-callout"><strong>{result.cooling_break_minutes} minutes</strong> of cooling/rest time required for this task.</div>
              )}
              <h3>Why this result?</h3>
              <ul className="reason-list">{result.reasons.map((reason, index) => <li key={`${reason}-${index}`}>{reason}</li>)}</ul>
              <div className="assessment-meta">
                <span>Checked window</span>
                <strong>{new Date(result.proposed_window.start).toLocaleString()} – {new Date(result.proposed_window.end).toLocaleTimeString()}</strong>
                <span>Forecast source</span>
                <strong>{result.forecast_id} · issued {new Date(result.forecast_issued_at).toLocaleTimeString()}</strong>
              </div>
            </section>
          ) : (
            <section className="card safety-empty">
              <div className="empty-icon">✓</div>
              <div className="eyebrow">Your result appears here</div>
              <h2>Ready when you are</h2>
              <p>Choose a preset or adjust the sample weather, then run the check to see the policy engine’s decision and explanation.</p>
            </section>
          )}

          <section className="card scenario-guide">
            <div className="eyebrow">Suggested walkthrough</div>
            <h3>Try these in order</h3>
            <ol>
              <li><span>01</span> Normal conditions <b>→</b> OK to proceed</li>
              <li><span>02</span> Caution heat <b>→</b> Extra breaks</li>
              <li><span>03</span> High heat <b>→</b> Reschedule</li>
              <li><span>04</span> Thunderstorm <b>→</b> Blocked</li>
              <li><span>05</span> Missing weather <b>→</b> Review required</li>
            </ol>
            <p className="demo-note">This is a demo policy and simulated data. It does not represent a site-approved policy or safety clearance.</p>
          </section>
        </aside>
      </div>
    </div>
  );
};
