# 📦 Upload Size Limits Documentation

**Date**: 2026-02-03  
**Feature**: Copilot Upload Limits & User Warnings  
**Status**: ✅ IMPLEMENTED

---

## Overview

Added comprehensive size limit checks to prevent sending oversized files to Copilot and to inform users about limits before processing.

---

## Limits Enforced

### 1. **Copilot Upload Limit: 5MB**
- **Where**: Checked in `action_deep_analyze()` before attempting upload
- **Action**: Block upload and show clear error message
- **Message Example**:
  ```
  File too large for Copilot analysis
  
  File size: 45.2MB
  Copilot limit: 5MB
  
  Cannot upload files larger than 5MB to Copilot service.
  ```

### 2. **Local Read Limit: 10MB**
- **Where**: Checked in `_read_file_safely()` before reading file
- **Action**: Return error message instead of attempting read
- **Message Example**:
  ```
  File too large to read locally (8.5MB)
  (Limit: 10MB)
  ```

### 3. **Content Preview Truncation: 5KB**
- **Where**: Applied in `action_deep_analyze()` after reading
- **Action**: Show first 5KB only, note remaining bytes
- **Message Example**:
  ```
  Content Preview:
  [file contents...]
  ... [truncated, 12500 more bytes]
  ```

---

## Limit Levels (Detailed)

```
File Upload Flow:
├── User selects file
├── Press 'd' for deep analysis
│
├─► CHECK: File size > 5MB?
│   ├─ YES → Block with error message
│   └─ NO → Continue
│
├─► CHECK: File extension safe?
│   ├─ YES (text file) → Continue
│   └─ NO (binary) → Warn user
│
├─► CHECK: File size > 10MB?
│   ├─ YES → Error message
│   └─ NO → Continue
│
├─► READ: First 5KB only
│   └─ Truncate if larger
│
└─► UPLOAD: Send to Copilot
    └─ Display analysis
```

---

## Safe Extensions (Text Files)

```
✅ Text:       .txt, .md, .log, .csv
✅ Code:       .py, .js, .html, .css, .cpp, .java, .go, .rs
✅ Config:     .json, .xml, .yml, .yaml, .ini, .cfg, .conf
✅ Scripts:    .sh, .bat, .sql
⚠️  Other:     Shows warning "may be binary file"
```

---

## User Experience

### Scenario 1: Small Text File (OK)
```
1. User clicks "config.json" (150 KB)
2. Presses 'd' key
3. System reads file ✅
4. Sends to Copilot ✅
5. Shows analysis ✅
```

### Scenario 2: Large File (Blocked)
```
1. User clicks "data.bin" (45 MB)
2. Presses 'd' key
3. System checks size ❌
4. Shows error:
   "File too large for Copilot analysis
    File size: 45.2MB
    Copilot limit: 5MB"
5. Prevents upload ✅
```

### Scenario 3: Binary File (Warning)
```
1. User clicks "image.jpg" (2 MB)
2. Presses 'd' key
3. System checks type ⚠️
4. Shows warning:
   "Warning: .jpg may be binary file
    (Showing as text...)"
5. Continues with caution ✅
```

---

## Code Implementation

### Copilot Upload Check (NEW)
```python
# Check file size limit for Copilot upload
copilot_upload_limit = 5 * 1024 * 1024  # 5MB
if hasattr(self.selected_node, 'size') and self.selected_node.size > copilot_upload_limit:
    size_mb = self.selected_node.size / (1024 * 1024)
    limit_mb = copilot_upload_limit / (1024 * 1024)
    self.notify(
        f"[red]File too large for Copilot analysis[/red]\n\n"
        f"File size: {size_mb:.1f}MB\n"
        f"Copilot limit: {limit_mb:.0f}MB\n\n"
        f"Cannot upload files larger than {limit_mb:.0f}MB to Copilot service.",
        severity="error",
        timeout=8
    )
    return
```

### Local Read Check (UPDATED)
```python
# Local read limit (for display purposes)
max_local_read = 10 * 1024 * 1024  # 10MB

if hasattr(self.selected_node, 'size') and self.selected_node.size > max_local_read:
    return f"[red]File too large to read locally ({self.format_size(self.selected_node.size)})[/red]\n(Limit: 10MB)"
```

---

## Error Messages

### Error Type 1: Copilot Upload Limit Exceeded
**Severity**: ERROR (red)  
**Timeout**: 8 seconds  
**Action**: Prevents any upload attempt

```
[red]File too large for Copilot analysis[/red]

File size: {actual_size}MB
Copilot limit: 5MB

Cannot upload files larger than 5MB to Copilot service.
```

### Error Type 2: Local Read Limit Exceeded
**Severity**: WARNING (yellow)  
**Timeout**: Inline in panel  
**Action**: Shows in analysis panel instead of blocking

```
[red]File too large to read locally ({size})[/red]
(Limit: 10MB)
```

### Error Type 3: Binary File Warning
**Severity**: WARNING (yellow)  
**Timeout**: Inline in panel  
**Action**: Continues but warns user

```
[yellow]Warning: .jpg may be binary file[/yellow]

(Showing as text...)
```

---

## Files Modified

### textual_ui.py
**Line 434-465**: `action_deep_analyze()` method
- Added Copilot upload limit check (5MB)
- Added clear error message with actual vs limit sizes
- Prevents upload if file exceeds limit

**Line 507-535**: `_read_file_safely()` method
- Updated local read limit message (10MB)
- Added clearer error formatting

---

## Testing Guide

### Test Case 1: Under Copilot Limit
```bash
# Create 2MB test file
fsutil file createnew test_2mb.txt 2097152

# Click in tree, press 'd'
# Expected: Reads and analyzes successfully ✅
```

### Test Case 2: Over Copilot Limit
```bash
# Create 10MB test file
fsutil file createnew test_10mb.txt 10485760

# Click in tree, press 'd'
# Expected: Error message, no upload ✅
```

### Test Case 3: Binary File
```bash
# Use any .jpg/.png/.exe file

# Click in tree, press 'd'
# Expected: Warning message, continues with caution ✅
```

---

## Limits Summary Table

| Scenario | Limit | Action | Message |
|----------|-------|--------|---------|
| File > 5MB | Copilot upload | Block | "Cannot upload files larger than 5MB" |
| File > 10MB | Local read | Block | "File too large to read locally" |
| Binary file | Type check | Warn | "May be binary file" |
| Content > 5KB | Preview | Truncate | "... [truncated, N more bytes]" |

---

## Future Enhancements

- [ ] Add streaming for large files (chunk upload)
- [ ] Add file compression before upload
- [ ] Add progress indicator for file reading
- [ ] Add configurable limit options
- [ ] Add file size info in directory tree
- [ ] Add "skip this file" option when limit exceeded

---

## Migration Notes

This feature maintains **backward compatibility**:
- ✅ Existing files under limits work as before
- ✅ Error messages are user-friendly and clear
- ✅ No breaking changes to API
- ✅ Silent failures prevented with explicit warnings

---

**Implementation Complete**: All size limits properly enforced with clear user messaging.

Generated: 2026-02-03
