import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import ScoreBar from './ScoreBar';

describe('ScoreBar', () => {
  it('does not present an unbounded retrieval score as a score out of ten', () => {
    render(<ScoreBar score={19.2} />);

    const score = screen.getByTitle('检索匹配分 19.2（仅用于本次结果排序）');
    expect(score).toBeInTheDocument();
    expect(score).not.toHaveTextContent('/ 10');
  });
});
