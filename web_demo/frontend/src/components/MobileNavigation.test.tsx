import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import MobileNavigation from './MobileNavigation';

function renderNavigation(open = true) {
  const onClose = vi.fn();
  const onNew = vi.fn();
  const onHistoryClick = vi.fn();
  const onLogout = vi.fn();
  render(
    <MobileNavigation
      open={open}
      onClose={onClose}
      onNew={onNew}
      history={['乙醚泄漏怎么办？']}
      onHistoryClick={onHistoryClick}
      onLogout={onLogout}
    />,
  );
  return { onClose, onNew, onHistoryClick, onLogout };
}

describe('MobileNavigation', () => {
  it('does not render the drawer while closed', () => {
    renderNavigation(false);

    expect(screen.queryByRole('dialog', { name: '移动端导航' })).not.toBeInTheDocument();
  });

  it('provides the desktop sidebar actions on mobile', () => {
    renderNavigation();

    expect(screen.getByRole('button', { name: '新建对话' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '知识库态势' })).toHaveAttribute('href', '#/kb');
    expect(screen.getByRole('button', { name: '乙醚泄漏怎么办？' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '退出登录' })).toBeInTheDocument();
  });

  it('selects a history item and closes the drawer', () => {
    const { onClose, onHistoryClick } = renderNavigation();

    fireEvent.click(screen.getByRole('button', { name: '乙醚泄漏怎么办？' }));

    expect(onHistoryClick).toHaveBeenCalledWith('乙醚泄漏怎么办？');
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('closes on Escape', () => {
    const { onClose } = renderNavigation();

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onClose).toHaveBeenCalledOnce();
  });
});
