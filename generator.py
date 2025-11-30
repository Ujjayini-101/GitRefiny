"""README generator using AI models."""
from typing import List, Optional, Dict
from models import AnalysisResult
import os
import requests
import json


class GeneratorError(Exception):
    """Custom exception for generator errors."""
    pass


class READMEGenerator:
    """Generates README content using external AI APIs."""
    
    # Default sections for README
    DEFAULT_SECTIONS = [
        'title', 'description', 'features', 'architecture',
        'file_structure', 'tech_stack', 'setup', 'usage',
        'api_endpoints', 'contributing'
    ]
    
    # API Configuration - FREE TIER APIs
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    
    def __init__(self):
        """Initialize README generator."""
        self.use_ai = bool(self.GROQ_API_KEY)
    

    
    def _call_groq_api(self, prompt: str) -> str:
        """
        Call Groq API with Llama 3 for README generation (FREE TIER).
        
        Args:
            prompt: The prompt with repository analysis
        
        Returns:
            Generated README markdown
        """
        if not self.GROQ_API_KEY:
            raise GeneratorError("Groq API key not configured")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert technical writer who creates beautiful, comprehensive README files for GitHub repositories."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 8000,
            "temperature": 0.7
        }
        
        try:
            print("Calling Groq API with Llama 3.3 70B...")
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            # Log response status
            print(f"Groq API response status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text
                print(f"Groq API error response: {error_detail}")
                
                # Handle specific error codes
                if response.status_code == 429:
                    raise GeneratorError("Groq API rate limit exceeded. Please wait a few minutes and try again.")
                elif response.status_code == 401:
                    raise GeneratorError("Groq API key is invalid or expired. Please check your API key.")
                elif response.status_code == 403:
                    raise GeneratorError("Groq API access forbidden. Please check your API key permissions.")
                else:
                    raise GeneratorError(f"Groq API returned {response.status_code}: {error_detail}")
            
            result = response.json()
            
            # Check if response has expected structure
            if 'choices' not in result or not result['choices']:
                raise GeneratorError(f"Groq API returned unexpected response structure: {result}")
            
            content = result['choices'][0]['message']['content']
            print(f"Groq API success! Generated {len(content)} characters")
            return content
            
        except requests.exceptions.Timeout:
            raise GeneratorError("Groq API request timed out after 60 seconds")
        except requests.exceptions.ConnectionError:
            raise GeneratorError("Failed to connect to Groq API. Check your internet connection.")
        except requests.exceptions.RequestException as e:
            raise GeneratorError(f"Groq API request failed: {str(e)}")
        except KeyError as e:
            raise GeneratorError(f"Groq API response missing expected field: {str(e)}")
        except Exception as e:
            raise GeneratorError(f"Groq API error: {str(e)}")
    
    def build_prompt(self, analysis: AnalysisResult, sections: Optional[List[str]] = None,
                    tone: str = 'professional') -> str:
        """
        Build comprehensive AI prompt from analysis data.
        
        Args:
            analysis: Repository analysis result
            sections: List of sections to include (None = all)
            tone: Tone for content (professional/concise/enthusiastic)
        
        Returns:
            Formatted prompt string for AI
        """
        if sections is None:
            sections = self.DEFAULT_SECTIONS
        
        # Tone instructions
        tone_instructions = {
            'professional': 'Use a professional, technical tone suitable for enterprise documentation.',
            'concise': 'Be brief and to-the-point. Use short sentences and bullet points.',
            'enthusiastic': 'Use an enthusiastic, engaging tone that excites developers about the project.'
        }
        
        tone_instruction = tone_instructions.get(tone, tone_instructions['professional'])
        
        # Format languages with percentages
        languages_text = ""
        if analysis.languages:
            sorted_langs = sorted(analysis.languages.items(), key=lambda x: x[1], reverse=True)
            languages_text = "\n".join([f"- {lang}: {pct:.1f}%" for lang, pct in sorted_langs[:5]])
        
        # Format tech stack
        tech_stack_text = ", ".join(analysis.detected_stack) if analysis.detected_stack else "Not detected"
        
        # Format file structure
        file_structure_text = "\n".join(analysis.file_tree_summary.top_level_structure[:20])
        
        # Build comprehensive prompt
        prompt = f"""You are an expert technical writer creating a beautiful, professional README.md for a GitHub repository.

REPOSITORY INFORMATION:
- Name: {analysis.repo_meta.name}
- Owner: {analysis.repo_meta.owner}
- Description: {analysis.repo_meta.description}
- Stars: {analysis.repo_meta.stars}
- Forks: {analysis.repo_meta.forks}
- URL: {analysis.repo_meta.url}

PROGRAMMING LANGUAGES:
{languages_text}

DETECTED TECH STACK:
{tech_stack_text}

PACKAGE MANIFESTS FOUND:
{', '.join(analysis.package_manifests) if analysis.package_manifests else 'None'}

FILE STRUCTURE (Top Level):
{file_structure_text}

PROJECT STATISTICS:
- Total Files: {analysis.file_tree_summary.total_files}
- Total Directories: {analysis.file_tree_summary.total_dirs}
- Max Depth: {analysis.file_tree_summary.max_depth}

SETUP HINTS:
{chr(10).join(analysis.hints)}

INSTRUCTIONS:
{tone_instruction}

IMPORTANT - MERMAID ARCHITECTURE DIAGRAMS:
You MUST create detailed, professional Mermaid diagrams that will render as VISUAL FLOWCHARTS.

**CRITICAL: Use PROPER Mermaid syntax - diagrams will render as visual graphics on GitHub!**

**Example 1 - Full Stack Web App:**
Use this Mermaid syntax (with triple backticks):
graph TB
    A[User/Browser] -->|HTTP Request| B[Frontend<br/>React/HTML/CSS/JS]
    B -->|API Calls| C[Backend API<br/>Node.js/Python]
    C -->|Query| D[(Database<br/>PostgreSQL/MongoDB)]
    D -->|Data| C
    C -->|JSON Response| B
    B -->|Render| A
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9

**Example 2 - Detailed Full Stack with Styling:**
Use this Mermaid syntax (with triple backticks):
flowchart TD
    Start([User Login]) --> Survey[Takes Career Survey]
    Survey --> Analysis[AI: Analyze Profile]
    Analysis --> Suggestions[AI Career Suggestions<br/>3 Categories]
    Suggestions --> Display[Display Results]
    Display --> End([User Reviews])
    
    style Start fill:#4CAF50,stroke:#2E7D32,color:#fff
    style Survey fill:#2196F3,stroke:#1565C0,color:#fff
    style Analysis fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style Suggestions fill:#FF9800,stroke:#E65100,color:#fff
    style Display fill:#00BCD4,stroke:#006064,color:#fff
    style End fill:#4CAF50,stroke:#2E7D32,color:#fff

**Example 3 - Backend API Flow:**
Use this Mermaid syntax (with triple backticks):
graph TB
    A[Client Request] -->|HTTP| B{{API Gateway}}
    B -->|Auth| C[Authentication]
    C -->|Valid| D[Business Logic]
    C -->|Invalid| E[Error Response]
    D -->|Query| F[(Database)]
    F -->|Data| D
    D -->|Process| G[Response Formatter]
    G -->|JSON| H[Client]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#ffebee
    style F fill:#e0f2f1
    style G fill:#fce4ec
    style H fill:#e1f5fe

**IMPORTANT STYLING RULES:**
- Use `style NodeName fill:#COLOR` to add colors
- Use descriptive node labels with `<br/>` for line breaks
- Use different shapes: `[]` for boxes, `()` for rounded, `{{}}` for diamonds, `[()]` for stadium
- Add edge labels with `|Label|` between arrows
- Make it visually appealing and easy to understand

Create a similar detailed, STYLED diagram based on the detected tech stack!

IMPORTANT - TECHNOLOGY BADGE REFERENCE:
Use these official shields.io badges for common technologies (use official logos, NOT emojis):

**Frontend:**
- ![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
- ![Vue.js](https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vue.js&logoColor=4FC08D)
- ![Angular](https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white)
- ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
- ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
- ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
- ![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
- ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

**Backend:**
- ![Node.js](https://img.shields.io/badge/Node.js-43853D?style=for-the-badge&logo=node.js&logoColor=white)
- ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
- ![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
- ![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
- ![Express.js](https://img.shields.io/badge/Express.js-404D59?style=for-the-badge&logo=express&logoColor=white)
- ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)
- ![Go](https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white)
- ![Java](https://img.shields.io/badge/Java-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
- ![Ruby](https://img.shields.io/badge/Ruby-CC342D?style=for-the-badge&logo=ruby&logoColor=white)
- ![PHP](https://img.shields.io/badge/PHP-777BB4?style=for-the-badge&logo=php&logoColor=white)

**Database:**
- ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
- ![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
- ![MySQL](https://img.shields.io/badge/MySQL-00000F?style=for-the-badge&logo=mysql&logoColor=white)
- ![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
- ![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

**DevOps & Tools:**
- ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
- ![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
- ![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
- ![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)
- ![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)
- ![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)

Use similar format for any other technologies detected. Find logo names at https://simpleicons.org/

Create a BEAUTIFUL, COMPREHENSIVE README.md with these requirements:

1. **Title Section**:
   - Use the repository name as the main title
   - Add relevant badges (stars, forks, license, build status)
   - Include a compelling tagline based on the description

2. **Description**:
   - Write an engaging overview (2-3 paragraphs)
   - Highlight the main purpose and key features
   - Mention the target audience

3. **Features** (if applicable):
   - List 5-8 key features with emojis
   - Make them specific to this project based on the tech stack

4. **Tech Stack**:
   - **IMPORTANT**: Use official technology icons/logos, NOT emojis!
   - Use shields.io badges with official logos for each technology
   - Format: ![TechName](https://img.shields.io/badge/TechName-HexColor?style=for-the-badge&logo=techname&logoColor=white)
   - Group by category (Frontend, Backend, Database, DevOps, etc.)
   - Examples:
     * ![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
     * ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
     * ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
     * ![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
     * ![Node.js](https://img.shields.io/badge/Node.js-43853D?style=for-the-badge&logo=node.js&logoColor=white)
     * ![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
     * ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
     * ![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
     * ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
     * ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
     * ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
   - Use appropriate colors and logos from https://simpleicons.org/
   - Make sure each technology has its official logo badge

5. **Architecture** (REQUIRED - MUST BE VISUAL!):
   - **CRITICAL**: Create a BEAUTIFUL, STYLED Mermaid diagram that renders as a visual flowchart
   - Use `flowchart TD` or `graph TB` for best visual results
   - **MUST include style definitions** for colored boxes (like the examples above)
   - Use descriptive labels with `<br/>` for multi-line text
   - Add edge labels with `|Label|` to show data flow
   - Create a comprehensive diagram showing:
     * User/Client interaction (start point)
     * Frontend components (if detected) - use blue/cyan colors
     * Backend services/APIs - use purple/violet colors
     * Database connections - use green colors
     * External services - use orange colors
     * Data flow between ALL components with labeled arrows
   - **Styling Requirements:**
     * Use `style NodeName fill:#COLOR,stroke:#DARKER_COLOR,color:#fff`
     * Different colors for different layers (Frontend, Backend, Database, etc.)
     * Make it look professional and visually appealing
     * Use shapes: `[]` boxes, `()` rounded, `{{}}` diamonds, `[()]` stadium, `[(DB)]` database
   - Example structure (use proper mermaid code blocks in output):
     * Start with flowchart TD or graph TB
     * Define nodes with shapes and labels
     * Connect with arrows and labels
     * Add style definitions for each node with colors
     * Use colors: Green for start/end, Blue for frontend, Purple for backend, Orange for processing, Cyan for logic, Red for errors, Teal for databases
   - Adapt the diagram based on detected technologies
   - Include ALL major components from the tech stack
   - Make it look like a professional architecture diagram with colors!

6. **Project Structure**:
   - Create a beautiful file tree using proper ASCII art
   - Use the actual top-level structure provided
   - Add comments explaining key directories
   - Format it properly with ├──, └──, and │ characters

7. **Installation**:
   - Provide step-by-step installation instructions
   - Use the detected package manifests to generate accurate commands
   - Include prerequisites
   - Add code blocks with proper syntax highlighting

8. **Usage**:
   - Provide clear usage examples
   - Include code snippets
   - Add screenshots placeholders if applicable

9. **API Documentation** (if backend detected):
   - Document main API endpoints
   - Include request/response examples

10. **Contributing**:
    - Standard contributing guidelines
    - Code of conduct mention
    - How to submit PRs

11. **License**:
    - License information placeholder

12. **Contact/Support**:
    - Links to issues, discussions
    - Maintainer information

FORMATTING REQUIREMENTS:
- Use proper markdown syntax throughout
- **CRITICAL**: Use official technology badges/icons for Tech Stack section (NOT emojis!)
- **CRITICAL**: Include a BEAUTIFUL, STYLED, COLORED Mermaid architecture diagram (REQUIRED!)
- **CRITICAL**: Architecture diagram MUST have style definitions with colors (see examples above)
- Use emojis for other sections (🚀 📦 🔧 💻 🎨 etc.) but NOT for technologies
- Use code blocks with language tags
- Mermaid diagrams MUST use:
  * Proper syntax: ```mermaid at start and ``` at end
  * `flowchart TD` or `graph TB` for best visual rendering
  * Style definitions: `style NodeName fill:#COLOR,stroke:#DARKER,color:#fff`
  * Descriptive labels with `<br/>` for line breaks
  * Edge labels: `-->|Label|` for data flow description
  * Different colors for different layers (Frontend=blue, Backend=purple, DB=green, etc.)
- Create tables where appropriate
- Add horizontal rules (---) to separate major sections
- Use blockquotes for important notes
- Make it visually appealing and easy to scan
- Ensure all technology badges use the shields.io format with official logos
- Architecture diagram should be comprehensive, colorful, and professional-looking

Generate ONLY the markdown content. Make it professional, beautiful, and comprehensive with a STUNNING visual architecture diagram!
"""
        
        return prompt
    
    def _format_languages(self, languages: dict) -> str:
        """Format language breakdown for prompt."""
        if not languages:
            return "Not detected"
        
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        return '\n'.join([f"- {lang}: {pct:.1f}%" for lang, pct in sorted_langs])
    
    def invoke_ai_model(self, prompt: str, model: str = 'Auto') -> str:
        """
        Invoke external AI model to generate content.
        
        Args:
            prompt: Prompt for AI model
            model: Model to use ('Llama 3' or 'Auto')
        
        Returns:
            Generated markdown content
        
        Raises:
            GeneratorError: If generation fails
        """
        # Try to use Groq API based on model selection
        if model == 'Llama 3' and self.GROQ_API_KEY:
            try:
                print("Using Llama 3.3 70B (Groq) for README generation...")
                return self._call_groq_api(prompt)
            except Exception as e:
                print(f"Groq API failed: {e}, falling back to template")
                raise  # Re-raise to prevent silent fallback
        
        elif model == 'Auto':
            # Try Groq Llama 3 (most reliable and fast)
            if self.GROQ_API_KEY:
                try:
                    print("Auto mode: Using Llama 3.3 70B (Groq)...")
                    return self._call_groq_api(prompt)
                except Exception as e:
                    error_msg = f"Groq failed: {str(e)}"
                    print(error_msg)
                    print("Falling back to enhanced template...")
        
        # Fallback to enhanced template if no API keys or all failed
        print("Using enhanced template (no API key or API failed)...")
        return self._generate_enhanced_template(prompt)
    
    def _generate_enhanced_template(self, prompt: str) -> str:
        """
        Generate enhanced README using template with better formatting.
        This is a fallback when AI APIs are not available.
        
        Args:
            prompt: Context from prompt
        
        Returns:
            Enhanced template-based README
        """
        # Parse the prompt to extract information
        lines = prompt.split('\n')
        repo_name = "Repository"
        owner = "owner"
        description = ""
        stars = 0
        forks = 0
        url = ""
        languages = []
        tech_stack = []
        manifests = []
        file_structure = []
        total_files = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if '- Name:' in line:
                repo_name = line.split(':', 1)[1].strip()
            elif '- Owner:' in line:
                owner = line.split(':', 1)[1].strip()
            elif '- Description:' in line:
                description = line.split(':', 1)[1].strip()
            elif '- Stars:' in line:
                try:
                    stars = int(line.split(':', 1)[1].strip())
                except:
                    pass
            elif '- Forks:' in line:
                try:
                    forks = int(line.split(':', 1)[1].strip())
                except:
                    pass
            elif '- URL:' in line:
                url = line.split(':', 1)[1].strip()
            elif 'PROGRAMMING LANGUAGES:' in line:
                # Get next few lines for languages
                for j in range(i+1, min(i+6, len(lines))):
                    if lines[j].strip().startswith('-'):
                        lang = lines[j].strip().split(':')[0].replace('-', '').strip()
                        if lang:
                            languages.append(lang)
            elif 'DETECTED TECH STACK:' in line and i+1 < len(lines):
                tech_line = lines[i+1].strip()
                if tech_line and tech_line != 'Not detected':
                    tech_stack = [t.strip() for t in tech_line.split(',')]
            elif 'PACKAGE MANIFESTS FOUND:' in line and i+1 < len(lines):
                manifest_line = lines[i+1].strip()
                if manifest_line and manifest_line != 'None':
                    manifests = [m.strip() for m in manifest_line.split(',')]
            elif 'FILE STRUCTURE (Top Level):' in line:
                for j in range(i+1, min(i+15, len(lines))):
                    if lines[j].strip() and not lines[j].strip().startswith('PROJECT'):
                        file_structure.append(lines[j].strip())
                    else:
                        break
            elif '- Total Files:' in line:
                try:
                    total_files = int(line.split(':')[1].strip())
                except:
                    pass
        
        # Generate tech stack with emojis
        tech_icons = {
            'javascript': '🟨 JavaScript',
            'typescript': '🔷 TypeScript',
            'python': '🐍 Python',
            'java': '☕ Java',
            'go': '🐹 Go',
            'rust': '🦀 Rust',
            'ruby': '💎 Ruby',
            'php': '🐘 PHP',
            'html': '🌐 HTML',
            'css': '🎨 CSS',
            'react': '⚛️ React',
            'vue': '💚 Vue.js',
            'node': '🟢 Node.js',
            'flask': '🌶️ Flask',
            'django': '🎸 Django',
            'postgres': '🐘 PostgreSQL',
            'mongo': '🍃 MongoDB',
            'docker': '🐳 Docker',
        }
        
        tech_list = []
        for tech in (tech_stack + languages):
            icon_found = False
            for key, value in tech_icons.items():
                if key in tech.lower():
                    tech_list.append(value)
                    icon_found = True
                    break
            if not icon_found:
                tech_list.append(f"🔧 {tech}")
        
        # Build file tree
        tree_lines = ["```"]
        tree_lines.append(f"{repo_name}/")
        for i, item in enumerate(file_structure[:12]):
            is_last = i == len(file_structure[:12]) - 1
            prefix = "└── " if is_last else "├── "
            tree_lines.append(prefix + item)
        if len(file_structure) > 12:
            tree_lines.append("└── ...")
        tree_lines.append("```")
        file_tree = "\n".join(tree_lines)
        
        # Build installation commands
        install_cmds = []
        if any('package.json' in m for m in manifests):
            install_cmds.append("npm install")
        if any('requirements.txt' in m for m in manifests):
            install_cmds.append("pip install -r requirements.txt")
        if any('go.mod' in m for m in manifests):
            install_cmds.append("go mod download")
        if not install_cmds:
            install_cmds = ["# See documentation for installation"]
        
        # Generate architecture diagram
        has_frontend = any(t in str(tech_stack).lower() for t in ['react', 'vue', 'html', 'angular'])
        has_backend = any(t in str(tech_stack).lower() for t in ['flask', 'django', 'express', 'node'])
        
        arch_diagram = ""
        if has_frontend or has_backend:
            arch_diagram = f"""
## 🏗️ Architecture

```mermaid
graph LR
    A[Client] -->|HTTP| B[{repo_name}]
    B -->|Process| C[Core Logic]
    C -->|Response| A
```
"""
        
        # Generate beautiful README
        readme = f"""<div align="center">

# {repo_name}

{description if description else f'A powerful {languages[0] if languages else "software"} project'}

[![Stars](https://img.shields.io/badge/⭐_stars-{stars}-yellow)](https://github.com/{owner}/{repo_name})
[![Forks](https://img.shields.io/badge/🍴_forks-{forks}-blue)](https://github.com/{owner}/{repo_name}/fork)
[![License](https://img.shields.io/badge/📄_license-MIT-green)](LICENSE)

[View Demo](https://github.com/{owner}/{repo_name}) · [Report Bug](https://github.com/{owner}/{repo_name}/issues) · [Request Feature](https://github.com/{owner}/{repo_name}/issues)

</div>

---

## 📋 Table of Contents

- [About](#about)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 About

**{repo_name}** is maintained by **{owner}** and has gained **{stars} stars** from the community.

This project leverages modern technologies to deliver a robust solution. With **{total_files} files** organized across multiple directories, it demonstrates professional software architecture and best practices.

---

## 🚀 Tech Stack

{chr(10).join(['- ' + tech for tech in tech_list[:10]])}

---
{arch_diagram}
## 📁 Project Structure

{file_tree}

**Key Directories:**
- Source code and main application logic
- Configuration and build files
- Documentation and resources

---

## 🛠️ Getting Started

### Prerequisites

Make sure you have the following installed:
- {languages[0] if languages else 'Required runtime'}
- Package manager ({manifests[0] if manifests else 'see documentation'})

### Installation

```bash
# Clone the repository
git clone {url if url else f'https://github.com/{owner}/{repo_name}.git'}

# Navigate to project directory
cd {repo_name}

# Install dependencies
{chr(10).join(install_cmds)}
```

---

## 💻 Usage

```bash
# Run the application
# Check the documentation for specific commands
```

For detailed usage instructions, please refer to the [documentation](https://github.com/{owner}/{repo_name}/wiki).

---

## 🤝 Contributing

Contributions are what make the open source community amazing! Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🔗 Links

- **Repository**: [{owner}/{repo_name}]({url if url else f'https://github.com/{owner}/{repo_name}'})
- **Issues**: [Report a bug](https://github.com/{owner}/{repo_name}/issues)
- **Discussions**: [Join the conversation](https://github.com/{owner}/{repo_name}/discussions)

---

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!

---

<div align="center">

**[⬆ back to top](#{repo_name.lower()})**

Made with ❤️ by [{owner}](https://github.com/{owner})

</div>
"""
        
        return readme
    
    def _build_file_tree(self, structure: List[str]) -> str:
        """Build a proper file tree structure."""
        if not structure:
            return "```\n.\n├── src/\n├── tests/\n└── README.md\n```"
        
        tree_lines = ["```"]
        tree_lines.append(".")
        
        for i, item in enumerate(structure[:15]):  # Limit to 15 items
            is_last = i == len(structure[:15]) - 1
            prefix = "└── " if is_last else "├── "
            tree_lines.append(prefix + item)
        
        if len(structure) > 15:
            tree_lines.append("└── ... (and more)")
        
        tree_lines.append("```")
        return "\n".join(tree_lines)
    
    def _generate_architecture_diagram(self, tech_stack: List[str], languages: Dict[str, float]) -> str:
        """Generate a Mermaid architecture diagram."""
        # Detect project type
        has_frontend = any(tech in str(tech_stack).lower() for tech in ['react', 'vue', 'angular', 'html'])
        has_backend = any(tech in str(tech_stack).lower() for tech in ['flask', 'django', 'express', 'node'])
        has_database = any(tech in str(tech_stack).lower() for tech in ['postgres', 'mongo', 'redis', 'sql'])
        
        diagram = ["```mermaid", "graph TD"]
        
        if has_frontend and has_backend:
            diagram.append("    A[Client/Browser] -->|HTTP/HTTPS| B[Frontend]")
            diagram.append("    B -->|API Calls| C[Backend Server]")
            if has_database:
                diagram.append("    C -->|Queries| D[Database]")
            diagram.append("    C -->|Response| B")
            diagram.append("    B -->|Render| A")
        elif has_backend:
            diagram.append("    A[Client] -->|Requests| B[Backend Server]")
            if has_database:
                diagram.append("    B -->|Queries| C[Database]")
                diagram.append("    C -->|Data| B")
            diagram.append("    B -->|Response| A")
        else:
            diagram.append("    A[User] -->|Interacts| B[Application]")
            diagram.append("    B -->|Processes| C[Core Logic]")
            diagram.append("    C -->|Output| A")
        
        diagram.append("```")
        return "\n".join(diagram)
    
    def _generate_template_readme(self, prompt: str) -> str:
        """
        Generate README using template with actual analysis data.
        
        Args:
            prompt: Context from prompt containing analysis data
        
        Returns:
            Customized README based on analysis
        """
        # Extract key info from prompt
        lines = prompt.split('\n')
        repo_name = "Repository"
        owner = "owner"
        description = ""
        stars = 0
        forks = 0
        languages = []
        tech_stack = []
        manifests = []
        hints = []
        total_files = 0
        top_level = []
        
        # Parse the prompt for actual data
        in_languages = False
        in_tech_stack = False
        in_manifests = False
        in_hints = False
        in_structure = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Repository:'):
                repo_name = line.split(':', 1)[1].strip()
            elif line.startswith('Owner:'):
                owner = line.split(':', 1)[1].strip()
            elif line.startswith('Description:'):
                description = line.split(':', 1)[1].strip()
            elif line.startswith('Stars:'):
                try:
                    stars = int(line.split(':', 1)[1].strip())
                except:
                    stars = 0
            elif line.startswith('Forks:'):
                try:
                    forks = int(line.split(':', 1)[1].strip())
                except:
                    forks = 0
            elif line.startswith('Languages:'):
                in_languages = True
                in_tech_stack = False
                in_manifests = False
                in_hints = False
                in_structure = False
            elif line.startswith('Tech Stack:'):
                in_languages = False
                in_tech_stack = True
                in_manifests = False
                in_hints = False
                in_structure = False
            elif line.startswith('Package Manifests:'):
                in_languages = False
                in_tech_stack = False
                in_manifests = True
                in_hints = False
                in_structure = False
            elif line.startswith('Setup Hints:'):
                in_languages = False
                in_tech_stack = False
                in_manifests = False
                in_hints = True
                in_structure = False
            elif line.startswith('File Structure'):
                in_languages = False
                in_tech_stack = False
                in_manifests = False
                in_hints = False
                in_structure = True
            elif line.startswith('Total Files:'):
                try:
                    total_files = int(line.split(':')[1].split()[0].strip())
                except:
                    pass
            elif in_languages and line.startswith('-'):
                lang = line.split(':')[0].replace('-', '').strip()
                if lang:
                    languages.append(lang)
            elif in_tech_stack and line:
                if line not in ['Not detected', '']:
                    tech_stack.extend([t.strip() for t in line.split(',') if t.strip()])
            elif in_manifests and line:
                if line not in ['None', '']:
                    manifests.extend([m.strip() for m in line.split(',') if m.strip()])
            elif in_hints and line:
                hints.append(line)
            elif in_structure and line and not line.startswith('Total'):
                top_level.append(line)
        
        # Build tech stack section
        tech_stack_text = ""
        if tech_stack:
            tech_stack_text = "**Technologies:** " + ", ".join(set(tech_stack))
        elif languages:
            tech_stack_text = "**Languages:** " + ", ".join(languages[:5])
        else:
            tech_stack_text = "**Tech Stack:** Modern development tools"
        
        # Build installation section
        install_commands = []
        if 'package.json' in str(manifests):
            install_commands.append("npm install")
        if 'requirements.txt' in str(manifests):
            install_commands.append("pip install -r requirements.txt")
        if 'pyproject.toml' in str(manifests):
            install_commands.append("poetry install")
        if 'go.mod' in str(manifests):
            install_commands.append("go mod download")
        if 'Cargo.toml' in str(manifests):
            install_commands.append("cargo build")
        
        if not install_commands:
            install_commands = ["# See package manifest files for installation instructions"]
        
        # Build file structure
        structure_text = "\n".join(top_level[:10]) if top_level else "├── src/\n├── tests/\n└── README.md"
        
        # Generate customized README
        readme = f"""# {repo_name}

{description if description else f'A {languages[0] if languages else "software"} project hosted on GitHub.'}

![Stars](https://img.shields.io/badge/stars-{stars}-yellow) ![Forks](https://img.shields.io/badge/forks-{forks}-blue)

## 📋 Overview

This repository contains the source code for **{repo_name}**, maintained by **{owner}**.

## 🚀 Tech Stack

{tech_stack_text}

{f"**Primary Languages:** {', '.join(languages[:3])}" if languages else ""}

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/{owner}/{repo_name}.git

# Navigate to project directory
cd {repo_name}

# Install dependencies
{chr(10).join(install_commands)}
```

## 📁 Project Structure

```
{structure_text}
```

{f"**Total Files:** {total_files}" if total_files > 0 else ""}

## 🔧 Usage

```bash
# Run the application
# Check the documentation for specific commands
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source. Please check the repository for license details.

## 🔗 Links

- **Repository:** https://github.com/{owner}/{repo_name}
- **Issues:** https://github.com/{owner}/{repo_name}/issues
- **Pull Requests:** https://github.com/{owner}/{repo_name}/pulls

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!

---

*Generated with [GitRefiny](https://github.com/yourusername/gitrefiny) - AI README Generator*
"""
        
        return readme
    
    def format_markdown(self, content: str) -> str:
        """
        Validate and format markdown content.
        
        Args:
            content: Raw markdown content
        
        Returns:
            Formatted markdown
        """
        # Basic formatting: ensure proper line breaks
        lines = content.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            formatted_lines.append(line)
            
            # Add extra line break after headers
            if line.startswith('#') and i < len(lines) - 1:
                if lines[i + 1] and not lines[i + 1].startswith('#'):
                    formatted_lines.append('')
        
        return '\n'.join(formatted_lines)
    
    def generate_readme(self, analysis: AnalysisResult, 
                       sections: Optional[List[str]] = None,
                       tone: str = 'professional',
                       model: str = 'Auto') -> str:
        """
        Generate complete README from analysis.
        
        Args:
            analysis: Repository analysis result
            sections: Sections to include (None = all)
            tone: Content tone
            model: AI model to use
        
        Returns:
            Generated markdown string
        
        Raises:
            GeneratorError: If generation fails
        """
        try:
            # Build prompt
            prompt = self.build_prompt(analysis, sections, tone)
            
            # Invoke AI model
            markdown = self.invoke_ai_model(prompt, model)
            
            # Format markdown
            formatted = self.format_markdown(markdown)
            
            return formatted
        
        except Exception as e:
            raise GeneratorError(f"Failed to generate README: {str(e)}")
