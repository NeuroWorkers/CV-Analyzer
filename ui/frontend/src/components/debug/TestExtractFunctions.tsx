import { extractHighlightTexts, extractTextFromMarkdownLink } from '../../core/utils/extractFunctions';

// Тест функций извлечения текста
console.log('=== Тест функций извлечения текста ===');

console.log('Тест 1: [REG.RU](https://reg.ru/)');
console.log('Результат:', extractHighlightTexts('[REG.RU](https://reg.ru/)'));

console.log('\nТест 2: обычный текст');
console.log('Результат:', extractHighlightTexts('обычный текст'));

console.log('\nТест 3: extractTextFromMarkdownLink');
console.log('Результат:', extractTextFromMarkdownLink('[REG.RU](https://reg.ru/)'));

console.log('\nТест 4: [REG.RU](https://reg.ru/);');
console.log('Результат:', extractHighlightTexts('[REG.RU](https://reg.ru/);'));

console.log('\nТест 5: короткое слово AI');
console.log('Результат:', extractHighlightTexts('AI'));

console.log('\nТест 6: короткое слово IT');
console.log('Результат:', extractHighlightTexts('IT'));

export {};
