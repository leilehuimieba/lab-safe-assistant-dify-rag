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
  model?: string;
}

export default function DecisionBadge({ decision, model }: Props) {
  let label = DECISION_LABEL[decision] ?? decision;
  if (decision === 'dify_answer') {
    if (model === 'local-fast-path') label = '本地快速回答';
    else if (model === 'dify-workflow') label = 'Dify 工作流';
    else if (model === 'kb-search') label = '本地检索';
  } else if (decision === 'structured_fallback') {
    label = '结构化兜底';
  }

  return (
    <span className={`badge dec-${decision}`}>
      <Icon name={DECISION_ICON[decision] ?? 'info'} size={11} stroke={2.2} />
      {label}
    </span>
  );
}
