import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { ICardData } from '../../types/cardTypes';

interface CardsState {
  cards: ICardData[];
  searchQuery: string;
  totalCount: number;
}

const initialState: CardsState = {
  cards: [],
  searchQuery: '',
  totalCount: 0,
};

const cardsSlice = createSlice({
  name: 'cards',
  initialState,
  reducers: {
    setCards: (state, action: PayloadAction<ICardData[]>) => {
      state.cards = action.payload;
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    setTotalCount: (state, action: PayloadAction<number>) => {
      state.totalCount = action.payload;
    },
  },
});

export const { setCards, setSearchQuery, setTotalCount } = cardsSlice.actions;
export default cardsSlice.reducer;
