import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import CitationCard from './CitationCard';

describe('CitationCard', () => {
  it('shows the source domain and PDF type before opening an external source', () => {
    render(
      <CitationCard
        citation={{
          kb_id: 'KB-1',
          title: 'Chemical Safety Guide',
          source_title: 'Safety Guide',
          source_org: 'Example University',
          source_url: 'https://safety.example.edu/guides/manual.pdf?download=1',
          risk_level: '高',
          snippet: 'Keep ignition sources away.',
          score: 0.92,
        }}
      />,
    );

    expect(screen.getByText('safety.example.edu')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByRole('link')).toHaveAttribute(
      'href',
      'https://safety.example.edu/guides/manual.pdf?download=1',
    );
  });
});
