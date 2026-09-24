export function priorityStyles(priority) {
  switch (priority) {
    case "high":
      return "bg-danger/10 text-danger";
    case "medium":
      return "bg-warning/10 text-warning";
    default:
      return "bg-elevated text-muted";
  }
}

export function priorityLabel(priority) {
  if (priority === "high") return "High priority";
  if (priority === "medium") return "Medium priority";
  return "Low priority";
}