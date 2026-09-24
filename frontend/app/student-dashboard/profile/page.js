"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  User,
  MapPin,
  Briefcase,
  FileText,
  Save,
  CheckCircle,
  AlertCircle,
  ChevronRight,
  DollarSign,
  Globe,
} from "lucide-react";
import DashboardSection, {
  SectionSkeleton,
  SectionError,
} from "@/components/dashboard/DashboardSection";
import DashboardShell from "@/components/dashboard/DashboardShell";
import { useProfile } from "@/hooks/useProfile";

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

function InputField({ label, id, type = "text", value, onChange, placeholder }) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-xs font-medium text-navy/70">
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-navy placeholder:text-navy/30 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
      />
    </div>
  );
}

function TextareaField({ label, id, value, onChange, placeholder, rows = 4 }) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-xs font-medium text-navy/70">
        {label}
      </label>
      <textarea
        id={id}
        rows={rows}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-navy placeholder:text-navy/30 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 resize-none"
      />
    </div>
  );
}

function TagInput({ label, id, tags, onChange, placeholder }) {
  const [input, setInput] = useState("");

  const addTag = () => {
    const trimmed = input.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed]);
    }
    setInput("");
  };

  const removeTag = (tag) => onChange(tags.filter((t) => t !== tag));

  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-xs font-medium text-navy/70">
        {label}
      </label>
      <div className="flex gap-2">
        <input
          id={id}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault();
              addTag();
            }
          }}
          placeholder={placeholder}
          className="flex-1 rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-navy placeholder:text-navy/30 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
        />
        <button
          type="button"
          onClick={addTag}
          className="rounded-lg border border-line bg-surface px-3 py-2 text-xs font-medium text-navy hover:bg-elevated transition-colors"
        >
          Add
        </button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 rounded-full bg-accent/10 px-2.5 py-1 text-xs font-medium text-accent"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="ml-1 text-accent/60 hover:text-accent transition-colors"
                aria-label={`Remove ${tag}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function CheckboxGroup({ label, options, selected, onChange }) {
  const toggle = (value) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-navy/70">{label}</p>
      <div className="flex flex-wrap gap-2">
        {options.map(({ value, label: optLabel }) => (
          <button
            key={value}
            type="button"
            onClick={() => toggle(value)}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
              selected.includes(value)
                ? "border-accent bg-accent/10 text-accent"
                : "border-line bg-canvas text-navy/60 hover:border-accent/40 hover:text-navy"
            }`}
          >
            {optLabel}
          </button>
        ))}
      </div>
    </div>
  );
}

