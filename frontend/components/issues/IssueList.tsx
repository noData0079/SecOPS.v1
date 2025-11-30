"use client";

import React from "react";
import IssueCard from "./IssueCard";
import Loader from "../shared/Loader";
import EmptyState from "../shared/EmptyState";
import { Issue } from "@/lib/types";

interface IssueListProps {
  loading: boolean;
  issues: Issue[];
  onSelect?: (issue: Issue) => void; // optional click handler
}

const IssueList: React.FC<IssueListProps> = ({ loading, issues, onSelect }) => {
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader />
      </div>
    );
  }

  if (!issues || issues.length === 0) {
    return (
      <EmptyState
        title="No Issues Found"
        description="Run security checks or sync integrations to populate issues."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4">
      {issues.map((issue) => (
        <IssueCard
          key={issue.id}
          issue={issue}
          onClick={() => onSelect?.(issue)}
        />
      ))}
    </div>
  );
};

export default IssueList;
