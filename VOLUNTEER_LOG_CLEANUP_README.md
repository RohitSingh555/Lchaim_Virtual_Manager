# Volunteer Log Cleanup Scripts

This directory contains scripts to clean up **ABSENT** volunteer log entries that fall outside student start and end dates, with automatic backup and restore functionality.

## Overview

The scripts will delete **ONLY ABSENT** `VolunteerLog` entries that have dates:
- **Before** the student's `start_date`
- **After** the student's `end_date` (if end_date is set)

**Important:** All **PRESENT** volunteer log entries are preserved, regardless of their dates.

## 🔄 Backup & Restore Features

- **Automatic Backup**: Before deletion, all volunteer logs to be deleted are automatically backed up to JSON files
- **Easy Restoration**: Use the restore scripts to bring back deleted entries if needed
- **Safe Restoration**: Restore scripts check for existing entries to avoid duplicates
- **Timestamped Backups**: Each backup file includes a timestamp for easy identification

## Available Scripts

### 1. Django Management Commands

#### Cleanup Command
**File:** `students/management/commands/cleanup_volunteer_logs.py`

**Usage:**
```bash
# Run from the project root directory
python manage.py cleanup_volunteer_logs [options]
```

**Options:**
- `--dry-run`: Show what would be deleted without actually deleting
- `--student-id ID`: Clean up logs for a specific student ID only
- `--verbose`: Show detailed information about each deletion
- `--backup-dir DIR`: Directory to store backup files (default: volunteer_log_backups)

#### Restore Command
**File:** `students/management/commands/restore_volunteer_logs.py`

**Usage:**
```bash
# Restore from a backup file
python manage.py restore_volunteer_logs BACKUP_FILE [options]
```

**Options:**
- `--dry-run`: Show what would be restored without actually restoring
- `--verbose`: Show detailed information about each restoration

### 2. Standalone Scripts

#### Cleanup Script
**File:** `cleanup_volunteer_logs_script.py`

**Usage:**
```bash
# Run from the project root directory
python cleanup_volunteer_logs_script.py [--dry-run] [--student-id ID] [--verbose] [--backup-dir DIR]
```

#### Restore Script
**File:** `restore_volunteer_logs_script.py`

**Usage:**
```bash
# Restore from a backup file
python restore_volunteer_logs_script.py BACKUP_FILE [--dry-run] [--verbose]
```

## Examples

### Cleanup with Backup

#### Dry Run (Recommended First Step)
```bash
# Django management command
python manage.py cleanup_volunteer_logs --dry-run --verbose

# Standalone script
python cleanup_volunteer_logs_script.py --dry-run --verbose
```

#### Clean Up All Students with Backup
```bash
# Django management command
python manage.py cleanup_volunteer_logs --verbose

# Standalone script
python cleanup_volunteer_logs_script.py --verbose
```

#### Clean Up Specific Student with Custom Backup Directory
```bash
# Django management command
python manage.py cleanup_volunteer_logs --student-id 123 --verbose --backup-dir my_backups

# Standalone script
python cleanup_volunteer_logs_script.py --student-id 123 --verbose --backup-dir my_backups
```

### Restore from Backup

#### Preview Restoration (Dry Run)
```bash
# Django management command
python manage.py restore_volunteer_logs volunteer_log_backups/volunteer_logs_backup_20241201_143022.json --dry-run --verbose

# Standalone script
python restore_volunteer_logs_script.py volunteer_log_backups/volunteer_logs_backup_20241201_143022.json --dry-run --verbose
```

#### Restore Deleted Entries
```bash
# Django management command
python manage.py restore_volunteer_logs volunteer_log_backups/volunteer_logs_backup_20241201_143022.json --verbose

# Standalone script
python restore_volunteer_logs_script.py volunteer_log_backups/volunteer_logs_backup_20241201_143022.json --verbose
```

## What the Scripts Do

