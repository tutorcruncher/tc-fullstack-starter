jest.mock('~/helpers/env', () => ({
  isDev: false,
  sentryDsn: undefined,
}));

import { reportError } from '~/helpers/monitoring';

describe('reportError', () => {
  let consoleError: jest.SpyInstance;

  beforeEach(() => {
    consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('is a no-op when not in development', () => {
    reportError(new Error('boom'));
    expect(consoleError).not.toHaveBeenCalled();
  });
});

describe('reportError in development', () => {
  let consoleError: jest.SpyInstance;

  beforeEach(() => {
    jest.resetModules();
    consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('logs the error to the console', async () => {
    jest.doMock('~/helpers/env', () => ({ isDev: true, sentryDsn: undefined }));
    const { reportError: devReportError } = await import('~/helpers/monitoring');
    const error = new Error('boom');
    devReportError(error);
    expect(consoleError).toHaveBeenCalledWith('[monitoring] reportError:', error);
  });
});
