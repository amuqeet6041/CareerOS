"use client";

import { useState } from "react";
import { Search } from "lucide-react";

// Search commit strategy: the query only fires on submit (Enter or button),
// never on a per-keystroke request.
export default function JobSearch({
  initialValue = "",
  onSearch,
  variant = "dark",
  placeholder = "Search jobs by title, company, or skill",
}) {
  const [value, setValue] = useState(initialValue);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSearch?.(value.trim());
  };

  return (
    <form onSubmit={handleSubmit} role="search" className="flex w-full gap-2">
      <div className="relative flex-1">
        <Search
          className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
          aria-hidden="true"
        />
        <input
          type="search"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          aria-label="Search jobs"
          className="w-full rounded-xl border border-line bg-surface py-3 pl-10 pr-4 text-sm text-navy shadow-sm placeholder:text-muted transition-colors outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
        />
      </div>
      <button
        type="submit"
        className="shrink-0 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-accent-light"
      >
        Search
      </button>
    </form>
  );
}