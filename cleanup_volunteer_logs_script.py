#!/usr/bin/env python
"""
Standalone script to delete ABSENT volunteer log entries that fall outside student start and end dates.

Usage:
    python cleanup_volunteer_logs_script.py [--dry-run] [--student-id ID] [--verbose] [--backup-dir DIR]

Options:
    --dry-run     Show what would be deleted without actually deleting
    --student-id  Clean up logs for a specific student ID only
    --verbose     Show detailed information about each deletion
    --backup-dir  Directory to store backup files (default: volunteer_log_backups)
"""

import os
import sys
import django
import argparse
import json
from datetime import date, datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'placement_portal.settings')
django.setup()

from students.models import StudentProfile, VolunteerLog
from django.core import serializers


def cleanup_volunteer_logs(dry_run=False, student_id=None, verbose=False, backup_dir='volunteer_log_backups'):
    print('Starting ABSENT volunteer log cleanup...')
    
    if dry_run:
        print('DRY RUN MODE - No actual deletions will be performed')
    
    # Create backup directory if it doesn't exist
    if not dry_run:
        os.makedirs(backup_dir, exist_ok=True)
        print(f'Backup directory: {backup_dir}')
    
    if student_id:
        try:
            students = [StudentProfile.objects.get(id=student_id)]
            print(f'Processing student ID: {student_id}')
        except StudentProfile.DoesNotExist:
            print(f'ERROR: Student with ID {student_id} not found')
            return
    else:
        students = StudentProfile.objects.all()
        print(f'Processing {students.count()} students')
    
    total_deleted = 0
    students_processed = 0
    students_with_issues = []
    all_logs_to_delete = []
    
    for student in students:
        if not student.start_date:
            if verbose:
                print(f'Student {student.id} ({student.first_name} {student.last_name}) has no start date - skipping')
            continue
        
        students_processed += 1
        student_deleted = 0
        
        volunteer_logs = VolunteerLog.objects.filter(student=student)
        
        logs_to_delete = []
        
        for log in volunteer_logs:
            should_delete = False
            reason = ""
            
            if log.status == 'Absent':
                if log.date < student.start_date:
                    should_delete = True
                    reason = f"absent entry before start date ({student.start_date})"
                
                elif student.end_date and log.date > student.end_date:
                    should_delete = True
                    reason = f"absent entry after end date ({student.end_date})"
            
            if should_delete:
                logs_to_delete.append((log, reason))
                all_logs_to_delete.append(log)
        
        if logs_to_delete:
            if verbose:
                print(f'\nStudent {student.id}: {student.first_name} {student.last_name}')
                print(f'  Start Date: {student.start_date}')
                print(f'  End Date: {student.end_date or "Not set"}')
                print(f'  Absent logs to delete: {len(logs_to_delete)}')
            
            for log, reason in logs_to_delete:
                if verbose:
                    print(f'    - {log.date} ({reason}) - Status: {log.status}')
                
                if not dry_run:
                    log.delete()
                
                student_deleted += 1
                total_deleted += 1
            
            if verbose:
                print(f'  Deleted: {student_deleted} absent logs')
        
        if student.end_date and student.end_date < student.start_date:
            students_with_issues.append({
                'id': student.id,
                'name': f"{student.first_name} {student.last_name}",
                'issue': 'End date is before start date',
                'start_date': student.start_date,
                'end_date': student.end_date
            })
    
    # Create backup if we have logs to delete
    backup_file = None
    if all_logs_to_delete and not dry_run:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'volunteer_logs_backup_{timestamp}.json')
        
        # Serialize the logs to JSON
        backup_data = serializers.serialize('json', all_logs_to_delete)
        
        with open(backup_file, 'w') as f:
            f.write(backup_data)
        
        print(f'Backup created: {backup_file}')
        print(f'Backup contains {len(all_logs_to_delete)} volunteer log entries')
    
    # Summary
    print('\n' + '='*50)
    print('CLEANUP SUMMARY')
    print('='*50)
    
    if dry_run:
        print(f'DRY RUN: Would have deleted {total_deleted} ABSENT volunteer log entries')
    else:
        print(f'Successfully deleted {total_deleted} ABSENT volunteer log entries')
    
    print(f'Students processed: {students_processed}')
    print(f'Students with issues: {len(students_with_issues)}')
    
    if backup_file:
        print(f'Backup file: {backup_file}')
        print(f'To restore deleted logs, use: python restore_volunteer_logs_script.py {backup_file}')
    
    if students_with_issues:
        print('\nSTUDENTS WITH POTENTIAL ISSUES:')
        print('-' * 40)
        for issue in students_with_issues:
            print(f'ID {issue["id"]}: {issue["name"]} - {issue["issue"]}')
            print(f'  Start: {issue["start_date"]}, End: {issue["end_date"]}')
    
    if not dry_run:
        print('\nCleanup completed successfully!')
    else:
        print('\nDry run completed. Run without --dry-run to perform actual deletions.')


def main():
    parser = argparse.ArgumentParser(
        description='Delete ABSENT volunteer log entries that fall outside student start and end dates'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--student-id',
        type=int,
        help='Clean up logs for a specific student ID only'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed information about each deletion'
    )
    parser.add_argument(
        '--backup-dir',
        type=str,
        default='volunteer_log_backups',
        help='Directory to store backup files (default: volunteer_log_backups)'
    )
    
    args = parser.parse_args()
    
    try:
        cleanup_volunteer_logs(
            dry_run=args.dry_run,
            student_id=args.student_id,
            verbose=args.verbose,
            backup_dir=args.backup_dir
        )
    except Exception as e:
        print(f'ERROR: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main() 