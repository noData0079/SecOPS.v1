# backend/src/integrations/iac/terraform.py

from __future__ import annotations

import logging
import shutil
import subprocess
from typing import Dict, List, Optional

from src.utils.config import Settings

logger = logging.getLogger(__name__)


class TerraformClient:
    """
    Wrapper around the Terraform CLI.

    This client assumes 'terraform' is installed and available in the PATH,
    or configured via Settings.TERRAFORM_BINARY_PATH.

    It executes commands in a specified working directory.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.binary_path = getattr(settings, "TERRAFORM_BINARY_PATH", "terraform")
        if not shutil.which(self.binary_path):
            logger.warning(
                "Terraform binary '%s' not found. IaC features will fail.",
                self.binary_path,
            )

    def _run_command(
        self, args: List[str], working_dir: str
    ) -> subprocess.CompletedProcess[str]:
        """
        Run a terraform command.
        """
        cmd = [self.binary_path] + args
        logger.info("Running Terraform: %s in %s", " ".join(cmd), working_dir)

        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                check=False,  # We handle return codes manually
            )
            if result.returncode != 0:
                logger.error(
                    "Terraform command failed: %s\nStdout: %s\nStderr: %s",
                    " ".join(cmd),
                    result.stdout,
                    result.stderr,
                )
            return result
        except FileNotFoundError:
            logger.error("Terraform binary not found at execution time.")
            raise RuntimeError("Terraform binary not found")
        except Exception as e:
            logger.exception("Unexpected error running Terraform")
            raise RuntimeError(f"Terraform execution failed: {e}") from e

    def init(self, working_dir: str) -> str:
        """
        Run 'terraform init'.
        Returns stdout if successful, raises RuntimeError otherwise.
        """
        res = self._run_command(["init", "-no-color"], working_dir)
        if res.returncode != 0:
            raise RuntimeError(f"terraform init failed: {res.stderr}")
        return res.stdout

    def plan(self, working_dir: str, out_file: Optional[str] = None) -> str:
        """
        Run 'terraform plan'.
        """
        args = ["plan", "-no-color", "-input=false"]
        if out_file:
            args.extend(["-out", out_file])

        res = self._run_command(args, working_dir)
        if res.returncode != 0:
            raise RuntimeError(f"terraform plan failed: {res.stderr}")
        return res.stdout

    def apply(self, working_dir: str, plan_file: Optional[str] = None) -> str:
        """
        Run 'terraform apply'.
        """
        args = ["apply", "-no-color", "-input=false", "-auto-approve"]
        if plan_file:
            args.append(plan_file)

        res = self._run_command(args, working_dir)
        if res.returncode != 0:
            raise RuntimeError(f"terraform apply failed: {res.stderr}")
        return res.stdout

    def destroy(self, working_dir: str) -> str:
        """
        Run 'terraform destroy'.
        """
        args = ["destroy", "-no-color", "-input=false", "-auto-approve"]
        res = self._run_command(args, working_dir)
        if res.returncode != 0:
            raise RuntimeError(f"terraform destroy failed: {res.stderr}")
        return res.stdout
