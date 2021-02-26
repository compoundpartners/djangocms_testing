from .page import PageCommand
from js_services.models import Service, ServicesConfig
from django.utils.text import slugify
from aldryn_categories.models import Category

class Command(PageCommand):
    help = 'Creates a Service with a .yaml template.'

    def _get_placeholder(self, obj, placeholder_name):
        if hasattr(obj, placeholder_name):
            return getattr(obj, placeholder_name)
        else:
            return None

    def _separete_data(self, data):
        data_m2m = {}
        keys = list(data.keys())
        for field in keys:
            if field in ['sections', 'categories']:
                data_m2m[field] = data[field]
                del data[field]
        return data, data_m2m

    def _create_obj(self, data):
        """
        Create a bare page without any plugins yet.
        """
        self._debug(data, 'Service data')
        data, data_m2m = self._separete_data(data)
        obj = Service.objects.create(**data)
        for field, values in data_m2m.items():
            field = getattr(obj, field)
            field.set(values)
        return obj

    def _validate_data(self, data):
        required_fields = ['title']
        for f in required_fields:
            if not f in data:
                return False, 'Value for "{field}" is missing.'.format(field=f)
        if 'sections' in data:
            data['sections'] = ServicesConfig.objects.filter(namespace__in=data['sections'])
        if 'categories' in data:
            data['categories'] = Category.objects.filter(translations__slug__in=data['categories'])
        if not 'slug' in data:
            data['slug'] = slugify(data['title'])
        if 'is_published' in data:
            data['is_published_trans'] = data['is_published']
        return True, 'All OK'

    def _get_queryset(self, **kwargs):
        return Service.objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'translations__slug': data['slug']}
