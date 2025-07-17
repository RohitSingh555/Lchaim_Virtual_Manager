#!/usr/bin/env python
"""
Standalone script to restore volunteer log entries from a backup file.

Usage:
    python restore_volunteer_logs_script.py BACKUP_FILE [--dry-run] [--verbose]

Arguments:
    BACKUP_FILE  Path to the backup JSON file to restore from

Options:
    --dry-run     Show what would be restored without actually restoring
    --verbose     Show detailed information about each restoration
"""

import os
import sys
import django
import argparse
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'placement_portal.settings')
django.setup()

from students.models import VolunteerLog, StudentProfile, Shift
from django.core import serializers


def restore_volunteer_logs(backup_file, dry_run=False, verbose=False):
    """
    Restore volunteer log entries from a backup file.
    
    Args:
        backup_file (str): Path to the backup JSON file
        dry_run (bool): If True, show what would be restored without actually restoring
        verbose (bool): If True, show detailed information about each restoration
    """
    print('Starting volunteer log restoration...')
    
    if dry_run:
        print('DRY RUN MODE - No actual restoration will be performed')
    
    # Check if backup file exists
    if not os.path.exists(backup_file):
        print(f'ERROR: Backup file not found: {backup_file}')
        return
    
    try:
        # Read the backup file
        with open(backup_file, 'r') as f:
            backup_data = f.read()
        
        # Deserialize the data
        objects = list(serializers.deserialize('json', backup_data))
        
        print(f'Found {len(objects)} volunteer log entries in backup')
        
        if dry_run:
            print(f'DRY RUN: Would restore {len(objects)} volunteer log entries')
            
            if verbose:
                for obj in objects:
                    log = obj.object
                    print(
                        f'  - Student: {log.student.first_name} {log.student.last_name} '
                        f'({log.student.id}), Date: {log.date}, Status: {log.status}'
                    )
            return
        
        # Restore the objects
        restored_count = 0
        skipped_count = 0
        error_count = 0
        
        for obj in objects:
            try:
                log = obj.object
                
                # Check if this log already exists (by student, date, and shift)
                existing_log = VolunteerLog.objects.filter(
                    student=log.student,
                    date=log.date,
                    shift=log.shift
                ).first()
                
                if existing_log:
                    if verbose:
                        print(
                            f'  SKIPPED: Log already exists for {log.student.first_name} '
                            f'{log.student.last_name} on {log.date}'
                        )
                    skipped_count += 1
                    continue
                
                # Save the log
                obj.save()
                restored_count += 1
                
                if verbose:
                    print(
                        f'  RESTORED: {log.student.first_name} {log.student.last_name} '
                        f'({log.student.id}), Date: {log.date}, Status: {log.status}'
                    )
                    
            except Exception as e:
                error_count += 1
                if verbose:
                    print(f'  ERROR restoring log: {e}')
        
        # Summary
        print('\n' + '='*50)
        print('RESTORATION SUMMARY')
        print('='*50)
        
        print(f'Successfully restored {restored_count} volunteer log entries')
        
        if skipped_count > 0:
            print(f'Skipped {skipped_count} entries (already exist)')
        
        if error_count > 0:
            print(f'Errors: {error_count} entries')
        
        print('\nRestoration completed successfully!')
        
    except Exception as e:
        print(f'Error reading backup file: {e}')
        return


def main():
    parser = argparse.ArgumentParser(
        description='Restore volunteer log entries from a backup file'
    )
    parser.add_argument(
        'backup_file',
        type=str,
        help='Path to the backup JSON file to restore from'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be restored without actually restoring'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed information about each restoration'
    )
    
    args = parser.parse_args()
    
    try:
        restore_volunteer_logs(
            backup_file=args.backup_file,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
    except Exception as e:
        print(f'ERROR: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main() 