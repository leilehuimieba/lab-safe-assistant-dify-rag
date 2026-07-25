interface Props {
  score: number;
}

export default function ScoreBar({ score }: Props) {
  return (
    <div className="score-bar" title={`检索匹配分 ${score}（仅用于本次结果排序）`}>
      <span className="score-label">匹配</span>
      <span className="num">{score.toFixed(1)}</span>
    </div>
  );
}
