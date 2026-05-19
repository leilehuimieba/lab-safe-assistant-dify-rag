import Icon, { type IconName } from './Icon';
import type { DecisionKind } from '../types/api';

export const DECISION_LABEL: Record<string, string> = {
  dify_answer: '已回答',
  dify_answer_guarded: '安全约束',
  dify_low_confidence: '低置信度',
  rule_blocked: '已拒绝',
  emergency_redirect: '紧急情况',
  need_more_info: '需要补充信息',
  structured_fallback: '兜底回答',
};

const DECISION_ICON: Record<string, IconName> = {
  dify_answer: 'shield',
  dify_answer_guarded: 'shield',
  dify_low_confidence: 'info',
  rule_blocked: 'ban',
  emergency_redirect: 'siren',
  need_more_info: 'question',
  structured_fallback: 'info',
};

interface Props {
  decision: DecisionKind;
}

export default function DecisionBadge({ decision }: Props) {
  return (
    <span className={`badge dec-${decision}`}>
      <Icon name={DECISION_ICON[decision] ?? 'info'} size={11} stroke={2.2} />
      {DECISION_LABEL[decision] ?? decision}
    </span>
  );
}
