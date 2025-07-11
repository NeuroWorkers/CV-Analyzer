import {  Container, Stack, Text } from '@mantine/core';
import { useDispatch, useSelector } from 'react-redux';

import { resetSearch } from '../../core/store/slices/cardsSlice';
import { Pagination, Search, Loader } from '../../components/ui';
import { CardsGrid } from '../../components/smart';
import type { IHomeProps } from '../../core/types/pages-types/homeTypes';
import type { RootState } from '../../core/store';

import { useState } from 'react'; 

export const Home = ({ 
  isLoading, 
  page, 
  handlePageChange, 
  totalCount 
}: IHomeProps) => {
  const dispatch = useDispatch();
  const searchQuery = useSelector((state: RootState) => state.cards.searchQuery);
  
  const [clearSignal, setClearSignal] = useState(false); 

  const handleResetSearch = () => {
    dispatch(resetSearch());
    setClearSignal(true); 
    setTimeout(() => setClearSignal(false), 100); 
  };

  // Определяем, выполняется ли поиск
  const isSearchMode = searchQuery && searchQuery.trim().length > 0;

  return (
    <Container style={{ position: 'relative' }}>
      <Stack>
        <Search isLoading={isLoading} clearSignal={clearSignal} handleResetSearch={handleResetSearch}/>
        
        {/* Показываем пагинацию только если не в режиме поиска */}
        {!isSearchMode && (
          <Pagination
            total={Math.ceil(totalCount / 6)}
            page={page}
            onChange={handlePageChange}
          />
        )}
        
        {/* Показываем количество найденных записей при поиске */}
        {isSearchMode && totalCount > 0 && (
          <Text ta="center" size="sm" c="dimmed">
            Найдено {totalCount} {totalCount === 1 ? 'запись' : totalCount < 5 ? 'записи' : 'записей'}
          </Text>
        )}
     
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
          <CardsGrid isLoading={isLoading} />
          <br />
        </div>
      </Stack>
    </Container>
  );
};

