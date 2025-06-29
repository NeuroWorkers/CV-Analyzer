import type { IHighlightProps } from '../../../core/types/ui-types/highlightTypes';

import styles from './Highlight.module.css'; 


export const Highlight = ({ text, highlights = [] }: IHighlightProps) => {
  if (!text) return null;
  if (!Array.isArray(highlights) || highlights.length === 0) return <>{text}</>;
  const escapedHighlights = highlights.map(h => h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp(`(${escapedHighlights.join('|')})`, 'gi');
  const parts = text.split(regex);
  return (
    <>
      {parts.map((part, i) =>
        highlights.some(h => h.toLowerCase() === part.toLowerCase()) ? (
          <mark key={i} className={styles.highlight}>{part}</mark>
        ) : (
          part
        )
      )}
    </>
  );
};
