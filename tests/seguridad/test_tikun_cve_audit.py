"""Tikún del Tikún — Structural regression test for dependency CVEs.

Ensures pip-audit reports 0 known vulnerabilities in installed packages.
Prevents WI-269-class regressions (CVEs creeping back via transitive deps).

Requires: pip-audit (pip install pip-audit)
"""
import subprocess
import sys
import unittest


class TestCVEAudit(unittest.TestCase):
    """Validates that all installed Python packages are free of known CVEs."""

    def test_zero_known_cves(self):
        """pip-audit debe reportar 0 vulnerabilidades conocidas."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip_audit", "--progress-spinner=off"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
        except FileNotFoundError:
            self.skipTest("pip-audit no instalado (pip install pip-audit)")
        except subprocess.TimeoutExpired:
            self.skipTest("pip-audit timeout (>120s) — posible problema de red")

        if result.returncode != 0:
            # Extract vulnerability lines (skip header/footer noise)
            lines = result.stdout.strip().split("\n")
            vuln_lines = [l for l in lines if "PYSEC-" in l or "CVE-" in l or "GHSA-" in l]
            detail = "\n".join(vuln_lines[:10]) if vuln_lines else result.stdout[-500:]
            self.fail(
                f"pip-audit encontró vulnerabilidades ({len(vuln_lines)} CVEs):\n{detail}"
            )


if __name__ == "__main__":
    unittest.main()

