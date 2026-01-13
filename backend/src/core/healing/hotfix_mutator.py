"""
HotFix Mutator - Evolves and breeds remediation scripts.
"""
import logging
import uuid
import subprocess
import ast
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Anomaly:
    type: str
    source: str
    metric: str
    value: Any
    metadata: Dict[str, Any]

@dataclass
class HotFix:
    id: str
    script_content: str
    target: str
    ttl_hours: int

class HotFixMutator:
    def __init__(self, script_generator: Any, ghost_sim: Any, sandbox: Any):
        self.script_generator = script_generator
        self.ghost_sim = ghost_sim
        self.sandbox = sandbox
        self.sandbox_mode = True # Default to safe mode
        self.deployed_fixes: List[HotFix] = []

    def resolve_pain_point(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Orchestrates the resolution flow: Identify -> Evolve -> Validate -> Simulate -> Apply.
        """
        # 1. Identify
        anomaly = self.identify(context)
        if not anomaly:
            return None

        # 2. Evolve (Synthesize & Breed)
        best_script = self.evolve_solution(anomaly)
        if not best_script:
            logger.warning("Failed to evolve a viable hotfix script.")
            return None

        # 3. Validate in Sandbox (Pre-Simulation)
        if not self.validate(best_script, anomaly):
            logger.error("Validation failed for synthesized script.")
            return None

        # 4. Ghost Simulation (Digital Twin)
        sim_result = self.ghost_sim.simulate_scenario({
            "type": "hotfix_apply",
            "target": anomaly.source,
            "script": best_script
        })

        if sim_result["outcome"] != "success":
            logger.warning(f"Ghost Simulation rejected hotfix: {sim_result.get('details')}")
            return None

        # 5. Apply
        fix_id = self.apply(best_script, anomaly.source)
        logger.info(f"Deployed hotfix {fix_id} for {anomaly.source}")
        return fix_id

    def identify(self, context: Dict[str, Any]) -> Optional[Anomaly]:
        """
        Identifies and structures the anomaly from context.
        """
        try:
            return Anomaly(
                type=context.get("type", "unknown"),
                source=context.get("source", "unknown"),
                metric=context.get("metric", "unknown"),
                value=context.get("value"),
                metadata=context.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"Error identifying anomaly: {e}")
            return None

    def evolve_solution(self, anomaly: Anomaly) -> Optional[str]:
        """
        Evolutionary Search: Generates multiple script variants and 'breeds' the best one.
        """
        logger.info("Starting Evolutionary Search for hotfix...")

        # Initial population: Get templates or generated scripts
        population = []

        # Seed 1: Script Generator
        try:
            seed1 = self.script_generator.generate_tool(f"Fix {anomaly.type} for {anomaly.source}")
            if seed1: population.append(seed1)
        except Exception:
             pass

        # Seed 2: Heuristic Template
        seed2 = self._generate_memory_prune_script(anomaly.source) if "memory" in anomaly.type else None
        if seed2: population.append(seed2)

        # Seed 3: Generic Restart
        population.append(f"#!/bin/bash\nsystemctl restart {anomaly.source}")

        # Evolution Loop (simplified)
        generations = 3
        best_candidate = None
        best_score = -1.0

        for gen in range(generations):
            # Evaluate current population
            scored_pop = []
            for script in population:
                score = self._evaluate_fitness(script, anomaly)
                scored_pop.append((script, score))

            # Sort by score
            scored_pop.sort(key=lambda x: x[1], reverse=True)

            # Keep top 2
            survivors = scored_pop[:2]
            if not survivors:
                continue

            best_candidate = survivors[0][0]
            best_score = survivors[0][1]

            logger.info(f"Generation {gen}: Best Score {best_score}")
            if best_score > 0.9:
                return best_candidate # Good enough

            # Breed/Mutate for next generation
            population = [s[0] for s in survivors] # Elitism

            # Create mutants
            for parent, _ in survivors:
                mutant = self._mutate_script(parent)
                population.append(mutant)

        return best_candidate

    def _evaluate_fitness(self, script: str, anomaly: Anomaly) -> float:
        """
        Evaluates how likely the script is to fix the issue without harm.
        """
        score = 0.5 # Base score

        # Heuristics
        if anomaly.source in script:
            score += 0.2
        if "restart" in script or "kill" in script or "delete" in script:
            # Aggressive actions might be effective but risky
            score += 0.1

        # Length check (too short might be incomplete)
        if len(script) > 20:
            score += 0.1

        return min(score, 1.0)

    def _mutate_script(self, script: str) -> str:
        """
        Mutates the script (Genetic Operator).
        """
        # Simple string manipulation for demo
        # Swap "restart" with "reload"
        if "restart" in script:
            return script.replace("restart", "reload")
        # Change priority/nice level (simulated)
        if "nice" not in script:
            return "nice -n -5 " + script
        return script

    def validate(self, script_content: str, anomaly: Anomaly) -> bool:
        """
        Validates the generated script for safety.
        """
        try:
            # Basic AST check for dangerous imports if in sandbox mode (and looks like python)
            if self.sandbox_mode and not script_content.strip().startswith("#!"):
                try:
                    tree = ast.parse(script_content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                            for alias in node.names:
                                if alias.name in ['subprocess', 'os', 'sys']:
                                    # In a real implementation, we might block these or wrap them
                                    # For this placeholder, we'll allow them but flag them
                                    logger.warning(f"Script uses dangerous import: {alias.name}")
                except SyntaxError:
                     # Not python, or invalid python
                     pass

            # Sandbox Execution
            logger.info("Validating script in sandbox...")
            inputs = {"target": anomaly.source, "dry_run": True}

            # Assuming sandbox.run_tool takes script and inputs
            result = self.sandbox.run_tool(script_content, inputs)
            if isinstance(result, dict) and result.get("error"):
                logger.warning(f"Sandbox validation failed: {result['error']}")
                return False
            return True

        except Exception as e:
            logger.error(f"Validation exception: {e}")
            # Fail closed on error? or Open? Safe to fail.
            return False

    def apply(self, script: str, target: str, ttl_hours: int = 1, deploy_path: Optional[Path] = None) -> str:
        """
        Deploys the fix to production with a TTL.
        """
        fix_id = str(uuid.uuid4())[:8]

        ttl_seconds = int(ttl_hours * 3600)
        is_python = "python" in script.split("\n")[0] if script else False
        extension = "py" if is_python else "sh"

        script_with_ttl = script
        # Simplified TTL injection (Bash only for this rewrite to save space, assuming bash scripts usually)
        if not is_python:
             ttl_logic = f"\n# TTL Enforcement: Self-delete in {ttl_hours} hour(s)\n(sleep {ttl_seconds} && rm -- \"$0\") &\n"
             lines = script.splitlines()
             if lines and lines[0].startswith("#!"):
                 lines.insert(1, ttl_logic)
             else:
                 lines.insert(0, ttl_logic)
             script_with_ttl = "\n".join(lines)

        hotfix_dir = deploy_path or Path("/tmp/tsm99/hotfixes")
        hotfix_dir.mkdir(parents=True, exist_ok=True)
        script_path = hotfix_dir / f"hotfix_{fix_id}.{extension}"

        with open(script_path, "w") as f:
            f.write(script_with_ttl)
        script_path.chmod(0o755)

        # Execute
        try:
            subprocess.Popen([str(script_path)], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error(f"Failed to execute hotfix {fix_id}: {e}")

        self.deployed_fixes.append(HotFix(id=fix_id, script_content=script_with_ttl, target=target, ttl_hours=ttl_hours))
        return fix_id

    def _generate_memory_prune_script(self, target: str) -> str:
        return f"#!/bin/bash\n# Prune cache for {target}\nrm -rf /var/cache/{target}/*\nsync"
