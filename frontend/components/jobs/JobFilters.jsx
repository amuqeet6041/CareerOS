"use client";

import { useState } from "react";

// Filter panel aligned with the /api/jobs query parameters (Phase 4 wires it
// to a jobs list via jobService/useJobs).
export default function JobFilters({ onChange }) {
  const [filters, setFilters] = useState({
    search: "",
    location: "",
    work_mode: "",
    employment_type: "",
  });

  const update = (key, value) => {
    const next = { ...filters, [key]: value };
    setFilters(next);
    onChange?.(next);
  };

  return (
    <aside className="space-y-4 rounded-lg border border-border bg-white p-4">
      <div>
        <label className="mb-1 block text-xs font-medium text-navy/70">Search</label>
        <input
          type="text"
          value={filters.search}
          onChange={(e) => update("search", e.target.value)}
          placeholder="Title, company, skill..."
          className="w-full rounded-md border border-border px-2 py-1 text-sm"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium text-navy/70">Location</label>
        <input
          type="text"
          value={filters.location}
          onChange={(e) => update("location", e.target.value)}
          className="w-full rounded-md border border-border px-2 py-1 text-sm"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium text-navy/70">Work Mode</label>
        <select
          value={filters.work_mode}
          onChange={(e) => update("work_mode", e.target.value)}
          className="w-full rounded-md border border-border px-2 py-1 text-sm"
        >
          <option value="">Any</option>
          <option value="remote">Remote</option>
          <option value="hybrid">Hybrid</option>
          <option value="onsite">On-site</option>
        </select>
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium text-navy/70">
          Employment Type
        </label>
        <select
          value={filters.employment_type}
          onChange={(e) => update("employment_type", e.target.value)}
          className="w-full rounded-md border border-border px-2 py-1 text-sm"
        >
          <option value="">Any</option>
          <option value="full-time">Full-time</option>
          <option value="part-time">Part-time</option>
          <option value="contract">Contract</option>
          <option value="internship">Internship</option>
          <option value="temporary">Temporary</option>
          <option value="freelance">Freelance</option>
        </select>
      </div>
    </aside>
  );
}