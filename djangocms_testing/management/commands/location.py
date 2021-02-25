from django.utils.text import slugify
from .page import PageCommand
from js_locations.models import Location

class Command(PageCommand):
    help = 'Creates a Location with a .yaml template.'

    def _get_placeholder(self, obj, placeholder_name):
        if hasattr(obj, placeholder_name):
            return getattr(obj, placeholder_name)
        else:
            return None

    def _create_obj(self, data):
        """
        Create a location without any plugins yet.
        """
        self._debug(data, 'Location data')
        obj = Location.objects.create(**data)
        return obj

    def _validate_data(self, data):
        required_fields = ['name']
        for f in required_fields:
            if not f in data:
                return False, 'Value for "{field}" is missing.'.format(field=f)
        if not 'slug' in data:
            data['slug'] = slugify(data['name'])
        return True, 'All OK'

    def _get_queryset(self, **kwargs):
        return Location.objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'translations__slug': data['slug']}


    def _check_url(self, data):
        return False
