from django.core.management.base import BaseCommand
from django.core import serializers
from students.models import VolunteerLog, StudentProfile, Shift
import json
import os


class Command(BaseCommand):
    help = 'Restore volunteer log entries from a backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to the backup JSON file to restore from',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without actually restoring',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about each restoration',
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write(
            self.style.SUCCESS('Starting volunteer log restoration...')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No actual restoration will be performed')
            )

        # Check if backup file exists
        if not os.path.exists(backup_file):
            self.stdout.write(
                self.style.ERROR(f'Backup file not found: {backup_file}')
            )
            return

        try:
            # Read the backup file
            with open(backup_file, 'r') as f:
                backup_data = f.read()

            # Deserialize the data
            objects = list(serializers.deserialize('json', backup_data))
            
            self.stdout.write(f'Found {len(objects)} volunteer log entries in backup')

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'DRY RUN: Would restore {len(objects)} volunteer log entries')
                )
                
                if verbose:
                    for obj in objects:
                        log = obj.object
                        self.stdout.write(
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
                            self.stdout.write(
                                f'  SKIPPED: Log already exists for {log.student.first_name} '
                                f'{log.student.last_name} on {log.date}'
                            )
                        skipped_count += 1
                        continue
                    
                    # Save the log
                    obj.save()
                    restored_count += 1
                    
                    if verbose:
                        self.stdout.write(
                            f'  RESTORED: {log.student.first_name} {log.student.last_name} '
                            f'({log.student.id}), Date: {log.date}, Status: {log.status}'
                        )
                        
                except Exception as e:
                    error_count += 1
                    if verbose:
                        self.stdout.write(
                            self.style.ERROR(f'  ERROR restoring log: {e}')
                        )

            # Summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write('RESTORATION SUMMARY')
            self.stdout.write('='*50)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully restored {restored_count} volunteer log entries')
            )
            
            if skipped_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'Skipped {skipped_count} entries (already exist)')
                )
            
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'Errors: {error_count} entries')
                )

            self.stdout.write(
                self.style.SUCCESS('\nRestoration completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading backup file: {e}')
            )
            return 