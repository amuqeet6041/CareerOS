// Helpers for mapping between the /api/jobs query-string contract and the
// plain filter object used by components/hooks. Query values are kept as
// strings so round-tripping URL -> filter -> URL is stable and lossless.

import { DEFAULT_SORT } from "@/lib/constants";

export const TEXT_QUERY_KEYS = [
  "search",
  "location",
  "city",
  "work_mode",
  "employment_type",
  "source",
  "sort",
];

export const NUM_QUERY_KEYS = ["salary_min", "salary_max"];

/**
 * Convert URLSearchParams (or the raw search string) into a filter object.
 * Unknown keys are ignored, invalid pages collapse to 1, and the sort
 * defaults to the backend default.
 */
export function queryToFilters(searchParams) {
  const filters = {};

  for (const key of TEXT_QUERY_KEYS) {
    const value = searchParams.get(key);
    if (value) filters[key] = value;
  }

  for (const key of NUM_QUERY_KEYS) {
    const value = searchParams.get(key);
    if (value && value !== "") filters[key] = value;
  }

  const page = Number(searchParams.get("page") || 1);
  filters.page = Number.isInteger(page) && page > 0 ? page : 1;

  filters.sort = filters.sort || DEFAULT_SORT;
  return filters;
}

/**
 * Serialize a filter object back into a query string. Empty/undefined values,
 * the default page, and the default sort are omitted.
 */
export function filtersToQuery(filters = {}) {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    if (key === "page" && Number(value) <= 1) continue;
    if (key === "sort" && value === DEFAULT_SORT) continue;
    params.set(key, String(value));
  }

  return params.toString();
}

/**
 * Keys that make up the "applied filter" state for the Clear Filters action.
 */
export function initialFilters() {
  return {
    search: "",
    location: "",
    city: "",
    work_mode: "",
    employment_type: "",
    salary_min: "",
    salary_max: "",
    source: "",
    sort: DEFAULT_SORT,
    page: 1,
  };
}

/**
 * Canonical signature used to detect external (URL) filter changes.
 */
export function serializeFilters(filters = {}) {
  return filtersToQuery(filters);
}