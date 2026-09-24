"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Briefcase,
  Check,
  CheckCircle2,
  FileText,
  FileUp,
  Loader2,
  Search,
  Sparkles,
  X,
} from "lucide-react";

import Button from "@/components/shared/Button";

// The modal is a UX representation of the real resume pipeline: the upload
// POST parses the document and runs AI/fallback analysis server-side before
// responding. Career insights and job matching are computed from the persisted
// resume on demand, so those stages resolve as soon as the upload returns.
const STAGES = [
  { key: "upload", label: "Uploading your resume", icon: FileUp },
  { key: "parse", label: "Parsing text & structure", icon: FileText },
  { key: "skills", label: "Analyzing skills", icon: Sparkles },
  { key: "experience", label: "Processing experience & education", icon: Briefcase },
  { key: "insights", label: "Generating career insights", icon: CheckCircle2 },
  { key: "jobs", label: "Matching relevant jobs", icon: Search },
  { key: "complete", label: "Finalizing your profile", icon: Check },
];

const STEP_MS = 520;
const MAX_ACTIVE_STEP = STAGES.length - 2; // never auto-reach "Complete"

export default function ResumeProcessingModal({
  open = false,
  status = "processing",
  result = null,
  errorMessage = "",
  fileName = "",
  onClose,
  onRetry,
  onViewResume,
  onViewInsights,
}) {
  const [activeStep, setActiveStep] = useState(0);
  const panelRef = useRef(null);

  const isProcessing = status === "processing";
  const isSuccess = status === "success";
  const isError = status === "error";

  // Advance the stage list while the real request is in flight.
  useEffect(() => {
    if (!open || !isProcessing) return;
    setActiveStep(0);
    const timer = setInterval(() => {
      setActiveStep((step) =>
        step < MAX_ACTIVE_STEP ? step + 1 : step,
      );
    }, STEP_MS);
    return () => clearInterval(timer);
  }, [open, isProcessing]);

  useEffect(() => {
    if (!open) return;
    panelRef.current?.focus();
    const handleKeyDown = (event) => {
      if (event.key === "Escape" && !isProcessing) onClose?.();
    };
    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, isProcessing, onClose]);

  if (!open) return null;

  const handleBackdropClick = (event) => {
    if (event.target === event.currentTarget && !isProcessing) onClose?.();
  };

  const failedStep = Math.min(activeStep, STAGES.length - 1);

  const stepState = (index) => {
    if (isSuccess) return "done";
    if (isError) {
      if (index < failedStep) return "done";
      if (index === failedStep) return "failed";
      return "pending";
    }
    if (index < activeStep) return "done";
    if (index === activeStep) return "active";
    return "pending";
  };

  const progressPct = isSuccess
    ? 100
    : Math.max(1, ((activeStep + (isError ? 0 : 1)) / STAGES.length) * 100);

  const skillCount = result?.skills?.length ?? 0;
  const experienceCount = result?.experience?.length ?? 0;
  const educationCount = result?.education?.length ?? 0;
  const certificationCount = result?.certifications?.length ?? 0;

  const summary = [
    { label: "Skills identified", value: skillCount },
    { label: "Experience roles", value: experienceCount },
    { label: "Education entries", value: educationCount },
    { label: "Certifications", value: certificationCount },
  ];

  const checklistByStep = {
    skills: skillCount ? `${skillCount} identified` : "None found",
    experience: `${experienceCount} roles · ${educationCount} degrees`,
    insights: isSuccess ? "Unlocked" : "",
    jobs: isSuccess ? "Unlocked" : "",
    complete: isSuccess ? "Done" : "",
  };

  return (
    <div
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/55 px-4 py-6 backdrop-blur-sm"
      onMouseDown={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-label={
        isSuccess
          ? "Resume analysis complete"
          : isError
            ? "Resume analysis failed"
            : "Analyzing your resume"
      }
    >
      <div
        ref={panelRef}
        tabIndex={-1}
        className="w-full max-w-md max-h-[92vh] animate-scale-in overflow-y-auto rounded-2xl border border-line bg-surface p-6 shadow-2xl shadow-black/20 outline-none sm:p-7"
      >
        {isSuccess ? (
          <>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3.5">
                <div className="animate-pop-in flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-success/10 text-success">
                  <CheckCircle2 className="h-6 w-6" strokeWidth={2.2} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold tracking-tight text-navy">
                    Resume analyzed
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-muted">
                    {fileName
                      ? `"${fileName}" was parsed and your profile updated.`
                      : "Your profile has been updated."}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-muted transition-colors hover:bg-elevated hover:text-navy focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-bright/60"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              {summary.map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl border border-line-subtle bg-elevated/60 px-4 py-3"
                >
                  <p className="text-xl font-bold tracking-tight text-navy">
                    {item.value}
                  </p>
                  <p className="mt-0.5 text-xs text-muted">{item.label}</p>
                </div>
              ))}
            </div>

            <ul className="mt-5 space-y-1.5">
              {STAGES.map((stage, index) => (
                <li
                  key={stage.key}
                  className="flex items-center justify-between gap-3 rounded-lg px-2 py-1.5 text-sm"
                >
                  <span className="flex items-center gap-2.5 text-navy/80">
                    <Check
                      className="h-4 w-4 shrink-0 text-success"
                      strokeWidth={2.4}
                    />
                    {stage.label}
                  </span>
                  {checklistByStep[stage.key] ? (
                    <span className="shrink-0 text-xs font-medium text-muted">
                      {checklistByStep[stage.key]}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>

            <div className="mt-6 flex flex-col-reverse gap-2.5 sm:flex-row">
              <Button variant="secondary" onClick={onClose}>
                Done
              </Button>
              {onViewInsights ? (
                <Button onClick={onViewInsights}>View career insights</Button>
              ) : null}
            </div>
          </>
        ) : null}

        {isError ? (
          <>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3.5">
                <div className="animate-pop-in flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-danger/10 text-danger">
                  <AlertCircle className="h-6 w-6" strokeWidth={2.2} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold tracking-tight text-navy">
                    Analysis didn&apos;t complete
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-muted">
                    {errorMessage || "Something went wrong while uploading. Please try again."}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-muted transition-colors hover:bg-elevated hover:text-navy focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-bright/60"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <ul className="mt-5 space-y-1.5">
              {STAGES.map((stage, index) => {
                const state = stepState(index);
                return (
                  <li
                    key={stage.key}
                    className={`flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm ${
                      state === "failed"
                        ? "font-medium text-danger"
                        : state === "done"
                          ? "text-navy/70"
                          : "text-muted/60"
                    }`}
                  >
                    {state === "done" ? (
                      <Check className="h-4 w-4 shrink-0 text-success" strokeWidth={2.4} />
                    ) : state === "failed" ? (
                      <AlertCircle className="h-4 w-4 shrink-0" strokeWidth={2.2} />
                    ) : (
                      <span className="ml-[5px] h-1.5 w-1.5 shrink-0 rounded-full bg-current" />
                    )}
                    {stage.label}
                  </li>
                );
              })}
            </ul>

            <div className="mt-6 flex flex-col-reverse gap-2.5 sm:flex-row">
              <Button variant="secondary" onClick={onClose}>
                Close
              </Button>
              {onRetry ? (
                <Button onClick={onRetry}>Try Again</Button>
              ) : null}
            </div>
          </>
        ) : null}

        {isProcessing ? (
          <>
            <div className="flex items-end justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-tight text-navy">
                  Analyzing your career profile
                </h2>
                <p className="mt-1 text-sm leading-6 text-muted">
                  {fileName
                    ? `Uploading "${fileName}" and extracting your resume intelligence...`
                    : "Uploading your resume and extracting structured intelligence..."}
                </p>
              </div>
              <button
                type="button"
                disabled
                aria-disabled="true"
                className="flex h-8 w-8 shrink-0 cursor-not-allowed items-center justify-center rounded-lg text-muted/40"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div
              aria-hidden="true"
              className="relative mx-auto mt-7 flex h-20 w-20 items-center justify-center"
            >
              <div className="absolute inset-0 rounded-full bg-primary/20 motion-safe:animate-pulse-ring" />
              <div className="absolute inset-0 rounded-full bg-primary/10 motion-safe:animate-pulse-ring [animation-delay:0.6s]" />
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-accent to-primary text-white shadow-glow-primary motion-safe:animate-pulse-soft">
                <Loader2 className="h-6 w-6 motion-safe:animate-spin" strokeWidth={2.2} />
              </div>
            </div>

            <div className="mt-7" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progressPct)}>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-elevated-strong">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-accent shadow-glow-primary transition-[width] duration-500 ease-out"
                  style={{ width: `${Math.min(progressPct, 100)}%` }}
                />
              </div>
              <p className="mt-2 text-xs font-medium text-muted">
                Step {activeStep + 1} of {STAGES.length} —{" "}
                <span className="sr-only" aria-live="polite">
                  {STAGES[activeStep].label}
                </span>
                <span aria-hidden="true">{STAGES[activeStep].label}</span>
              </p>
            </div>

            <ul className="mt-4 space-y-1.5">
              {STAGES.map((stage, index) => {
                const state = stepState(index);
                const StageIcon = stage.icon;
                return (
                  <li
                    key={stage.key}
                    className={`flex items-center justify-between gap-3 rounded-lg px-2 py-2 ${
                      state === "active" ? "bg-accent/5" : ""
                    }`}
                  >
                    <span className="flex items-center gap-2.5 text-sm text-navy/80">
                      <span
                        className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md ${
                          state === "done"
                            ? "bg-success/10 text-success"
                            : state === "active"
                              ? "bg-accent/10 text-accent motion-safe:animate-pulse-soft"
                              : "bg-elevated text-muted/50"
                        }`}
                      >
                        {state === "done" ? (
                          <Check className="h-3.5 w-3.5" strokeWidth={2.6} />
                        ) : state === "active" ? (
                          <StageIcon className="h-3.5 w-3.5" strokeWidth={2.2} />
                        ) : (
                          <span className="h-1.5 w-1.5 rounded-full bg-current" />
                        )}
                      </span>
                      {stage.label}
                    </span>
                    {state === "active" ? (
                      <Loader2
                        className="h-3.5 w-3.5 shrink-0 text-accent motion-safe:animate-spin"
                        aria-hidden="true"
                      />
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </>
        ) : null}
      </div>
    </div>
  );
}