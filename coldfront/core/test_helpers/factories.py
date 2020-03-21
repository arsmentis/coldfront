from factory import (
    DjangoModelFactory,
    lazy_attribute,
    SubFactory,
)

from django.contrib.auth.models import User
from coldfront.core.field_of_science.models import FieldOfScience
from coldfront.core.project.models import (
    Project,
    ProjectAttributeType,
    ProjectStatusChoice,
)
from coldfront.core.publication.models import PublicationSource
from coldfront.core.utils.eav.models import CustomizedBooleanChoice


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User


class FieldOfScienceFactory(DjangoModelFactory):
    class Meta:
        model = FieldOfScience


class ProjectStatusChoiceFactory(DjangoModelFactory):
    class Meta:
        model = ProjectStatusChoice


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    title = 'Test project!'
    pi = SubFactory(UserFactory)
    description = 'This is a project description.'
    field_of_science = SubFactory(FieldOfScienceFactory)
    status = SubFactory(ProjectStatusChoiceFactory)
    force_review = False
    requires_review = False


class CustomizedBooleanChoiceFactory(DjangoModelFactory):
    class Meta:
        model = CustomizedBooleanChoice

    true = 'Yup!'
    false = 'no...'


class ProjectAttributeTypeFactory(DjangoModelFactory):
    class Meta:
        model = ProjectAttributeType

    class Params:
        # needed because of the lazy attribute
        true = None
        false = None

    name = 'Test attribute type!'
    datatype = ProjectAttributeType.TEXT  # a very forgiving default

    @lazy_attribute
    def custom_boolean_choice(self):
        if self.datatype != ProjectAttributeType.BOOLEAN:
            return None

        if not self.true and not self.false:
            return CustomizedBooleanChoiceFactory()

        return CustomizedBooleanChoiceFactory(true=self.true, false=self.false)


class PublicationSourceFactory(DjangoModelFactory):
    class Meta:
        model = PublicationSource

    name = 'doi'
    url = 'https://doi.org/'
