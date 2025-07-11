import { Alert, Text, Button, Group } from '@mantine/core';
import { FiSearch, FiHome } from 'react-icons/fi';

import styles from './NoResultsAlert.module.css';

interface NoResultsAlertProps {
  searchQuery?: string;
  onGoToHome?: () => void;
}

export const NoResultsAlert = ({ searchQuery, onGoToHome }: NoResultsAlertProps) => {
  // Если поисковый запрос пустой, значит поиск был отменен
  const isSearchCancelled = !searchQuery || searchQuery.trim().length === 0;
  
  return (
    <Alert
      icon={<FiSearch size={16} />}
      title={isSearchCancelled ? "Поиск отменен" : "Ничего не найдено"}
      color={isSearchCancelled ? "blue" : "gray"}
      variant="light"
      className={styles.noResultsAlert}
    >
      <Text size="sm" c="dimmed" className={styles.description}>
        {isSearchCancelled 
          ? 'Введите поисковый запрос или перейдите на главную страницу для просмотра всех записей.'
          : `По запросу "${searchQuery}" не найдено ни одного результата.`
        }
      </Text>
      {!isSearchCancelled && (
        <Text size="sm" c="dimmed" className={styles.suggestion}>
          Возможно, стоит попробовать более общие термины или сбросить фильтры.
        </Text>
      )}
      {isSearchCancelled && onGoToHome && (
        <Group mt="md">
          <Button 
            variant="light" 
            leftSection={<FiHome size={16} />}
            onClick={onGoToHome}
          >
            Перейти на главную
          </Button>
        </Group>
      )}
    </Alert>
  );
};
