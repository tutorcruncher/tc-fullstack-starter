import { screen } from '@testing-library/react';
import { Heading } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('Heading', () => {
  it('renders its children', () => {
    renderWithRouter(<Heading>Page title</Heading>);
    expect(screen.getByRole('heading', { name: 'Page title' })).toBeInTheDocument();
  });

  it('renders an h1 at level 1 by default', () => {
    renderWithRouter(<Heading>Title</Heading>);
    expect(screen.getByRole('heading', { level: 1, name: 'Title' })).toBeInTheDocument();
  });

  it.each([
    [1, 'text-h1'],
    [2, 'text-h2'],
    [3, 'text-h3'],
    [4, 'text-body'],
    [5, 'text-body'],
    [6, 'text-small'],
  ] as const)('maps level %s to its text size token', (level, sizeClass) => {
    renderWithRouter(<Heading level={level}>Title</Heading>);
    expect(screen.getByRole('heading', { name: 'Title' })).toHaveClass(sizeClass);
  });

  it('derives the semantic tag from the level', () => {
    renderWithRouter(<Heading level={3}>Title</Heading>);
    expect(screen.getByRole('heading', { level: 3, name: 'Title' })).toBeInTheDocument();
  });

  it('uses the as tag to keep the document outline correct', () => {
    renderWithRouter(
      <Heading level={1} as="h2">
        Title
      </Heading>,
    );
    expect(screen.getByRole('heading', { level: 2, name: 'Title' })).toHaveClass('text-h1');
  });

  it('applies the level margin by default', () => {
    renderWithRouter(<Heading level={2}>Title</Heading>);
    expect(screen.getByRole('heading', { name: 'Title' })).toHaveClass('mb-3');
  });

  it('omits the margin when noMargin is set', () => {
    renderWithRouter(
      <Heading level={2} noMargin>
        Title
      </Heading>,
    );
    expect(screen.getByRole('heading', { name: 'Title' })).not.toHaveClass('mb-3');
  });
});
