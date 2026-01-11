"""
Outcome Intelligence Module

Converts action results into numeric intelligence for learning.

Components:
- OutcomeScorer: Score actions (0-100)
- CausalGraph: Attribute success/failure to actions
- FailureClassifier: Categorize failures
- ConfidenceUpdater: Update tool/policy confidence
"""

from .scorer import (
    OutcomeScorer,
    OutcomeScore,
    ActionOutcome,
    OutcomeCategory,
    OutcomeBatcher,
)

from .causal_graph import (
    CausalGraph,
    CausalNode,
    CausalEdge,
    CausalRelation,
    CausalAttribution,
)

from .failure_classifier import (
    FailureClassifier,
    ClassifiedFailure,
    FailureType,
    FailureSeverity,
    failure_classifier,
)

from .confidence_updater import (
    ConfidenceUpdater,
    ConfidenceRecord,
    confidence_updater,
)


__all__ = [
    # Scorer
    "OutcomeScorer",
    "OutcomeScore",
    "ActionOutcome",
    "OutcomeCategory",
    "OutcomeBatcher",
    # Causal Graph
    "CausalGraph",
    "CausalNode",
    "CausalEdge",
    "CausalRelation",
    "CausalAttribution",
    # Failure Classifier
    "FailureClassifier",
    "ClassifiedFailure",
    "FailureType",
    "FailureSeverity",
    "failure_classifier",
    # Confidence Updater
    "ConfidenceUpdater",
    "ConfidenceRecord",
    "confidence_updater",
]
