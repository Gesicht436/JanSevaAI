import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

describe('JanSevaAI Unified App Component', () => {
  it('renders navbar and initial intake view properly', async () => {
    render(<App />);

    expect(screen.getByText(/JanSeva AI/i)).toBeInTheDocument();
    expect(screen.getByText(/Conversational Intake/i)).toBeInTheDocument();
    expect(screen.getByText(/Review Your Extracted Profile/i)).toBeInTheDocument();
  });

  it('populates fields when selecting a demo preset', async () => {
    // Mock match response
    (globalThis.fetch as any).mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/api/match')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              state_filter_applied: true,
              counts: { eligible: 3, needs_more_info: 1, ineligible: 0, closed: 0, excluded_by_state: 0 },
              followup_fields: ['caste_category'],
              unlock_summary: '3 eligible schemes found for your profile.',
              results: {
                eligible: [
                  {
                    slug: 'mudra-loan',
                    name: 'Pradhan Mantri MUDRA Yojana',
                    ministry_or_department: 'Ministry of Finance',
                    level: 'Central',
                    beneficiary_states: [],
                    categories: ['Banking, Financial Services and Insurance'],
                    verdict: 'eligible',
                    benefit_snippet: 'Collateral-free micro loans up to Rs 10 Lakhs.',
                    verified_ratio: 1.0,
                    missing_fields: [],
                    criteria_results: [],
                  },
                ],
                needs_more_info: [],
                ineligible: [],
                closed: [],
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            status: 'ready',
            total_schemes: 15,
            compiled_schemes: 15,
            total_criteria: 40,
          }),
      });
    });

    render(<App />);

    const itPresetBtn = screen.getByText(/IT Professional/i);
    expect(itPresetBtn).toBeInTheDocument();
    fireEvent.click(itPresetBtn);

    await waitFor(() => {
      expect(screen.getByText(/Pradhan Mantri MUDRA Yojana/i)).toBeInTheDocument();
    });
  });
});
