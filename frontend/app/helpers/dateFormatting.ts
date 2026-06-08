import { DateTime } from 'luxon';

/**
 * Default timezone for formatting. Change this to your app's primary timezone,
 * or pass an explicit `timezone` argument per call.
 */
export const DEFAULT_TIMEZONE = 'UTC';

/** Default Luxon format token for {@link formatDate}. */
export const DEFAULT_DATE_FORMAT = 'cccc, MMMM d, yyyy';

/** Default Luxon format token for {@link formatTime}. */
export const DEFAULT_TIME_FORMAT = 'h:mm a';

/** Default Luxon format token for {@link formatDateTime}. */
export const DEFAULT_FORMAT = `${DEFAULT_DATE_FORMAT} ${DEFAULT_TIME_FORMAT}`;

/**
 * Format an ISO-8601 string as a date using Luxon format tokens. Returns
 * 'Invalid Date' for unparseable input.
 */
export function formatDate(
  iso: string,
  format = DEFAULT_DATE_FORMAT,
  timezone = DEFAULT_TIMEZONE,
): string {
  const dt = DateTime.fromISO(iso, { zone: timezone });
  if (!dt.isValid) {
    return 'Invalid Date';
  }
  return dt.toFormat(format);
}

/**
 * Format an ISO-8601 string as a time using Luxon format tokens. Returns
 * 'Invalid Date' for unparseable input.
 */
export function formatTime(
  iso: string,
  format = DEFAULT_TIME_FORMAT,
  timezone = DEFAULT_TIMEZONE,
): string {
  const dt = DateTime.fromISO(iso, { zone: timezone });
  if (!dt.isValid) {
    return 'Invalid Date';
  }
  return dt.toFormat(format);
}

/**
 * Format an ISO-8601 string as a combined date + time using Luxon format
 * tokens. Returns 'Invalid Date' for unparseable input.
 */
export function formatDateTime(
  iso: string,
  format = DEFAULT_FORMAT,
  timezone = DEFAULT_TIMEZONE,
): string {
  const dt = DateTime.fromISO(iso, { zone: timezone });
  if (!dt.isValid) {
    return 'Invalid Date';
  }
  return dt.toFormat(format);
}

/** Return a new `Date` with `n` days added (positive or negative). */
export function addDays(date: Date, n: number): Date {
  return DateTime.fromJSDate(date).plus({ days: n }).toJSDate();
}
