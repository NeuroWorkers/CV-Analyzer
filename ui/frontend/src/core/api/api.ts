// @ts-nocheck
import type { ICardData } from '../types/ui-types/cardTypes';

export const fetchCards = async (url: string, pageNum: number, search: string): Promise<{ cards: ICardData[]; totalCount: number }> => {
  try {
    const endpoint = search
      ? `${url}/get_relevant_nodes/${encodeURIComponent(search)}/${pageNum}`
      : `${url}/get_all_nodes/${pageNum}`;

    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}, message: ${await response.text()}`);
    }

    const rawData: any[] = await response.json();

    const cards = rawData.filter((item, index) => index !== rawData.length - 1 || !('count' in item));
    const totalCount = rawData[rawData.length - 1]?.count ?? 0;
    
    const data = cards.map((card) => ({
      author: card.author ?? 'N/A',
      text: card.text ?? 'No content available.',
      highlight_text: card.highlight_text ?? null,
      photo: card.photo ? `${card.photo}` : 'https://i0.wp.com/zblibrary.info/wp-content/uploads/sites/76/2017/03/default-user.png',
      date: card.date ?? new Date().toISOString(),
    }));

    return { cards: data, totalCount };
  } catch (error) {
    console.error('Fetch error:', error);
    return { cards: [], totalCount: 0 };
  }
};