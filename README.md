# SpecClarify

Turn vague requirements into executable specs.

## Usage

```bash
# Direct input (JSON)
spec-clarify "I want a small app where users can sign up."

# Direct input with pretty JSON
spec-clarify --pretty "I want a login page."

# Read from file
spec-clarify --input-file requirements.txt

# Write output to file
spec-clarify "User needs dashboard" --output result.json

# Markdown format
spec-clarify "Build an MVP for feedback" --format markdown

# Full example: file in, markdown out
spec-clarify --input-file req.txt --format markdown --output spec.md
```
