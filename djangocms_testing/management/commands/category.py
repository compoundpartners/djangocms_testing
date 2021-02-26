from django.utils.text import slugify
from .page import PageCommand
from aldryn_categories.models import Category

class Command(PageCommand):
    help = 'Creates a Category with a .yaml template.'

    def _create_obj(self, data):
        """
        Create a location without any plugins yet.
        """
        self._debug(data, 'Category data')
        root = Category.objects.first().get_root()
        obj = root.add_child(**data)
        obj.save()
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
        return Category.objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'translations__slug': data['slug']}


    def _check_url(self, data):
        return False
