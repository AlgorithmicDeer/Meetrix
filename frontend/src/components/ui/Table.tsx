/**
 * Kawaii-Brutalism Table component.
 */

import { ReactNode } from 'react';

interface TableProps {
  children: ReactNode;
  className?: string;
}

export function Table({ children, className = '' }: TableProps) {
  return (
    <table className={`w-full border-3 border-kb-black ${className}`}>
      {children}
    </table>
  );
}

interface TableHeaderProps {
  children: ReactNode;
}

export function TableHeader({ children }: TableHeaderProps) {
  return (
    <thead className="bg-kb-black text-kb-white">
      {children}
    </thead>
  );
}

interface TableBodyProps {
  children: ReactNode;
}

export function TableBody({ children }: TableBodyProps) {
  return <tbody>{children}</tbody>;
}

interface TableRowProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export function TableRow({ children, className = '', onClick }: TableRowProps) {
  return (
    <tr
      className={`border-b-2 border-kb-black bg-kb-white even:bg-kb-muted ${
        onClick ? 'cursor-pointer hover:bg-kb-lavender transition-colors duration-75' : ''
      } ${className}`}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

interface TableHeadProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export function TableHead({ children, className = '', onClick }: TableHeadProps) {
  return (
    <th
      className={`border-r-2 border-kb-white px-4 py-3 font-mono font-bold text-xs uppercase tracking-widest text-left ${
        onClick ? 'cursor-pointer hover:bg-kb-white hover:text-kb-black transition-colors duration-75' : ''
      } ${className}`}
      onClick={onClick}
    >
      {children}
    </th>
  );
}

interface TableCellProps {
  children: ReactNode;
  className?: string;
}

export function TableCell({ children, className = '' }: TableCellProps) {
  return (
    <td className={`border-r-2 border-kb-black px-4 py-3 font-sans text-sm ${className}`}>
      {children}
    </td>
  );
}

// Made with Bob
