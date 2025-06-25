import { Container, Stack } from '@mantine/core';
import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchCards } from './core/api/api';
import { Pagination, Search } from './components/ui';
import { CardsGrid } from './components/smart/cards-grid/CardsGrid';
import { setCards, setTotalCount } from './core/store/slices/cardsSlice';
import type { RootState } from './core/store';
import {Loader} from './components/ui/loader/Loader';


export const App = () => {
  const dispatch = useDispatch();
  const URL = useSelector ((state: RootState) => state.config.url);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const cards = useSelector((state: RootState) => state.cards.cards);
  const totalCount = useSelector((state: RootState) => state.cards.totalCount);
  const searchQuery = useSelector((state: RootState) => state.cards.searchQuery);

  const loadCards = async (pageToLoad: number, query: string) => {
    setIsLoading(true);
    try {
      const { cards, totalCount } = await fetchCards(URL, pageToLoad, query);
      dispatch(setCards(cards));
      dispatch(setTotalCount(totalCount));
    } catch (error) {
      console.error('Error loading cards:', error);
      dispatch(setCards([]));
      dispatch(setTotalCount(0));
    } finally {
      setIsLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    loadCards(newPage, searchQuery);
  };

  useEffect(() => {
    if (cards.length === 0 && !status) {
      setStatus(true);
      loadCards(page, searchQuery);
    }
  }, [cards.length, status]);

  useEffect(() => {
    setPage(1);
    loadCards(1, searchQuery);
  }, [searchQuery]);

  return (
    <Container style={{ position: 'relative' }}>
      <Stack>
        <Search isLoading={isLoading} />
        {isLoading && (
          <Loader
            color="lime"
            size="md"
            style={{ alignSelf: 'center' }}
          />
        )}
        <div
          style={{
            transition: 'filter 0.3s ease',
            filter: isLoading ? 'blur(4px)' : 'none',
          }}
        >
          <CardsGrid />
          <br/>
          <Pagination
            total={Math.ceil(totalCount / 6)}
            page={page}
            onChange={handlePageChange}
          />
           <br/>
        </div>
      </Stack>
    </Container>
  );
};