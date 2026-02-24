import re
import logging
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

def register(mcp: FastMCP):
    @mcp.tool()
    def format_commit_message(type: str, scope: str, description: str, body: str = "", footer: str = "") -> str:
        """
        Format a commit message according to Conventional Commits specification.
        
        Args:
            type: Commit type (feat, fix, docs, style, refactor, test, chore, perf).
            scope: Scope of the change (e.g., auth, api, filename). Optional.
            description: Short description in imperative mood.
            body: Optional detailed body.
            footer: Optional footer (e.g., BREAKING CHANGE, Closes #123).
        
        Returns:
            Formatted commit message string.
        """
        # Validate type
        valid_types = ["feat", "fix", "docs", "style", "refactor", "test", "chore", "perf"]
        if type not in valid_types:
            return f"❌ Error: Invalid type '{type}'. Must be one of: {', '.join(valid_types)}"
        
        # Build header
        if scope:
            header = f"{type}({scope}): {description}"
        else:
            header = f"{type}: {description}"
            
        message = [header]
        
        if body:
            message.append("")
            message.append(body)
            
        if footer:
            message.append("")
            message.append(footer)
            
        return "\n".join(message)

    @mcp.tool()
    def validate_branch_name(name: str) -> str:
        """
        Validate if a branch name follows the 'type/short-description' convention.
        
        Usage Heuristics:
        - Use before creating a new branch to ensure compliance.
        
        Returns:
            '✅ Valid' or an error message with examples.
        """
        pattern = r'^(feature|fix|hotfix|refactor|docs)/[a-z0-9-]+$'
        if re.match(pattern, name):
            return f"✅ Valid branch name: {name}"
            
        return (
            f"❌ Invalid branch name: '{name}'.\n"
            "Format: type/short-description (lowercase, hyphens)\n"
            "Examples:\n"
            "  - feature/oauth-login\n"
            "  - fix/null-pointer\n"
            "  - docs/update-readme"
        )

    @mcp.tool()
    def get_pr_template(type: str) -> str:
        """
        Get the standard PR body template.
        
        Args:
            type: 'default' is currently the only supported type.
            
        Returns:
            Markdown string for PR body.
        """
        return """## Summary
[1-2 sentence description of what this PR does]

## Changes
- [Bullet list of specific changes]
- [Include file names when helpful]

## Testing
- [ ] Unit tests pass
- [ ] Manual testing completed
- [ ] No regressions

## Related
- Closes #<issue_number>
"""
