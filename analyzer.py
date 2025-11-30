"""Repository analyzer using GitHub API via MCP."""
import requests
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from models import AnalysisResult, RepoMetadata, FileTreeSummary


class AnalyzerError(Exception):
    """Custom exception for analyzer errors."""
    pass


class RepositoryAnalyzer:
    """Analyzes GitHub repositories using GitHub API."""
    
    GITHUB_API_BASE = "https://api.github.com"
    
    # Package manifest files to detect
    MANIFEST_FILES = {
        'package.json': 'Node.js',
        'requirements.txt': 'Python',
        'pyproject.toml': 'Python',
        'Pipfile': 'Python',
        'go.mod': 'Go',
        'Cargo.toml': 'Rust',
        'pom.xml': 'Java/Maven',
        'build.gradle': 'Java/Gradle',
        'Gemfile': 'Ruby',
        'composer.json': 'PHP'
    }
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize analyzer.
        
        Args:
            token: Optional GitHub Personal Access Token for private repos
        """
        self.token = token
        self.headers = {}
        if token:
            self.headers['Authorization'] = f'token {token}'
    
    def fetch_repo_metadata(self, owner: str, repo: str) -> RepoMetadata:
        """
        Fetch repository metadata from GitHub API.
        
        Args:
            owner: Repository owner
            repo: Repository name
        
        Returns:
            RepoMetadata object
        
        Raises:
            AnalyzerError: If API request fails
        """
        url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return RepoMetadata(
                name=data['name'],
                owner=data['owner']['login'],
                description=data.get('description', ''),
                stars=data.get('stargazers_count', 0),
                forks=data.get('forks_count', 0),
                default_branch=data.get('default_branch', 'main'),
                url=data['html_url']
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise AnalyzerError("Repository not found. Check URL and access permissions.")
            elif e.response.status_code == 403:
                # Check if it's rate limiting
                if 'rate limit' in e.response.text.lower() or 'x-ratelimit-remaining' in e.response.headers:
                    remaining = e.response.headers.get('x-ratelimit-remaining', '0')
                    reset_time = e.response.headers.get('x-ratelimit-reset', 'unknown')
                    raise AnalyzerError(f"GitHub API rate limit exceeded. Remaining: {remaining}. Please try again later or provide a GitHub Personal Access Token for higher limits.")
                else:
                    raise AnalyzerError("Access forbidden. This repository may be private or require authentication. Please provide a Personal Access Token.")
            elif e.response.status_code == 401:
                raise AnalyzerError("Invalid or expired Personal Access Token.")
            else:
                raise AnalyzerError(f"GitHub API error: {e.response.status_code}")
        except requests.exceptions.Timeout:
            raise AnalyzerError("GitHub API request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            raise AnalyzerError(f"Network error: {str(e)}")
    
    def fetch_file_tree(self, owner: str, repo: str, branch: str) -> List[dict]:
        """
        Fetch complete file tree recursively.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
        
        Returns:
            List of file/directory objects
        
        Raises:
            AnalyzerError: If API request fails
        """
        url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
        params = {'recursive': '1'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('truncated'):
                raise AnalyzerError("Repository too large for analysis. Try a smaller repository.")
            
            return data.get('tree', [])
        except requests.exceptions.HTTPError as e:
            raise AnalyzerError(f"Failed to fetch file tree: {e.response.status_code}")
        except requests.exceptions.Timeout:
            raise AnalyzerError("File tree request timed out. Repository may be too large.")
        except requests.exceptions.RequestException as e:
            raise AnalyzerError(f"Network error fetching file tree: {str(e)}")
    
    def fetch_languages(self, owner: str, repo: str) -> Dict[str, float]:
        """
        Fetch language breakdown.
        
        Args:
            owner: Repository owner
            repo: Repository name
        
        Returns:
            Dictionary of language: percentage
        """
        url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/languages"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Convert byte counts to percentages
            total = sum(data.values())
            if total == 0:
                return {}
            
            return {lang: (bytes / total) * 100 for lang, bytes in data.items()}
        except Exception:
            # Language data is optional, return empty dict on error
            return {}
    
    def identify_package_manifests(self, file_tree: List[dict]) -> List[str]:
        """
        Identify package manifest files in the tree.
        
        Args:
            file_tree: List of file objects from GitHub API
        
        Returns:
            List of manifest filenames found
        """
        manifests = []
        for item in file_tree:
            if item['type'] == 'blob':
                filename = item['path'].split('/')[-1]
                if filename in self.MANIFEST_FILES:
                    manifests.append(filename)
        
        return list(set(manifests))  # Remove duplicates
    
    def detect_tech_stack(self, file_tree: List[dict], languages: Dict[str, float], 
                         manifests: List[str]) -> List[str]:
        """
        Detect technology stack from file patterns and languages.
        
        Args:
            file_tree: List of file objects
            languages: Language breakdown
            manifests: Package manifest files
        
        Returns:
            List of detected technologies
        """
        stack = []
        
        # Add languages
        stack.extend(languages.keys())
        
        # Add frameworks from manifests
        for manifest in manifests:
            if manifest in self.MANIFEST_FILES:
                tech = self.MANIFEST_FILES[manifest]
                if tech not in stack:
                    stack.append(tech)
        
        # Detect common frameworks from file patterns
        file_paths = [item['path'] for item in file_tree if item['type'] == 'blob']
        
        # Frontend frameworks
        if any('react' in path.lower() for path in file_paths):
            stack.append('React')
        if any('vue' in path.lower() for path in file_paths):
            stack.append('Vue.js')
        if any('angular' in path.lower() for path in file_paths):
            stack.append('Angular')
        
        # Backend frameworks
        if any('flask' in path.lower() or 'app.py' in path for path in file_paths):
            stack.append('Flask')
        if any('django' in path.lower() for path in file_paths):
            stack.append('Django')
        if any('express' in path.lower() for path in file_paths):
            stack.append('Express.js')
        
        # Databases
        if any('postgres' in path.lower() or 'pg' in path.lower() for path in file_paths):
            stack.append('PostgreSQL')
        if any('mongo' in path.lower() for path in file_paths):
            stack.append('MongoDB')
        if any('redis' in path.lower() for path in file_paths):
            stack.append('Redis')
        
        return list(set(stack))  # Remove duplicates
    
    def analyze_file_tree(self, file_tree: List[dict]) -> FileTreeSummary:
        """
        Analyze file tree structure.
        
        Args:
            file_tree: List of file objects
        
        Returns:
            FileTreeSummary object
        """
        files = [item for item in file_tree if item['type'] == 'blob']
        dirs = [item for item in file_tree if item['type'] == 'tree']
        
        # Get top-level structure
        top_level = set()
        for item in file_tree:
            parts = item['path'].split('/')
            if len(parts) > 0:
                top_level.add(parts[0] + ('/' if len(parts) > 1 else ''))
        
        # Calculate max depth
        max_depth = max((len(item['path'].split('/')) for item in file_tree), default=0)
        
        return FileTreeSummary(
            total_files=len(files),
            total_dirs=len(dirs),
            top_level_structure=sorted(list(top_level))[:20],  # Limit to 20 items
            max_depth=max_depth
        )
    
    def suggest_setup_steps(self, manifests: List[str], languages: Dict[str, float]) -> List[str]:
        """
        Suggest setup steps based on detected manifests.
        
        Args:
            manifests: List of package manifest files
            languages: Language breakdown
        
        Returns:
            List of setup step hints
        """
        hints = []
        
        if 'package.json' in manifests:
            hints.append("Node.js project detected")
            hints.append("Run: npm install")
        
        if 'requirements.txt' in manifests:
            hints.append("Python project detected")
            hints.append("Run: pip install -r requirements.txt")
        
        if 'pyproject.toml' in manifests:
            hints.append("Python Poetry project detected")
            hints.append("Run: poetry install")
        
        if 'go.mod' in manifests:
            hints.append("Go project detected")
            hints.append("Run: go mod download")
        
        if 'Cargo.toml' in manifests:
            hints.append("Rust project detected")
            hints.append("Run: cargo build")
        
        if 'Gemfile' in manifests:
            hints.append("Ruby project detected")
            hints.append("Run: bundle install")
        
        if not hints and languages:
            primary_lang = max(languages.items(), key=lambda x: x[1])[0]
            hints.append(f"Primary language: {primary_lang}")
        
        return hints
    
    def analyze_repository(self, owner: str, repo: str) -> AnalysisResult:
        """
        Perform complete repository analysis.
        
        Args:
            owner: Repository owner
            repo: Repository name
        
        Returns:
            AnalysisResult object
        
        Raises:
            AnalyzerError: If analysis fails
        """
        # Fetch metadata
        repo_meta = self.fetch_repo_metadata(owner, repo)
        
        # Fetch file tree
        file_tree = self.fetch_file_tree(owner, repo, repo_meta.default_branch)
        
        # Fetch languages
        languages = self.fetch_languages(owner, repo)
        
        # Identify manifests
        manifests = self.identify_package_manifests(file_tree)
        
        # Detect tech stack
        detected_stack = self.detect_tech_stack(file_tree, languages, manifests)
        
        # Analyze file tree
        file_tree_summary = self.analyze_file_tree(file_tree)
        
        # Generate hints
        hints = self.suggest_setup_steps(manifests, languages)
        
        return AnalysisResult(
            repo_meta=repo_meta,
            languages=languages,
            file_tree_summary=file_tree_summary,
            detected_stack=detected_stack,
            package_manifests=manifests,
            hints=hints,
            cached_at=datetime.now()
        )
