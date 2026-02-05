import React from "react";

interface Column<T> {
    key: keyof T | string;
    header: string;
    render?: (item: T) => React.ReactNode;
    className?: string;
}

interface DataTableProps<T> {
    data: T[];
    columns: Column<T>[];
    loading?: boolean;
    emptyMessage?: string;
    onRowClick?: (item: T) => void;
    className?: string;
}

export function DataTable<T extends { id?: string }>({
    data,
    columns,
    loading = false,
    emptyMessage = "No data available",
    onRowClick,
    className = "",
}: DataTableProps<T>) {
    if (loading) {
        return (
            <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-12 bg-slate-100 rounded-lg animate-pulse" />
                ))}
            </div>
        );
    }

    if (data.length === 0) {
        return (
            <div className="text-center py-12 text-slate-500">
                <svg className="mx-auto h-12 w-12 text-slate-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p>{emptyMessage}</p>
            </div>
        );
    }

    return (
        <div className={`overflow-x-auto ${className}`}>
            <table className="w-full">
                <thead>
                    <tr className="border-b border-slate-200">
                        {columns.map((column) => (
                            <th
                                key={String(column.key)}
                                className={`px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider ${column.className || ""}`}
                            >
                                {column.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                    {data.map((item, index) => (
                        <tr
                            key={item.id || index}
                            onClick={() => onRowClick?.(item)}
                            className={`hover:bg-purple-50/60 transition-colors ${onRowClick ? "cursor-pointer" : ""}`}
                        >
                            {columns.map((column) => (
                                <td key={String(column.key)} className={`px-4 py-3 text-sm text-slate-700 ${column.className || ""}`}>
                                    {column.render
                                        ? column.render(item)
                                        : String(item[column.key as keyof T] || "-")}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}











