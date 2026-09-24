"use client";

import { useEffect, useState } from "react";
import { WORK_MODE_OPTIONS, EMPLOYMENT_TYPE_OPTIONS } from "@/lib/constants";
import { initialFilters } from "@/lib/jobQuery";

// Controlled filter panel for /api/jobs. Field edits accumulate in local
// draft state (no per-keystroke requests); changes commit only on Apply.
// The draft resets whenever the externally-applied filter value changes.
export default function JobFilters({
  value,
  externalKey,
  onApply,
  onClear,
  showSearch = false,
}) {
  const [draft, setDraft] = useState(() => ({ ...initialFilters(), ...value }));

  useEffect(() => {
    setDraft({ ...initialFilters(), ...value });
  }, [externalKey]);

  const update = (key, fieldValue) =>
    setDraft((prev) => ({ ...prev, [key]: fieldValue }));

  const handleApply = () => onApply?.({ ...draft });

  const handleClear = () => {
    setDraft(initialFilters());
    onClear?.();
  };

  const inputClass =
    "w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-navy outline-none transition-colors focus:border-accent";

  return (
    <aside className="space-y-4 rounded-lg border border-line bg-surface p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-navy">Filters</h2>
        <button
          type="button"
          onClick={handleClear}
          className="text-xs font-medium text-navy/50 transition-colors hover:text-navy"
        >
          Clear
        </button>
      </div>

      {showSearch ? (
        <div>
          <label htmlFor="job-filter-search" className="mb-1 block text-xs font-medium text-navy/70">
            Search
          </label>
          <input
            id="job-filter-search"
            type="search"
            value={draft.search}
            onChange={(event) => update("search", event.target.value)}
            placeholder="Title, company, skill..."
            className={inputClass}
          />
        </div>
      ) : null}

      <div>
        <label htmlFor="job-filter-location" className="mb-1 block text-xs font-medium text-navy/70">
          Location
        </label>
        <input
          id="job-filter-location"
          type="text"
          value={draft.location}
          onChange={(event) => update("location", event.target.value)}
          placeholder="e.g. Lahore"
          className={inputClass}
        />
      </div>

      <div>
        <label htmlFor="job-filter-city" className="mb-1 block text-xs font-medium text-navy/70">
          City
        </label>
        <input
          id="job-filter-city"
          type="text"
          value={draft.city}
          onChange={(event) => update("city", event.target.value)}
          placeholder="e.g. Lahore"
          className={inputClass}
        />
      </div>

      <div>
        <label htmlFor="job-filter-work-mode" className="mb-1 block text-xs font-medium text-navy/70">
          Work mode
        </label>
        <select
          id="job-filter-work-mode"
          value={draft.work_mode}
          onChange={(event) => update("work_mode", event.target.value)}
          className={inputClass}
        >
          {WORK_MODE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="job-filter-type" className="mb-1 block text-xs font-medium text-navy/70">
          Employment type
        </label>
        <select
          id="job-filter-type"
          value={draft.employment_type}
          onChange={(event) => update("employment_type", event.target.value)}
          className={inputClass}
        >
          {EMPLOYMENT_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="job-filter-salary-min" className="mb-1 block text-xs font-medium text-navy/70">
          Minimum salary
        </label>
        <input
          id="job-filter-salary-min"
          type="number"
          min="0"
          step="1000"
          value={draft.salary_min}
          onChange={(event) => update("salary_min", event.target.value)}
          placeholder="e.g. 50000"
          className={inputClass}
        />
      </div>

      <div>
        <label htmlFor="job-filter-salary-max" className="mb-1 block text-xs font-medium text-navy/70">
          Maximum salary
        </label>
        <input
          id="job-filter-salary-max"
          type="number"
          min="0"
          step="1000"
          value={draft.salary_max}
          onChange={(event) => update("salary_max", event.target.value)}
          placeholder="e.g. 120000"
          className={inputClass}
        />
      </div>

      <div>
        <label htmlFor="job-filter-source" className="mb-1 block text-xs font-medium text-navy/70">
          Source
        </label>
        <input
          id="job-filter-source"
          type="text"
          value={draft.source}
          onChange={(event) => update("source", event.target.value)}
          placeholder="e.g. demo"
          className={inputClass}
        />
      </div>

      <button
        type="button"
        onClick={handleApply}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-light"
      >
        Apply Filters
      </button>
    </aside>
  );
}