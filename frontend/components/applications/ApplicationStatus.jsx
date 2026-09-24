// Status badge for a tracked application. Statuses come straight from the
// backend's allowed set: applied | in_review | interview | offer | rejected.
// Labels are always shown next to a color so status is never conveyed by
// color alone.
const STATUS_STYLES = {
  applied: "border border-line bg-elevated text-navy/70",
  in_review: "border border-info/30 bg-info/10 text-info",
  interview: "border border-violet/30 bg-violet/10 text-violet",
  offer: "border border-success/30 bg-success/10 text-success",
  rejected: "border border-danger/30 bg-danger/10 text-danger",
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
    STATUS_STYLES[status] ?? "border border-line bg-elevated text-navy/70";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}