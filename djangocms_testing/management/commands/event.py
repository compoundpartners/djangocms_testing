from .page import PageCommand
from js_events.models import Event, EventsConfig
from django.utils.text import slugify
from js_services.models import Service
from js_locations.models import Location
from aldryn_people.models import Person

class Command(PageCommand):
    help = 'Creates a Event with a .yaml template.'

    def _get_placeholder(self, obj, placeholder_name):
        if hasattr(obj, placeholder_name):
            return getattr(obj, placeholder_name)
        else:
            return None

    def _separete_data(self, data):
        data_m2m = {}
        keys = list(data.keys())
        for field in keys:
            if field in ['services', 'locations']:
                data_m2m[field] = data[field]
                del data[field]
        return data, data_m2m

    def _create_obj(self, data):
        """
        Create a bare page without any plugins yet.
        """
        data, data_m2m = self._separete_data(data)
        self._debug(data, 'Event data')
        obj = Event.objects.create(**data)
        for field, values in data_m2m.items():
            field = getattr(obj, field)
            field.set(values)
        return obj

    def _validate_data(self, data):
        required_fields = ('title', 'app_config')
        for f in required_fields:
            if not f in data:
                return False, 'Value for "{field}" is missing.'.format(field=f)
        try:
            data['app_config'] = EventsConfig.objects.get(namespace=data['app_config'])
        except EventsConfig.DoesNotExist:
            return False, 'App config "%s" does not exist.' % data['app_config']
        if not 'slug' in data:
            data['slug'] = slugify(data['title'])
        if 'services' in data:
            data['services'] = Service.objects.filter(translations__slug__in=data['services'])
        if 'locations' in data:
            data['locations'] = Location.objects.filter(translations__slug__in=data['locations'])
        if 'host' in data:
            data['host'] = Person.objects.filter(translations__slug=data['host']).first()
        return True, 'All OK'

    def _get_queryset(self, **kwargs):
        return Event.all_objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'translations__slug': data['slug']}
