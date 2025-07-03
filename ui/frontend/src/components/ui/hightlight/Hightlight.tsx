import type { IHighlightProps } from '../../../core/types/ui-types/highlightTypes';

import styles from './Highlight.module.css'; 


export const Highlight = ({ text, highlights = [] }: IHighlightProps) => {
  if (!text) return null;
  
  // Нормализуем highlights в массив строк и разбиваем на отдельные слова
  const normalizedHighlights = !highlights 
    ? [] 
    : typeof highlights === 'string' 
      ? highlights.split(/\s+/).filter(word => word.length > 0) // Разбиваем строку на слова
      : Array.isArray(highlights) 
        ? highlights.flatMap(h => h.split(/\s+/).filter(word => word.length > 0)) // Разбиваем каждую строку на слова
        : [];
        
  if (normalizedHighlights.length === 0) return <>{text}</>;
  
  const escapedHighlights = normalizedHighlights.map(h => h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  // Для кириллицы используем более простой подход без \b
  const regex = new RegExp(`(${escapedHighlights.join('|')})`, 'gi');
  const parts = text.split(regex);
  
  return (
    <>
      {parts.map((part, i) =>
        normalizedHighlights.some(h => h.toLowerCase() === part.toLowerCase()) ? (
          <mark key={i} className={styles.highlight}>{part}</mark>
        ) : (
          part
        )
      )}
    </>
  );
};
