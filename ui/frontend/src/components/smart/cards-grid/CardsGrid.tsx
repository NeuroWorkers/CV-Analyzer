import { SimpleGrid } from '@mantine/core';
import { useSelector } from 'react-redux';

import type { RootState } from '../../../core/store';
import { CardComponent } from '../../ui';


export const CardsGrid = () => {
  const cards = useSelector((state: RootState) => state.cards.cards);
  return (
    <SimpleGrid
      cols={{ base: 1, sm: 2, md: 2 }}
      spacing={{ base: 'sm', sm: 'lg' }}
    >
      {cards.map((card, index) => 
        <CardComponent key={index} data={card} />
      )}
    </SimpleGrid>
  );
};