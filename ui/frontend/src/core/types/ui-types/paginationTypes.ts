export interface IPaginationProps {
  total: number
  page: number
  onChange: (page: number) => void
}