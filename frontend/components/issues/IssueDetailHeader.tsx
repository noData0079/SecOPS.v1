"use client";

import React from "react";
import clsx from "clsx";
import { Issue } from "@/lib/types";
import IssueSeverityIndicator from "./IssueSeverityIndicator";
import IssueStatusIndicator from "./IssueStatusIndicator";
import Button from "../shared/Button";

interface IssueDetailHeaderProps {
  issue: Issue;
  onResolve?: (issueId: string) => void;
  className?: string;
}

const IssueDetailHeader: React.FC<IssueDetailHeaderProps> = ({
  issue,
  onResolve,
  className,
}) => {
  return (
    <div className={clsx("border-b pb-4 flex flex-col gap-3", className)}>
      {/* Title Row */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Left: Issue Title */}
        <div>
          <h1 className="text-xl font-semibold text-neutral-900">
            {issue.title}
          </h1>

          <div className="mt-1 flex gap-4 items-center">
            <IssueSeverityIndicator severity={issue.severity} size="sm" />
            <IssueStatusIndicator status={issue.status} size="sm" />
          </div>
        </div>

        {/* Right: Resolve Button */}
        {onResolve && issue.status !== "resolved" && (
          <Button
            variant="primary"
            onClick={() => onResolve(issue.id)}
            className="w-fit"
          >
            Mark as Resolved
          </Button>
        )}
      </div>

      {/* Metadata Row */}
      <div className="text-sm text-neutral-600 flex flex-wrap gap-4 mt-1">
        <span>
          <span className="font-medium text-neutral-700">Issue ID:</span>{" "}
          {issue.id}
        </span>

        {issue.created_at && (
          <span>
            <span className="font-medium text-neutral-700">Created:</span>{" "}
            {new Date(issue.created_at).toLocaleString()}
          </span>
        )}

        {issue.source && (
          <span>
            <span className="font-medium text-neutral-700">Source:</span>{" "}
            {issue.source}
          </span>
        )}
      </div>
    </div>
  );
};

export default IssueDetailHeader;
