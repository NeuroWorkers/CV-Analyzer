export const extractUsername = (input: string): string => {
  const match = input.match(/^@(\S+)/);
  return match ? `@${match[1]}` : '';
}

export const extractFullName = (input: string): string => {
  const withoutUsername = input.replace(/^@\S+\s*/, '');
  return withoutUsername.trim();
}
