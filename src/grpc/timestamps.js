// Conversión de fechas entre texto ISO (web) y Timestamp { seconds, nanos } (gRPC).
export function toTimestamp(value) {
  if (!value) return undefined;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return undefined;

  const milliseconds = date.getTime();
  const seconds = Math.floor(milliseconds / 1000);
  return { seconds: String(seconds), nanos: (milliseconds - seconds * 1000) * 1_000_000 };
}

export function fromTimestamp(value) {
  if (!value) return value;
  if (typeof value === 'string') return value;
  if (value instanceof Date) return value.toISOString();

  if (typeof value === 'object' && value.seconds !== undefined) {
    const milliseconds = Number(value.seconds) * 1000 + Number(value.nanos || 0) / 1_000_000;
    return new Date(milliseconds).toISOString();
  }

  return value;
}

export function normalizeDates(value) {
  if (Array.isArray(value)) return value.map(normalizeDates);
  if (!value || typeof value !== 'object') return value;

  return Object.fromEntries(Object.entries(value).map(([key, nestedValue]) => {
    if (['fechaInicio', 'fechaFin', 'fechaNacimiento', 'createdAt', 'updatedAt'].includes(key)) {
      return [key, fromTimestamp(nestedValue)];
    }
    return [key, normalizeDates(nestedValue)];
  }));
}