export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function isNonEmpty(value) {
  return typeof value === "string" && value.trim().length > 0;
}

export function isAllowedResumeFile(file) {
  const allowed = [".pdf", ".doc", ".docx"];
  return allowed.some((ext) => file?.name?.toLowerCase().endsWith(ext));
}
