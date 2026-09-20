export default function Loading({
  label = "Loading...",
  size = "md",
  className = "",
}) {
  const sizes = {
    sm: "h-3.5 w-3.5 border-2",
    md: "h-4 w-4 border-2",
    lg: "h-6 w-6 border-4",
  };

  return (
    <div
      className={`flex items-center justify-center gap-2.5 py-8 text-sm text-slate-500 ${className}`}
    >
      <span
        className={`animate-spin rounded-full border-[#3B82F6] border-t-transparent ${
          sizes[size] ?? sizes.md
        }`}
      />

      <span>{label}</span>
    </div>
  );
}