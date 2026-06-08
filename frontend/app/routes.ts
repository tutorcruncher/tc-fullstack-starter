import { type RouteConfig, index, layout, route } from '@react-router/dev/routes';

/**
 * Programmatic route manifest (React Router framework mode). `react-router
 * typegen` reads this to generate the per-route `+types/*` modules, so every
 * route declared here gets type-safe `Route.LoaderArgs` / `Route.ActionArgs` /
 * `Route.ComponentProps`.
 *
 * The example "Items" feature follows the resource file convention:
 *   <resource>/<resource>.tsx   list
 *   <resource>-layout.tsx       parent that loads the record + <Outlet context>
 *   <resource>-detail.tsx       detail child (index of the layout)
 *   <resource>-new.tsx          create
 *   <resource>-edit.tsx         edit
 *
 * Scaffold a new resource by analogy.
 */
export default [
  index('routes/home.tsx'),

  route('items', 'routes/items/items.tsx'),
  route('items/new', 'routes/items/item-new.tsx'),
  layout('routes/items/item-layout.tsx', [
    route('items/:itemId', 'routes/items/item-detail.tsx'),
    route('items/:itemId/edit', 'routes/items/item-edit.tsx'),
  ]),

  route('*', 'routes/not-found.tsx'),
] satisfies RouteConfig;
