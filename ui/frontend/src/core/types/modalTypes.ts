import type { ICardData } from "./cardTypes";

export interface IModalProps {
  opened: boolean;
  close: () => void;
  data: ICardData;
}