"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

function buildPageItems(current, total) {
  if (total <= 7) {
    return Array.from({ length: total }, (_, index) => index + 1);
  }

  const candidates = new Set([1, total, current - 1, current, current + 1]);
  const sorted = [...candidates]
    .filter((page) => page >= 1 && page <= total)
    .sort((a, b) => a - b);

  const items = [];
  let previous = 0;
  for (const page of sorted) {
    if (page - previous > 1) items.push("ellipsis");
    items.push(page);
    previous = page;
  }
  return items;
}

export default function JobPagination({ page = 1, totalPages = 1, onPageChange }) {
  if (!totalPages || totalPages <= 1) return null;

  const items = buildPageItems(page, totalPages);

  const go = (target) => {
    if (target >= 1 && target <= totalPages && target !== page) {
      onPageChange?.(target);
    }
  };

  const buttonClass =
    "inline-flex h-9 w-9 items-center justify-center rounded-md text-sm font-medium transition-colors";

  return (
    <nav
      aria-label="Jobs pagination"
      className="mt-8 flex items-center justify-center gap-1.5"
    >
      <button
        type="button"
        aria-label="Previous page"
        disabled={page <= 1}
        onClick={() => go(page - 1)}
        className={`${buttonClass} border border-line bg-surface text-navy hover:bg-elevated disabled:cursor-not-allowed disabled:opacity-40`}
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      {items.map((item, index) =>
        item === "ellipsis" ? (
          <span
            key={`ellipsis-${index}`}
            aria-hidden="true"
            className="inline-flex h-9 w-6 items-center justify-center text-sm text-navy/40"
          >
            &hellip;
          </span>
        ) : (
          <button
            key={item}
            type="button"
            aria-label={`Page ${item}`}
            aria-current={item === page ? "page" : undefined}
            onClick={() => go(item)}
            className={
              item === page
                ? `${buttonClass} bg-primary text-white`
                : `${buttonClass} border border-line bg-surface text-navy hover:bg-elevated`
            }
          >
            {item}
          </button>
        )
      )}

      <button
        type="button"
        aria-label="Next page"
        disabled={page >= totalPages}
        onClick={() => go(page + 1)}
        className={`${buttonClass} border border-line bg-surface text-navy hover:bg-elevated disabled:cursor-not-allowed disabled:opacity-40`}
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </nav>
  );
}