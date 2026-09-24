export default function EducationList({ education = [] }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-navy">Education</h3>
      {education.length === 0 ? (
        <p className="text-sm text-navy/50">No education records extracted yet.</p>
      ) : (
        <ul className="space-y-2">
          {education.map((item, idx) => (
            <li key={idx} className="rounded-md border border-line bg-surface p-3 text-sm">
              <p className="font-medium text-navy">{item.degree}</p>
              <p className="text-navy/60">{item.institution}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
