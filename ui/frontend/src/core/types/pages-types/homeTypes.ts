export interface IHomeProps {
  isLoading: boolean;
  page: number;
  handlePageChange: (page: number) => void;
  totalCount: number;
}