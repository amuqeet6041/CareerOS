export default function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  ...props
}) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 motion-safe:hover:-translate-y-0.5 motion-safe:active:translate-y-0 disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-bright/60 active:scale-[0.98]";

  const sizes = {
    sm: "px-3.5 py-2 text-sm",
    md: "px-5 py-2.5 text-sm",
    lg: "px-6 py-3 text-base",
  };

  const variants = {
    primary:
      "bg-primary text-white shadow-glow-primary motion-safe:hover:shadow-glow-primary hover:bg-accent-light hover:shadow-glow-primary",

    secondary:
      "border border-line bg-elevated text-navy hover:bg-elevated-strong hover:border-line",

    outline:
      "border border-accent/40 bg-accent/5 text-accent hover:border-accent/60 hover:bg-accent/10",

    ghost: "text-navy/70 hover:bg-elevated hover:text-navy",

    dark: "border border-line bg-navy text-canvas hover:bg-accent hover:text-white",
  };

  return (
    <button
      className={`${base} ${sizes[size] ?? sizes.md} ${
        variants[variant] ?? variants.primary
      } ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}