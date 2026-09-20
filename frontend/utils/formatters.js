export function formatSalary(min, max, currency = "USD") {
  if (!min && !max) return "Not specified";
  if (min && max) return `${currency} ${min.toLocaleString()} - ${max.toLocaleString()}`;
  return `${currency} ${(min || max).toLocaleString()}`;
}

export function formatDate(dateString) {
  if (!dateString) return "";
  return new Date(dateString).toLocaleDateString();
}

export function formatPercentage(value) {
  return `${Math.round(value)}%`;
}
