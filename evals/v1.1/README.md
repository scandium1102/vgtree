# VGTREE v1.1 evaluation fixtures

These fixtures test deterministic contracts for website, vision, research, ROS observation, agent runtime, and Context Budget selection.

`python scripts/validate_v1_1_evals.py` validates the committed fixture shapes with the standard library. The behavioral result example is shape-only and is not counted as a measured trial.

A measured behavioral result must disclose the provider, model selector, reasoning setting, date, available tools, trial count, fixture digest, artifact references, and claim scope. Results apply only to the recorded environment; they are not universal token, quality, or productivity claims.

The ROS observer fixture is read-only. It must never add `cmd-vel`, actuator commands, or control mutation.
