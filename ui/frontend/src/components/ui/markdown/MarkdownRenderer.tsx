import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

import styles from './MarkdownRenderer.module.css';

interface MarkdownRendererProps {
  children: string;
  className?: string;
}

export const MarkdownRenderer = ({ children, className }: MarkdownRendererProps) => {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
      components={{
        // Стилизация ссылок
        a: ({ node, ...props }) => (
          <a 
            {...props} 
            className={styles.link}
            target="_blank" 
            rel="noopener noreferrer"
          />
        ),
        // Стилизация жирного текста
        strong: ({ node, ...props }) => (
          <strong {...props} className={styles.bold} />
        ),
        // Стилизация абзацев
        p: ({ node, ...props }) => (
          <p {...props} className={styles.paragraph} />
        ),
        // Стилизация списков
        ul: ({ node, ...props }) => (
          <ul {...props} className={styles.list} />
        ),
        li: ({ node, ...props }) => (
          <li {...props} className={styles.listItem} />
        ),
        // Стилизация заголовков
        h1: ({ node, ...props }) => (
          <h1 {...props} className={styles.heading1} />
        ),
        h2: ({ node, ...props }) => (
          <h2 {...props} className={styles.heading2} />
        ),
        h3: ({ node, ...props }) => (
          <h3 {...props} className={styles.heading3} />
        ),
      }}      >
        {children}
      </ReactMarkdown>
    </div>
  );
};
