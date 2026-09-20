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

  const dark = variant === "dark";

  const handleSubmit = (event) => {
    event.preventDefault();
    onSearch?.(value.trim());
  };

  return (
    <form onSubmit={handleSubmit} role="search" className="flex w-full gap-2">
      <div className="relative flex-1">
        <Search
          className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <input
          type="search"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          aria-label="Search jobs"
          className={`w-full rounded-xl py-3 pl-10 pr-4 text-sm outline-none transition-colors ${
            dark
              ? "border border-white/15 bg-white/10 text-white placeholder:text-slate-400 focus:border-white/30 focus:bg-white/15"
              : "border border-border bg-white text-navy placeholder:text-navy/40 focus:border-accent"
          }`}
        />
      </div>
      <button
        type="submit"
        className="shrink-0 rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-accent-light"
      >
        Search
      </button>
    </form>
  );
}