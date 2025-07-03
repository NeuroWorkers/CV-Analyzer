import { useMemo } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

import type { IHighlightProps } from '../../../core/types/ui-types/highlightTypes';
import styles from './Highlight.module.css'; 

export const HighlightWithMarkdown = ({ text, highlights = [] }: IHighlightProps) => {
  const processedHtml = useMemo(() => {
    if (!text) return '';

    const normalizeHighlights = (input: string | string[] | null | undefined): string[] => {
      if (!input) return [];

      const rawList = typeof input === 'string' ? [input] : Array.isArray(input) ? input : [];

      return rawList
        .flatMap(item =>
          item
            .split(/[\s,;|]+/)
            .map(word => word.trim())
            .filter(word => word.length >= 3)
        );
    };

    const normalizedHighlights = normalizeHighlights(highlights);

    console.log("Исходный input: " + JSON.stringify(highlights));
    console.log("Итог normalizedHighlights: " + JSON.stringify(normalizedHighlights));

    try {
      marked.setOptions({
        breaks: true,
        gfm: true,
      });

      const rawHtml = marked.parse(text, { async: false }) as string;

      let cleanHtml = DOMPurify.sanitize(rawHtml, {
        ALLOWED_TAGS: [
          'p', 'br', 'strong', 'em', 'b', 'i', 'u', 's',
          'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'blockquote', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
          'mark'
        ],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
      }) as string;

      if (normalizedHighlights.length > 0) {
        const escapedHighlights = normalizedHighlights.map(h =>
          h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        );

        const regex = new RegExp(
          `(?<!\\p{L})(${escapedHighlights.join('|')})(?!\\p{L})`,
          'giu'
        );

        cleanHtml = cleanHtml.replace(regex, (match) => {
          return `<mark class="${styles.highlight}">${match}</mark>`;
        });
      }

      return cleanHtml;
    } catch (error) {
      console.error('Error processing markdown with highlights:', error);
      return text;
    }
  }, [text, highlights]);

  if (!processedHtml) return null;

  return (
    <div
      className={styles.markdownContainer}
      dangerouslySetInnerHTML={{ __html: processedHtml }}
    />
  );
};