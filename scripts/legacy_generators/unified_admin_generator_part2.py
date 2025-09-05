#!/usr/bin/env python3
"""
統一管理後台架構生成器 - 第二部分
TypeScript類型定義和接口
"""

class TypeDefinitionsGenerator:
    """TypeScript類型定義生成器"""
    
    def __init__(self, base_path: str):
        self.types_path = f"{base_path}/admin/types"
    
    def generate_admin_types(self) -> str:
        """生成管理後台核心類型定義"""
        return '''/**
 * 管理後台核心類型定義
 * 基於API分析結果生成的統一類型系統
 */

// 基礎響應類型
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  message?: string;
  success: boolean;
  timestamp?: string;
}

// 分頁類型
export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// 用戶管理類型
export interface User {
  id: string;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  avatar?: string;
  role: UserRole;
  status: UserStatus;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user'
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended'
}

// 系統管理類型
export interface SystemStatus {
  status: 'healthy' | 'warning' | 'error';
  uptime: number;
  version: string;
  services: ServiceStatus[];
  metrics: SystemMetrics;
}

export interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'error';
  uptime: number;
  lastCheck: string;
}

export interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    incoming: number;
    outgoing: number;
  };
}'''
    
    def generate_component_types(self) -> str:
        """生成組件相關類型"""
        return '''/**
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
}'''