from django.test import TestCase

from coldfront.core.test_helpers.factories import (
    ProjectAttributeTypeFactory,
)
from coldfront.core.project.forms import (
    ProjectAttributeModelForm,
)
from coldfront.core.utils.eav import DataTypes


class TestProjectAttributeModelForm(TestCase):
    Form = ProjectAttributeModelForm

    class Data:
        def __init__(self):
            self.attribute_type = ProjectAttributeTypeFactory()


    def _arbitrary_bound_form(self):
        form_data = {
            'project_attribute_type': self.data.attribute_type.pk,
            'value': 'anything',
        }
        return self.Form(form_data)

    def setUp(self):
        # we don't create a form here because Form instances are supposed to be treated as immutable
        # ref: https://docs.djangoproject.com/en/2.2/ref/forms/api/#bound-and-unbound-forms
        self.data = self.Data()

    def test_construct_empty(self):
        form = self.Form()

        self.assertIsNotNone(form)

    def test_fields(self):
        form = self.Form()

        self.assertIn('value', form.fields)
        self.assertNotIn('_value', form.fields)

    def test_bound_form_basic(self):
        form = self._arbitrary_bound_form()

        self.assertTrue(form.is_bound)

        self.assertFalse(hasattr(form, 'cleaned_data'))
        form.full_clean()
        self.assertNotEqual(len(form.cleaned_data), 0)
        self.assertTrue(form.is_valid())

    def test_type_mismatch(self):
        wrongtype_data = {
            DataTypes.BOOLEAN: 'quantum particle',
            DataTypes.INT: 'clearly not an integer',
            DataTypes.FLOAT: '127.0.0.1',
            # not real, but for reference:
            # DataTypes.TEXT: "something that isn't text",
            DataTypes.DATE: 'February 30th, 1984',
        }

        for item in wrongtype_data.items():
            (datatype, value) = item
            with self.subTest(item=item):
                attribute_type = ProjectAttributeTypeFactory(datatype=datatype)

                form_data = {
                    'project_attribute_type': attribute_type.pk,
                    'value': value,
                }
                form = self.Form(form_data)

                form.full_clean()

                self.assertFalse(form.is_valid())
                self.assertNotEqual(len(form.errors), 0)
