export const extractUsername = (input: string): string => {
  const match = input.match(/^@(\S+)/);
  return match ? `@${match[1]}` : '';
}

export const extractUsernameWithoutAt = (input: string): string => {
  const match = input.match(/^@(\S+)/);
  return match ? match[1] : '';
}

export const extractFullName = (input: string): string => {
  const withoutUsername = input.replace(/^@\S+\s*/, '');
  return withoutUsername.trim();
}

export const extractTextFromMarkdownLink = (input: string): string => {
  // Извлекаем текст из markdown ссылки [текст](url)
  const match = input.match(/\[([^\]]+)\]/);
  return match ? match[1] : input;
}

export const extractHighlightTexts = (highlight: string): string[] => {
  // Если это markdown ссылка, извлекаем из неё текст
  if (highlight.includes('[') && highlight.includes(']')) {
    const linkText = extractTextFromMarkdownLink(highlight);
    // Возвращаем только текст внутри ссылки для подсветки
    return [linkText];
  }
  return [highlight];
}
