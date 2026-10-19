"""Concorde on the NEOS Server through its XML-RPC interface.

A TSPLIB instance is wrapped in the NEOS job document for the Concorde solver, submitted,
polled until completion and the raw result text (the same log the web form returns) is
handed back to the caller, who stores it next to the instance as concorde.sol.
"""

from __future__ import annotations

import time
import xmlrpc.client

from app.config import get_settings

JOB_TEMPLATE = """<document>
<category>co</category>
<solver>concorde</solver>
<inputMethod>TSP</inputMethod>
<email><![CDATA[{email}]]></email>
<inputType><![CDATA[{input_type}]]></inputType>
<tsp><![CDATA[{tsp}]]></tsp>
<algorithm><![CDATA[{algorithm}]]></algorithm>
<fixed><![CDATA[{fixed}]]></fixed>
</document>"""

FIXED_SEED = "99"          # reproducible runs; empty string = random seed


def solve_tsp(tsplib_text: str, input_type: str | None = None, algorithm: str | None = None) -> str:
    """Submit one TSPLIB instance to NEOS/Concorde and return the raw result text."""
    settings = get_settings()
    if not settings.NEOS_EMAIL:
        raise RuntimeError("NEOS_EMAIL is not set (put it in .env.local)")
    job = JOB_TEMPLATE.format(email=settings.NEOS_EMAIL, input_type=input_type or settings.NEOS_INPUT_TYPE,
                              tsp=tsplib_text, algorithm=algorithm or settings.NEOS_ALGORITHM, fixed=FIXED_SEED)
    server = xmlrpc.client.ServerProxy(settings.NEOS_URL)
    number, password = server.submitJob(job)
    if number == 0:
        raise RuntimeError(f"NEOS rejected the job: {password}")
    return _wait_for_result(server, number, password, settings.NEOS_TIMEOUT_S)


def _wait_for_result(server, number: int, password: str, timeout_s: int) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        status = server.getJobStatus(number, password)
        if status == "Done":
            result = server.getFinalResults(number, password)
            return result.data.decode() if isinstance(result, xmlrpc.client.Binary) else str(result)
        if status in ("Unknown Job", "Bad Password"):
            raise RuntimeError(f"NEOS job {number}: {status}")
        time.sleep(5)
    raise TimeoutError(f"NEOS job {number} did not finish within {timeout_s} s")