### Cleanup Process
1. **Iterate through all students** (or a specific student if ID is provided)
2. **Skip students without start dates** (they can't be processed)
3. **Find ABSENT volunteer logs** that fall outside the valid date range:
   - **Absent** logs with dates before `start_date`
   - **Absent** logs with dates after `end_date` (if end_date exists)
4. **Preserve all PRESENT logs** regardless of their dates
5. **Create automatic backup** of all logs to be deleted
6. **Delete the invalid ABSENT logs** (unless in dry-run mode)
7. **Report issues** like students with end dates before start dates
8. **Provide a summary** of the cleanup operation

### Restore Process
1. **Read the backup JSON file** containing deleted volunteer logs
2. **Check for existing entries** to avoid duplicates
3. **Restore missing entries** to the database
4. **Skip entries that already exist** (safe restoration)
5. **Provide detailed summary** of restoration results

## Safety Features

- **Automatic backup creation** before any deletion
- **Only deletes ABSENT entries**: All PRESENT entries are preserved
- **Dry-run mode**: Always test with `--dry-run` first to see what would be deleted/restored
- **Verbose output**: Use `--verbose` to see exactly what's being processed
- **Individual student processing**: Use `--student-id` to process only one student
- **Safe restoration**: Restore scripts check for existing entries to prevent duplicates
- **Error handling**: Scripts handle missing students and other errors gracefully

## Output Example

### Cleanup Output
```
Starting ABSENT volunteer log cleanup...
Backup directory: volunteer_log_backups
Processing 50 students

Student 123: John Doe
  Start Date: 2024-01-15
  End Date: 2024-05-15
  Absent logs to delete: 2
    - 2024-01-10 (absent entry before start date (2024-01-15)) - Status: Absent
    - 2024-05-20 (absent entry after end date (2024-05-15)) - Status: Absent
  Deleted: 2 absent logs

Backup created: volunteer_log_backups/volunteer_logs_backup_20241201_143022.json
Backup contains 8 volunteer log entries

==================================================
CLEANUP SUMMARY
==================================================
Successfully deleted 8 ABSENT volunteer log entries
Students processed: 50
Students with issues: 2
Backup file: volunteer_log_backups/volunteer_logs_backup_20241201_143022.json
To restore deleted logs, use: python manage.py restore_volunteer_logs volunteer_log_backups/volunteer_logs_backup_20241201_143022.json

Cleanup completed successfully!
```

### Restore Output
```
Starting volunteer log restoration...
Found 8 volunteer log entries in backup

  RESTORED: John Doe (123), Date: 2024-01-10, Status: Absent
  RESTORED: John Doe (123), Date: 2024-05-20, Status: Absent
  SKIPPED: Log already exists for Jane Smith on 2024-01-15

==================================================
RESTORATION SUMMARY
==================================================
Successfully restored 7 volunteer log entries
Skipped 1 entries (already exist)
Errors: 0 entries

Restoration completed successfully!
```

## Backup File Structure

Backup files are stored in JSON format using Django's serializer, containing:
- Complete volunteer log data
- Student relationships
- Shift relationships
- All field values including dates, times, status, notes, etc.

**Backup file naming convention:**
```
volunteer_logs_backup_YYYYMMDD_HHMMSS.json
```

## Important Notes

- **Backup files are created automatically** before any deletion (unless in dry-run mode)
- **Backup directory is created automatically** if it doesn't exist
- **Always run with `--dry-run` first** to see what will be deleted
- **Students without start dates** are skipped (they need start dates to be processed)
- **Students with end dates before start dates** are flagged as issues but not processed
- **The scripts only delete ABSENT VolunteerLog entries** - PRESENT entries are always preserved
- **The scripts don't modify student profiles** - only volunteer logs are affected
- **Restore scripts are safe** - they won't create duplicate entries

## Why Only Absent Entries?

The scripts are designed to only delete **ABSENT** entries because:

1. **Present entries represent actual attendance** and should be preserved for record-keeping
2. **Absent entries outside the valid date range** are likely erroneous or unnecessary
3. **This approach is safer** and prevents accidental deletion of important attendance data

## Troubleshooting

### Common Issues

1. **"Student with ID X not found"**
   - Check that the student ID exists in the database

2. **"No students processed"**
   - Check that students have start dates set

3. **"Backup file not found"**
   - Verify the backup file path is correct
   - Check that the backup file exists in the specified location

4. **Permission errors**
   - Make sure you have write access to the database and backup directory

### Getting Help

If you encounter issues:
1. Run with `--verbose` to see detailed output
2. Check the database directly to verify student data
3. Ensure Django is properly configured and the database is accessible
4. Verify backup files are readable and contain valid JSON data 