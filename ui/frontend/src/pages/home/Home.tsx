import { Container, Stack } from '@mantine/core';

import { Pagination, Search } from '../../components/ui';
import {Loader} from '../../components/ui';
import { CardsGrid } from '../../components/smart';
import type { IHomeProps } from '../../core/types/pages-types/homeTypes';


export const Home = ({ 
  isLoading, 
  page, 
  handlePageChange, 
  totalCount 
}: IHomeProps) => {
  return <Container style={{ position: 'relative' }}>
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
}