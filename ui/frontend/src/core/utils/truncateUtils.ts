import { marked } from 'marked';
import DOMPurify from 'dompurify';

/**
 * Обрезает markdown текст, сохраняя структуру и не показывая HTML теги
 * @param text - исходный markdown текст
 * @param maxLength - максимальная длина текста в символах
 * @returns обрезанный текст без видимых HTML тегов
 */
export const truncateMarkdown = (text: string, maxLength: number): string => {
  if (!text) return '';
  
  // Если текст короче максимальной длины, возвращаем как есть
  if (text.length <= maxLength) return text;

  try {
    // Сначала конвертируем markdown в HTML
    marked.setOptions({
      breaks: true,
      gfm: true,
    });

    const rawHtml = marked.parse(text, { async: false }) as string;
    
    // Очищаем HTML
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
      ALLOWED_TAGS: [
        'p', 'br', 'strong', 'em', 'b', 'i', 'u', 's', 
        'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'code', 'pre'
      ],
      ALLOWED_ATTR: ['href', 'target', 'rel'],
    });

    // Создаем временный элемент для извлечения только текста
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = cleanHtml;
    const plainText = tempDiv.textContent || tempDiv.innerText || '';

    // Обрезаем только текст без тегов
    if (plainText.length <= maxLength) {
      return text; // Возвращаем исходный markdown, если текст помещается
    }

    // Находим подходящее место для обрезки
    let truncatedText = plainText.slice(0, maxLength);
    
    // Пытаемся обрезать по предложению
    const lastPeriod = truncatedText.lastIndexOf('.');
    const lastNewline = truncatedText.lastIndexOf('\n');
    const lastSpace = truncatedText.lastIndexOf(' ');
    
    // Выбираем лучшее место для обрезки
    const cutPoints = [lastPeriod, lastNewline, lastSpace].filter(point => point > maxLength * 0.7);
    const bestCutPoint = Math.max(...cutPoints);
    
    if (bestCutPoint > 0) {
      truncatedText = truncatedText.slice(0, bestCutPoint);
    }

    // Теперь пытаемся найти соответствующий кусок в исходном markdown
    // Это приблизительная логика, которая пытается сохранить структуру
    const words = truncatedText.split(' ');
    const targetLength = words.length;
    
    // Разбиваем исходный текст на слова и берем нужное количество
    const originalWords = text.split(' ');
    if (originalWords.length > targetLength) {
      const truncatedMarkdown = originalWords.slice(0, targetLength).join(' ');
      return truncatedMarkdown + '...';
    }

    return truncatedText + '...';
    
  } catch (error) {
    console.error('Error truncating markdown:', error);
    
    // Fallback: простая обрезка по словам
    const words = text.split(' ');
    if (words.length > 30) {
      return words.slice(0, 30).join(' ') + '...';
    }
    
    return text;
  }
};

/**
 * Более простая и безопасная версия - обрезает markdown по словам, избегая разрыва тегов
 * @param text - исходный markdown текст
 * @param maxWords - максимальное количество слов
 * @returns обрезанный текст
 */
export const truncateMarkdownByWords = (text: string, maxWords: number): string => {
  if (!text) return '';
  
  // Удаляем лишние пробелы и переносы строк
  const cleanText = text.replace(/\s+/g, ' ').trim();
  
  const words = cleanText.split(' ');
  if (words.length <= maxWords) return cleanText;
  
  // Берем первые maxWords слов
  let truncated = words.slice(0, maxWords).join(' ');
  
  // Проверяем балансировку основных markdown тегов
  const markdownTags = [
    { open: /\*\*/g, close: /\*\*/g, name: 'bold' },
    { open: /(?<!\*)\*(?!\*)/g, close: /(?<!\*)\*(?!\*)/g, name: 'italic' },
    { open: /`/g, close: /`/g, name: 'code' },
    { open: /\[/g, close: /\]/g, name: 'link' },
    { open: /~/g, close: /~/g, name: 'strike' }
  ];
  
  let hasUnbalancedTags = false;
  
  for (const tag of markdownTags) {
    const openMatches = (truncated.match(tag.open) || []).length;
    const closeMatches = (truncated.match(tag.close) || []).length;
    
    // Для парных тегов проверяем четность
    if (tag.name === 'bold' || tag.name === 'italic' || tag.name === 'code' || tag.name === 'strike') {
      if (openMatches % 2 !== 0) {
        hasUnbalancedTags = true;
        break;
      }
    }
    // Для ссылок проверяем соответствие открывающих и закрывающих скобок
    else if (tag.name === 'link') {
      if (openMatches !== closeMatches) {
        hasUnbalancedTags = true;
        break;
      }
    }
  }
  
  // Если есть несбалансированные теги, ищем безопасное место для обрезки
  if (hasUnbalancedTags) {
    // Ищем последний полный абзац или предложение
    const lastPeriod = truncated.lastIndexOf('.');
    const lastNewline = truncated.lastIndexOf('\n');
    const lastExclamation = truncated.lastIndexOf('!');
    const lastQuestion = truncated.lastIndexOf('?');
    
    const safeCutPoints = [lastPeriod, lastNewline, lastExclamation, lastQuestion]
      .filter(point => point > truncated.length * 0.6);
    
    if (safeCutPoints.length > 0) {
      const bestCutPoint = Math.max(...safeCutPoints);
      truncated = truncated.slice(0, bestCutPoint + 1);
    } else {
      // Если не можем найти безопасное место, обрезаем по словам более агрессивно
      const safeWords = words.slice(0, Math.floor(maxWords * 0.8));
      truncated = safeWords.join(' ');
    }
  }
  
  return truncated.trim() + '...';
};
