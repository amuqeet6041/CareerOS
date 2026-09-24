export default function SkillsList({ skills = [] }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-navy">Skills</h3>
      {skills.length === 0 ? (
        <p className="text-sm text-navy/50">No skills extracted yet.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {skills.map((skill, idx) => (
            <span
              key={skill?.id ?? idx}
              className="rounded-full border border-accent/15 bg-accent/10 px-3 py-1 text-xs font-medium text-accent"
            >
              {skill?.name ?? skill}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
