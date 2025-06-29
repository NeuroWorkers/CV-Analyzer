export const extractUsername = (input: string): string => {
  const match = input.match(/^@([^ ]+)/);
  return match ? match[1] : '';
}

export const extractFullName = (input: string): string => {
  const match = input.match(/\(([^)]+)\)/);
  return match ? match[1] : '';
}