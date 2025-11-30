"""URL validation and parsing utilities for GitHub repositories."""
import re
from typing import Tuple, Optional


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_github_url(url: str) -> Tuple[str, str]:
    """
    Validate and parse a GitHub repository URL.
    
    Args:
        url: GitHub repository URL in format:
             - https://github.com/{owner}/{repo}
             - github.com/{owner}/{repo}
    
    Returns:
        Tuple of (owner, repo)
    
    Raises:
        ValidationError: If URL format is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError(
            "Invalid GitHub URL format. Expected: https://github.com/{owner}/{repo}"
        )
    
    # Remove trailing slashes and whitespace
    url = url.strip().rstrip('/')
    
    # Pattern to match GitHub URLs
    # Supports: https://github.com/owner/repo or github.com/owner/repo
    pattern = r'^(?:https?://)?github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)$'
    
    match = re.match(pattern, url)
    
    if not match:
        raise ValidationError(
            "Invalid GitHub URL format. Expected: https://github.com/{owner}/{repo} "
            "or github.com/{owner}/{repo}"
        )
    
    owner, repo = match.groups()
    
    # Remove .git suffix if present
    if repo.endswith('.git'):
        repo = repo[:-4]
    
    return owner, repo


def parse_github_url(url: str) -> Optional[dict]:
    """
    Parse GitHub URL and return structured data.
    
    Args:
        url: GitHub repository URL
    
    Returns:
        Dictionary with 'owner', 'repo', and 'url' keys, or None if invalid
    """
    try:
        owner, repo = validate_github_url(url)
        return {
            'owner': owner,
            'repo': repo,
            'url': f'https://github.com/{owner}/{repo}'
        }
    except ValidationError:
        return None
