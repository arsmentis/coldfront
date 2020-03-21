from ast import literal_eval
import datetime


class DataTypes:
    # DO NOT edit these values - to support new types, only add values after
    BOOLEAN = 0
    INT = 1
    FLOAT = 2
    TEXT = 3
    DATE = 4

    # also DO NOT edit this
    # handcrafted database migrations, or a new DATE type, are needed to change the stored format
    DATE_STR_FORMAT = "%Y-%m-%d"

    # idempotent methods - bool() and date* are not, so we must implement
    class ConvertIdempotent:
        @staticmethod
        def BOOLEAN(value):
            if isinstance(value, bool):
                return value

            if value == 'True':
                return True
            if value == 'False':
                return False
            # also support any capitalization
            vlower = value.lower()
            if vlower == 'true':
                return True
            if vlower == 'false':
                return False

            raise TypeError('Unexpected value/type')

        @staticmethod
        def DATE(value):
            if isinstance(value, datetime.date):
                return value
            if isinstance(value, datetime.datetime):
                return value.date()
            if isinstance(value, str):
                return datetime.datetime.strptime(value.strip(), DataTypes.DATE_STR_FORMAT).date()
            raise TypeError('Unexpected value/type')

        # with a backing type of str, float() by itself with have a slight
        # potential to cause precision loss
        # we can reduce that some by conservatively converting to int if valid
        @staticmethod
        def FLOAT(value):
            if isinstance(value, str):
                try:
                    converted = literal_eval(value)
                except SyntaxError as e:
                    raise TypeError('Unexpected value/type') from e
                if isinstance(converted, (int, float)):
                    return converted
            elif isinstance(value, (int, float)):
                return value
            raise TypeError('Unexpected value/type')

    # these must align in index
    converters = (
        ConvertIdempotent.BOOLEAN,
        int,
        ConvertIdempotent.FLOAT,
        str.strip,
        ConvertIdempotent.DATE,
    )
