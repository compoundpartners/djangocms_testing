from .page import PageCommand
from aldryn_people.models import Group
from django.utils.text import slugify

class Command(PageCommand):
    help = 'Creates a Group with a .yaml template.'

    def _get_placeholder(self, obj, placeholder_name):
        if hasattr(obj, placeholder_name):
            return getattr(obj, placeholder_name)
        else:
            return None

    def _create_obj(self, data):
        """
        Create a bare page without any plugins yet.
        """
        self._debug(data, 'Group data')
        obj = Group.objects.create(**data)
        return obj

    def _validate_data(self, data):
        required_fields = ['name',]
        for f in required_fields:
            if not f in data:
                return False, 'Value for "{field}" is missing.'.format(field=f)
        if not 'slug' in data:
            data['slug'] = slugify(data['name'])
        if not 'namespace' in data:
            data['namespace'] = slugify(data['name'])
        return True, 'All OK'

    def _get_queryset(self, **kwargs):
        return Group.objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'translations__slug': data['slug']}
