import type { ReactNode } from 'react';

export interface Column<T> {
  key: string;
  label: string;
  align?: 'left' | 'center' | 'right';
  width?: string;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  caption?: string;
  emptyState?: ReactNode;
}

export default function DataTable<T>({ columns, data, keyExtractor, caption, emptyState }: DataTableProps<T>) {
  if (data.length === 0 && emptyState) {
    return <>{emptyState}</>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full table-fixed border-collapse">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr className="bg-gray-50 border-b-[1px] border-gray-100">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={`h-9 px-3 text-caption font-medium text-gray-600 uppercase tracking-[0.05em] ${
                  col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
                }`}
                style={col.width ? { width: col.width } : undefined}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              className="bg-white border-b-[0.5px] border-gray-100 hover:bg-gray-50 transition-colors duration-150 group"
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`h-11 px-3 text-body text-gray-800 truncate ${
                    col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
                  }`}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
