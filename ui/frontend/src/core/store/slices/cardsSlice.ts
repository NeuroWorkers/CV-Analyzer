import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { CardsState, ICardData } from '../../types/ui-types/cardTypes';

const initialState: CardsState = {
  cards: [],
  searchQuery: '',
  totalCount: 0,
  connectionError: false,
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
    resetSearch: () => initialState,
    setTotalCount: (state, action: PayloadAction<number>) => {
      state.totalCount = action.payload;
    },
    setConnectionError: (state, action: PayloadAction<boolean>) => {
      state.connectionError = action.payload;
    },
  },
});

export const { setCards, setSearchQuery, resetSearch, setTotalCount, setConnectionError } = cardsSlice.actions;
export default cardsSlice.reducer;
