import { SimpleGrid } from '@mantine/core';
import { useSelector } from 'react-redux';

import type { RootState } from '../../../core/store';
import { CardComponent, NoResultsAlert } from '../../ui';

interface CardsGridProps {
  isLoading?: boolean;
  onGoToHome?: () => void;
}

export const CardsGrid = ({ isLoading = false, onGoToHome }: CardsGridProps) => {
  const cards = useSelector((state: RootState) => state.cards.cards);
  const searchQuery = useSelector((state: RootState) => state.cards.searchQuery);
  
  // Не показываем "Ничего не найдено" во время загрузки
  if (!isLoading && cards.length === 0) {
    return <NoResultsAlert searchQuery={searchQuery} onGoToHome={onGoToHome} />;
  }
  
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