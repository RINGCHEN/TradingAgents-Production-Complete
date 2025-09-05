/**
 * 組件相關類型定義
 */

// 通用組件屬性
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
  loading?: boolean;
  error?: string | null;
}

// 表格組件類型
export interface TableColumn<T = any> {
  key: keyof T | string;
  title: string;
  dataIndex?: keyof T;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  width?: number | string;
}

export interface TableProps<T = any> extends BaseComponentProps {
  columns: TableColumn<T>[];
  dataSource: T[];
  pagination?: PaginationParams;
  onPaginationChange?: (pagination: PaginationParams) => void;
  rowKey?: keyof T | ((record: T) => string);
  selection?: {
    selectedRowKeys: string[];
    onChange: (selectedRowKeys: string[]) => void;
  };
}

// 表單組件類型
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'date' | 'checkbox';
  required?: boolean;
  placeholder?: string;
  options?: { label: string; value: any }[];
  validation?: {
    pattern?: RegExp;
    min?: number;
    max?: number;
    message?: string;
  };
}

export interface FormProps extends BaseComponentProps {
  fields: FormField[];
  initialValues?: Record<string, any>;
  onSubmit: (values: Record<string, any>) => void;
  submitText?: string;
  resetText?: string;
}