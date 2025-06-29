import { TextInput, ActionIcon } from '@mantine/core';
import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion } from 'framer-motion';
import { FiSearch } from 'react-icons/fi';

import { setSearchQuery } from '../../../core/store/slices/cardsSlice';
import type { RootState } from '../../../core/store';
import type { ISearchProps } from '../../../core/types/ui-types/searchTypes';


export const Search = ({ isLoading }: ISearchProps) => {
  const dispatch = useDispatch();
  const searchQuery = useSelector((state: RootState) => state.cards.searchQuery);
  const [inputValue, setInputValue] = useState(searchQuery);

  const handleSearch = () => {
    dispatch(setSearchQuery(inputValue));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="w-full max-w-md mx-auto mt-6"
    >
      <br />
      <TextInput
        placeholder="Поиск..."
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            handleSearch();
          }
        }}
        rightSection={
          <ActionIcon
            onClick={handleSearch}
            color="dark"
            variant="filled"
            size="lg"
            styles={{ root: { borderRadius: '0 8px 8px 0', height: '100%', transition: 'background-color 0.3s ease' } }}
            disabled={isLoading} 
          >
            <FiSearch size={20} />
          </ActionIcon>
        }
        styles={{
          input: {
            borderRadius: '8px',
            border: '1px solid #e2e8f0',
            padding: '10px 16px',
            fontSize: '16px',
            transition: 'all 0.3s ease',
            '&:focus': {
              borderColor: '#3b82f6',
              boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.1)',
            },
          },
        }}
      />

    </motion.div>
  );
};