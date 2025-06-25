export interface ICardData {
  author: string;
  text: string;
  date?: string;
  photo?: string;
}

export interface ICardProps {
  data: ICardData;
}