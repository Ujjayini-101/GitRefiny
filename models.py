"""Data models for GitRefiny."""
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime


@dataclass
class RepoMetadata:
    """Repository metadata from GitHub API."""
    name: str
    owner: str
    description: str
    stars: int
    forks: int
    default_branch: str
    url: str


@dataclass
class FileTreeSummary:
    """Summary of repository file tree."""
    total_files: int
    total_dirs: int
    top_level_structure: List[str]
    max_depth: int


@dataclass
class AnalysisResult:
    """Complete repository analysis result."""
    repo_meta: RepoMetadata
    languages: Dict[str, float]
    file_tree_summary: FileTreeSummary
    detected_stack: List[str]
    package_manifests: List[str]
    hints: List[str]
    cached_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'repo_meta': {
                'name': self.repo_meta.name,
                'owner': self.repo_meta.owner,
                'description': self.repo_meta.description,
                'stars': self.repo_meta.stars,
                'forks': self.repo_meta.forks,
                'default_branch': self.repo_meta.default_branch,
                'url': self.repo_meta.url
            },
            'languages': self.languages,
            'file_tree_summary': {
                'total_files': self.file_tree_summary.total_files,
                'total_dirs': self.file_tree_summary.total_dirs,
                'top_level_structure': self.file_tree_summary.top_level_structure,
                'max_depth': self.file_tree_summary.max_depth
            },
            'detected_stack': self.detected_stack,
            'package_manifests': self.package_manifests,
            'hints': self.hints
        }


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
