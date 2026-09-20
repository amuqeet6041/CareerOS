export default function Button({
children,
variant = "primary",
size = "md",
className = "",
...props
}) {
const base =
"inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500/40";

const sizes = {
sm: "px-3.5 py-2 text-sm",
md: "px-5 py-2.5 text-sm",
lg: "px-6 py-3 text-base",
};

const variants = {
primary:
"bg-[#3B82F6] text-white shadow-lg shadow-blue-500/20 hover:bg-[#2563EB] hover:shadow-blue-500/30",


secondary:
  "border border-white/10 bg-white/[0.04] text-slate-200 hover:border-white/20 hover:bg-white/[0.08] hover:text-white",

outline:
  "border border-blue-400/30 bg-blue-500/[0.05] text-blue-300 hover:border-blue-400/50 hover:bg-blue-500/10 hover:text-blue-200",

ghost:
  "text-slate-300 hover:bg-white/[0.05] hover:text-white",

dark:
  "bg-[#0B1B30] text-white border border-white/[0.08] hover:bg-[#10243D]",

};

return (
<button
className={`${base} ${sizes[size] ?? sizes.md} ${
        variants[variant] ?? variants.primary
      } ${className}`}
{...props}
>
{children} </button>
);
}
