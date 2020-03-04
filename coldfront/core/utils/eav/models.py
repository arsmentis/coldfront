from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords


class CustomizedBooleanChoice(TimeStampedModel):
    true = models.CharField(max_length=30)
    false = models.CharField(max_length=30)

    history = HistoricalRecords()

    def __str__(self):
        return '{}/{}'.format(self.true, self.false)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('true', 'false'), name='unique_entry'),
        ]
