import { Pagination as MantinePagination } from '@mantine/core';

import type { IPaginationProps } from '../../../core/types/ui-types/paginationTypes';


export const Pagination = ({ total, page, onChange }: IPaginationProps) => (
  <div style={{ display: 'flex', justifyContent: 'center' }}>
    <MantinePagination 
      total={total} 
      color="black" 
      value={page} 
      onChange={onChange} />
  </div>
);