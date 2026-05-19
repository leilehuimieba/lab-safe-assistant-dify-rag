interface RiskBadgeProps {
  level: string;
}

export default function RiskBadge({ level }: RiskBadgeProps) {
  if (!level) return null;
  return (
    <span className={`badge risk-${level}`}>
      <span className="b-dot" />
      风险 {level}
    </span>
  );
}
