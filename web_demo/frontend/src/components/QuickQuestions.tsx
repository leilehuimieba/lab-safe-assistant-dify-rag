import Icon from './Icon';
import { QUICK_QUESTIONS } from './quickQuestions';

interface Props {
  onPick: (q: string, i: number) => void;
}

export default function QuickQuestions({ onPick }: Props) {
  return (
    <div className="empty-tips">
      <button className="empty-tip" onClick={() => onPick(QUICK_QUESTIONS[0], 0)}>
        <span className="et-icon"><Icon name="droplet" size={14} /></span>
        <span>实验室发生化学品<strong>泄漏</strong>时，第一步应该怎么做？</span>
      </button>
      <button className="empty-tip" onClick={() => onPick(QUICK_QUESTIONS[1], 1)}>
        <span className="et-icon"><Icon name="shield" size={14} /></span>
        <span>使用<strong>浓硫酸</strong>需要佩戴哪些防护装备？</span>
      </button>
      <button className="empty-tip" onClick={() => onPick(QUICK_QUESTIONS[3], 3)}>
        <span className="et-icon"><Icon name="fire" size={14} /></span>
        <span>实验室发生<strong>火灾</strong>的应急处理流程？</span>
      </button>
      <button className="empty-tip" onClick={() => onPick(QUICK_QUESTIONS[2], 2)}>
        <span className="et-icon"><Icon name="alert" size={14} /></span>
        <span>离心机运转时<strong>能不能</strong>打开盖子？</span>
      </button>
    </div>
  );
}
