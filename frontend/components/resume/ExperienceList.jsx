export default function ExperienceList({ experience = [] }) {
  const formatDate = (value) => {
    if (!value) return null;
    const [year, month] = value.split("-");
    const monthName = new Date(`${year}-${month}-01`).toLocaleString("en-US", {
      month: "short",
      year: "numeric",
    });
    return monthName;
  };

  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-navy">Experience</h3>
      {experience.length === 0 ? (
        <p className="text-sm text-navy/50">No work experience extracted yet.</p>
      ) : (
        <ul className="space-y-2">
          {experience.map((item, idx) => {
            const start = formatDate(item.start_date);
            const end = item.currently_employed ? "Present" : formatDate(item.end_date);
            const period = start || end ? `${start || "Unknown"} - ${end || "Unknown"}` : null;
            return (
              <li key={idx} className="rounded-md border border-line bg-surface p-3 text-sm">
                <p className="font-medium text-navy">{item.title}</p>
                <p className="text-navy/60">{item.company}</p>
                {period && <p className="text-navy/50">{period}</p>}
                {item.location && <p className="text-navy/50">{item.location}</p>}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
