from logging import getLogger
from pprint import pformat

import six
import yaml
from django.core import management
from django.core.management.base import BaseCommand

from djangocms_testing import conf

logger = getLogger(__file__)

class Command(BaseCommand):
    help = 'Run scripts with a .yaml template.'

    def add_arguments(self, parser):
        parser.add_argument(
            'source',
            nargs='+',
            type=open,
            help='A yaml file containing the page description.')
        parser.add_argument(
            '--dont_check_url',
            action='store_false',
            dest='check_url',
            default=True,
            help='Check url.'
        )
        parser.add_argument(
            '-o',
            '--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help='Delete an existing object if exists.'
        )

    def _debug(self, data, heading=None):
        if self.verbosity > 2:
            self.stdout.write('----- {heading}\n'.format(
                heading=(heading or 'debug message')))
            self.stdout.write(pformat(data, indent=2))
            self.stdout.write('-----\n')

    def _validate_data(self, data):
        """
        title
        slug
        template
        placeholder based on template
        check each plugin exists
        """
        #required_fields = ('title', 'slug')
        #for f in required_fields:
        #    if not f in data:
        #        return False, 'Value for "{field}" is missing.'.format(field=f)

        # if data['template'] not in ('generic_page', 'topic_page'):
            # return False, 'Template must be either "generic_page" or "topic_page".'

        return True, 'All OK'

    def handle(self, *args, **kwargs):
        self.verbosity = kwargs['verbosity']

        for source in kwargs['source']:
            try:
                data = yaml.load(source, Loader=yaml.Loader)
            except yaml.scanner.ScannerError as e:
                self.stderr.write('Could not parse .yaml file. Error was:\n\n{e}'.format(e=e))
                return 0

            valid, reason = self._validate_data(data)
            if not valid:
                self.stderr.write('.yaml file is invalid. Reason: {0}'.format(reason))
                return 0

            self._debug(data, 'Parsed YAML data')

            for commands in data:
                command, options = list(commands.items())[0]
                params = []
                if 'source' in options:
                    params.append(options.pop('source'))
                if kwargs['overwrite']:
                    options['overwrite'] = kwargs['overwrite']
                if kwargs['verbosity']:
                    options['verbosity'] = kwargs['verbosity']
                if not kwargs['check_url']:
                    options['dont_check_url'] = True
                management.call_command(command, *params, **options)
