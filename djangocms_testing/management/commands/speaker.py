from django.utils.text import slugify
from .page import PageCommand
from js_events.models import Speaker
from js_services.models import Service
from js_locations.models import Location

class Command(PageCommand):
    help = 'Creates a Speaker with a .yaml template.'

    def _get_placeholder(self, obj, placeholder_name):
        return None

    def _create_obj(self, data):
        """
        Create a bare page without any plugins yet.
        """
        self._debug(data, 'Speaker data')
        obj = Speaker.objects.create(**data)
        return obj

    def _validate_data(self, data):
        if 'name' in data:
            names = data['name'].split(' ', 2)
            names += names
            del data['name']
            data['first_name'] = names[0]
            data['last_name'] = names[1]
        else:
            required_fields = ('first_name', 'last_name')
            for f in required_fields:
                if not f in data:
                    return False, 'Value for "{field}" is missing.'.format(field=f)
            names = [data['first_name'], data['last_name']]
        if not 'slug' in data:
            data['slug'] = slugify(' '.join(names[:2]))
        return True, 'All OK'

    def _get_queryset(self, **kwargs):
        return Speaker.objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'slug': data['slug']}
