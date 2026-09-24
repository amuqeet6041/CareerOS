"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { SlidersHorizontal } from "lucide-react";

import Modal from "@/components/shared/Modal";
import { useJobs } from "@/hooks/useJobs";
import { useJobMatches } from "@/hooks/useJobMatches";
import { useSavedJobs } from "@/hooks/useSavedJobs";
import { useApplications } from "@/hooks/useApplications";
import { useAuth } from "@/hooks/useAuth";
import { queryToFilters, filtersToQuery, serializeFilters } from "@/lib/jobQuery";
import { SORT_OPTIONS } from "@/lib/constants";

import JobSearch from "./JobSearch";
import JobFilters from "./JobFilters";
import JobList from "./JobList";
import JobPagination from "./JobPagination";
import JobHero from "./JobHero";

// Single orchestrator for both jobs surfaces. The URL query string is the
// filter source of truth; every applied change is pushed back through a
// no-op-guarded router.replace so back/forward and shared links work.
export default function JobsExplorer({ variant = "public" }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const externalFilters = queryToFilters(searchParams);

  const syncUrl = useCallback(
    (filters) => {
      const qs = filtersToQuery(filters);
      const current = window.location.search.replace(/^\?/, "");
      if (qs === current) return;
      router.replace(`${pathname}?${qs}`, { scroll: false });
    },
    [pathname, router]
  );

  const {
    jobs,
    total,
    page,
    totalPages,
    loading,
    error,
    query,
    setQuery,
    clearFilters,
    refetch,
  } = useJobs({ initialFilters: externalFilters, onFiltersChange: syncUrl });

  const { matchMap, loadingIds } = useJobMatches(jobs, {
    enabled: variant === "dashboard" && isAuthenticated && !authLoading,
  });

  const saved = useSavedJobs({
    enabled: variant === "dashboard" && isAuthenticated && !authLoading,
  });

  const applications = useApplications({
    enabled: variant === "dashboard" && isAuthenticated && !authLoading,
  });

  const [searchDraft, setSearchDraft] = useState(query.search || "");
  useEffect(() => {
    setSearchDraft(query.search || "");
  }, [query.search]);

  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  const handleSearch = (term) => setQuery({ search: term, page: 1 });

  const applyFilters = (draft) => {
    setQuery({ ...draft, page: 1 });
    setMobileFiltersOpen(false);
  };

  const handleClear = () => {
    clearFilters();
    setMobileFiltersOpen(false);
  };

  const handleSort = (event) => setQuery({ sort: event.target.value, page: 1 });

  const hasActiveFilters = Object.entries(query).some(
    ([key, value]) => key !== "page" && key !== "sort" && value !== ""
  );

  const externalKey = serializeFilters(query);

  return (
    <>
      {variant === "public" ? (
        <JobHero>
          <p className="mb-3 -mt-2 text-sm leading-6 text-ink-muted">
            {isAuthenticated
              ? "Find roles that match your skills and experience."
              : "Browse live opportunities. Sign in to see your personalized match score for every job."}
          </p>
          <JobSearch
            initialValue={searchDraft}
            onSearch={handleSearch}
            variant="dark"
          />
        </JobHero>
      ) : null}

      <div
        className={
          variant === "public"
            ? "mx-auto w-full max-w-6xl px-4 py-10 sm:px-6"
            : "mx-auto w-full max-w-6xl px-4 pb-10 pt-2 sm:px-6"
        }
      >
        {variant === "dashboard" ? (
          <div className="mb-5 max-w-2xl">
            <JobSearch
              initialValue={searchDraft}
              onSearch={handleSearch}
              variant="light"
            />
          </div>
        ) : null}

        {variant === "dashboard" && !isAuthenticated && !authLoading ? (
          <div className="mb-5 rounded-lg border border-accent/20 bg-accent/5 px-4 py-3 text-sm text-navy/70">
            Sign in to see personalized match scores.{" "}
            <Link href="/login" className="font-medium text-accent hover:underline">
              Sign in
            </Link>
          </div>
        ) : null}

        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-navy/60" role="status">
            Showing {total} {total === 1 ? "job" : "jobs"}
          </p>

          <div className="flex items-center gap-3">
            <label htmlFor="jobs-sort" className="sr-only">
              Sort jobs
            </label>
            <select
              id="jobs-sort"
              value={query.sort}
              onChange={handleSort}
              className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-navy outline-none transition-colors focus:border-accent"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setMobileFiltersOpen(true)}
              className="inline-flex items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2 text-sm font-medium text-navy transition-colors hover:bg-elevated lg:hidden"
            >
              <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
              Filters
            </button>
          </div>
        </div>

        <div className="grid items-start gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
          <div className="hidden lg:block">
            <JobFilters
              value={query}
              externalKey={externalKey}
              onApply={applyFilters}
              onClear={handleClear}
            />
          </div>

          <div>
            <JobList
              jobs={jobs}
              loading={loading}
              error={error}
              onRetry={refetch}
              matchMap={variant === "dashboard" ? matchMap : null}
              loadingMatchIds={variant === "dashboard" ? loadingIds : []}
              savedIds={variant === "dashboard" ? saved.savedIds : null}
              appliedIds={variant === "dashboard" ? applications.appliedIds : null}
              saveDisabled={variant === "dashboard" && saved.loading}
              authenticated={isAuthenticated && !authLoading}
              onToggleSave={saved.toggle}
              onApplyTracked={applications.markApplied}
              emptyAction={
                hasActiveFilters ? (
                  <button
                    type="button"
                    onClick={handleClear}
                    className="rounded-md border border-line px-4 py-2 text-sm font-medium text-navy transition-colors hover:bg-elevated"
                  >
                    Clear filters
                  </button>
                ) : null
              }
            />
          </div>
        </div>

        <JobPagination
          page={page}
          totalPages={totalPages}
          onPageChange={(target) => setQuery({ page: target })}
        />
      </div>

      <Modal
        open={mobileFiltersOpen}
        onClose={() => setMobileFiltersOpen(false)}
        title="Filters"
      >
        <JobFilters
          value={query}
          externalKey={externalKey}
          onApply={applyFilters}
          onClear={handleClear}
          showSearch
        />
      </Modal>
    </>
  );
}