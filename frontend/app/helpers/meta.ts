/**
 * App display name used as the `<title>` suffix and OG site name. Change this
 * to your app's name — it is a placeholder.
 */
export const APP_NAME = 'RR Starter';

/**
 * A single meta tag. Structurally compatible with React Router's
 * `Route.MetaDescriptors` (an array of these), so every route's `meta()` can
 * return `buildMetaData(...)` directly.
 */
type MetaDescriptor = { title: string } | { property: string; content: string };

/**
 * Build the standard `<title>` plus basic Open Graph tags for a page, suffixing
 * the title with {@link APP_NAME}. Every route's `meta()` returns this.
 */
export function buildMetaData(title: string): MetaDescriptor[] {
  const fullTitle = `${title} | ${APP_NAME}`;
  return [
    { title: fullTitle },
    { property: 'og:title', content: fullTitle },
    { property: 'og:site_name', content: APP_NAME },
  ];
}