function SaveBar({ saving, saved, saveError, onSave, label = "Save changes" }) {
  return (
    <div className="flex items-center gap-3 pt-2">
      <button
        type="button"
        onClick={onSave}
        disabled={saving}
        className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-glow-primary transition-all duration-200 hover:bg-accent-light disabled:opacity-50"
      >
        <Save className="h-4 w-4" />
        {saving ? "Saving…" : label}
      </button>
      {saved && (
        <span className="inline-flex items-center gap-1.5 text-sm font-medium text-success">
          <CheckCircle className="h-4 w-4" />
          Saved
        </span>
      )}
      {saveError && (
        <span className="inline-flex items-center gap-1.5 text-sm font-medium text-danger">
          <AlertCircle className="h-4 w-4" />
          {saveError}
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WORK_MODES = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

const EMPLOYMENT_TYPES = [
  { value: "full-time", label: "Full-time" },
  { value: "part-time", label: "Part-time" },
  { value: "contract", label: "Contract" },
  { value: "internship", label: "Internship" },
  { value: "freelance", label: "Freelance" },
];

const CAREER_LEVELS = [
  { value: "entry", label: "Entry level" },
  { value: "junior", label: "Junior" },
  { value: "mid", label: "Mid level" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead / Principal" },
];

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function ProfilePage() {
  const {
    profile,
    preferences,
    loading,
    error,
    saving,
    saveError,
    saved,
    loadProfile,
    saveProfile,
    loadPreferences,
    savePreferences,
  } = useProfile();

  // Profile form state
  const [headline, setHeadline] = useState("");
  const [bio, setBio] = useState("");
  const [location, setLocation] = useState("");
  const [country, setCountry] = useState("");

  // Preferences form state
  const [prefRoles, setPrefRoles] = useState([]);
  const [prefWorkModes, setPrefWorkModes] = useState([]);
  const [prefEmpTypes, setPrefEmpTypes] = useState([]);
  const [prefIndustries, setPrefIndustries] = useState([]);
  const [prefSkills, setPrefSkills] = useState([]);
  const [prefLocation, setPrefLocation] = useState("");
  const [salaryMin, setSalaryMin] = useState("");
  const [salaryMax, setSalaryMax] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [careerLevel, setCareerLevel] = useState("");
  const [openToRelocate, setOpenToRelocate] = useState(false);

  // Separate saved/saving state for preferences so each section has its own bar
  const [prefSaving, setPrefSaving] = useState(false);
  const [prefSaved, setPrefSaved] = useState(false);
  const [prefSaveError, setPrefSaveError] = useState(null);

  // -------------------------------------------------------------------------
  // Load data
  // -------------------------------------------------------------------------
  useEffect(() => {
    loadProfile();
    loadPreferences();
  }, [loadProfile, loadPreferences]);

  // Sync profile fields when data arrives
  useEffect(() => {
    if (profile) {
      setHeadline(profile.headline ?? "");
      setBio(profile.bio ?? "");
      setLocation(profile.location ?? "");
      setCountry(profile.country ?? "");
    }
  }, [profile]);

  // Sync preferences fields when data arrives
  useEffect(() => {
    if (preferences) {
      setPrefRoles(preferences.preferred_roles ?? []);
      setPrefWorkModes(preferences.preferred_work_modes ?? []);
      setPrefEmpTypes(preferences.preferred_employment_types ?? []);
      setPrefIndustries(preferences.preferred_industries ?? []);
      setPrefSkills(preferences.preferred_skills ?? []);
      setPrefLocation(preferences.preferred_location ?? "");
      setSalaryMin(preferences.salary_min != null ? String(preferences.salary_min) : "");
      setSalaryMax(preferences.salary_max != null ? String(preferences.salary_max) : "");
      setCurrency(preferences.currency ?? "USD");
      setCareerLevel(preferences.career_level ?? "");
      setOpenToRelocate(preferences.open_to_relocate ?? false);
    }
  }, [preferences]);

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------
  const handleSaveProfile = () => {
    saveProfile({ headline, bio, location, country });
  };

  const handleSavePreferences = async () => {
    setPrefSaving(true);
    setPrefSaveError(null);
    setPrefSaved(false);
    try {
      await savePreferences({
        preferred_roles: prefRoles,
        preferred_work_modes: prefWorkModes,
        preferred_employment_types: prefEmpTypes,
        preferred_industries: prefIndustries,
        preferred_skills: prefSkills,
        preferred_location: prefLocation || null,
        salary_min: salaryMin ? parseFloat(salaryMin) : null,
        salary_max: salaryMax ? parseFloat(salaryMax) : null,
        currency: currency || "USD",
        career_level: careerLevel || null,
        open_to_relocate: openToRelocate,
      });
      setPrefSaved(true);
      setTimeout(() => setPrefSaved(false), 3000);
    } catch (err) {
      setPrefSaveError(err.message || "Failed to save preferences");
    } finally {
      setPrefSaving(false);
    }
  };

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  if (loading && !profile && !preferences) {
    return (
      <DashboardShell maxWidth="5xl">
        <div className="space-y-6">
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      </DashboardShell>
    );
  }

  if (error && !profile) {
    return (
      <DashboardShell maxWidth="5xl">
        <SectionError message={error} onRetry={loadProfile} />
      </DashboardShell>
    );
  }

  return (
    <DashboardShell maxWidth="5xl">
      <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-navy">Profile</h1>
        <p className="mt-1 text-sm text-navy/50">
          Manage your public profile and career preferences.
        </p>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Basic Info                                                           */}
      {/* ------------------------------------------------------------------ */}
      <DashboardSection
        title="Basic Information"
        subtitle="Displayed on your profile and shared with employers."
      >
        <div className="space-y-4">
          {/* Identity row (read-only) */}
          {profile && (
            <div className="flex items-center gap-3 rounded-xl border border-line bg-surface p-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent/10">
                <User className="h-5 w-5 text-accent" />
              </div>
              <div>
                <p className="text-sm font-semibold text-navy">{profile.name}</p>
                <p className="text-xs text-navy/50">{profile.email}</p>
              </div>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <InputField
              label="Professional headline"
              id="headline"
              value={headline}
              onChange={setHeadline}
              placeholder="e.g. Senior Data Analyst | Python & SQL"
            />
            <InputField
              label="Location (city)"
              id="location"
              value={location}
              onChange={setLocation}
              placeholder="e.g. London"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <InputField
              label="Country"
              id="country"
              value={country}
              onChange={setCountry}
              placeholder="e.g. United Kingdom"
            />
          </div>

          <TextareaField
            label="Bio"
            id="bio"
            value={bio}
            onChange={setBio}
            placeholder="A short professional summary about yourself…"
            rows={4}
          />

          <SaveBar
            saving={saving}
            saved={saved}
            saveError={saveError}
            onSave={handleSaveProfile}
            label="Save profile"
          />
        </div>
      </DashboardSection>

      {/* ------------------------------------------------------------------ */}
      {/* CV-Extracted Data (read-only link)                                  */}
      {/* ------------------------------------------------------------------ */}
      <DashboardSection
        title="Resume Data"
        subtitle="Extracted automatically from your uploaded CV."
        actionHref="/student-dashboard/resume"
        actionLabel="View & manage resume →"
      >
        <div className="flex items-start gap-3 rounded-xl border border-line bg-surface p-4">
          <FileText className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
          <div>
            <p className="text-sm text-navy">
              Your skills, work experience, education, and certifications are pulled
              from your uploaded CV and displayed on the{" "}
              <Link
                href="/student-dashboard/resume"
                className="font-medium text-accent underline-offset-2 hover:underline"
              >
                Resume page
              </Link>
              .
            </p>
            <p className="mt-1 text-xs text-navy/50">
              To update this data, re-upload your CV or edit it on the Resume page.
              CareerOS will not overwrite changes you make here.
            </p>
          </div>
        </div>
      </DashboardSection>

      {/* ------------------------------------------------------------------ */}
      {/* Career Preferences                                                   */}
      {/* ------------------------------------------------------------------ */}
      <DashboardSection
        title="Career Preferences"
        subtitle="Help CareerOS find jobs that match exactly what you're looking for."
      >
        <div className="space-y-5">
          {/* Preferred roles */}
          <TagInput
            label="Preferred job titles / roles"
            id="pref-roles"
            tags={prefRoles}
            onChange={setPrefRoles}
            placeholder="Type a role and press Enter…"
          />

          {/* Work mode */}
          <CheckboxGroup
            label="Preferred work mode"
            options={WORK_MODES}
            selected={prefWorkModes}
            onChange={setPrefWorkModes}
          />

          {/* Employment type */}
          <CheckboxGroup
            label="Preferred employment type"
            options={EMPLOYMENT_TYPES}
            selected={prefEmpTypes}
            onChange={setPrefEmpTypes}
          />

          {/* Career level */}
          <div className="space-y-1">
            <label htmlFor="career-level" className="block text-xs font-medium text-navy/70">
              Career level
            </label>
            <select
              id="career-level"
              value={careerLevel}
              onChange={(e) => setCareerLevel(e.target.value)}
              className="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-navy transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 sm:w-48"
            >
              <option value="">— Select level —</option>
              {CAREER_LEVELS.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Preferred location + relocation */}
          <div className="grid gap-4 sm:grid-cols-2">
            <InputField
              label="Preferred job location"
              id="pref-location"
              value={prefLocation}
              onChange={setPrefLocation}
              placeholder="e.g. London, Remote, Anywhere"
            />
            <div className="flex items-end pb-1">
              <label className="flex cursor-pointer items-center gap-2.5">
                <input
                  type="checkbox"
                  checked={openToRelocate}
                  onChange={(e) => setOpenToRelocate(e.target.checked)}
                  className="h-4 w-4 rounded border-line text-accent focus:ring-accent/20"
                />
                <span className="text-sm text-navy">Open to relocation</span>
              </label>
            </div>
          </div>

          {/* Salary */}
          <div className="space-y-1">
            <p className="text-xs font-medium text-navy/70">Expected salary range</p>
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <DollarSign className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-navy/30" />
                <input
                  type="number"
                  value={salaryMin}
                  onChange={(e) => setSalaryMin(e.target.value)}
                  placeholder="Min"
                  className="w-28 rounded-lg border border-line bg-canvas pl-7 pr-3 py-2 text-sm text-navy transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
                />
              </div>
              <span className="text-navy/40 text-sm">–</span>
              <div className="relative">
                <DollarSign className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-navy/30" />
                <input
                  type="number"
                  value={salaryMax}
                  onChange={(e) => setSalaryMax(e.target.value)}
                  placeholder="Max"
                  className="w-28 rounded-lg border border-line bg-canvas pl-7 pr-3 py-2 text-sm text-navy transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
                />
              </div>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-navy transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
              >
                <option value="USD">USD</option>
                <option value="GBP">GBP</option>
                <option value="EUR">EUR</option>
                <option value="AED">AED</option>
                <option value="CAD">CAD</option>
                <option value="AUD">AUD</option>
                <option value="INR">INR</option>
              </select>
            </div>
          </div>

          {/* Industries */}
          <TagInput
            label="Preferred industries"
            id="pref-industries"
            tags={prefIndustries}
            onChange={setPrefIndustries}
            placeholder="e.g. Finance, Healthcare, Tech…"
          />

          {/* Skills */}
          <TagInput
            label="Key skills you want to use"
            id="pref-skills"
            tags={prefSkills}
            onChange={setPrefSkills}
            placeholder="e.g. Python, SQL, Power BI…"
          />

          <SaveBar
            saving={prefSaving}
            saved={prefSaved}
            saveError={prefSaveError}
            onSave={handleSavePreferences}
            label="Save preferences"
          />
        </div>
      </DashboardSection>
      </div>
    </DashboardShell>
  );
}
