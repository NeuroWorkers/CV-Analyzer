export interface ICardData {
  author: string;
  text: string;
  date?: string;
  highlightText?: string[] | null;
  photo?: string;
}

export interface CardsState {
  cards: ICardData[];
  searchQuery: string;
  totalCount: number;
}

export interface ICardProps {
  data: ICardData;
}