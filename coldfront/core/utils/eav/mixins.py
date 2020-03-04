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

    # idempotent conversion that can be used to convert to/from a backing value
    def convert_backing_value(self, value):
        return DataTypes.converters[self.datatype](value)


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

    def clean(self, *args, **kwargs):
        if self.custom_boolean_choice:
            if not self.datatype == DataTypes.BOOLEAN:
                raise ValidationError('Invalid datatype to apply custom boolean choice. Select boolean or remove custom boolean choice.')
        super().clean(*args, **kwargs)

    def __str__(self):
        if self.custom_boolean_choice:
            return '{} ({})'.format(super().__str__(), self.custom_boolean_choice)
        return super().__str__()
