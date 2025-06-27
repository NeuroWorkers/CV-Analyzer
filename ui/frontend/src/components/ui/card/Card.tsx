import { Anchor, Button, Skeleton } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import styles from './Card.module.css';
import type { ICardProps } from '../../../core/types/cardTypes';
import { ModalWindow } from '../modal/ModalWindow';
import { useSelector } from 'react-redux';
import type { RootState } from '../../../core/store';

export const CardComponent = ({ data }: ICardProps) => {
  const [opened, { open, close }] = useDisclosure(false);
  const [isLoading, setIsLoading] = useState(true);
  const URL = useSelector((state: RootState) => state.config.url);
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  function extractUsername(input: string): string {
    const match = input.match(/^@([^ ]+)/);
    return match ? match[1] : '';
  }

  function extractFullName(input: string): string {
    const match = input.match(/\(([^)]+)\)/);
    return match ? match[1] : '';
  }

  // Truncate text while preserving Markdown structure
  function truncateMarkdown(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    const truncated = text.slice(0, maxLength);
    const lastPeriod = truncated.lastIndexOf('.');
    const lastNewline = truncated.lastIndexOf('\n');
    const lastIndex = Math.max(lastPeriod, lastNewline);
    return lastIndex > -1 ? truncated.slice(0, lastIndex + 1) + '...' : truncated + '...';
  }

  return (
    <>
      <div className={styles.card}>
        {isLoading ? (
          <div className={styles.skeletonContainer}>
            <Skeleton height={100} width={100} radius="md" style={{ margin: '20px' }} />
            <div className={styles.skeletonContent}>
              {/* Username */}
              <Skeleton height={16} width="30%" radius="sm" mb="0.5rem" />
              {/* Full Name */}
              <Skeleton height={20} width="50%" radius="sm" mb="0.5rem" />
              {/* Markdown Text: Paragraphs, Bold Headers, Lists */}
              <div className={styles.text}>
                {/* Paragraph */}
                <Skeleton
                  height={40}
                  width="100%"
                  radius="sm"
                  mb="0.5rem"
                  className={styles.markdownParagraph}
                />
                {/* Bold Header (e.g., **Про себя:**) */}
                <Skeleton
                  height={16}
                  width="25%"
                  radius="sm"
                  mb="0.5rem"
                  className={styles.markdownStrong}
                />
                {/* Paragraph */}
                <Skeleton
                  height={40}
                  width="100%"
                  radius="sm"
                  mb="0.5rem"
                  className={styles.markdownParagraph}
                />
                {/* Bold Header (e.g., **Про опыт:**) */}
                <Skeleton
                  height={16}
                  width="25%"
                  radius="sm"
                  mb="0.5rem"
                  className={styles.markdownStrong}
                />
                {/* List Items (e.g., 📍 items) */}
                <div className={styles.markdownList}>
                  <Skeleton
                    height={12}
                    width="80%"
                    radius="sm"
                    mb="0.25rem"
                    className={styles.markdownListItem}
                  />
                  <Skeleton
                    height={12}
                    width="85%"
                    radius="sm"
                    mb="0.25rem"
                    className={styles.markdownListItem}
                  />
                  <Skeleton
                    height={12}
                    width="75%"
                    radius="sm"
                    mb="0.25rem"
                    className={styles.markdownListItem}
                  />
                </div>
              </div>
              <div className={styles.skeletonFooter}>
                <Skeleton height={16} width="30%" radius="sm" mb="0.5rem" />
                <Skeleton height={32} width={100} radius="sm" />
              </div>
            </div>
          </div>
        ) : (
          <>
            {data.photo && (
              <div className={styles.imageContainer}>
                <img src={`${URL}/${data.photo}`} key={data.photo} alt={data.author} className={styles.image} />
              </div>
            )}
            <div className={styles.content}>
              {data.author && (
                <Anchor href={`https://t.me/${extractUsername(data.author)}`} target="_blank">
                  @{extractUsername(data.author)}
                </Anchor>
              )}
              {data.author && <h3 className={styles.author}>{extractFullName(data.author)}</h3>}
              <div className={styles.text}>
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className={styles.markdownParagraph}>{children}</p>,
                    strong: ({ children }) => <strong className={styles.markdownStrong}>{children}</strong>,
                    ul: ({ children }) => <ul className={styles.markdownList}>{children}</ul>,
                    li: ({ children }) => <li className={styles.markdownListItem}>{children}</li>,
                    a: ({ href, children }) => (
                      <a href={href} className={styles.markdownLink} target="_blank" rel="noopener noreferrer">
                        {children}
                      </a>
                    ),
                  }}
                >
                  {truncateMarkdown(data.text, 400)}
                </ReactMarkdown>
              </div>
              <div className={styles.footer}>
                {data.date && <p className={styles.date}>{data.date}</p>}
                <Button className={styles.button} variant="light" color="teal" onClick={open}>
                  Подробнее
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
      <ModalWindow opened={opened} close={close} data={data} />
    </>
  );
};