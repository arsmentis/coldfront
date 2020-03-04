from . import DataTypes
from .models import CustomizedBooleanChoice

from django.core.exceptions import ValidationError
from django.db import models


# Django requires validator functions to - well - not be methods...
def _datatype_is_valid(input_to_check):
    if input_to_check not in (t[0] for t in AttributeTypesModelMixin.TYPE_CHOICES):
        raise ValidationError('{} is not within the valid range'.format(input_to_check))


class AttributeTypesModelMixin(DataTypes, models.Model):
    # we don't want Django's typical model inheritance to apply
    class Meta:
        abstract = True

    # it is unnecessary, but recommended, that these align in index with DataTypes values
    TYPE_CHOICES = (
        (DataTypes.BOOLEAN, 'boolean'),
        (DataTypes.INT, 'integer'),
        (DataTypes.FLOAT, 'float'),
        (DataTypes.TEXT, 'text'),
        (DataTypes.DATE, 'date'),
    )

    datatype = models.SmallIntegerField(choices=TYPE_CHOICES, validators=[_datatype_is_valid])

    def save(self, *args, **kwargs):
        # enforce validation at the model layer for datatype choices
        _datatype_is_valid(self.datatype)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_datatype_display()

    @property
    def datatype_display(self):
        # in Django 2.2, get_FOO_display() is not overrideable
        # as such, we create a property that is
        # that allows subclasses to override this

        # for this base mixin, we simply use the implementation of get_FOO_display()
        return self.get_datatype_display()

    # idempotent conversion that can be used to convert to/from a backing value
    def convert_backing_value(self, value):
        return DataTypes.converters[self.datatype](value)

    # subclass may optionally implement
    def to_display_value(self, value):
        return value

    # subclass may optionally implement
    def from_display_value(self, value, *args, **kwargs):
        return value

    class AdminMixin:
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # make sure we use 'datatype_display' instead of 'datatype'
            try:
                if 'datatype' in self.list_display:
                    self.list_display = [
                        'datatype_display' if f == 'datatype' else f
                        for f in self.list_display
                    ]
            except AttributeError as e:
                # we should never get here, assuming Django admin operates as we expect
                raise AssertionError('Expected attribute to exist') from e

        # unfortunately we must even shim it here, to maintain a short description
        def datatype_display(self, obj):
            return obj.datatype_display
        datatype_display.short_description = 'datatype'


class AttributeValuesModelMixin(models.Model):
    # we don't want Django's typical model inheritance to apply
    class Meta:
        abstract = True

    _value = models.TextField()

    @property
    def value(self):
        return self.attributetype.convert_backing_value(self._value)

    @value.setter
    def value(self, new_value):
        try:
            self._value = self.attributetype.convert_backing_value(new_value)
        except (ValueError, TypeError) as e:
            raise ValidationError(*e.args) from e

    @property
    def attributetype(self):
        raise NotImplementedError('Subclass must implement!')

    @property
    def display_value(self):
        return self.attributetype.to_display_value(self.value)

    def from_display_value(self, value, *args, **kwargs):
        return self.attributetype.from_display_value(value, *args, **kwargs)

    class AdminMixin:
        # Django admin uses a ModelForm by default, and this does not represent
        # properties

        # as such, we implement a "shim" here to take _value and use the value setter
        def save_model(self, request, obj, form, change, *args, **kwargs):
            # we may also have a display value to convert from
            # for anywhere else in the app, we can use a form/template and do input/display nicely
            # for Django admin, however, we'd rather not edit the template
            new_value = obj.from_display_value(obj._value)

            # invoke setter
            obj.value = new_value

            super().save_model(request, obj, form, change, *args, **kwargs)


class CustomizedBooleanChoiceAttributeTypesModelMixin(AttributeTypesModelMixin):
    # we don't want Django's typical model inheritance to apply
    class Meta(AttributeTypesModelMixin.Meta):
        abstract = True  # subclasses are assumed concrete by default, so we set abstract again

    custom_boolean_choice = models.ForeignKey(
        CustomizedBooleanChoice,
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,  # if the choice is deleted, we fall back to True/False
    )

    def to_display_value(self, value):
        if self.custom_boolean_choice:
            if self.datatype == DataTypes.BOOLEAN:
                return self.custom_boolean_choice.true if value else self.custom_boolean_choice.false
            raise TypeError('Invalid datatype to apply custom_boolean_choice')
        return value

    def from_display_value(self, value, strict=False):
        if self.custom_boolean_choice and self.datatype == DataTypes.BOOLEAN:
            cust_bool = self.custom_boolean_choice
            vlower = value.lower()

            if vlower == cust_bool.true.lower():
                return True
            elif vlower == cust_bool.false.lower():
                return False

            if strict:
                raise TypeError('Unexpected value/type')

        # no-op otherwise
        return value

    def clean(self, *args, **kwargs):
        if self.custom_boolean_choice:
            if not self.datatype == DataTypes.BOOLEAN:
                raise ValidationError('Invalid datatype to apply custom boolean choice. Select boolean or remove custom boolean choice.')
        super().clean(*args, **kwargs)

    def __str__(self):
        if self.custom_boolean_choice:
            return '{} ({})'.format(super().__str__(), self.custom_boolean_choice)
        return super().__str__()

    @property
    def datatype_display(self):
        # use *this* class-layer's __str__ representation
        return CustomizedBooleanChoiceAttributeTypesModelMixin.__str__(self)

    class AdminMixin(AttributeTypesModelMixin.AdminMixin):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # make sure we do a select_related if we would display the datatype
            try:
                if 'datatype_display' in self.list_display:
                    field = 'custom_boolean_choice'
                    if not self.list_select_related:
                        self.list_select_related = [field]
                    elif field not in self.list_select_related:
                        self.list_select_related = list(self.list_select_related) + [field]
            except AttributeError as e:
                # we should never get here, assuming Django admin operates as we expect
                raise AssertionError('Expected attribute to exist') from e
