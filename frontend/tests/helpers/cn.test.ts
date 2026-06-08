import { cn } from '~/helpers/cn';

describe('cn', () => {
  it.each([
    [['a', 'b'], 'a b'],
    [['a', false, 'b'], 'a b'],
    [['a', null, undefined, 'b'], 'a b'],
    [['a', { b: true, c: false }], 'a b'],
    [['a', ['b', 'c']], 'a b c'],
    [[], ''],
    [['a', '', 'b'], 'a b'],
  ])('composes %j into %p', (inputs, expected) => {
    expect(cn(...inputs)).toBe(expected);
  });
});
