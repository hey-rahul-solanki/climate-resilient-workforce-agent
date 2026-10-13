import type { LocationCatalog } from '../types';

/**
 * Default location catalog matching src/workforce_agent/locations/vadodara.json
 * Allows the frontend to render rich, realistic operations data in standalone mode.
 */
export const defaultVadodaraCatalog: LocationCatalog = {
  location_id: 'vadodara-gujarat',
  display_name: 'Vadodara, Gujarat',
  country: 'IN',
  sites: [
    {
      site_id: 'VAD-PLANT-01',
      name: 'Vadodara Process Plant',
      latitude: 22.3072,
      longitude: 73.1812,
      timezone: 'Asia/Kolkata',
      operating_hours: [
        { weekday: 0, start_local: '06:00:00', end_local: '18:00:00' },
        { weekday: 1, start_local: '06:00:00', end_local: '18:00:00' },
        { weekday: 2, start_local: '06:00:00', end_local: '18:00:00' },
        { weekday: 3, start_local: '06:00:00', end_local: '18:00:00' },
        { weekday: 4, start_local: '06:00:00', end_local: '18:00:00' },
        { weekday: 5, start_local: '06:00:00', end_local: '14:00:00' },
      ],
      hazards: ['extreme_heat', 'monsoon', 'chemical', 'height'],
    },
    {
      site_id: 'VAD-SUB-02',
      name: 'Vadodara North Substation',
      latitude: 22.3511,
      longitude: 73.189,
      timezone: 'Asia/Kolkata',
      operating_hours: [
        { weekday: 0, start_local: '07:00:00', end_local: '19:00:00' },
        { weekday: 1, start_local: '07:00:00', end_local: '19:00:00' },
        { weekday: 2, start_local: '07:00:00', end_local: '19:00:00' },
        { weekday: 3, start_local: '07:00:00', end_local: '19:00:00' },
        { weekday: 4, start_local: '07:00:00', end_local: '19:00:00' },
      ],
      hazards: ['extreme_heat', 'electrical', 'lightning', 'high_wind'],
    },
    {
      site_id: 'VAD-PIPE-03',
      name: 'Mahisagar Pipeline Corridor',
      latitude: 22.2784,
      longitude: 73.1288,
      timezone: 'Asia/Kolkata',
      operating_hours: [
        { weekday: 0, start_local: '05:30:00', end_local: '17:30:00' },
        { weekday: 1, start_local: '05:30:00', end_local: '17:30:00' },
        { weekday: 2, start_local: '05:30:00', end_local: '17:30:00' },
        { weekday: 3, start_local: '05:30:00', end_local: '17:30:00' },
        { weekday: 4, start_local: '05:30:00', end_local: '17:30:00' },
      ],
      hazards: ['extreme_heat', 'monsoon', 'confined_space'],
    },
  ],
};
