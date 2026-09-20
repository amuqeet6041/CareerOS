// Status badge for a tracked application. Statuses come straight from the
// backend's allowed set: applied | in_review | interview | offer | rejected.
// Labels are always shown next to a color so status is never conveyed by
// color alone.
const STATUS_STYLES = {
  applied: "border border-border bg-surface text-navy/70",
  in_review: "border border-sky-200 bg-sky-50 text-sky-700",
  interview: "border border-violet-200 bg-violet-50 text-violet-700",
  offer: "border border-green-200 bg-green-50 text-green-700",
  rejected: "border border-red-200 bg-red-50 text-red-600",
};

const STATUS_LABELS = {
  applied: "Applied",
  in_review: "In Review",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
};

export { STATUS_LABELS };

export default function ApplicationStatus({ status }) {
  const label = STATUS_LABELS[status] ?? status;
  const style =
    STATUS_STYLES[status] ?? "border border-border bg-surface text-navy/70";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}