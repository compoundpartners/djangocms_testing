from .page import PageCommand
from aldryn_newsblog.models import Article, NewsBlogConfig
from django.utils.text import slugify
from js_services.models import Service
from js_locations.models import Location

class Command(PageCommand):
    help = 'Creates a Article with a .yaml template.'

    def _get_placeholder(self, obj, placeholder_name):
        if hasattr(obj, placeholder_name):
            return getattr(obj, placeholder_name)
        else:
            return None

    def _separete_data(self, data):
        data_m2m = {}
        keys = list(data.keys())
        for field in keys:
            if field in ['services', 'categories', 'locations']:
                data_m2m[field] = data[field]
                del data[field]
        return data, data_m2m

    def _create_obj(self, data):
        """
        Create a bare page without any plugins yet.
        """
        data, data_m2m = self._separete_data(data)
        self._debug(data, 'Article data')
        obj = Article.objects.create(**data)
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
            data['app_config'] = NewsBlogConfig.objects.get(namespace=data['app_config'])
        except NewsBlogConfig.DoesNotExist:
            return False, 'App config "%s" does not exist.' % data['app_config']
        if not 'slug' in data:
            data['slug'] = slugify(data['title'])
        if 'services' in data:
            data['services'] = Service.objects.filter(translations__slug__in=data['services'])
        if 'locations' in data:
            data['locations'] = Location.objects.filter(translations__slug__in=data['locations'])
        return True, 'All OK'

    def _get_queryset(self, **kwargs):
        return Article.objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'translations__slug': data['slug']}
