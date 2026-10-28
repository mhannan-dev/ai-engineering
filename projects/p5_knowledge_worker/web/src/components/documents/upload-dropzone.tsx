"use client";

import { useRef, useState, type DragEvent } from "react";

import { SUPPORTED_EXTENSIONS } from "@/lib/api";

const MAX_MB = 25;

export function UploadDropzone({
  onFiles,
  busy,
}: {
  onFiles: (files: File[]) => void;
  busy: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const files = Array.from(event.dataTransfer.files);
    if (files.length) onFiles(files);
  }

  return (
    <div
      id="upload-dropzone"
      role="button"
      tabIndex={0}
      aria-label="Upload documents"
      onClick={() => inputRef.current?.click()}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`group relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-900 dark:focus-visible:outline-zinc-50 ${
        dragging
          ? "scale-[1.01] border-zinc-900 bg-zinc-100 dark:border-zinc-100 dark:bg-zinc-800"
          : "border-zinc-300 bg-white hover:border-zinc-400 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:border-zinc-500 dark:hover:bg-zinc-800/60"
      }`}
    >
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-zinc-700 transition-transform group-hover:-translate-y-0.5 dark:bg-zinc-800 dark:text-zinc-200">
        {busy ? (
          <svg className="h-6 w-6 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden>
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
            <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
          </svg>
        ) : (
          <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 16V4m0 0-4 4m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
          </svg>
        )}
      </span>
      <div>
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          {busy ? "Uploading…" : "Drop files here or click to browse"}
        </p>
        <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
          PDF, DOCX, Markdown, HTML or TXT · up to {MAX_MB} MB · English &amp; বাংলা (Unicode)
        </p>
      </div>
      <input
        ref={inputRef}
        id="upload-input"
        type="file"
        multiple
        accept={SUPPORTED_EXTENSIONS.join(",")}
        className="sr-only"
        onChange={(event) => {
          const files = Array.from(event.target.files ?? []);
          if (files.length) onFiles(files);
          event.target.value = "";
        }}
      />
    </div>
  );
}
