"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/shared/Button";
import { useAuth } from "@/hooks/useAuth";
import { register } from "@/services/authService";

const INPUT_CLASS =
  "w-full rounded-xl border border-line bg-canvas px-3.5 py-2.5 text-sm text-navy placeholder:text-muted/70 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20";

export default function RegisterForm() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(form);
      try {
        await signIn({ email: form.email, password: form.password });
        router.push("/student-dashboard");
        router.refresh();
      } catch (_) {
        // Account created, but automatic sign-in failed; the user can complete
        // the flow through the login page instead.
        router.push("/login");
      }
    } catch (err) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1.5 block text-xs font-medium text-navy/80">
          Full name
        </label>
        <input
          type="text"
          name="name"
          value={form.name}
          onChange={handleChange}
          required
          autoComplete="name"
          className={INPUT_CLASS}
        />
      </div>
      <div>
        <label className="mb-1.5 block text-xs font-medium text-navy/80">
          Email
        </label>
        <input
          type="email"
          name="email"
          value={form.email}
          onChange={handleChange}
          required
          autoComplete="email"
          className={INPUT_CLASS}
        />
      </div>
      <div>
        <label className="mb-1.5 block text-xs font-medium text-navy/80">
          Password
        </label>
        <input
          type="password"
          name="password"
          value={form.password}
          onChange={handleChange}
          required
          autoComplete="new-password"
          className={INPUT_CLASS}
        />
      </div>
      {error ? <p className="text-sm text-danger">{error}</p> : null}
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "Creating account..." : "Create account"}
      </Button>
    </form>
  );
}