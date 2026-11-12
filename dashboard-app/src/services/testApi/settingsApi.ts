import { testApiClient } from './client';
import type { TestAppSettings } from '../../types/testEngine';

export const testSettingsApi = {
  getSettings: async () => {
    return testApiClient<TestAppSettings>('/api/settings', {
      method: 'GET',
    });
  },

  updateSettings: async (settings: Partial<TestAppSettings>) => {
    return testApiClient<null>('/api/settings', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
  },
};
