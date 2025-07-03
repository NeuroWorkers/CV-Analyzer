import { useState, useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { fetchCards } from './core/api/api';
import { setCards, setTotalCount } from './core/store/slices/cardsSlice';
import type { RootState } from './core/store';
import { Home } from './pages/home/Home';


export const App = () => {
  const dispatch = useDispatch();
  const URL = useSelector ((state: RootState) => state.config.url);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const cards = useSelector((state: RootState) => state.cards.cards);
  const totalCount = useSelector((state: RootState) => state.cards.totalCount);
  const searchQuery = useSelector((state: RootState) => state.cards.searchQuery);

  const loadCards = useCallback(async (pageToLoad: number, query: string) => {
    setIsLoading(true)
    try {
      const { cards, totalCount } = await fetchCards(URL, pageToLoad, query);
      dispatch(setCards(cards))
      dispatch(setTotalCount(totalCount))
    } catch (error) {
      console.error('Error loading cards:', error)
      dispatch(setCards([]))
      dispatch(setTotalCount(0))
    } finally {
      setIsLoading(false)
    }
  }, [URL, dispatch])

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage)
    loadCards(newPage, searchQuery)
  }, [loadCards, searchQuery])

  useEffect(() => {
    // Загружаем карточки только при инициализации (когда нет карточек и не было загрузки)
    if (cards.length === 0 && !status && !searchQuery) {
      setStatus(true)
      loadCards(page, searchQuery)
    }
  }, [cards.length, status, searchQuery, loadCards, page])

  useEffect(() => {
    // Загружаем карточки только при изменении поискового запроса (не при инициализации)
    if (searchQuery) {
      setPage(1)
      loadCards(1, searchQuery)
    }
  }, [searchQuery, loadCards])

  return <Home 
    isLoading={isLoading} 
    page={page} 
    handlePageChange={handlePageChange} 
    totalCount={totalCount}
  />
}