import React, { useMemo } from 'react';
import { sanitizeHtml } from './sanitize';

interface Props {
  content: string;
}

export const HtmlSandbox: React.FC<Props> = ({ content }) => {
  const safeDoc = useMemo(() => {
    const sanitized = sanitizeHtml(content);
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <style>
            body {
              font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              padding: 1.5rem;
              margin: 0;
              color: #1a1611;
              background-color: #ffffff;
            }
          </style>
        </head>
        <body>
          ${sanitized}
        </body>
      </html>
    `;
  }, [content]);

  return (
    <div className="w-full h-full min-h-[450px] bg-white rounded-lg border border-paper-300 overflow-hidden shadow-inner">
      <iframe
        title="Artifact Sandbox Preview"
        srcDoc={safeDoc}
        sandbox="allow-scripts"
        className="w-full h-full min-h-[450px] border-0"
      />
    </div>
  );
};
