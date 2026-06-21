const LOG_KEY = "safesphere_logs";
const SETTINGS_KEY = "safesphere_settings";

export function getLogs() {
  try {
    return JSON.parse(localStorage.getItem(LOG_KEY) || "[]");
  } catch {
    return [];
  }
}

export function addLog(entry) {
  const logs = getLogs();
  const next = [{ id: crypto.randomUUID(), createdAt: new Date().toISOString(), ...entry }, ...logs].slice(0, 100);
  localStorage.setItem(LOG_KEY, JSON.stringify(next));
  return next;
}

export function updateLog(id, patch) {
  const next = getLogs().map((item) => (item.id === id ? { ...item, ...patch } : item));
  localStorage.setItem(LOG_KEY, JSON.stringify(next));
  return next;
}

export function getSettings() {
  try {
    return JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

export function saveSettings(settings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}
