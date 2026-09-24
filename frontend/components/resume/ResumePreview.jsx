export default function ResumePreview({ fileName, uploadedAt }) {
  if (!fileName) {
    return (
      <p className="text-sm text-navy/60">No resume uploaded yet.</p>
    );
  }

  return (
    <div className="rounded-2xl border border-line bg-surface p-4 shadow-card">
      <p className="text-sm font-medium text-navy">{fileName}</p>
      {uploadedAt ? (
        <p className="text-xs text-navy/50">Uploaded {uploadedAt}</p>
      ) : null}
    </div>
  );
}
