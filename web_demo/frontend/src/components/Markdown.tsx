import { useMemo } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

interface Props {
  source: string;
}

export default function Markdown({ source }: Props) {
  const html = useMemo(() => {
    if (!source) return '';
    marked.setOptions({ breaks: true, gfm: true });
    const raw = marked.parse(source) as string;
    return DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } });
  }, [source]);
  return <div className="md" dangerouslySetInnerHTML={{ __html: html }} />;
}
