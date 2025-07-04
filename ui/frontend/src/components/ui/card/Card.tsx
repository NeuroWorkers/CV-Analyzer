import { Anchor, Button } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useSelector } from 'react-redux';

import type { ICardProps } from '../../../core/types/ui-types/cardTypes';
import type { RootState } from '../../../core/store';
import { ModalWindow } from '../modal/ModalWindow';
import { extractFullName, extractUsername } from '../../../core/utils/extractFunctions';
import { truncateMarkdownByWords } from '../../../core/utils/truncateUtils';
import { HighlightWithMarkdown } from '../hightlight/HighlightWithMarkdown';
import { MarkdownRenderer } from '../markdown/MarkdownRenderer';

import styles from './Card.module.css';


export const CardComponent = ({ data }: ICardProps) => {
  const [opened, { open, close }] = useDisclosure(false);
  const URL = useSelector((state: RootState) => state.config.url);
  
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
                    {extractUsername(data.author)}
                  </Anchor>
                )}
                {data.author && <h3 className={styles.author}>{extractFullName(data.author)}</h3>}
              </div>
            </div>
            <hr className={styles.divider} />
            <div className={styles.text}>
              {data.highlight_text ? (
                <div className={styles.markdownParagraph}>
                  <HighlightWithMarkdown 
                    text={truncateMarkdownByWords(data.text ?? '', 50)} 
                    highlights={data.highlight_text} 
                  />
                </div>
              ) : (
                <MarkdownRenderer className={styles.markdownParagraph}>
                  {truncateMarkdownByWords(data.text, 50)}
                </MarkdownRenderer>
              )}
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