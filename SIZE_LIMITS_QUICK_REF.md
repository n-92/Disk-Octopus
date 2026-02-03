# 📊 Upload Size Limits - Quick Reference

## The Limits

| Limit Type | Size | Purpose |
|-----------|------|---------|
| **Copilot Upload** | **5 MB** | Prevent oversized uploads to Copilot service |
| **Local Read** | **10 MB** | Prevent reading huge files into memory |
| **Content Preview** | **5 KB** | Show only first 5KB in analysis panel |

---

## What Happens at Each Limit

### ❌ Over 5MB (Copilot Limit)
```
User presses 'd' on 10MB file
↓
BLOCKED ❌
↓
Shows error:
"File too large for Copilot analysis

File size: 10.0MB
Copilot limit: 5MB

Cannot upload files larger than 5MB to Copilot service."
↓
No analysis performed
```

### ❌ Over 10MB (Local Read Limit)
```
File gets selected
↓
Attempts to read
↓
Size check triggers
↓
Shows: "File too large to read locally (12.5MB)"
↓
No preview shown
```

### ⚠️ Binary File Detection
```
User selects .jpg, .exe, .bin, etc.
↓
Extension check triggers
↓
Shows warning: "Warning: .jpg may be binary file"
↓
Continues at user risk
```

### ✂️ Over 5KB (Content Truncation)
```
File read (OK - under 10MB)
↓
Content is 8KB
↓
Auto-truncated to 5KB
↓
Shows: "... [truncated, 3000 more bytes]"
↓
Analysis continues with first 5KB
```

---

## User Scenarios

### ✅ Scenario 1: Small File (OK)
```
config.json (150 KB)
  ↓ Copilot limit check: 150 KB < 5 MB ✓
  ↓ Local read check: 150 KB < 10 MB ✓
  ↓ Read file ✓
  ↓ Upload to Copilot ✓
  ↓ Show analysis ✓
```

### ❌ Scenario 2: Large File (BLOCKED)
```
database.bin (25 MB)
  ↓ Copilot limit check: 25 MB > 5 MB ✗
  ↓ ERROR: "File too large for Copilot analysis"
  ↓ User sees error message
  ↓ No upload attempted
```

### ⚠️ Scenario 3: Image File (WARNING)
```
photo.jpg (2 MB)
  ↓ Copilot limit check: 2 MB < 5 MB ✓
  ↓ Local read check: 2 MB < 10 MB ✓
  ↓ Extension check: .jpg = binary ⚠️
  ↓ Warning: "May be binary file"
  ↓ User can choose to continue or cancel
```

---

## How to Test

```bash
# Test 1: Create 2MB file (should work)
fsutil file createnew small.txt 2097152
# Result: Analyzes successfully ✅

# Test 2: Create 10MB file (should fail)
fsutil file createnew large.txt 10485760
# Result: Shows "File too large for Copilot analysis" ❌

# Test 3: Create binary file
# Use any .jpg, .exe, .png
# Result: Shows binary file warning ⚠️
```

---

## Error Messages by Type

### Type 1: Copilot Upload Too Large
**Color**: 🔴 Red (ERROR)  
**Duration**: 8 seconds  
**Action**: Blocks upload
```
File too large for Copilot analysis

File size: 45.2MB
Copilot limit: 5MB

Cannot upload files larger than 5MB to Copilot service.
```

### Type 2: Local Read Too Large
**Color**: 🟡 Yellow (WARNING)  
**Duration**: Persistent  
**Action**: Shows in panel
```
File too large to read locally (12.5MB)
(Limit: 10MB)
```

### Type 3: Binary File Detected
**Color**: 🟡 Yellow (WARNING)  
**Duration**: Persistent  
**Action**: Shows in preview
```
Warning: .exe may be binary file

(Showing as text...)
```

---

## Key Bindings

| Key | Action | Respects Limits |
|-----|--------|-----------------|
| `d` | Deep Analyze | ✅ Yes - checks 5MB/10MB |
| `a` | Analyze | ✅ Yes - file extension only |

---

## Supported File Types

### ✅ Safe Text Files (Recommended)
```
Code:     .py, .js, .html, .css, .cpp, .java, .go, .rs, .rb, .php
Text:     .txt, .md, .log, .csv, .doc
Config:   .json, .xml, .yml, .yaml, .ini, .cfg, .conf, .toml
Scripts:  .sh, .bat, .sql, .ps1
```

### ⚠️ Binary Files (Shows Warning)
```
Images:    .jpg, .png, .gif, .bmp, .ico
Archives:  .zip, .rar, .7z, .tar
Binary:    .exe, .dll, .bin, .o, .class
Other:     Anything not in safe list
```

---

## What If...

### File is too large?
**Use**: Only send text files under 5MB to Copilot  
**Alternative**: Extract relevant sections first

### Need to analyze large file?
**Option 1**: Split file into smaller chunks  
**Option 2**: Analyze specific sections  
**Option 3**: Use file compression first

### Binary file keeps showing warning?
**Normal behavior**: System correctly detects binary files  
**Not a bug**: Warnings help protect against analysis errors

---

**Last Updated**: 2026-02-03  
**Status**: ✅ All limits properly enforced
