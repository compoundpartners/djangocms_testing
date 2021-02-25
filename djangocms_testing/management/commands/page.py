from logging import getLogger
from pprint import pformat

import six
import yaml
from cms import api
from cms.models.pagemodel import Page
from cms.models.placeholdermodel import Placeholder
from cms.plugin_pool import plugin_pool
from cms.utils.conf import get_cms_setting
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from aldryn_people.models import Group, Person
from aldryn_newsblog.models import NewsBlogConfig
from js_events.models import EventsConfig, Event, Speaker
from js_services.models import Service

from djangocms_testing import conf

logger = getLogger(__file__)
loremipsum = (
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Scripta sane et '
    'multa et polita, sed nescio quo pacto auctoritatem oratio non habet. '
    'Gerendus est mos, modo recte sentiat. Quo plebiscito decreta a senatu '
    'est consuli quaestio Cn. Quis Aristidem non mortuum diligit? Respondeat '
    'totidem verbis.'
)


class PageCommand(BaseCommand):
    help = 'Creates a CMS page with a .yaml template.'

    DEFAULT_LANGUAGE = conf.DEFAULT_LANGUAGE
    DEFAULT_TEMPLATE = conf.DEFAULT_TEMPLATE

    # ToDo:
    #  * Dump page to YAML
    def add_arguments(self, parser):
        parser.add_argument(
            'source',
            nargs='*',
            type=open,
            help='A yaml file containing the object description.')

        parser.add_argument(
            '--site-id',
            action='store',
            dest='site_id',
            default=1,
            type=int,
            help='The Site which the object is created for.'
        )

        parser.add_argument(
            '-o',
            '--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help='Delete an existing object if exists.'
        )
        parser.add_argument(
            '--dont_check_url',
            action='store_false',
            dest='check_url',
            default=True,
            help='Don\'t check url.'
        )
        parser.add_argument(
            '-d',
            '--data',
            dest='override_data',
            default=[],
            action='append',
            nargs='*',
            type=str,
            help='Override data for the object.'
        )

    def _debug(self, data, heading=None):
        if self.verbosity > 2:
            self.stdout.write('----- {heading}\n'.format(
                heading=(heading or 'debug message')))
            self.stdout.write(pformat(data, indent=2))
            self.stdout.write('-----\n')

    def _get_template(self, data):
        """
        Returns the appropriate template for the object.
        This can be overridden to get different templates based on the site, arguments, or data.
        """
        return get_cms_setting('TEMPLATES')[0][0]

    def _create_obj(self, data):
        return self._create_page(data)

    def _get_placeholder(self, obj, placeholder_name):
        try:
            return obj.placeholders.get(slot=placeholder_name)
        except Placeholder.DoesNotExist:
            # Placeholder not available for this template.
            return None

    def _create_page(self, data):
        """
        Create a bare page without any plugins yet.
        """
        page_data = {
            'title': data['title'],
            'slug': data['slug'],
            'language': self.language,
            'template': self._get_template(data),
            'parent': None,
            'site': self.site,
            'position': 'last-child',
            'in_navigation': True,
            'soft_root': data.get('soft_root', False),
            'apphook': data.get('apphook', None),
            'apphook_namespace': data.get('apphook_namespace', None),
            'created_by': 'Python API via YAML page builder',
        }
        self._debug(page_data, 'CMS Api Page data')
        page = api.create_page(**page_data)
        if data.get('publish', True):
            page.publish(self.language)
        return page.reload()

    def _attach_plugin(self, placeholder, plugin_name, plugin_data,
                       parent_plugin=None):
        """
        Creates a sample obj and attaches the given Plugin with
        the plugin data.
        """
        subplugin_list = plugin_data.pop('subplugins', [])

        if parent_plugin:
            self._debug(plugin_name, 'Sub Plugin')
        else:
            self._debug(plugin_name, 'Plugin')

        # ----------------------------------------------------------------------
        # Replace $image values with proper objects
        data = {}
        for k, v in six.iteritems(plugin_data):
            if isinstance(v, dict):
                key, value = list(v.items())[0]
                if key in self.sample_data and not isinstance(value, list):
                    data[k] = self.sample_data[key](value)
            elif v in self.sample_data:
                data[k] = self.sample_data[v]
            else:
                data[k] = v

        # ----------------------------------------------------------------------
        self._debug(plugin_data, 'New plugin data')

        if placeholder:
            new_plugin = api.add_plugin(
                target=parent_plugin,
                placeholder=placeholder,
                plugin_type=plugin_name,
                language=self.language,
                position='last-child',
                **data
            )
            # update m2m
            data = {}
            for k, v in six.iteritems(plugin_data):
                if isinstance(v, dict):
                    key, value = list(v.items())[0]
                    if key in self.sample_data and isinstance(value, list):
                        data[k] = self.sample_data[key](value)
            for field, values in six.iteritems(data):
                field = getattr(new_plugin, field)
                field.set(values)

            for plugin in subplugin_list:
                plugin_name, plugin_data = next(iter(plugin.items()))
                if not plugin_name in self.all_plugins:
                    self.stderr.write('Plugin {name} does not exist. Skipping...'.format(
                        name=plugin_name))
                self._attach_plugin(placeholder, plugin_name, plugin_data,
                                    parent_plugin=new_plugin)

            return new_plugin

    def _generate_sample_data(self):
        """
        For more complex use cases, this should be overriden to include more support data (i.e. images, models, etc)
        """
        return {
            '$loremipsum': '<p>{0}</p>'.format(loremipsum),
            '$service': lambda x: Service.objects.get(translations__slug=x),
            '$services': lambda x: Service.objects.filter(translations__slug__in=x),
            '$person': lambda x: Person.objects.get(translations__slug=x),
            '$people': lambda x: Person.objects.filter(translations__slug__in=x),
            '$group': lambda x: Group.objects.get(translations__slug=x),
            '$groups': lambda x: Group.objects.filter(translations__slug__in=x),
            '$speakers': lambda x: Speaker.objects.filter(slug__in=x),
            '$events': lambda x: Event.objects.filter(translations__slug__in=x),
            '$event_sections': lambda x: EventsConfig.objects.filter(namespace__in=x),
            '$article_sections': lambda x: NewsBlogConfig.objects.filter(namespace__in=x),
        }

    def _validate_data(self, data):
        """
        title
        slug
        template
        placeholder based on template
        check each plugin exists
        """
        required_fields = ['title']
        for f in required_fields:
            if not f in data:
                return False, 'Value for "{field}" is missing.'.format(field=f)

        # if data['template'] not in ('generic_page', 'topic_page'):
            # return False, 'Template must be either "generic_page" or "topic_page".'

        if not 'slug' in data:
            data['slug'] = slugify(data['title'])
        return True, 'All OK'

    def _get_queryset(self, **kwargs):
        return Page.objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'title_set__slug': data['slug']}

    def handle(self, *args, **kwargs):
        self.verbosity = kwargs['verbosity']
        self.overwrite = kwargs['overwrite']
        self.site_id = kwargs['site_id']
        self.check_url = kwargs['check_url']
        override_data = dict(kwargs['override_data'])


        self.site = self.site_id and Site.objects.get(id=self.site_id) or Site.objects.get_current()
        self.all_plugins = [i.__name__ for i in plugin_pool.get_all_plugins()]
        self.sample_data = self._generate_sample_data()
        self.language = self.DEFAULT_LANGUAGE

        sources = kwargs['source']
        if sources == []:
            sources = [None]
        for source in sources:
            try:
                if source is None:
                    data = {}
                else:
                    data = yaml.load(source, Loader=yaml.Loader)
                data.update(override_data)
                placeholders_data = {}
                if 'placeholders' in data:
                    placeholders_data = data['placeholders']
                    del data['placeholders']
            except yaml.scanner.ScannerError as e:
                self.stderr.write('Could not parse .yaml file. Error was:\n\n{e}'.format(e=e))
                return 0

            valid, reason = self._validate_data(data)
            if not valid:
                self.stderr.write('.yaml file is invalid. Reason: {0}'.format(reason))
                return 0

            self._debug(data, 'Parsed YAML data')

            queryset = self._get_queryset(**self._get_queryset_kwargs(data))
            self._debug(queryset, 'Existing objects')

            if queryset and self.overwrite:
                self.stdout.write('Found {num} objects with this slug. Deleting...'.format(
                    num=len(queryset)))
                for obj in queryset:
                    try:
                        obj.delete()
                    except:
                        pass
            elif queryset and not self.overwrite:
                self.stderr.write('A object with this kwargs %s already exists. '
                                  'Use the argument --overwrite to delete.' % self._get_queryset_kwargs(data))
                return 0

            self.language = data.get('language', self.DEFAULT_LANGUAGE)

            obj = self._create_obj(data)

            for placeholder_name, plugin_list in placeholders_data.items():
                placeholder = self._get_placeholder(obj, placeholder_name)
                for plugin in plugin_list:
                    plugin_name, plugin_data = next(iter(plugin.items()))
                    if not plugin_name in self.all_plugins:
                        self.stderr.write(f'Plugin {plugin_name} does not exist. Skipping...')
                    self._attach_plugin(placeholder, plugin_name, plugin_data)

            if hasattr(obj, 'get_absolute_url') and self._check_url(data) and self.check_url:
                language = data.get('language', self.DEFAULT_LANGUAGE)
                url = obj.get_absolute_url(language)
                print(f'OK. Object URL: http://{self.site.domain}{url}', file=self.stdout)
            else:
                print(f'OK. Object is created', file=self.stdout)

    def _check_url(self, data):
        return True

class Command(PageCommand):
    pass
