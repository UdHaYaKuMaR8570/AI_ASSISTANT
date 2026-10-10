import React from 'react';

interface Props {
  content: string;
}

function renderInline(text: string): React.ReactNode {
  // Replace inline code, bold, italics
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let keyIdx = 0;

  while (remaining) {
    // Check for inline code `...`
    const codeMatch = remaining.match(/^`([^`]+)`/);
    if (codeMatch) {
      parts.push(
        <code key={keyIdx++} className="bg-paper-200 text-coral-700 font-mono text-xs px-1.5 py-0.5 rounded">
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeMatch[0].length);
      continue;
    }

    // Check for bold **...**
    const boldMatch = remaining.match(/^\*\*([^*]+)\*\*/);
    if (boldMatch) {
      parts.push(
        <strong key={keyIdx++} className="font-semibold text-ink">
          {boldMatch[1]}
        </strong>
      );
      remaining = remaining.slice(boldMatch[0].length);
      continue;
    }

    // Check for citation brackets [Guest — Episode, HH:MM:SS]
    const citeMatch = remaining.match(/^\[([^\]]+—[^\]]+)\]/);
    if (citeMatch) {
      parts.push(
        <span key={keyIdx++} className="inline-block px-1.5 py-0.5 bg-paper-200 text-coral-600 rounded text-xs font-mono font-medium mx-0.5">
          {citeMatch[1]}
        </span>
      );
      remaining = remaining.slice(citeMatch[0].length);
      continue;
    }

    // Plain text character
    const nextSpecial = remaining.search(/[`*\[]/);
    if (nextSpecial === -1) {
      parts.push(remaining);
      break;
    } else if (nextSpecial > 0) {
      parts.push(remaining.slice(0, nextSpecial));
      remaining = remaining.slice(nextSpecial);
    } else {
      parts.push(remaining[0]);
      remaining = remaining.slice(1);
    }
  }

  return parts;
}

export const MarkdownView: React.FC<Props> = ({ content }) => {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBuffer: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${i}`} className="bg-[#1A1611] text-[#FAF6F0] p-4 rounded-lg overflow-x-auto font-mono text-xs my-3 leading-relaxed">
            <code>{codeBuffer.join('\n')}</code>
          </pre>
        );
        codeBuffer = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      continue;
    }

    if (line.startsWith('# ')) {
      elements.push(
        <h1 key={`h1-${i}`} className="font-serif text-2xl font-bold tracking-tight text-ink mt-6 mb-3">
          {line.slice(2)}
        </h1>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h2 key={`h2-${i}`} className="font-serif text-xl font-semibold text-ink mt-5 mb-2.5 border-b border-paper-300 pb-1">
          {line.slice(3)}
        </h2>
      );
    } else if (line.startsWith('### ')) {
      elements.push(
        <h3 key={`h3-${i}`} className="font-serif text-base font-semibold text-ink mt-4 mb-2">
          {line.slice(4)}
        </h3>
      );
    } else if (line.startsWith('> ')) {
      elements.push(
        <blockquote key={`quote-${i}`} className="border-l-4 border-coral-500 pl-4 py-1 italic text-ink-muted my-3 bg-paper-100 rounded-r">
          {renderInline(line.slice(2))}
        </blockquote>
      );
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      elements.push(
        <li key={`li-${i}`} className="ml-5 list-disc text-sm text-ink-light leading-relaxed mb-1">
          {renderInline(line.slice(2))}
        </li>
      );
    } else if (/^\d+\.\s/.test(line)) {
      const textAfterNum = line.replace(/^\d+\.\s/, '');
      elements.push(
        <li key={`oli-${i}`} className="ml-5 list-decimal text-sm text-ink-light leading-relaxed mb-1">
          {renderInline(textAfterNum)}
        </li>
      );
    } else if (line.trim() === '') {
      // spacing
    } else {
      elements.push(
        <p key={`p-${i}`} className="text-sm text-ink-light leading-relaxed mb-3">
          {renderInline(line)}
        </p>
      );
    }
  }

  if (inCodeBlock && codeBuffer.length > 0) {
    elements.push(
      <pre key="code-tail" className="bg-[#1A1611] text-[#FAF6F0] p-4 rounded-lg overflow-x-auto font-mono text-xs my-3 leading-relaxed">
        <code>{codeBuffer.join('\n')}</code>
      </pre>
    );
  }

  return (
    <div className="prose prose-stone max-w-none text-[#1A1611] font-sans leading-relaxed">
      {elements}
    </div>
  );
};
