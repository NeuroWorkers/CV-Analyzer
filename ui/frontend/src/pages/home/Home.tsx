import {  Container, Stack } from '@mantine/core';
import { useDispatch } from 'react-redux';

import { resetSearch } from '../../core/store/slices/cardsSlice';
import { Pagination, Search, Loader } from '../../components/ui';
import { CardsGrid } from '../../components/smart';
import type { IHomeProps } from '../../core/types/pages-types/homeTypes';

import { useState } from 'react'; 

export const Home = ({ 
  isLoading, 
  page, 
  handlePageChange, 
  totalCount 
}: IHomeProps) => {
  const dispatch = useDispatch();
  
  const [clearSignal, setClearSignal] = useState(false); 

  const handleResetSearch = () => {
    dispatch(resetSearch());
    setClearSignal(true); 
    setTimeout(() => setClearSignal(false), 100); 
  };

  return (
    <Container style={{ position: 'relative' }}>
      <Stack>
        
        <Search isLoading={isLoading} clearSignal={clearSignal} handleResetSearch={handleResetSearch}/>
     
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
          <Pagination
            total={Math.ceil(totalCount / 6)}
            page={page}
            onChange={handlePageChange}
          />
          <br />
        </div>
      </Stack>
    </Container>
  );
};

