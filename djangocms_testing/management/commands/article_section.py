from django.utils.text import slugify
from aldryn_newsblog.models import NewsBlogConfig
from .page import PageCommand


class Command(PageCommand):
    help = 'Creates a Article app config with a .yaml template.'

    def _get_placeholder(self, obj, placeholder_name):
        if hasattr(obj, placeholder_name):
            return getattr(obj, placeholder_name)
        else:
            return None

    def _create_obj(self, data):
        """
        Create a bare page without any plugins yet.
        """
        self._debug(data, 'Article app config data')
        obj = NewsBlogConfig.objects.create(**data)
        return obj

    def _validate_data(self, data):
        required_fields = ['app_title']
        for f in required_fields:
            if not f in data:
                return False, 'Value for "{field}" is missing.'.format(field=f)
        if not 'namespace' in data:
            data['namespace'] = slugify(data['app_title'])
        return True, 'All OK'

    def _get_queryset(self, **kwargs):
        return NewsBlogConfig.objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'namespace': data['namespace']}
