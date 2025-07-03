import { useMemo } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

import type { IHighlightProps } from '../../../core/types/ui-types/highlightTypes';
import styles from './Highlight.module.css'; 

export const HighlightWithMarkdown = ({ text, highlights = [] }: IHighlightProps) => {
  const processedHtml = useMemo(() => {
    if (!text) return '';

    // Нормализуем highlights в массив слов
    const normalizedHighlights = !highlights
      ? []
      : typeof highlights === 'string'
        ? highlights.split(/\s+/).filter(word => word.length > 0)
        : Array.isArray(highlights)
          ? highlights.flatMap(h => h.split(/\s+/).filter(word => word.length > 0)) // Разбиваем каждую строку на слова
          : [];

    console.log("Исходный input: " + JSON.stringify(highlights));
    console.log("Тип highlights: " + typeof highlights);
    console.log("Итог normalizedHighlights: " + JSON.stringify(normalizedHighlights));

    try {
      // Настраиваем marked для правильного рендеринга
      marked.setOptions({
        breaks: true, // Преобразуем переносы строк в <br>
        gfm: true,    // Поддержка GitHub Flavored Markdown
      });

      // Преобразуем markdown в HTML (используем синхронную версию parse)
      const rawHtml = marked.parse(text, { async: false }) as string;
      
      // Очищаем HTML с помощью DOMPurify
      let cleanHtml = DOMPurify.sanitize(rawHtml, {
        ALLOWED_TAGS: [
          'p', 'br', 'strong', 'em', 'b', 'i', 'u', 's', 
          'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'blockquote', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'td', 'th', 'mark'
        ],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
      }) as string;

      if (normalizedHighlights.length > 0) {
        const escapedHighlights = normalizedHighlights.map(h => 
          h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        );

     const regex = new RegExp(
  `(?<![\\wА-Яа-яёЁ])(${escapedHighlights.join('|')})(?![\\wА-Яа-яёЁ])`,
  'gi'
);
        // @ts-ignore
        cleanHtml = cleanHtml.replace(regex, (match) =>
  `<mark class="${styles.highlight}">${match}</mark>`
);
      }

      return cleanHtml;
    } catch (error) {
      console.error('Error processing markdown with highlights:', error);
      return text; // Возвращаем исходный текст в случае ошибки
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
