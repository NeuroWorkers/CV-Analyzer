// @ts-nocheck
import { Anchor, Button } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useSelector } from 'react-redux';

import type { ICardProps } from '../../../core/types/cardTypes';
import type { RootState } from '../../../core/store';
import { ModalWindow } from '../modal/ModalWindow';
import { extractFullName, extractUsername } from '../../../core/utils/extractFunctions';

import styles from './Card.module.css';


export const CardComponent = ({ data }: ICardProps) => {
  const [opened, { open, close }] = useDisclosure(false);
  const URL = useSelector((state: RootState) => state.config.url);
  
  const truncateMarkdown = (text: string, maxLength: number): string => {
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
        <div className={styles.content}>
            <div className={styles.header}>
              {data.photo && (
                <div className={styles.imageContainer}>
                  <img src={data.photo.startsWith('http') ? data.photo : `${URL}${data.photo}`} key={data.photo} alt={data.author} className={styles.image} />
                </div>
              )}
              <div className={styles.authorInfo}>
                {data.author && !data.author.includes('собаки') && (
                  <Anchor href={`https://t.me/${extractUsername(data.author)}`} target="_blank">
                    @{extractUsername(data.author)}
                  </Anchor>
                )}
                {data.author && <h3 className={styles.author}>{extractFullName(data.author)}</h3>}
              </div>
            </div>
            <hr className={styles.divider} />
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
                {truncateMarkdown(data.text, 200)}
              </ReactMarkdown>
            </div>
            <div className={styles.footer}>
              {/* {data.date && <p className={styles.date}>{data.date}</p>} */}
              <Button className={styles.button} variant="light" color="teal" onClick={open}>
                Подробнее
              </Button>
            </div>
          </div>
      </div>
      <ModalWindow opened={opened} close={close} data={data} />
    </>
  );
};