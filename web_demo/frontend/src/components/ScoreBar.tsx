interface Props {
  score: number;
}

export default function ScoreBar({ score }: Props) {
  const pct = Math.max(0, Math.min(100, (score / 10) * 100));
  return (
    <div className="score-bar" title={`匹配分 ${score} / 10`}>
      <div className="track">
        <div className="fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="num">{score.toFixed(1)}</span>
    </div>
  );
}
