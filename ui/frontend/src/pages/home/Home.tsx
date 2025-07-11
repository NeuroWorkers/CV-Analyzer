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
  const connectionError = useSelector((state: RootState) => state.cards.connectionError);
  
  const [clearSignal, setClearSignal] = useState(false); 

  const handleResetSearch = () => {
    dispatch(resetSearch());
    setClearSignal(true); 
    setTimeout(() => setClearSignal(false), 100); 
  };

  const handleGoToHome = () => {
    // Сбрасываем поиск и возвращаемся к первой странице
    dispatch(resetSearch());
    handlePageChange(1);
  };

  // Определяем, выполняется ли поиск
  const isSearchMode = searchQuery && searchQuery.trim().length > 0;

  return (
    <Container style={{ position: 'relative' }}>
      <Stack>
        <Search isLoading={isLoading} clearSignal={clearSignal} handleResetSearch={handleResetSearch}/>
        
        {/* Показываем ошибку соединения */}
        {connectionError && (
          <Text ta="center" size="md" c="red" style={{ 
            padding: '20px', 
            border: '1px solid #ff6b6b', 
            borderRadius: '8px', 
            backgroundColor: '#ffe0e0' 
          }}>
            ❌ Ошибка соединения с сервером. Проверьте подключение к интернету и попробуйте снова.
          </Text>
        )}
        
        {/* Показываем количество найденных записей при поиске и без ошибки соединения */}
        {isSearchMode && totalCount > 0 && !connectionError && (
          <Text ta="center" size="sm" c="dimmed">
            Найдено {totalCount} {totalCount === 1 ? 'запись' : totalCount < 5 ? 'записи' : 'записей'}
          </Text>
        )}
     
        {isLoading && !connectionError && (
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
            display: connectionError ? 'none' : 'block',
          }}
        >
          <CardsGrid isLoading={isLoading} onGoToHome={handleGoToHome} />
          <br />
          
          {/* Показываем пагинацию только если не в режиме поиска и нет ошибки соединения */}
          {!isSearchMode && !connectionError && (
            <Pagination
              total={Math.ceil(totalCount / 6)}
              page={page}
              onChange={handlePageChange}
            />
          )}
          
          <br />
        </div>
      </Stack>
    </Container>
  );
};

