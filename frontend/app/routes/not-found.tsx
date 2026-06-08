import type { Route } from './+types/not-found';
import { Button, Heading } from '~/components/ui';
import { buildMetaData } from '~/helpers/meta';

export function meta(): Route.MetaDescriptors {
  return buildMetaData('Page not found');
}

/**
 * Catch-all `*` route for unmatched paths. The root `ErrorBoundary` handles
 * thrown 404s from loaders/actions; this renders a friendly page for URLs that
 * match no route at all.
 */
export default function NotFound() {
  return (
    <main className="flex min-h-[70vh] flex-col items-center justify-center px-4 text-center">
      <p className="mb-2 text-display font-semibold text-neutral-300">404</p>
      <Heading level={2} as="h1">
        Page not found
      </Heading>
      <p className="mb-8 max-w-md text-body text-neutral-700">
        Sorry, we couldn&rsquo;t find the page you were looking for. It may have been moved or no
        longer exists.
      </p>
      <Button href="/">Back to home</Button>
    </main>
  );
}
