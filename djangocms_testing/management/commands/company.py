from django.core.management.base import BaseCommand
from django.utils.text import slugify
from .page import PageCommand
from js_services.models import Service
from js_events.models import Event
from aldryn_newsblog.models import Article
from aldryn_people.models import Person

try:
    from js_companies.models import Company

    class Command(PageCommand):
        help = 'Creates a Company with a .yaml template.'

        def _create_obj(self, data):
            """
            Create a location without any plugins yet.
            """
            self._debug(data, 'Company data')
            data, data_m2m = self._separete_data(data)
            obj = Company.objects.create(**data)
            for field, values in data_m2m.items():
                field = getattr(obj, field)
                field.set(values)
            return obj

        def _separete_data(self, data):
            data_m2m = {}
            keys = list(data.keys())
            for field in keys:
                if field not in ['name']:
                    data_m2m[field] = data[field]
                    del data[field]
            return data, data_m2m

        def _validate_data(self, data):
            required_fields = ['name']
            for f in required_fields:
                if not f in data:
                    return False, 'Value for "{field}" is missing.'.format(field=f)
            if 'articles' in data:
                data['articles'] = Article.objects.filter(translations__slug__in=data['articles']).order_by('?')[0:1]
            if 'events' in data:
                data['events'] = Event.objects.filter(translations__slug__in=data['events']).order_by('?')[0:1]
            if 'services' in data:
                data['services'] = Service.objects.filter(translations__slug__in=data['services']).order_by('?')[0:1]
            if 'people' in data:
                data['people'] = Person.objects.filter(translations__slug__in=data['people']).order_by('?')[0:1]
            return True, 'All OK'

        def _get_queryset(self, **kwargs):
            return Company.objects.filter(**kwargs)

        def _get_queryset_kwargs(self, data):
            return {'name': data['name']}

        def _check_url(self, data):
            return False
except ImportError:
    class Command(PageCommand):
        def handle(self, *args, **kwargs):
            pass
