import { Pagination as MantinePagination } from '@mantine/core';

export const Pagination = ({ total, page, onChange }: { total: number; page: number; onChange: (page: number) => void }) => (
  <div style={{ display: 'flex', justifyContent: 'center' }}>
    <MantinePagination 
      total={total} 
      color="black" 
      value={page} 
      onChange={onChange} />
  </div>
);