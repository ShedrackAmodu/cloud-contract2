"""
Django management command to calculate fitness margin improvements
Usage: python manage.py calculate_fitness_margin [baseline_file.json]
"""
from django.core.management.base import BaseCommand
import json
import os
import sys
from pathlib import Path

# Add privacy_smartcontracts directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PRIVACY_DIR = BASE_DIR / 'privacy_smartcontracts'
sys.path.insert(0, str(PRIVACY_DIR))

from fitness_margin_calculator import FitnessMarginCalculator

class Command(BaseCommand):
    help = 'Calculate fitness margin improvements from system metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--baseline',
            type=str,
            help='Path to baseline JSON file for comparison',
            default=None
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: fitness_margin_results.json)',
            default='fitness_margin_results.json'
        )

    def handle(self, *args, **options):
        baseline_file = options['baseline']
        output_file = options['output']
        
        self.stdout.write(self.style.SUCCESS('Calculating fitness margin improvements...'))
        
        baseline_data = None
        if baseline_file and os.path.exists(baseline_file):
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
            self.stdout.write(self.style.SUCCESS(f'Loaded baseline from {baseline_file}'))
        
        calculator = FitnessMarginCalculator()
        results = calculator.calculate_fitness_margins(baseline_data)
        calculator.save_results(results, output_file)
        calculator.generate_report(results)
        
        self.stdout.write(self.style.SUCCESS(f'\nResults saved to {output_file}'))

