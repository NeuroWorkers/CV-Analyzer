import { Alert, Text } from '@mantine/core';
import { FiSearch } from 'react-icons/fi';

import styles from './NoResultsAlert.module.css';

interface NoResultsAlertProps {
  searchQuery?: string;
}

export const NoResultsAlert = ({ searchQuery }: NoResultsAlertProps) => {
  return (
    <Alert
      icon={<FiSearch size={16} />}
      title="Ничего не найдено"
      color="gray"
      variant="light"
      className={styles.noResultsAlert}
    >
      <Text size="sm" c="dimmed" className={styles.description}>
        {searchQuery 
          ? `По запросу "${searchQuery}" не найдено ни одного результата.`
          : 'Попробуйте изменить параметры поиска или проверить правильность написания.'
        }
      </Text>
      <Text size="sm" c="dimmed" className={styles.suggestion}>
        Возможно, стоит попробовать более общие термины или сбросить фильтры.
      </Text>
    </Alert>
  );
};
