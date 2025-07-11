import type { ICardData } from '../types/ui-types/cardTypes';
import { getSessionId } from '../utils/session';

interface RawDataItem {
  count?: number;
  [key: string]: unknown;
}

interface ApiResponse {
  data: RawDataItem[];
  count: number;
  highlight_text?: string[][];
}

export const fetchCards = async (url: string, pageNum: number, search: string): Promise<{ cards: ICardData[]; totalCount: number; error?: string }> => {
  try {
    const sessionId = getSessionId();
    const endpoint = search
      ? `${url}/get_relevant_nodes/${sessionId}/${encodeURIComponent(search)}`
      : `${url}/get_all_nodes/${sessionId}/${pageNum}`;

    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}, message: ${await response.text()}`);
    }

    const responseData: ApiResponse = await response.json();

    // Если ответ содержит структуру с data и highlight_text массивами
    if (responseData.data && Array.isArray(responseData.data)) {
      const cards = responseData.data;
      const totalCount = responseData.count ?? 0;
      
      const data: ICardData[] = cards.map((card) => ({
        author: String(card.author ?? 'N/A'),
        text: String(card.text ?? 'No content available.'),
        highlight_text: Array.isArray(card.hl) ? card.hl : (card.hl ? [String(card.hl)] : null),
        photo: card.photo ? `${card.photo}` : 'https://i0.wp.com/zblibrary.info/wp-content/uploads/sites/76/2017/03/default-user.png',
        date: String(card.date ?? new Date().toISOString()),
      }));

      return { cards: data, totalCount };
    } else {
      // Для обратной совместимости с предыдущим форматом
      const rawData: RawDataItem[] = responseData as any;
      const cards = rawData.filter((item, index) => index !== rawData.length - 1 || !('count' in item));
      const totalCount = rawData[rawData.length - 1]?.count ?? 0;
      
      const data: ICardData[] = cards.map((card) => ({
        author: String(card.author ?? 'N/A'),
        text: String(card.text ?? 'No content available.'),
        highlight_text: card.highlight_text ? String(card.highlight_text) : null,
        photo: card.photo ? `${card.photo}` : 'https://i0.wp.com/zblibrary.info/wp-content/uploads/sites/76/2017/03/default-user.png',
        date: String(card.date ?? new Date().toISOString()),
      }));

      return { cards: data, totalCount };
    }
  } catch (error) {
    console.error('Fetch error:', error);
    
    // Определяем тип ошибки
    let errorMessage = 'Неизвестная ошибка';
    if (error instanceof TypeError && error.message.includes('fetch')) {
      errorMessage = 'Ошибка соединения с сервером';
    } else if (error instanceof Error) {
      errorMessage = error.message;
    }
    
    return { cards: [], totalCount: 0, error: errorMessage };
  }
};