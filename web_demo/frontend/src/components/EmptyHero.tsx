import Icon from './Icon';
import QuickQuestions from './QuickQuestions.tsx';

interface Props {
  onPick: (q: string, i: number) => void;
}

export default function EmptyHero({ onPick }: Props) {
  return (
    <div className="empty-hero">
      <div className="icon">
        <Icon name="flask" size={28} stroke={1.6} />
      </div>
      <h1>你好，我是实验室安全小助手</h1>
      <p>我会基于规范、SOP 与你的提问，提供安全、可追溯的操作建议。</p>
      <QuickQuestions onPick={onPick} />
    </div>
  );
}
