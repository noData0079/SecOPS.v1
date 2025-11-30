"use client";

import React, { useState } from "react";
import clsx from "clsx";
import { Copy, Check, ChevronDown, ChevronRight } from "lucide-react";

interface IssueFixBlockProps {
  title?: string;                   // e.g. "Suggested Fix", "AI-Generated Resolution"
  fixText: string;                  // markdown / plaintext fix explanation
  codeBlock?: string;               // optional code patch / commands
  collapsedByDefault?: boolean;     // whether the block starts collapsed
}

/* -------------------------------------------------------------------------- */
/*                            Copy Button (Reusable)                           */
/* -------------------------------------------------------------------------- */

const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch (err) {
      console.error("Copy failed:", err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={clsx(
        "flex items-center gap-1 px-2 py-1 text-xs font-medium",
        "rounded-md bg-neutral-100 hover:bg-neutral-200 text-neutral-700 border border-neutral-300",
        "transition-all"
      )}
    >
      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
};

/* -------------------------------------------------------------------------- */
/*                               Main Component                                */
/* -------------------------------------------------------------------------- */

const IssueFixBlock: React.FC<IssueFixBlockProps> = ({
  title = "Suggested Fix",
  fixText,
  codeBlock,
  collapsedByDefault = false,
}) => {
  const [open, setOpen] = useState(!collapsedByDefault);

  return (
    <div className="w-full p-4 border rounded-xl bg-white shadow-sm mt-4">
      {/* Header */}
      <div
        className="flex items-center justify-between cursor-pointer select-none"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-2">
          {open ? (
            <ChevronDown className="w-4 h-4 text-neutral-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-neutral-500" />
          )}
          <h3 className="font-semibold text-neutral-900">{title}</h3>
        </div>
      </div>

      {/* Body */}
      {open && (
        <div className="mt-3 space-y-4">
          {/* Fix Explanation */}
          <div className="text-sm text-neutral-700 leading-relaxed whitespace-pre-line">
            {fixText}
          </div>

          {/* Code Block */}
          {codeBlock && (
            <div className="relative mt-2 border rounded-lg bg-neutral-900 text-neutral-100 p-3 font-mono text-xs overflow-x-auto">
              <div className="absolute top-2 right-2">
                <CopyButton text={codeBlock} />
              </div>

              <pre className="whitespace-pre">
                <code>{codeBlock}</code>
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default IssueFixBlock;
