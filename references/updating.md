# Updating the Skill

**Note:** This update workflow is specific to Claude and the Claude platform. Other AI agents or configurations may use different conventions for skill management.

## Version Information

The installed skill version is stored in the SKILL.md frontmatter:

```yaml
metadata:
  version: 0.1.0
  repository: https://github.com/mhalle/idc-skill
```

## Checking for Updates

To check if a newer version is available:

**Recommended approach:** Use bash with curl to query the GitHub API directly:
```bash
curl -s https://api.github.com/repos/mhalle/idc-skill/releases/latest
```

Parse the JSON response to extract the `tag_name` field (e.g., `v0.2.0`) and compare against the installed `metadata.version` (strip the `v` prefix for comparison).

**Alternative approaches** (less reliable in restricted environments):
- `web_search` may not find the specific repository
- `web_fetch` requires the URL from search results or user input first

## Updating on Claude Platform

If a newer version is available and the user wants to update:

1. **Inform the user** that a new version is available, noting what version they have and what the latest version is.

2. **Offer to download the update.** If the user accepts:

3. **Download the latest skill package** from:
   ```
   https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill
   ```

4. **Present the `.skill` file to the user as an output file.** The user can then:
   - Download the file from the conversation
   - Install the updated skill through the Claude platform skill management interface

## Updating in Claude Code

For Claude Code installations, the user can update manually:

**If installed via git clone:**
```bash
cd ~/.claude/skills/idc-skill  # or project-level path
git pull origin main
```

**If installed from a release:**
```bash
curl -L https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill -o idc-skill.zip
unzip -o idc-skill.zip -d ~/.claude/skills/
```

## Version History

See the [GitHub releases page](https://github.com/mhalle/idc-skill/releases) for a complete version history and changelog.
