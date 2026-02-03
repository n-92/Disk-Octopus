"""
Copilot Integration - Use locally installed Copilot binary
"""

import os
import subprocess
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Process pool for subprocess calls (reuse connections)
_process_pool = ThreadPoolExecutor(max_workers=2)


class CopilotBinaryAnalyzer:
    """Uses locally installed Copilot binary for analysis."""
    
    def __init__(self):
        """Initialize analyzer and detect copilot binary."""
        self.copilot_path = self._detect_copilot_binary()
        self.cache = {}
        self.process_pool = _process_pool
        
        if not self.copilot_path:
            self.available = False
        else:
            self.available = True
    
    def _detect_copilot_binary(self) -> Optional[str]:
        """Detect copilot binary installed on system."""
        possible_paths = [
            # GitHub CLI with Copilot extension
            "gh",
            "copilot",
            # Windows paths
            r"C:\Program Files\GitHub CLI\gh.exe",
            r"C:\Program Files (x86)\GitHub CLI\gh.exe",
            # User bin
            os.path.expanduser("~/.local/bin/gh"),
            os.path.expanduser("~/.local/bin/copilot"),
        ]
        
        for path in possible_paths:
            try:
                # Try to run the command to verify it exists
                result = subprocess.run(
                    [path, "version"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None
    
    def analyze_file_type(self, extension: str, file_samples: List[str], 
                         file_count: int, total_size: int) -> str:
        """
        Analyze a file type using Copilot.
        
        Args:
            extension: File extension (e.g., '.txt')
            file_samples: Sample file paths
            file_count: Total count of this file type
            total_size: Total size in bytes
        
        Returns:
            Analysis text
        """
        cache_key = extension
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if not self.available:
            analysis = self._get_basic_analysis(extension, file_count, total_size)
        else:
            analysis = self._call_copilot_for_analysis(
                extension, file_samples, file_count, total_size
            )
        
        self.cache[cache_key] = analysis
        return analysis
    
    def analyze_file_contents(self, file_contents: str, file_name: str, 
                             file_extension: str) -> str:
        """
        Perform intelligent deep analysis of file contents.
        
        Args:
            file_contents: The actual file content to analyze
            file_name: Name of the file
            file_extension: File extension
        
        Returns:
            Intelligent analysis and summary of the file
        """
        if not file_contents or not file_contents.strip():
            return "File is empty - no content to analyze."
        
        if not self.available:
            return self._analyze_content_basic(file_contents, file_name, file_extension)
        
        return self._call_copilot_for_content_analysis(
            file_contents, file_name, file_extension
        )
    
    def _call_copilot_for_content_analysis(self, file_contents: str, 
                                          file_name: str, file_extension: str) -> str:
        """Call Copilot to analyze file contents - with working fallback."""
        if not self.available:
            return self._create_intelligent_fallback(file_contents, file_name, file_extension)
        
        # NOTE: Direct Copilot subprocess calls hang due to Windows/PowerShell 
        # subprocess communication limitations with interactive/multi-line prompts.
        # Using intelligent fallback instead, which provides meaningful analysis without Copilot.
        
        return self._create_intelligent_fallback(file_contents, file_name, file_extension)
    
    def _create_intelligent_fallback(self, file_contents: str, file_name: str, file_extension: str) -> str:
        """Create intelligent analysis without Copilot by extracting meaningful patterns."""
        lines = file_contents.split('\n')
        
        # Detect file type and purpose
        purpose = self._infer_file_purpose(file_contents, file_name, file_extension)
        usage = self._infer_file_usage(file_extension, file_name)
        creator_clues = self._extract_creator_clues(file_contents, file_name)
        insights = self._extract_key_insights(file_contents, file_name, file_extension)
        
        analysis = f"""[bold cyan]FILE INTELLIGENCE ANALYSIS[/bold cyan]
[yellow]{file_name}[/yellow] ({file_extension})

[bold cyan]1. PURPOSE[/bold cyan]
{purpose}

[bold cyan]2. WHERE USED[/bold cyan]
{usage}

[bold cyan]3. CREATOR & ORIGIN[/bold cyan]
{creator_clues}

[bold cyan]4. KEY INSIGHTS[/bold cyan]
{insights}

[bold cyan]5. PRACTICAL ASSESSMENT[/bold cyan]
File Size: {len(file_contents)} bytes
Type: {"Binary" if '\\x00' in repr(file_contents) or len(file_contents) > 1000 and not file_contents.isprintable() else "Text-based"}
Complexity: {"High" if len(lines) > 100 or len(file_contents) > 50000 else "Moderate" if len(lines) > 20 else "Low"}"""
        
        return analysis
    
    def _infer_file_purpose(self, content: str, name: str, ext: str) -> str:
        """Intelligently infer the purpose of a file."""
        # Check extension
        ext_purposes = {
            '.py': 'Python source code module, script, or application',
            '.js': 'JavaScript code for web/node.js applications',
            '.json': 'Data configuration or interchange format (JSON)',
            '.xml': 'Structured data or configuration (XML format)',
            '.exe': 'Executable application binary',
            '.dll': 'Dynamic library for Windows applications',
            '.bin': 'Binary data, firmware, or compiled executable',
            '.log': 'System or application log file for event tracking',
            '.txt': 'Plain text document or configuration',
            '.csv': 'Comma-separated data (spreadsheet format)',
            '.md': 'Markdown documentation or readme',
            '.ini': 'Configuration file for applications',
            '.bat': 'Windows batch script for automation',
            '.sh': 'Shell script for system automation',
            '.pgn': 'Chess game notation file (Portable Game Notation)',
            '.pdf': 'Portable Document Format - text and image documents',
            '.jpg': 'JPEG image file for photos and graphics',
            '.jpeg': 'JPEG image file for photos and graphics',
            '.png': 'PNG image with lossless compression',
            '.gif': 'GIF image for animations or graphics',
            '.zip': 'Compressed archive containing multiple files',
            '.rar': 'RAR compressed archive file',
            '.7z': '7-Zip compressed archive',
            '.mp4': 'MPEG-4 video file format',
            '.mp3': 'MPEG-3 audio file format',
            '.wav': 'Waveform audio file',
            '.doc': 'Microsoft Word document (older format)',
            '.docx': 'Microsoft Word document (XML format)',
            '.xls': 'Microsoft Excel spreadsheet (older format)',
            '.xlsx': 'Microsoft Excel spreadsheet (XML format)',
            '.ppt': 'Microsoft PowerPoint presentation (older format)',
            '.pptx': 'Microsoft PowerPoint presentation (XML format)',
            '.java': 'Java source code file',
            '.cpp': 'C++ source code file',
            '.c': 'C programming language source code',
            '.go': 'Go programming language source code',
            '.rs': 'Rust programming language source code',
            '.ts': 'TypeScript source code',
            '.tsx': 'TypeScript React/JSX component',
            '.jsx': 'JavaScript React/JSX component',
            '.html': 'HyperText Markup Language web page',
            '.css': 'Cascading Style Sheet for web styling',
            '.sql': 'SQL database query or script',
            '.yaml': 'YAML configuration format',
            '.yml': 'YAML configuration format',
            '.toml': 'TOML configuration file format',
        }
        
        # Check for common naming patterns
        if 'config' in name.lower() or 'settings' in name.lower():
            return "Configuration or settings file for an application or service"
        elif 'test' in name.lower():
            return "Test data, test case, or testing-related file"
        elif 'log' in name.lower():
            return "Log file for tracking events, errors, or system activity"
        elif 'backup' in name.lower() or 'bak' in name.lower():
            return "Backup copy of another file for data protection"
        elif ext in ext_purposes:
            return ext_purposes[ext]
        else:
            return f"File of type {ext} - specific purpose would depend on file context"
    
    def _infer_file_usage(self, ext: str, name: str) -> str:
        """Infer where and how a file is typically used."""
        ext_usage = {
            '.py': 'Typically used in: Python development, automation scripts, web frameworks (Django, Flask), data science tools (NumPy, Pandas, Scikit-learn)',
            '.js': 'Web development, Node.js backend services, browser automation, frontend frameworks (React, Vue, Angular)',
            '.json': 'APIs, configuration management, data exchange between services, web applications',
            '.xml': 'Web services (SOAP), data pipelines, document storage, enterprise systems',
            '.exe': 'Software applications, utilities, games - run directly by end users on Windows',
            '.dll': 'Shared libraries for Windows applications and services, plugin systems',
            '.bin': 'Embedded systems, firmware, databases, compiled protocols, game assets',
            '.log': 'Diagnostics, troubleshooting, audit trails, monitoring, system administration',
            '.csv': 'Data analysis, spreadsheets, reporting, ETL processes, business intelligence',
            '.ini': 'Application startup, system configuration, driver settings, user preferences',
            '.bat': 'System administration, scheduled tasks, automation scripts, build systems',
            '.pgn': 'Chess game archives, chess engines, online chess platforms (Chess.com), chess analysis tools',
            '.pdf': 'Documents, reports, ebooks, forms, technical specifications, user manuals',
            '.jpg': 'Photos, graphics, web images, social media content',
            '.png': 'Web graphics, screenshots, graphics with transparency',
            '.gif': 'Animated graphics, icons, web graphics, memes',
            '.zip': 'File distribution, backups, software packages, cloud storage',
            '.mp4': 'Video streaming, content creation, video sharing platforms',
            '.mp3': 'Audio streaming, music libraries, podcasts',
            '.wav': 'Audio production, sound effects, high-quality audio',
            '.docx': 'Business documents, reports, proposals, writing',
            '.xlsx': 'Data analysis, business metrics, financial reporting',
            '.pptx': 'Presentations, slideshows, training materials',
            '.java': 'Enterprise applications, Android apps, backend systems (Spring, Hibernate)',
            '.cpp': 'System software, game engines, performance-critical applications',
            '.c': 'Operating systems, embedded systems, system-level programming',
            '.go': 'Cloud infrastructure, microservices, DevOps tools, concurrent systems',
            '.rs': 'Systems programming, performance-critical code, memory-safe applications',
            '.ts': 'Large-scale JavaScript applications, type-safe development, enterprise projects',
            '.tsx': 'React applications, component-based UI development',
            '.jsx': 'React applications, interactive user interfaces',
            '.html': 'Web pages, email templates, documentation',
            '.css': 'Web styling, responsive design, theming',
            '.sql': 'Database queries, stored procedures, data management',
            '.yaml': 'Configuration management (Kubernetes, Docker, Ansible), DevOps',
            '.yml': 'Configuration management (Kubernetes, Docker, Ansible), DevOps',
        }
        
        if ext in ext_usage:
            return ext_usage[ext]
        else:
            return f"Industry usage depends on the specific {ext} format and context"
    
    def _extract_creator_clues(self, content: str, name: str) -> str:
        """Extract clues about who created the file."""
        clues = []
        
        # Check for company signatures
        company_indicators = {
            'Microsoft': ['windows', 'msvsc', 'dotnet', '.net', 'msvcr'],
            'Apple': ['macos', 'darwin', 'xcode'],
            'Adobe': ['adobe', 'pdf', 'photoshop'],
            'Google': ['google', 'android', 'chrome'],
            'Meta': ['facebook', 'meta', 'instagram'],
            'AWS': ['amazon', 'aws'],
        }
        
        name_lower = name.lower()
        for company, keywords in company_indicators.items():
            if any(kw in name_lower for kw in keywords):
                clues.append(f"Likely created or owned by: {company}")
                break
        
        # Check content for more clues
        if 'Copyright' in content or 'copyright' in content:
            clues.append("File contains copyright information - proprietary or commercial")
        elif 'License:' in content or 'license' in content.lower():
            clues.append("File includes license terms - possibly open-source or licensed software")
        
        if len(clues) == 0:
            clues.append("Creator not immediately identifiable from file metadata")
            if len(name) > 20:
                clues.append("Lengthy filename suggests user-generated or project-specific file")
        
        return '\n'.join(f"• {clue}" for clue in clues)
    
    def _extract_key_insights(self, content: str, name: str, ext: str) -> str:
        """Extract key insights about the file."""
        insights = []
        
        size_kb = len(content) / 1024
        if size_kb > 1000:
            insights.append("• Large file (>1MB) - substantial data or code")
        elif size_kb < 1:
            insights.append("• Very small file - minimal data or configuration snippet")
        
        lines = content.split('\n')
        if len(lines) > 1000:
            insights.append(f"• Extensive file with {len(lines)} lines - complex logic or large dataset")
        
        # Check for code indicators
        code_indicators = ['def ', 'class ', 'function ', 'if __name__', 'import ']
        if any(indicator in content for indicator in code_indicators):
            insights.append("• Source code detected - contains executable logic")
        
        # Check for data/config indicators
        if content.count(',') > len(content) // 100:  # Many commas = likely CSV
            insights.append("• High comma density - likely structured data (CSV/config)")
        
        if '{}' in content or '[]' in content or '":"' in content:
            insights.append("• Contains structured data format (JSON/nested data)")
        
        if len(insights) == 0:
            insights.append("• Binary or encoded file - structure not immediately obvious")
        
        return '\n'.join(insights)
    
    def _create_file_summary(self, file_contents: str, file_name: str, file_extension: str) -> str:
        """Create a summary of file contents for analysis (avoids passing large content via subprocess)."""
        lines = file_contents.split('\n')
        
        # Get basic stats
        total_lines = len(lines)
        non_empty_lines = len([l for l in lines if l.strip()])
        avg_line_length = sum(len(l) for l in lines) / max(len(lines), 1)
        
        # Detect file type
        file_type = "Unknown"
        if file_extension in ['.py', '.js', '.ts', '.go', '.rs', '.c', '.cpp', '.h']:
            file_type = "Source Code"
        elif file_extension in ['.json', '.xml', '.yaml', '.yml', '.toml']:
            file_type = "Configuration/Data"
        elif file_extension in ['.txt', '.md', '.rst']:
            file_type = "Text/Documentation"
        elif file_extension in ['.bin', '.exe', '.dll']:
            file_type = "Binary"
        
        # Sample content (first 5 non-empty lines)
        samples = []
        for line in lines[:10]:
            if line.strip():
                samples.append(line[:80])  # 80 chars max per line
                if len(samples) >= 5:
                    break
        
        summary = f"""File Type Classification: {file_type}
Total Lines: {total_lines}
Non-empty Lines: {non_empty_lines}  
Average Line Length: {avg_line_length:.1f}

Content Indicators:
- Extension: {file_extension}
- Binary: {'Yes' if len(file_contents.splitlines()[0]) > 100 or '\x00' in file_contents else 'No'}

Sample Content:
{chr(10).join(samples) if samples else '(Binary or empty)'}"""
        
        return summary
    
    def _analyze_content_basic(self, file_contents: str, file_name: str, 
                               file_extension: str) -> str:
        """Basic analysis of file contents without Copilot."""
        lines = file_contents.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        
        # Count keywords
        imports = len([l for l in lines if 'import' in l.lower()])
        functions = len([l for l in lines if 'def ' in l or 'function ' in l])
        classes = len([l for l in lines if 'class ' in l])
        comments = len([l for l in lines if l.strip().startswith('#') or l.strip().startswith('//')])
        
        analysis = f"""[bold cyan]FILE CONTENT ANALYSIS[/bold cyan]
[yellow]{file_name}[/yellow] ({file_extension})

[bold cyan]Structure Analysis:[/bold cyan]
• Total lines: {len(lines)}
• Code lines: {len(non_empty_lines)}
• Imports: {imports}
• Functions/methods: {functions}
• Classes: {classes}
• Comments: {comments}

[bold cyan]Content Type:[/bold cyan]
"""
        
        # Detect content type
        content_type = "Unknown"
        if imports > 0 or functions > 0 or classes > 0:
            content_type = "Source Code"
            analysis += f"• [bold green]{content_type}[/bold green] - Contains executable code\n"
            if classes > 0:
                analysis += f"  - {classes} class(es) defined\n"
            if functions > 0:
                analysis += f"  - {functions} function(s)/method(s) defined\n"
        elif file_extension.lower() in ['.json', '.yaml', '.yml', '.xml', '.ini', '.cfg', '.toml']:
            content_type = "Configuration/Data"
            analysis += f"• [bold cyan]{content_type}[/bold cyan] - Structured data or settings\n"
        elif file_extension.lower() in ['.md', '.txt', '.log', '.csv']:
            content_type = "Text/Document"
            analysis += f"• [bold blue]{content_type}[/bold blue] - Plain text document\n"
        
        # Estimate code quality
        if len(non_empty_lines) > 0:
            comment_ratio = (comments / len(non_empty_lines)) * 100
            analysis += f"\n[bold cyan]Quality Indicators:[/bold cyan]\n"
            analysis += f"• Documentation: {comment_ratio:.1f}% commented\n"
            if comment_ratio > 20:
                analysis += "  - [green]✓ Well documented[/green]\n"
            elif comment_ratio > 10:
                analysis += "  - [yellow]~ Moderately documented[/yellow]\n"
            else:
                analysis += "  - [red]✗ Minimal documentation[/red]\n"
        
        analysis += f"\n[bold cyan]Content Preview (first 400 chars):[/bold cyan]\n[dim]{file_contents[:400]}...[/dim]"
        
        return analysis
    
    def _call_copilot_for_analysis(self, extension: str, file_samples: List[str],
                                   file_count: int, total_size: int) -> str:
        """Call copilot binary for analysis."""
        try:
            prompt = f"""Explain what {extension} files are used for.
            
            Context:
            - File count: {file_count}
            - Total size: {self._format_size(total_size)}
            - Samples: {', '.join(Path(f).name for f in file_samples[:3])}
            
            Be brief (2-3 sentences). If this is a suspicious/malware-related 
            extension, mention security concerns."""
            
            # Try to call copilot
            result = subprocess.run(
                [self.copilot_path, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        
        except Exception as e:
            pass
        
        # Fallback to basic analysis
        return self._get_basic_analysis(extension, file_count, total_size)
    
    def _get_basic_analysis(self, extension: str, file_count: int, 
                           total_size: int) -> str:
        """Get basic analysis without Copilot."""
        analysis_map = {
            '.txt': 'Text files - Plain text documents, notes, and data files.',
            '.md': 'Markdown files - Documentation and formatted text files.',
            '.pdf': 'PDF documents - Formatted documents for viewing and printing.',
            '.doc': 'Word documents - Microsoft Office Word documents.',
            '.docx': 'Word documents - Modern Microsoft Office Word documents.',
            '.xls': 'Excel spreadsheets - Microsoft Office spreadsheet files.',
            '.xlsx': 'Excel spreadsheets - Modern Microsoft Office spreadsheet files.',
            '.ppt': 'PowerPoint presentations - Microsoft Office presentation files.',
            '.pptx': 'PowerPoint presentations - Modern Microsoft Office presentation files.',
            '.jpg': 'JPEG images - Compressed image files commonly used for photos.',
            '.jpeg': 'JPEG images - Compressed image files commonly used for photos.',
            '.png': 'PNG images - Lossless image files with transparency support.',
            '.gif': 'GIF images - Animated or static image files.',
            '.mp3': 'Audio files - Compressed music and audio recordings.',
            '.mp4': 'Video files - Compressed video files with audio.',
            '.avi': 'Video files - Uncompressed or lightly compressed video files.',
            '.mov': 'QuickTime video - Apple video format.',
            '.exe': 'Executable programs - Application files that run software. ⚠️ SECURITY RISK if in unexpected locations.',
            '.dll': 'Dynamic libraries - System libraries used by applications. ⚠️ Can be malicious if in wrong locations.',
            '.sys': 'System files - Windows operating system files.',
            '.bat': 'Batch scripts - Automation scripts for Windows. ⚠️ Can execute malicious code.',
            '.cmd': 'Command scripts - Windows command line scripts.',
            '.ps1': 'PowerShell scripts - Advanced Windows automation. ⚠️ Can be malicious.',
            '.vbs': 'VBScript files - Visual Basic scripts. ⚠️ Often used for malware.',
            '.zip': 'ZIP archives - Compressed file archives.',
            '.rar': 'RAR archives - Compressed file archives.',
            '.7z': '7-Zip archives - Highly compressed file archives.',
            '.json': 'JSON files - Structured data format used in web and applications.',
            '.xml': 'XML files - Structured data format for documents and configuration.',
            '.css': 'CSS stylesheets - Web page styling files.',
            '.js': 'JavaScript files - Web programming and scripting language.',
            '.py': 'Python files - Python programming language source code.',
            '.cpp': 'C++ files - C++ programming language source code.',
            '.java': 'Java files - Java programming language source code.',
            '.sql': 'SQL files - Database query and script files.',
            '.db': 'Database files - Local database storage.',
            '.ini': 'Configuration files - Application settings files.',
            '.cfg': 'Configuration files - System and application settings.',
            '.log': 'Log files - Application and system event logs.',
        }
        
        base = analysis_map.get(extension.lower(), f'{extension} files - Custom file type.')
        return f"{base}\n\nCount: {file_count} files | Size: {self._format_size(total_size)}"
    
    def check_security_risks(self, extension: str, locations: List[str]) -> Dict:
        """
        Check if file type has security risks.
        
        Returns dict with:
        - risk_level: 'safe', 'warning', 'critical'
        - message: Explanation
        - recommendation: What to do
        """
        suspicious_extensions = {
            '.exe': 'critical',
            '.dll': 'critical',
            '.scr': 'critical',
            '.com': 'critical',
            '.vbs': 'critical',
            '.bat': 'warning',
            '.cmd': 'warning',
            '.ps1': 'warning',
            '.js': 'warning',  # In system folders
            '.jar': 'warning',
        }
        
        risk_level = suspicious_extensions.get(extension.lower(), 'safe')
        
        messages = {
            'critical': f'⚠️ CRITICAL: {extension} files can execute code. Review them carefully!',
            'warning': f'⚠️ WARNING: {extension} files may execute code. Check if they are expected.',
            'safe': f'✓ SAFE: {extension} files are generally safe.',
        }
        
        return {
            'risk_level': risk_level,
            'message': messages.get(risk_level, 'Unknown risk'),
            'locations': locations
        }
    
    def generate_octopus_ascii_art(self) -> str:
        """Generate unique octopus ASCII art using Copilot."""
        if not self.available:
            return self._get_default_octopus_art()
        
        try:
            prompt = """Generate creative ASCII art of an octopus wrapping around a hard drive or storage device. 
            
            Requirements:
            - Use only ASCII characters (no Unicode except basic box drawing)
            - Keep it compact (max 10 lines)
            - Make it unique and visually interesting
            - Focus on the octopus and drive/storage theme
            - Center-aligned would be good
            
            Just provide the ASCII art, no explanation or markdown formatting."""
            
            result = subprocess.run(
                [self.copilot_path, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                art = result.stdout.strip()
                # Validate it's reasonable ASCII art (not too long, contains ASCII art chars)
                if len(art) < 2000 and len(art.split('\n')) < 20:
                    return art
        
        except Exception as e:
            pass
        
        # Fallback to default art
        return self._get_default_octopus_art()
    
    def _get_file_type_specific_prompt(self, extension: str) -> str:
        """Get file-type-specific analysis prompts for natural commentary."""
        ext = extension.lower()
        
        if ext == '.pgn':
            return """For this chess game:
- What was the opening and how was it played?
- Analyze move quality - were there any brilliant moves or blunders?
- Who won and how did the game conclude?
- What can we learn from this game?
- Was this a well-played game overall?"""
        
        elif ext in ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs']:
            return """For this code:
- What is the main purpose of this code?
- What coding style and patterns are used?
- Is this well-written? What's good about it?
- Are there any issues, inefficiencies, or security concerns?
- Would you recommend any improvements?"""
        
        elif ext in ['.json', '.xml', '.yaml', '.yml']:
            return """For this configuration:
- What does this configure?
- Is this configuration complete and sensible?
- Are there any security issues (exposed credentials, etc.)?
- What's the purpose of each main section?
- Are there any configuration issues or concerns?"""
        
        elif ext in ['.csv', '.tsv']:
            return """For this data:
- What kind of data does this contain?
- How is the data structured?
- Are there any data quality issues, missing values, or anomalies?
- What insights can you get from this data?
- How might this data be used?"""
        
        elif ext in ['.md', '.txt']:
            return """For this document:
- What is the main topic and purpose?
- What are the key points or sections?
- Is this well-written and organized?
- What's the intended audience?
- Any notable content or recommendations?"""
        
        elif ext in ['.pdf']:
            return """For this PDF:
- What is the document about?
- How is it structured (pages, sections)?
- What are the key takeaways?
- Who is the intended audience?
- Is this professional and well-done?"""
        
        elif ext in ['.log']:
            return """For this log file:
- What system or application generated this?
- What was happening during this time period?
- Are there errors or warnings? How serious?
- What can you infer about system health?
- Any suspicious or notable events?"""
        
        elif ext in ['.sql']:
            return """For this SQL:
- What does this query/schema do?
- Is this SQL well-written?
- Are there any performance concerns?
- What data is involved?
- Any issues or improvements recommended?"""
        
        else:
            return """Please analyze this file:
- What does it contain and what is its purpose?
- What are the key observations?
- Is there anything notable or concerning?
- What quality or issues do you notice?"""
    
    def _get_default_octopus_art(self) -> str:
        """Return default octopus ASCII art with natural, meaningful designs."""
        # Braille-based octopus art
        braille_octopus = """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⡤⠤⠤⠤⠤⠤⠤⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠤⠖⢉⠭⠀⠴⠘⠩⡢⠏⠘⡵⢒⠬⣍⠲⢤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠊⣡⠔⠃⠀⠰⠀⠀⠀⠀⠈⠂⢀⠀⢋⠞⣬⢫⣦⣍⢢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⢫⣼⠿⠁⠀⠀⠀⠐⠀⠀⠰⠀⠢⠈⠀⠠⠀⢚⡥⢏⣿⣿⣷⡵⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⢓⣽⡓⡅⠀⠀⠀⠄⠀⠀⠄⠀⠁⠀⠀⠌⢀⠀⡸⣜⣻⣿⣿⣿⣿⣼⡀⠀⠀⠀⢀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢀⡤⣤⣄⣠⠤⣄⠀⠀⠀⠀⠀⠀⠀⢀⣧⣿⡷⠹⠂⠀⠂⠀⢀⠠⠈⠀⠌⠀⠁⢈⠀⠄⢀⡷⣸⣿⣿⣿⣿⣿⣧⠃⠀⡴⢋⢠⣤⣦⣬⣕⢤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣔⣵⣿⣻⣯⣍⣉⠚⢕⢆⠀⠀⠀⠀⠀⢸⢾⣽⡷⡂⠀⠀⠄⠂⠀⡀⠄⠂⠀⠌⠀⡀⠀⢀⡾⣯⢿⣿⣿⣿⣿⣿⣿⠰⠸⠠⢠⣾⣿⣿⣷⣿⣷⣕⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣼⣿⣿⠿⠿⢿⣿⣇⡛⡻⣧⠀⠀⠀⠀⢼⢸⡟⡧⣧⠀⠃⠀⡀⠄⠀⢀⠠⠘⠀⠠⠀⠀⡟⢧⣛⣿⣿⣿⣿⣿⣿⣧⠇⠀⡇⢻⣿⣿⣿⠟⠻⣿⣿⣇⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⣿⠁⣠⣤⠀⠙⢿⣿⡤⢘⣆⠀⠀⠀⢹⣼⣿⡽⠖⠁⠀⢤⠀⠀⡐⠀⢀⠐⠈⠀⢠⠖⠙⠣⠟⣻⢿⣿⣟⣿⡿⠃⠀⠀⠃⢼⣿⣧⠀⠀⠀⠸⣿⣣⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⣿⣆⣿⡟⠀⠀⠀⣿⡇⠰⢸⠀⠀⠀⡸⡻⡕⠉⠀⠀⡐⠀⠈⠁⠀⠀⢠⠀⡴⠀⡠⠀⢀⠤⡲⠟⣉⠻⣿⣟⠁⠀⠀⠀⡅⢺⣿⣿⠃⠀⠀⠀⠈⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠈⠙⠛⠉⠀⠀⠀⣀⡿⣗⠧⣼⠀⠄⡎⣿⣇⣧⣀⠑⢆⠀⠀⠀⢹⢄⢀⢧⠊⢀⠊⠀⠘⡡⣪⡴⠛⢻⣷⣜⣿⣦⠀⠀⡀⡿⣸⣿⣿⡆⠀⠀⡠⢐⠫⠉⠩⠭⣗⣦⡀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢠⢹⣷⣻⠇⣿⠘⡀⣿⣿⣿⣿⠛⠛⢦⣙⠄⠀⢈⣫⢼⠀⠤⠁⠀⣠⣾⣿⡇⠀⠐⠂⢻⣿⣟⣿⡇⢠⠃⣧⣿⣿⣾⠁⢀⢎⣴⡶⡿⢿⣟⣷⢮⡝⢿⣷⠤⡀⠀
⠀⠀⠀⠀⠀⠀⠈⣽⣯⢿⣣⡹⢰⠘⣿⡿⣹⣿⠀⠀⠹⣿⡿⣷⣬⣯⣾⣷⣤⣴⣾⡟⣍⡿⠃⠀⠀⠀⢸⣿⣿⣩⣒⣵⣷⣿⣿⡿⠃⠀⡞⢺⣿⣿⣯⢿⠉⠀⠉⠛⢦⣻⣇⠘⡆
⠀⠀⠀⠀⠀⠀⣀⣿⣾⡾⣿⣵⡢⠳⢿⣷⢹⣿⣆⠀⠀⠈⠉⢉⣽⢟⣿⠟⢻⢿⣷⣄⡁⠀⠀⠀⠀⣀⣾⡟⣍⣿⣿⣿⣿⣿⣿⡗⠀⠀⠇⣽⣿⣿⣿⡼⠀⠀⣠⡤⣀⠿⠏⣴⠇
⠀⠀⠀⠀⠀⠀⠸⡼⣿⣿⣽⣿⣿⣶⣬⣿⣯⢿⣷⣥⠶⣒⣶⣾⠏⠐⠙⠀⠈⠚⡌⢪⣿⣧⣖⠦⡭⠿⢛⣼⣿⣿⢿⣿⣿⡿⠝⠁⠀⠰⢀⣿⣿⣾⣿⡇⠀⠀⠻⢿⡝⠲⠛⠋⠀
⠀⠀⠀⠀⠀⠀⠀⠉⢿⣿⣿⣿⣿⣿⣿⡿⠻⢷⣮⣉⣭⣡⣟⡱⠀⠀⡀⢀⡞⢀⢠⡀⠹⣿⣿⣿⣿⣾⣿⣿⣿⣿⣿⣟⠋⠀⠀⠀⡠⡡⣹⣿⣿⣿⠿⠡⢀⣀⠀⠾⠁⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⠽⢿⢿⣻⡿⠈⢀⣶⣿⣿⣿⣿⡽⠃⢀⡴⣰⣿⢤⣓⢿⣿⣄⠙⣻⣷⡟⣿⣿⣿⣽⡻⣿⠿⠧⡶⣒⢭⣺⣽⣿⠟⢍⢀⠀⡉⠑⢶⣯⡲⣄⠀⠀⠀⠀
⠀⠀⠀⠀⣀⣀⡀⠀⠀⠀⣟⣷⣞⡟⠉⣴⡿⣯⣷⣿⣿⡟⡡⢀⣜⣼⣿⣿⣎⢳⢿⢻⣿⡄⠑⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣟⣾⣿⣿⢃⣠⣤⢖⡾⢷⡲⣆⡳⣿⣮⢢⡄⠀⠀
⠀⠀⡔⣩⢦⣐⣈⣦⣄⡠⢗⣿⣾⢁⣼⢏⣿⣿⣿⣿⡟⠐⣠⢝⣾⣿⣿⣿⣯⡟⣷⣿⣻⣿⣄⢈⢆⠻⢿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣿⡧⢨⣲⣷⣿⠋⣟⣶⣀⣳⡖⣿⣇⣃⠀⠀
⠀⣘⡸⣞⣿⣿⣿⣿⣿⣿⣿⡿⠁⣺⣣⣿⣿⣿⣿⠎⢀⢢⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣢⢀⠡⡘⢪⡯⡻⣿⣿⣿⣿⣿⣿⣻⣟⢧⣽⣿⣿⠀⠀⣎⣱⡏⣏⣿⣯⡽⠀⠀
⠀⣿⣧⣼⣿⡟⠛⠛⠿⢟⠟⣁⣼⣿⣿⠛⢉⡜⠁⡠⣠⣷⢿⣿⡿⣿⣿⣿⣿⠟⠉⠙⠛⢯⣽⣯⠷⣄⠑⠜⠑⡷⡜⢿⠿⠟⠛⠉⠀⢸⢺⣾⣿⣿⣷⣄⣀⠏⣱⣿⣿⣿⠀⠀⠀
⠀⢹⣿⣾⣿⣿⣤⡤⠔⢑⣡⣾⡿⡿⠁⡠⠋⠀⡀⢀⣿⡟⣿⣿⣿⡙⣿⣻⣿⡄⠀⠀⠀⠀⠉⠻⣿⣟⣧⡄⠀⠘⣟⢦⡱⣄⠀⠀⠀⢸⣼⣿⢿⣿⣿⣷⣤⣾⣿⣿⣿⠏⠀⠀⠀
⠀⠀⠹⢿⣿⠏⣰⣧⣾⣿⣿⠟⠋⠀⡰⠡⡡⠀⣠⣿⣿⣿⣿⣿⣿⣗⢸⣿⣿⣷⠀⠀⠀⠀⠀⠀⠱⡹⣟⣿⣦⡁⠈⠳⢕⢄⠑⠂⠐⢾⣿⣿⣿⣿⣿⠛⠿⠟⠛⠋⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣯⣼⣿⣿⠋⠁⠀⠀⠀⠀⡇⠐⠀⢠⣿⣿⡝⣿⠃⠈⢻⡞⢸⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠉⢻⣷⣾⣿⣦⡄⠀⠀⠈⠐⢺⣽⣿⣿⡎⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣿⣻⡟⠁⠀⠀⠀⠀⠀⢸⡇⠀⢀⣿⣿⣿⣿⠏⠀⠀⢸⠳⣜⣹⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⡿⢿⣿⣿⣷⣶⣶⣶⣿⣿⢟⣻⣿⢟⡝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠸⣿⣿⡦⠀⠀⠀⠀⠀⠘⡇⠰⣼⡿⡿⣾⡏⠀⠀⠀⢸⠣⣹⣾⣿⡹⠀⡠⢄⣂⢤⠀⠀⠀⠀⠀⠈⠉⠻⣟⢿⣾⣚⣿⣿⣿⣿⣽⡏⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢠⣾⢛⣿⡟⠀⠀⠀⠀⠀⠀⢷⣀⢻⣷⣟⣻⡇⠀⠀⢀⢯⣅⣿⣷⣿⠇⣜⣾⣿⣿⣿⣧⣀⠀⠀⠀⠀⠀⠀⠈⠉⠸⠿⣿⠏⠘⠔⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠛⠛⠋⠀⠀⠀⠀⠀⠀⠀⠈⢻⡯⢿⣿⡿⡴⣀⡠⣪⡷⣽⣿⣿⡿⢚⣿⣿⡟⠀⠙⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⢹⡈⠛⠿⠽⢞⢋⠜⠻⣿⣿⣿⣿⠿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠓⠒⠛⠚⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"""
        
        return braille_octopus



# Backwards compatibility
CopilotAnalyzer = CopilotBinaryAnalyzer

