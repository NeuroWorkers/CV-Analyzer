import { useMemo } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

import styles from './MarkdownRenderer.module.css';

interface MarkdownRendererProps {
  children: string;
  className?: string;
}

export const MarkdownRenderer = ({ children, className }: MarkdownRendererProps) => {
  const sanitizedHtml = useMemo(() => {
    try {
      // Настраиваем marked для правильного рендеринга
      marked.setOptions({
        breaks: true, // Преобразуем переносы строк в <br>
        gfm: true,    // Поддержка GitHub Flavored Markdown
      });

      // Преобразуем markdown в HTML (используем синхронную версию parse)
      const rawHtml = marked.parse(children, { async: false }) as string;
      
      // Очищаем HTML с помощью DOMPurify
      return DOMPurify.sanitize(rawHtml, {
        ALLOWED_TAGS: [
          'p', 'br', 'strong', 'em', 'b', 'i', 'u', 's', 
          'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'blockquote', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
        ],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
      });
    } catch (error) {
      console.error('Error parsing markdown:', error);
      return children; // Возвращаем исходный текст в случае ошибки
    }
  }, [children]);

  return (
    <div 
      className={`${styles.markdownContainer} ${className || ''}`}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  );
};
