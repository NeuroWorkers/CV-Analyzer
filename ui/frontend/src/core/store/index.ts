import { configureStore } from '@reduxjs/toolkit';
import cardsReducer from './slices/cardsSlice';
import configReducer from './slices/initSlice';

export const store = configureStore({
  reducer: {
    cards: cardsReducer,
    config: configReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;