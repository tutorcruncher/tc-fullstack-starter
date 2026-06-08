import type { Item } from '~/types';

export const mockItem: Item = {
  id: 1,
  name: 'First item',
  description: 'A representative item used across tests.',
  status: 'active',
  category: 'general',
};

export const mockItems: Item[] = [
  mockItem,
  {
    id: 2,
    name: 'Second item',
    description: 'A draft item with no category.',
    status: 'draft',
    category: null,
  },
  {
    id: 3,
    name: 'Third item',
    description: 'An archived item.',
    status: 'archived',
    category: 'internal',
  },
];

/**
 * Build a list of `count` distinct items, overriding any fields via `overrides`.
 * Use this when a test needs more rows than the {@link mockItems} fixture (e.g.
 * to exercise pagination).
 */
export function buildItems(count: number, overrides: Partial<Item> = {}): Item[] {
  return Array.from({ length: count }, (_unused, index) => ({
    id: index + 1,
    name: `Item ${index + 1}`,
    description: `Description for item ${index + 1}.`,
    status: 'active',
    category: 'general',
    ...overrides,
  }));
}
