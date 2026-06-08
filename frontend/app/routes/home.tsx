import type { Route } from './+types/home';
import { Button, Card, Heading } from '~/components/ui';
import { ArrowRight } from '~/components/icons/Icon';
import { APP_NAME, buildMetaData } from '~/helpers/meta';

export function meta(): Route.MetaDescriptors {
  return buildMetaData('Home');
}

/**
 * Index route. A neutral welcome screen linking into the example "Items"
 * feature, which exercises the full vertical slice (loader/action data flow,
 * list/detail/form, the UI primitives). Replace this with your app's landing
 * content.
 */
export default function Home() {
  return (
    <main className="container-narrow py-16">
      <Heading level={1}>Welcome to {APP_NAME}</Heading>
      <p className="mb-8 max-w-prose text-body text-neutral-700">
        A React Router v7 starter wired up with SSR, typed loaders and actions, a single API client,
        and a small set of UI primitives. The example feature below shows the whole stack working
        end to end.
      </p>

      <Card className="max-w-md">
        <Heading level={3} as="h2">
          Items
        </Heading>
        <p className="mb-5 text-body text-neutral-700">
          Browse, search, create, edit, and delete records — the reference vertical slice.
        </p>
        <Button href="/items" icon={<ArrowRight size={16} />} iconPosition="right">
          View items
        </Button>
      </Card>
    </main>
  );
}
