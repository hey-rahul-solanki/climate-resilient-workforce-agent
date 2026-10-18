import type { ReactNode } from 'react';

type ListBlock = { type: 'ordered' | 'unordered'; items: string[] };
type Block = { type: 'paragraph'; items: string[] } | ListBlock;

function inlineMarkdown(value: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const pattern = /(\*\*.+?\*\*|`[^`]+`|\*[^*]+\*)/g;
  let cursor = 0;
  for (const match of value.matchAll(pattern)) {
    const index = match.index ?? 0;
    if (index > cursor) parts.push(value.slice(cursor, index));
    const token = match[0];
    if (token.startsWith('**')) parts.push(<strong key={index}>{token.slice(2, -2)}</strong>);
    else if (token.startsWith('`')) parts.push(<code key={index}>{token.slice(1, -1)}</code>);
    else parts.push(<em key={index}>{token.slice(1, -1)}</em>);
    cursor = index + token.length;
  }
  if (cursor < value.length) parts.push(value.slice(cursor));
  return parts;
}

function parseBlocks(source: string): Block[] {
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  let list: ListBlock | null = null;
  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ type: 'paragraph', items: [paragraph.join(' ')] });
    paragraph = [];
  };
  const flushList = () => { if (list) blocks.push(list); list = null; };
  for (const rawLine of source.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) { flushParagraph(); flushList(); continue; }
    const ordered = line.match(/^\d+[.)]\s+(.+)$/);
    const unordered = line.match(/^[-*+]\s+(.+)$/);
    const type = ordered ? 'ordered' : unordered ? 'unordered' : null;
    if (type) {
      flushParagraph();
      if (list && list.type !== type) flushList();
      list ??= { type, items: [] };
      list.items.push((ordered ?? unordered)![1]);
    } else { flushList(); paragraph.push(line); }
  }
  flushParagraph(); flushList();
  return blocks;
}

export function ChatMarkdown({ text }: { text: string }) {
  return <div className="chat-markdown">{parseBlocks(text).map((block, index) => {
    if (block.type === 'ordered') return <ol key={index}>{block.items.map((item, i) => <li key={i}>{inlineMarkdown(item)}</li>)}</ol>;
    if (block.type === 'unordered') return <ul key={index}>{block.items.map((item, i) => <li key={i}>{inlineMarkdown(item)}</li>)}</ul>;
    return <p key={index}>{inlineMarkdown(block.items[0])}</p>;
  })}</div>;
}
