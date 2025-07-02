// @ts-nocheck
import { Modal } from '@mantine/core';
import { useSelector } from 'react-redux';

import type { IModalProps } from '../../../core/types/ui-types/modalTypes';
import type { RootState } from '../../../core/store';
import { extractFullName, extractUsername } from '../../../core/utils/extractFunctions';
import { Highlight } from '../hightlight/Hightlight';
import { HighlightWithMarkdown } from '../hightlight/HighlightWithMarkdown';
import { MarkdownRenderer } from '../markdown/MarkdownRenderer';

import styles from './ModalWindow.module.css';


export const ModalWindow = ({ opened, close, data }: IModalProps) => {
  const URL = useSelector((state: RootState) => state.config.url);
  console.log(data.text)
  return (
    <Modal
      opened={opened}
      onClose={close}
      title={
        <div className={styles.title}>
          {data.author && (
            <a
              href={`https://t.me/${extractUsername(data.author)}`}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.authorLink}
            >
              {extractUsername(data.author)}
            </a>
          )}
        </div>
      }
      centered
      transitionProps={{
        transition: 'fade',
        duration: 300,
        timingFunction: 'ease-in-out',
      }}
      overlayProps={{
        opacity: 0.55,
        blur: 3,
      }}
    >
      <div className={styles.content}>
        {data.photo && (
          <>
            <img
              src={data.photo.startsWith('http') ? data.photo : `${URL}${data.photo}`}
              alt={data.author}
              className={styles.image}
            />
            <span className={styles.authorName}>{extractFullName(data.author)}</span>
          </>
        )}
        <div className={styles.text}>
          {data.highlightText ? (
            <div className={styles.markdownParagraph}>
              <HighlightWithMarkdown 
                text={data.text ?? ''} 
                highlights={data.highlightText} 
              />
            </div>
          ) : (
            <MarkdownRenderer className={styles.markdownParagraph}>
              {data.text}
            </MarkdownRenderer>
          )}
        </div>
        {data.date && (
          <p className={styles.date}>
            <strong>Дата:</strong> {data.date}
          </p>
        )}
      </div>
    </Modal>
  );
};