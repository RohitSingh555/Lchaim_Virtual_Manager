from django.core.management.base import BaseCommand
from django.db import transaction
from students.models import StudentProfile, VolunteerLog
from datetime import date
import json
import os
from django.core import serializers


class Command(BaseCommand):
    help = 'Delete ABSENT volunteer log entries that fall outside student start and end dates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--student-id',
            type=int,
            help='Clean up logs for a specific student ID only',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about each deletion',
        )
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='volunteer_log_backups',
            help='Directory to store backup files (default: volunteer_log_backups)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        student_id = options['student_id']
        verbose = options['verbose']
        backup_dir = options['backup_dir']

        self.stdout.write(
            self.style.SUCCESS('Starting ABSENT volunteer log cleanup...')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No actual deletions will be performed')
            )

        # Create backup directory if it doesn't exist
        if not dry_run:
            os.makedirs(backup_dir, exist_ok=True)
            self.stdout.write(f'Backup directory: {backup_dir}')

        # Get students to process
        if student_id:
            try:
                students = [StudentProfile.objects.get(id=student_id)]
                self.stdout.write(f'Processing student ID: {student_id}')
            except StudentProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Student with ID {student_id} not found')
                )
                return
        else:
            students = StudentProfile.objects.all()
            self.stdout.write(f'Processing {students.count()} students')

        total_deleted = 0
        students_processed = 0
        students_with_issues = []
        all_logs_to_delete = []

        for student in students:
            if not student.start_date:
                if verbose:
                    self.stdout.write(
                        f'Student {student.id} ({student.first_name} {student.last_name}) has no start date - skipping'
                    )
                continue

            students_processed += 1
            student_deleted = 0

            # Get all volunteer logs for this student
            volunteer_logs = VolunteerLog.objects.filter(student=student)

            # Find logs to delete (only ABSENT entries)
            logs_to_delete = []

            for log in volunteer_logs:
                should_delete = False
                reason = ""

                # Only delete ABSENT entries that fall outside date range
                if log.status == 'Absent':
                    # Check if log date is before start date
                    if log.date < student.start_date:
                        should_delete = True
                        reason = f"absent entry before start date ({student.start_date})"

                    # Check if log date is after end date (if end date exists)
                    elif student.end_date and log.date > student.end_date:
                        should_delete = True
                        reason = f"absent entry after end date ({student.end_date})"

                if should_delete:
                    logs_to_delete.append((log, reason))
                    all_logs_to_delete.append(log)

            # Process deletions
            if logs_to_delete:
                if verbose:
                    self.stdout.write(
                        f'\nStudent {student.id}: {student.first_name} {student.last_name}'
                    )
                    self.stdout.write(f'  Start Date: {student.start_date}')
                    self.stdout.write(f'  End Date: {student.end_date or "Not set"}')
                    self.stdout.write(f'  Absent logs to delete: {len(logs_to_delete)}')

                for log, reason in logs_to_delete:
                    if verbose:
                        self.stdout.write(
                            f'    - {log.date} ({reason}) - Status: {log.status}'
                        )

                    if not dry_run:
                        log.delete()
                    
                    student_deleted += 1
                    total_deleted += 1

                if verbose:
                    self.stdout.write(f'  Deleted: {student_deleted} absent logs')

            # Check for students with potential issues
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
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'volunteer_logs_backup_{timestamp}.json')
            
            # Serialize the logs to JSON
            backup_data = serializers.serialize('json', all_logs_to_delete)
            
            with open(backup_file, 'w') as f:
                f.write(backup_data)
            
            self.stdout.write(
                self.style.SUCCESS(f'Backup created: {backup_file}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Backup contains {len(all_logs_to_delete)} volunteer log entries')
            )

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('CLEANUP SUMMARY')
        self.stdout.write('='*50)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would have deleted {total_deleted} ABSENT volunteer log entries')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {total_deleted} ABSENT volunteer log entries')
            )

        self.stdout.write(f'Students processed: {students_processed}')
        self.stdout.write(f'Students with issues: {len(students_with_issues)}')

        if backup_file:
            self.stdout.write(f'Backup file: {backup_file}')

        if students_with_issues:
            self.stdout.write('\nSTUDENTS WITH POTENTIAL ISSUES:')
            self.stdout.write('-' * 40)
            for issue in students_with_issues:
                self.stdout.write(
                    f'ID {issue["id"]}: {issue["name"]} - {issue["issue"]}'
                )
                self.stdout.write(
                    f'  Start: {issue["start_date"]}, End: {issue["end_date"]}'
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('\nCleanup completed successfully!')
            )
            if backup_file:
                self.stdout.write(
                    self.style.SUCCESS(f'To restore deleted logs, use: python manage.py restore_volunteer_logs {backup_file}')
                )
        else:
            self.stdout.write(
                self.style.WARNING('\nDry run completed. Run without --dry-run to perform actual deletions.')
            ) 