import { APP_NAME, buildMetaData } from '~/helpers/meta';

describe('buildMetaData', () => {
  it('suffixes the title with the app name', () => {
    const [title] = buildMetaData('Items');
    expect(title).toEqual({ title: `Items | ${APP_NAME}` });
  });

  it('returns the og:title, and og:site_name tags alongside the title', () => {
    expect(buildMetaData('Items')).toEqual([
      { title: `Items | ${APP_NAME}` },
      { property: 'og:title', content: `Items | ${APP_NAME}` },
      { property: 'og:site_name', content: APP_NAME },
    ]);
  });

  it('handles an empty title', () => {
    expect(buildMetaData('')).toEqual([
      { title: ` | ${APP_NAME}` },
      { property: 'og:title', content: ` | ${APP_NAME}` },
      { property: 'og:site_name', content: APP_NAME },
    ]);
  });
});

describe('APP_NAME', () => {
  it('exposes the configured app name', () => {
    expect(APP_NAME).toBe('RR Starter');
  });
});
