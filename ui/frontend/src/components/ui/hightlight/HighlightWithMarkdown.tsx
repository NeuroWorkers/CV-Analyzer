import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

import type { IHighlightProps } from '../../../core/types/ui-types/highlightTypes';
import styles from './Highlight.module.css'; 

export const HighlightWithMarkdown = ({ text, highlights = [] }: IHighlightProps) => {
  if (!text) return null;
  
  // Нормализуем highlights в массив слов
  const normalizedHighlights = !highlights 
    ? [] 
    : typeof highlights === 'string' 
      ? highlights.split(/\s+/).filter(word => word.length > 0) // Разбиваем строку на слова
      : Array.isArray(highlights) 
        ? highlights.flatMap(h => h.split(/\s+/).filter(word => word.length > 0)) // Разбиваем каждую строку на слова
        : [];
  
  if (normalizedHighlights.length === 0) {
    // Если нет подсветки, показываем как markdown
    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          a: ({ node, ...props }) => (
            <a 
              {...props} 
              className={styles.link}
              target="_blank" 
              rel="noopener noreferrer"
            />
          ),
          strong: ({ node, ...props }) => (
            <strong {...props} className={styles.bold} />
          ),
          p: ({ node, ...props }) => (
            <p {...props} className={styles.paragraph} />
          ),
          ul: ({ node, ...props }) => (
            <ul {...props} className={styles.list} />
          ),
          li: ({ node, ...props }) => (
            <li {...props} className={styles.listItem} />
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    );
  }

  // Если есть подсветка, используем простую текстовую подсветку с базовой markdown поддержкой
  const highlightText = (content: string) => {
    const escapedHighlights = normalizedHighlights.map(h => h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    // Для кириллицы используем более простой подход без \b
    const regex = new RegExp(`(${escapedHighlights.join('|')})`, 'gi');
    const parts = content.split(regex);
    
    return parts.map((part, i) =>
      normalizedHighlights.some(h => h.toLowerCase() === part.toLowerCase()) ? (
        <mark key={i} className={styles.highlight}>{part}</mark>
      ) : (
        <span key={i}>{part}</span>
      )
    );
  };

  // Простая обработка некоторых markdown элементов
  const renderWithBasicMarkdown = (content: string) => {
    // Разбиваем по строкам для сохранения переносов
    const lines = content.split('\n');
    
    return lines.map((line, lineIndex) => {
      // Обрабатываем жирный текст
      const boldRegex = /\*\*(.*?)\*\*/g;
      const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
      
      const elements = [];
      let lastIndex = 0;
      
      // Находим все жирные участки и ссылки
      const matches = [];
      let match;
      
      // Ищем жирный текст
      while ((match = boldRegex.exec(line)) !== null) {
        matches.push({
          type: 'bold',
          start: match.index,
          end: match.index + match[0].length,
          content: match[1],
          full: match[0]
        });
      }
      
      // Ищем ссылки
      linkRegex.lastIndex = 0;
      while ((match = linkRegex.exec(line)) !== null) {
        matches.push({
          type: 'link',
          start: match.index,
          end: match.index + match[0].length,
          content: match[1],
          url: match[2],
          full: match[0]
        });
      }
      
      // Сортируем по позиции
      matches.sort((a, b) => a.start - b.start);
      
      // Обрабатываем совпадения
      for (const matchItem of matches) {
        // Добавляем текст до совпадения
        if (matchItem.start > lastIndex) {
          const textBefore = line.slice(lastIndex, matchItem.start);
          elements.push(...highlightText(textBefore));
        }
        
        // Добавляем обработанное совпадение
        if (matchItem.type === 'bold') {
          elements.push(
            <strong key={`bold-${lineIndex}-${matchItem.start}`} className={styles.bold}>
              {highlightText(matchItem.content)}
            </strong>
          );
        } else if (matchItem.type === 'link') {
          elements.push(
            <a 
              key={`link-${lineIndex}-${matchItem.start}`}
              href={matchItem.url}
              className={styles.link}
              target="_blank"
              rel="noopener noreferrer"
            >
              {highlightText(matchItem.content)}
            </a>
          );
        }
        
        lastIndex = matchItem.end;
      }
      
      // Добавляем оставшийся текст
      if (lastIndex < line.length) {
        const textAfter = line.slice(lastIndex);
        elements.push(...highlightText(textAfter));
      }
      
      // Если нет совпадений, просто подсвечиваем всю строку
      if (matches.length === 0) {
        elements.push(...highlightText(line));
      }
      
      return (
        <span key={lineIndex}>
          {elements}
          {lineIndex < lines.length - 1 && <br />}
        </span>
      );
    });
  };

  return (
    <div className={styles.container}>
      {renderWithBasicMarkdown(text)}
    </div>
  );
};
