export interface ICardData {
  author: string;
  text: string;
  date?: string;
  highlight_text?: string | string[] | null;
  photo?: string;
}

export interface CardsState {
  cards: ICardData[];
  searchQuery: string;
  totalCount: number;
  connectionError: boolean;
}

export interface ICardProps {
  data: ICardData;
}