export default function ExperienceList({ experience = [] }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-navy">Experience</h3>
      {experience.length === 0 ? (
        <p className="text-sm text-navy/50">No work experience extracted yet.</p>
      ) : (
        <ul className="space-y-2">
          {experience.map((item, idx) => (
            <li key={idx} className="rounded-md border border-border bg-white p-3 text-sm">
              <p className="font-medium text-navy">{item.title}</p>
              <p className="text-navy/60">{item.company}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
