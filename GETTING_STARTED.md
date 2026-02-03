# 🚀 Getting Started with Copilot Disk Visualizer

## Quick Start (2 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Visualizer
```bash
python main.py
```

### 3. Select Your Drive
When prompted, enter the drive letter you want to explore (e.g., `C` for C:\)

### 4. Explore!
- Enter numbers `0-9` to navigate into directories
- Press `a` to analyze with Copilot
- Press `b` to go back
- Press `q` to quit
- Press `h` for help

---

## Features Walkthrough

### 📊 Visual Treemap
The main visualization shows your disk usage as colored rectangles. Larger chunks = larger folders.

```
█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░██░░░░░░░██░░░░░██░░░░█
█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░██░░░░░░░██░░░░░██░░░░█
█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░██░░░░░░░██░░░░░██░░░░█
```

Each color represents a different folder or file.

### 📋 Item Table
Below the visualization, you see the top items ranked by size:
- ID: Number to press to navigate
- Name: Folder/file name
- Size: Total size (includes subdirectories)
- Type: Directory or file

### 🤖 AI Analysis
Press `a` to have Copilot analyze the current directory:
- Detects file types
- Understands directory purpose
- Provides insights about contents

---

## Command Reference

| Command | Action | Notes |
|---------|--------|-------|
| `0-9` | Enter directory | Navigates into the selected folder |
| `b` | Go back | Returns to parent directory |
| `a` | Analyze | Uses Copilot to understand contents |
| `r` | Refresh | Redraw the current view |
| `h` | Help | Shows command help |
| `q` | Quit | Exit the application |
| Enter | Refresh | Same as `r` |

---

## Common Use Cases

### 📦 Finding Large Folders
1. Start the tool
2. Look at the treemap - largest colored areas are biggest folders
3. Navigate into them with number keys
4. Drill down until you find what's taking up space

### 🧹 Cleaning Up Disk Space
1. Use the visualizer to identify large directories
2. Press `a` to understand what each folder contains
3. Safely delete unwanted directories
4. Run the visualizer again to see freed space

### 📊 Understanding Project Structure
1. Point to your project folder
2. Use numbers to navigate through files
3. Press `a` to get AI insights about what each folder does
4. Better understand your codebase organization

### 🔍 System Analysis
1. Start from C:\ on Windows
2. Explore top-level directories
3. Find which applications use the most space
4. Identify duplicate or backup folders

---

## Keyboard Shortcuts Explained

### Navigation Shortcuts
```
0-9   → Select and open numbered item
b     → Back (go to parent)
r     → Refresh display
```

### Analysis Shortcuts
```
a     → Analyze with Copilot
```

### Interface Shortcuts
```
h     → Help menu
q     → Quit
Enter → Refresh
```

---

## Tips & Tricks

### 🎯 Efficient Navigation
- Use `b` to retrace your steps
- Press numbers quickly to drill down deep
- Use `r` to refresh if display looks wrong

### 🤖 Smart Analysis
- Use Copilot analysis on unknown directories
- Cached analyses load instantly on second view
- Combine navigation with analysis for best insights

### 💡 Finding Duplicates
- Look for similarly named folders
- Check their sizes with analysis
- Navigate into them to compare contents

### ⚡ Performance Tips
- Initial scan shows progress bar
- Large drives (~1TB) may take 30-60 seconds to scan
- Subsequent navigation is instant
- Analysis is cached by directory

---

## Troubleshooting

### "Access Denied" Messages
- **Normal behavior** - system folders are protected
- Scanner skips them gracefully
- Try analyzing accessible directories instead

### Slow Scanning
- Large drives take time initially
- 1TB drives typically scan in 30-90 seconds
- Progress bar shows current status
- Wait for "Scan complete!" message

### GitHub Token Setup
When you first run the tool without a token:
- A helpful setup guide automatically appears
- Follow the 4 simple steps to get your GitHub token
- You don't need it - tool works fine without it (uses mock analysis)
- Add it anytime to unlock AI features

**Quick Setup:**
1. Visit https://github.com/settings/tokens
2. Create a "classic" token with "repo" and "gist" scopes
3. In PowerShell, run: `$env:GITHUB_TOKEN = "your_token"`
4. Restart the tool

**Make it permanent:**
```powershell
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "your_token", "User")
```

### Terminal Display Issues
- Make sure terminal window is at least 80x20 characters
- Try maximizing the terminal
- Some terminals may render colors differently

---

## Advanced Usage

### Analyzing Specific Directory
You can point to any directory, not just drive roots:

```bash
# Edit main.py or call scanner directly
scanner = DiskScanner('C:\\Users\\YourName\\Documents')
```

### Programmatic Access
Use the scanner directly in your code:

```python
from disk_scanner import DiskScanner

scanner = DiskScanner('C:\\')
root = scanner.scan()

print(f"Total size: {root.format_size()}")
print(f"File count: {root.file_count}")
```

---

## What Makes This Different

### vs. Wiztree
- ✅ Terminal-based (no GUI needed)
- ✅ AI-powered insights
- ✅ Open source
- ✅ Cross-platform capable
- ❌ Slightly slower (Python vs. C)

### vs. `du` Command
- ✅ Visual treemap
- ✅ Interactive navigation
- ✅ Pretty formatting
- ✅ AI analysis
- ❌ Not CLI-only (requires Python)

### vs. File Explorers
- ✅ Shows all sizes at a glance
- ✅ Beautiful visualization
- ✅ AI insights
- ✅ Fast navigation
- ✅ Easy to find large folders

---

## Next Steps

1. **Try the Demo**: `python demo.py`
2. **Run Main App**: `python main.py`
3. **Explore Your Drive**: Follow the prompts
4. **Use Analysis**: Press `a` to understand folders
5. **Share Results**: Great for showing team members disk usage

---

**Happy exploring! 🚀**

Have questions? Check the README.md for more details!
