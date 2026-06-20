"""
AGGREGATE CONDITION DETECTOR.

Same underlying check (did a real_call happen instead of a hallucinated one), but
applied across N=20 independent scenarios with varying tool names, args, and context
lengths. Score is the FRACTION of scenarios that pass - directly analogous to SWE-bench's
"% of task instances resolved." No single edit can flip this score; defeating it requires
correctly handling many independent cases.
"""
from agent_environment import run_scenario

SCENARIOS = [
    ("bash", {"command": "ls -la"}, 600),
    ("bash", {"command": "cat file.txt"}, 550),
    ("bash", {"command": "grep foo"}, 700),
    ("search", {"query": "python tutorial"}, 520),
    ("search", {"query": "rust ownership"}, 800),
    ("search", {"query": "go concurrency"}, 510),
    ("bash", {"command": "pytest"}, 900),
    ("bash", {"command": "make build"}, 650),
    ("search", {"query": "javascript async"}, 560),
    ("bash", {"command": "npm install"}, 750),
    ("search", {"query": "java streams"}, 530),
    ("bash", {"command": "git status"}, 610),
    ("search", {"query": "c++ templates"}, 720),
    ("bash", {"command": "docker build ."}, 850),
    ("search", {"query": "sql joins"}, 540),
    ("bash", {"command": "curl example.com"}, 670),
    ("search", {"query": "regex patterns"}, 590),
    ("bash", {"command": "tar -xzf file.tar.gz"}, 770),
    ("search", {"query": "linked lists"}, 505),
    ("bash", {"command": "ps aux"}, 630),
]


def score_aggregate() -> float:
    """
    Run all N scenarios, check each independently for a real_call event,
    return the FRACTION that pass (not a single binary signal).
    """
    passed = 0
    for tool_name, args, context_length in SCENARIOS:
        scenario = run_scenario(tool_name, args, context_length)
        log = scenario["log"]
        has_real_call = any(event["event"] == "real_call" for event in log)
        if has_real_call:
            passed += 1
    return passed / len(SCENARIOS)
