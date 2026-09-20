export function formatSalary(min, max, currency = "USD") {
  if (!min && !max) return "Not specified";
  if (min && max) return `${currency} ${min.toLocaleString()} - ${max.toLocaleString()}`;
  return `${currency} ${(min || max).toLocaleString()}`;
}

export function formatDate(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString();
}

export function formatPercentage(value) {
  const rounded = Math.round(value);
  return `${rounded}%`;
}

/**
 * Null-safe percentage formatter for match components. Returns null when the
 * value is unknown so callers never render a misleading 0%.
 */
export function formatMatchPercentage(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return null;
  }
  return formatPercentage(value);
}

/**
 * Turn a canonical dotted value (full-time, on-site) into a human label.
 */
export function humanizeLabel(value) {
  if (!value) return "";
  return String(value)
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

/**
 * Describe the experience band of a job from its min/max year bounds.
 * Returns an empty string when neither bound is set.
 */
export function formatExperienceRequirement(minimumYears, maximumYears) {
  if (minimumYears == null && maximumYears == null) return "";
  if (minimumYears != null && maximumYears != null && minimumYears === maximumYears) {
    return `${minimumYears} yrs`;
  }
  if (minimumYears != null) return `${minimumYears}+ yrs`;
  return `Up to ${maximumYears} yrs`;
}

/**
 * Human labels for the backend's experience_status values (matching_engine).
 */
export const EXPERIENCE_STATUS_LABELS = {
  meets_requirement: "Meets the experience requirement",
  below_minimum: "Below the minimum experience requirement",
  above_maximum: "Above the maximum experience requirement",
  unknown: "Experience requirement cannot be evaluated",
  no_requirement: "No experience requirement",
};