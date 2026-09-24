export default function CertificationsList({ certifications = [] }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-navy">Certifications</h3>
      {certifications.length === 0 ? (
        <p className="text-sm text-navy/50">No certifications extracted yet.</p>
      ) : (
        <ul className="space-y-2">
          {certifications.map((item, idx) => (
            <li key={idx} className="rounded-md border border-line bg-surface p-3 text-sm">
              <p className="font-medium text-navy">{item.name}</p>
              {item.issuer ? <p className="text-navy/60">{item.issuer}</p> : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}