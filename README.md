# idc-skill

A skill for exploring cancer imaging data from the Imaging Data Commons (IDC).

## Installation

### Claude Code

Copy the `idc-skill` folder to your `.claude/skills/` directory:

**Project-level** (applies to a specific project):
```bash
cp -r idc-skill /path/to/your/project/.claude/skills/
```

**User-level** (applies globally):
```bash
cp -r idc-skill ~/.claude/skills/
```

### Claude Platform

1. Zip the skill folder (skill zipfiles typically use the `.skill` extension):
   ```bash
   zip -r idc-skill.skill idc-skill
   ```

2. Upload `idc-skill.skill` through the Claude platform skill installation interface.

## Usage

Once installed, the skill is triggered automatically when you ask about:
- IDC collections or datasets
- Cancer imaging data
- DICOM series queries
- CT, MR, PET scans
- Medical imaging metadata

You can also invoke it directly with `/idc-skill`.

## Contents

- `SKILL.md` - Main skill instructions and workflows
- `references/schema_reference.md` - Database schema documentation
- `references/query_patterns.md` - SQL query examples
