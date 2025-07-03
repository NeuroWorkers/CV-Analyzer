import { useMemo } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

import type { IHighlightProps } from '../../../core/types/ui-types/highlightTypes';
import styles from './Highlight.module.css'; 

export const HighlightWithMarkdown = ({ text, highlights = [] }: IHighlightProps) => {
  const processedHtml = useMemo(() => {
    if (!text) return '';

const normalizedHighlights = !highlights
  ? []
  : typeof highlights === 'string'
    ? highlights.split(/\s+/).filter(word => word.length > 0)
    : Array.isArray(highlights)
      ? highlights.flatMap(h => h.split(/\s+/).filter(word => word.length > 0))
      : [];

// Показываем шаги
alert("Исходный input: " + JSON.stringify(highlights));
alert("Тип highlights: " + typeof highlights);

if (!highlights) {
  alert("highlights отсутствует ⇒ возвращается []");
} else if (typeof highlights === 'string') {
  alert("highlights — строка\nРазбиваем по пробелам и фильтруем пустые: " + JSON.stringify(
    highlights.split(/\s+/).filter(word => word.length > 0)
  ));
} else if (Array.isArray(highlights)) {
  alert("highlights — массив строк\nДля каждой строки: split и filter\nРезультат: " + JSON.stringify(
    highlights.flatMap(h => h.split(/\s+/).filter(word => word.length > 0))
  ));
} else {
  alert("highlights — неизвестного типа ⇒ возвращается []");
}

alert("Итог normalizedHighlights: " + JSON.stringify(normalizedHighlights));

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
          'blockquote', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
        ],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
      }) as string;

      // Если есть слова для подсветки, применяем их
      if (normalizedHighlights.length > 0) {
        // Создаем регулярное выражение для поиска слов
        const escapedHighlights = normalizedHighlights.map(h => 
          h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        );
        
        // Ищем слова, но не внутри HTML тегов
        const regex = new RegExp(`\\b(${escapedHighlights.join('|')})\\b`, 'gi');
        
        // Применяем подсветку только к тексту, не к HTML тегам
        cleanHtml = cleanHtml.replace(regex, (match) => {
          return `<mark class="${styles.highlight}">${match}</mark>`;
        });
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
