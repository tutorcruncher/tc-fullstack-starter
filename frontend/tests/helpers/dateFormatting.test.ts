import {
  addDays,
  DEFAULT_DATE_FORMAT,
  DEFAULT_FORMAT,
  DEFAULT_TIME_FORMAT,
  DEFAULT_TIMEZONE,
  formatDate,
  formatDateTime,
  formatTime,
} from '~/helpers/dateFormatting';

describe('formatDate', () => {
  it('formats an ISO string with the default format', () => {
    expect(formatDate('2024-01-15T13:45:00Z')).toBe('Monday, January 15, 2024');
  });

  it('formats with a custom format token', () => {
    expect(formatDate('2024-01-15T13:45:00Z', 'yyyy-MM-dd')).toBe('2024-01-15');
  });

  it('shifts the date into the requested timezone', () => {
    expect(formatDate('2024-01-15T23:30:00Z', 'yyyy-MM-dd', 'America/New_York')).toBe('2024-01-15');
  });

  it('crosses the day boundary when the timezone shifts past midnight', () => {
    expect(formatDate('2024-01-16T03:30:00Z', 'yyyy-MM-dd', 'America/New_York')).toBe('2024-01-15');
  });

  it('returns Invalid Date for unparseable input', () => {
    expect(formatDate('not-a-date')).toBe('Invalid Date');
  });
});

describe('formatTime', () => {
  it('formats an ISO string with the default format', () => {
    expect(formatTime('2024-01-15T13:45:00Z')).toBe('1:45 PM');
  });

  it('formats with a custom format token', () => {
    expect(formatTime('2024-01-15T13:45:00Z', 'HH:mm')).toBe('13:45');
  });

  it('shifts the time into the requested timezone', () => {
    expect(formatTime('2024-01-15T13:45:00Z', 'HH:mm', 'America/New_York')).toBe('08:45');
  });

  it('returns Invalid Date for unparseable input', () => {
    expect(formatTime('not-a-date')).toBe('Invalid Date');
  });
});

describe('formatDateTime', () => {
  it('formats an ISO string with the default combined format', () => {
    expect(formatDateTime('2024-01-15T13:45:00Z')).toBe('Monday, January 15, 2024 1:45 PM');
  });

  it('formats with a custom format token', () => {
    expect(formatDateTime('2024-01-15T13:45:00Z', 'yyyy-MM-dd HH:mm')).toBe('2024-01-15 13:45');
  });

  it('shifts the datetime into the requested timezone', () => {
    expect(formatDateTime('2024-01-15T13:45:00Z', 'yyyy-MM-dd HH:mm', 'America/New_York')).toBe(
      '2024-01-15 08:45',
    );
  });

  it('returns Invalid Date for unparseable input', () => {
    expect(formatDateTime('not-a-date')).toBe('Invalid Date');
  });
});

describe('addDays', () => {
  it('adds positive days', () => {
    expect(addDays(new Date('2024-01-15T00:00:00Z'), 5).toISOString()).toBe(
      '2024-01-20T00:00:00.000Z',
    );
  });

  it('subtracts with negative days', () => {
    expect(addDays(new Date('2024-01-15T00:00:00Z'), -5).toISOString()).toBe(
      '2024-01-10T00:00:00.000Z',
    );
  });

  it('returns the same instant when adding zero days', () => {
    expect(addDays(new Date('2024-01-15T00:00:00Z'), 0).toISOString()).toBe(
      '2024-01-15T00:00:00.000Z',
    );
  });
});

describe('date formatting constants', () => {
  it('exposes the documented default tokens', () => {
    expect(DEFAULT_TIMEZONE).toBe('UTC');
    expect(DEFAULT_DATE_FORMAT).toBe('cccc, MMMM d, yyyy');
    expect(DEFAULT_TIME_FORMAT).toBe('h:mm a');
    expect(DEFAULT_FORMAT).toBe('cccc, MMMM d, yyyy h:mm a');
  });
});
