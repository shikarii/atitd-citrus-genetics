import { useState, useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";

interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  defaultSort?: SortingState;
  filterPlaceholder?: string;
  downloadFilename?: string;
}

export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  defaultSort = [],
  filterPlaceholder = "Filter...",
  downloadFilename,
}: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>(defaultSort);
  const [globalFilter, setGlobalFilter] = useState("");

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const csvContent = useMemo(() => {
    if (!downloadFilename) return null;
    const headers = columns.map((c) => (c as { header?: string }).header ?? (c as { accessorKey?: string }).accessorKey ?? "");
    const rows = data.map((row) =>
      columns.map((c) => {
        const key = (c as { accessorKey?: string }).accessorKey;
        if (!key) return "";
        const val = row[key];
        if (val === null || val === undefined) return "";
        if (typeof val === "string") return val;
        if (typeof val === "number" || typeof val === "boolean") return String(val);
        if (typeof val === "object") return JSON.stringify(val);
        return "";
      }),
    );
    return [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  }, [data, columns, downloadFilename]);

  return (
    <div>
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:justify-between mb-3">
        <input
          type="text"
          value={globalFilter}
          onChange={(e) => { setGlobalFilter(e.target.value); }}
          placeholder={filterPlaceholder}
          className="px-3 py-1.5 text-sm border border-slate-300 dark:border-neutral-600 dark:bg-neutral-800 dark:text-neutral-200 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 dark:focus:ring-neutral-400 focus:border-transparent w-full sm:w-64"
        />
        {csvContent && downloadFilename && (
          <a
            href={`data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`}
            download={downloadFilename}
            className="text-sm text-teal-600 hover:text-teal-700 dark:text-neutral-400 dark:hover:text-neutral-200 font-medium"
          >
            Download CSV
          </a>
        )}
      </div>

      <div className="scroll-shadow-x">
        <div className="overflow-x-auto border border-slate-200 dark:border-neutral-700 rounded-lg">
          <table className="w-full text-sm">
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id} className="bg-slate-50 dark:bg-neutral-800 border-b border-slate-200 dark:border-neutral-700">
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-2 py-1.5 sm:px-3 sm:py-2 text-left font-semibold text-slate-700 dark:text-neutral-300 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-neutral-700 whitespace-nowrap"
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {{ asc: " \u2191", desc: " \u2193" }[header.column.getIsSorted() as string] ?? ""}
                      </div>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="border-b border-slate-100 dark:border-neutral-700 hover:bg-slate-50 dark:hover:bg-neutral-750 dark:hover:bg-neutral-700/50">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-2 py-1.5 sm:px-3 sm:py-2 text-slate-700 dark:text-neutral-300 whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-2 text-xs text-slate-400 dark:text-neutral-500">
        {table.getFilteredRowModel().rows.length} of {data.length} rows
      </div>
    </div>
  );
}
