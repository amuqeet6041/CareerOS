"use client";

import { useState } from "react";
import Button from "@/components/shared/Button";
import { uploadResume } from "@/services/resumeService";

export default function ResumeUpload({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setStatus("uploading");
    setError(null);
    try {
      const result = await uploadResume(file);
      setStatus("success");
      onUploaded?.(result);
    } catch (err) {
      setStatus("error");
      setError(err.message || "Upload failed");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-border bg-white p-6">
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
      {status === "error" ? <p className="mt-2 text-sm text-red-600">{error}</p> : null}
      {status === "success" ? (
        <p className="mt-2 text-sm text-success">Resume uploaded successfully.</p>
      ) : null}
    </form>
  );
}
