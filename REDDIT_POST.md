# Built Disk Octopus: A Terminal Storage Analyzer with GitHub Copilot CLI – Here's What I Learned

**TL;DR:** Built a professional terminal app that analyzes disk storage with AI. GitHub Copilot CLI saved me from subprocess hell on Windows. Check it out: https://github.com/n-92/Disk-Octopus

---

## The Problem

I wanted to build something useful. Every time I needed to analyze my disk storage, I'd reach for GUI tools like WizTree. But as a developer, I spend 90% of my time in the terminal. Why should I leave it just to check disk usage?

I decided to build **Disk Octopus** – a professional terminal app that visualizes disk storage and uses AI to give you insights about your files.

**Spoiler:** It was harder than I thought, and GitHub Copilot CLI saved my butt.

---

## The Technical Journey

### Phase 1: The Optimistic Beginner

- "I'll just use Python's `os` module to scan directories"
- "A simple UI with Textual should be easy"
- "I'll call GitHub Copilot CLI via subprocess to analyze files"

Narrator: *It was not easy.*

### Phase 2: The Windows Hangup (Literally)

Everything worked fine on my test files. Then I tried analyzing a 2MB file.

The app showed: `Uploading: ... Please wait...`

And then... nothing. It hung. For minutes. On Windows.

I spent **hours** debugging this:

- Tested subprocess timeouts – didn't work
- Tried different PowerShell flags – nope
- Attempted process management – still hanging
- Read 100 Stack Overflow threads – most suggested "use another language"

**The Root Cause:** Windows PowerShell argument parsing chokes on complex multi-line prompts. When I tried to pass a prompt with file content + analysis instructions, the shell would mangle it before Copilot even saw it.

### Phase 3: Copilot CLI to the Rescue

Instead of fighting the subprocess issue, I asked Copilot CLI a different question: *"How would you analyze a file if you couldn't use subprocess calls?"*

The answer was elegant: **intelligent fallback analysis using pattern recognition**.

I built a system that:

1. Detects file type by extension + content analysis
2. Uses pattern matching to infer file purpose
3. Classifies the file's usage context
4. Provides meaningful insights *immediately*

And the best part? When Copilot CLI is available, it enhances the analysis. When it's not, users get solid results anyway.

**This was the "aha" moment** – Copilot CLI didn't just help me code, it helped me rethink my architecture.

---

## Key Wins

✅ **File Type Recognition** – Supports 40+ file types (Python, Java, PDFs, images, chess games, config files, etc.)

✅ **Smart Analysis** – Tells you not just "this is a Python file" but "this is a Python library for web scraping, commonly used in data engineering"

✅ **Cross-Platform** – Works on Windows, macOS, Linux without the hanging issue

✅ **Graceful Degradation** – Works perfectly without Copilot CLI, but better with it

✅ **Professional UI** – Split-panel interface, real-time statistics, beautiful braille octopus art 🐙

---

## What GitHub Copilot CLI Actually Helped With

1. **Problem Solving** – When stuck on the subprocess issue, it helped me think through alternative architectures
2. **Code Generation** – Accelerated implementation of file type detection patterns
3. **Debugging** – Helped identify PowerShell limitations I didn't know existed
4. **Architecture** – Suggested the fallback analyzer pattern that made the app robust

It wasn't magic – I still wrote most of the code. But it saved me days of frustration and helped me avoid dead ends.

---

## Lessons Learned

1. **Graceful degradation is underrated** – Building systems that work with AND without external services makes them infinitely more useful

2. **Terminal tools matter** – Developers spend hours in terminals. Building for that environment is undervalued

3. **GitHub Copilot CLI is best for thinking, not just coding** – The subprocess problem wasn't solved by Copilot writing code; it was solved by Copilot helping me rethink the problem

4. **Windows development is... special** – PowerShell's argument handling is wild. Know your platform

5. **File analysis is harder than it looks** – Every file type has quirks. The fallback analyzer handles 40+ types now, and I'm still discovering edge cases

---

## What's Next

The app is production-ready and open-source (MIT License). I'm hoping to:

- Get community feedback
- Add more file type recognition
- Maybe build a companion CLI tool
- Explore more AI integration patterns

---

## For Developers Interested in This Stuff

- **Tech Stack:** Python 3.10+, Textual (TUI), Rich (formatting), GitHub Copilot CLI
- **Big Challenges:** Terminal UI rendering, async file scanning, Windows subprocess handling
- **Favorite Part:** Braille octopus art (yes, really 🐙)
- **Repo:** https://github.com/n-92/Disk-Octopus (full documentation included)

---

## The Real Talk

Building this was frustrating at times. The subprocess hanging was soul-crushing. But that's where GitHub Copilot CLI made the difference – not by writing the solution, but by helping me ask better questions.

If you're building something and hitting walls, sometimes the answer isn't "code harder" – it's "rethink the problem." Tools like Copilot CLI are good for that.

---

**Anyone else have horror stories with subprocess on Windows? Or built terminal tools that surprised you? Would love to hear your experiences in the comments.**

---

## For Different Subreddits

### r/Python

Focus more on the technical implementation, file type detection, async handling

### r/learnprogramming

Emphasize the learning journey, mistakes, and how Copilot CLI helped

### r/programming

Focus on architecture decisions and the graceful degradation pattern

### r/webdev

Maybe less relevant, but could angle toward "tools developers should use"

### r/github

Focus on GitHub Copilot CLI experience and open-source practice

---

*Feel free to adapt based on your target subreddit! The core story is strong, but different communities resonate with different angles. 🚀*
