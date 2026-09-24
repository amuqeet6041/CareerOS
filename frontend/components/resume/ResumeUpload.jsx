"use client";

import { forwardRef, useImperativeHandle, useState } from "react";
import Button from "@/components/shared/Button";
import { uploadResume } from "@/services/resumeService";

const ResumeUpload = forwardRef(
  ({ onUploaded, onFlowStart, onFlowSuccess, onFlowError }, ref) => {
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState("idle"); // idle | uploading | success | error
    const [error, setError] = useState(null);

    // When the parent owns the processing flow (resume processing modal), the
    // inline status messages are suppressed to avoid duplication.
    const hasFlow =
      Boolean(onFlowStart) || Boolean(onFlowSuccess) || Boolean(onFlowError);

    const submit = async () => {
      if (!file) return;

      setStatus("uploading");
      setError(null);
      onFlowStart?.();
      try {
        const result = await uploadResume(file);
        setStatus("success");
        onUploaded?.(result);
        onFlowSuccess?.(result);
      } catch (err) {
        setStatus("error");
        setError(err.message || "Upload failed");
        onFlowError?.(err);
      }
    };

    useImperativeHandle(ref, () => ({ submit }));

    const handleSubmit = (e) => {
      e.preventDefault();
      submit();
    };

    return (
      <form
        onSubmit={handleSubmit}
        className="animate-fade-in-up rounded-2xl border border-line bg-surface p-6 shadow-card"
      >
        <label className="mb-2 block text-sm font-medium text-navy">
          Upload your resume (PDF or DOCX)
        </label>
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm text-navy/70"
        />
        <div className="mt-4">
          <Button type="submit" disabled={!file || status === "uploading"}>
            {status === "uploading" ? "Uploading..." : "Upload Resume"}
          </Button>
        </div>
        {!hasFlow && status === "error" ? (
          <p className="mt-2 text-sm text-danger">{error}</p>
        ) : null}
        {!hasFlow && status === "success" ? (
          <p className="mt-2 text-sm text-success">
            Resume uploaded successfully.
          </p>
        ) : null}
      </form>
    );
  },
);

ResumeUpload.displayName = "ResumeUpload";

export default ResumeUpload;