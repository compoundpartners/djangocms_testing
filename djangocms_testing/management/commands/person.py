from django.utils.text import slugify
from .page import PageCommand
from aldryn_people.models import Person, Group
from js_services.models import Service
from js_locations.models import Location

class Command(PageCommand):
    help = 'Creates a Person with a .yaml template.'

    def _get_placeholder(self, obj, placeholder_name):
        if hasattr(obj, placeholder_name):
            return getattr(obj, placeholder_name)
        else:
            return None

    def _separete_data(self, data):
        data_m2m = {}
        keys = list(data.keys())
        for field in keys:
            if field in ['groups', 'services']:
                data_m2m[field] = data[field]
                del data[field]
        return data, data_m2m

    def _create_obj(self, data):
        """
        Create a bare page without any plugins yet.
        """
        data, data_m2m = self._separete_data(data)
        self._debug(data, 'Person data')
        obj = Person.objects.create(**data)
        for field, values in data_m2m.items():
            field = getattr(obj, field)
            field.set(values)
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
        if 'groups' in data:
            data['groups'] = Group.objects.filter(translations__slug__in=data['groups'])
        if 'services' in data:
            data['services'] = Service.objects.filter(translations__slug__in=data['services'])
        if 'location' in data:
            data['location'] = Location.objects.filter(translations__slug=data['location']).first()
        return True, 'All OK'

    def _get_queryset(self, **kwargs):
        return Person.objects.filter(**kwargs)

    def _get_queryset_kwargs(self, data):
        return {'translations__slug': data['slug']}
