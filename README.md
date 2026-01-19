# idc-skill

A skill for exploring cancer imaging data from the Imaging Data Commons (IDC).

## Installation

### Download from GitHub Releases

The latest release is always available at:
[https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill](https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill)

All versioned releases can be found at:
[https://github.com/mhalle/idc-skill/releases](https://github.com/mhalle/idc-skill/releases)

### Claude Code

Download and extract to your `.claude/skills/` directory:

**Project-level** (applies to a specific project):
```bash
curl -LO https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill
unzip idc-skill.skill -d /path/to/your/project/.claude/skills/
```

**User-level** (applies globally):
```bash
curl -LO https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill
unzip idc-skill.skill -d ~/.claude/skills/
```

Or clone the repository directly:
```bash
git clone https://github.com/mhalle/idc-skill.git ~/.claude/skills/idc-skill
```

### Claude Platform

1. Download the latest `.skill` file from [GitHub Releases](https://github.com/mhalle/idc-skill/releases/latest)

2. Upload `idc-skill.skill` through the Claude platform skill installation interface.

## Checking for Updates

The installed skill version is stored in the `metadata.version` field of `SKILL.md`.

To check for updates, compare your installed version against the latest release:

```bash
# Get latest release version from GitHub
curl -s https://api.github.com/repos/mhalle/idc-skill/releases/latest | grep '"tag_name"'
```

**Note:** Automatic version checking requires platform support. The skill includes its version in the frontmatter metadata, but discovering the installed version programmatically depends on the host environment's capabilities.

See [references/updating.md](references/updating.md) for detailed update procedures.

## Usage

Once installed, the skill is triggered automatically when you mention:
- IDC
- Imaging Data Commons
- IDC collections

You can also invoke it directly with `/idc-skill`.

## Contents

- `SKILL.md` - Main skill instructions and workflows
- `references/schema_reference.md` - Database schema documentation
- `references/query_patterns.md` - SQL query examples
- `references/updating.md` - Detailed update procedures for different platforms

## Developer

### Releasing a New Version

The version number in `SKILL.md` (under `metadata.version`) must be kept in sync with the git tag.

When releasing:

1. Update `metadata.version` in `SKILL.md` to match the new version
2. Commit the change
3. Create a matching git tag (with `v` prefix):
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

The GitHub Actions workflow will automatically package and publish the `.skill` files when a tag is pushed.
