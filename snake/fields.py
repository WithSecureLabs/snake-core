"""The fields module.

This replicates and extends the marshmallow fields module.

NOTEs:
    * We are bringing fields into our namespace.

TODOs:
    * Extend all fields with a valid arguments option.
"""

# pylint: disable=arguments-differ
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

import marshmallow.exceptions
import marshmallow.fields
from marshmallow.fields import __all__  # noqa
from marshmallow.utils import missing


class SnakeField:
    def __init__(self, *args, **kwargs):
        # Get our kwargs, handle them, remove them, pass it on
        # TODO: We should support ranges for number based items which
        # marshmallow alread supports, we just need to expose in to_dict
        if 'values' in kwargs:
            self.__values = kwargs['values']
            del kwargs['values']
            kwargs['validate'] = self.values_validator
        else:
            self.__values = []
        super().__init__(*args, **kwargs)

    @property
    def values(self):
        if hasattr(self.__values, '__call__'):
            return self.__values()
        else:
            return self.__values

    def values_validator(self, value):
        if value not in self.values:
            raise marshmallow.exceptions.ValidationError("'%s' must be in '%s'" % value, self.values)

    def to_dict(self):
        # Resolve Aliases:
        # URL = Url
        # Str = String
        # Bool = Boolean
        # Int = Integer
        type_ = type(self).__name__
        if type_ is 'Str':
            type_ = 'string'
        elif type_ is 'Bool':
            type_ = 'boolean'
        elif type_ is 'Int':
            type_ = 'integer'
        else:
            type_.lower()
        default = self.default if type(self.default) is not type(missing) else None
        return {
            'default': default,
            'required': self.required,
            'type': type_,
            'values': self.values
        }


# This is a bit grim, but we can dynamically extend all Marshmallow field objects
for field in __all__:
    ignore = ['Dict', 'Field']
    if field not in ignore:
        cls = getattr(marshmallow.fields, field)
        globals()[field] = type(field, (SnakeField,cls,), {})
    else:
        cls = getattr(marshmallow.fields, field)
        globals()[field] = type(field, (cls,), {})


# Fields
class Enum(Str):  # noqa
    """The enum field.

    This adds the `type` fields that is used to set the type of the enum and
    used for validation.

    Attributes:
        enum_type (:obj:`IterableType`): The enum type for the field.
    """

    def __init__(self, *args, **kwargs):
        if 'type' in kwargs:
            enum_type = kwargs.pop('type')
        else:
            enum_type = args[:-1]
        # super().__init__(self, *args, **kwargs)  # FIXME: Causes a recursion Error
        Str.__init__(self, *args, **kwargs)  # noqa
        self.enum_type = enum_type
        if not self.validators:
            self.validators = [self.validate_type]

    def validate_type(self, value):
        """The validation method.

        This checks that the value is indeed in the enum and therefore checks
        validity.
        """
        if value in self.enum_type:
            return True
        return False


class ObjectId(Str):  # noqa
    """The object id field.

    This is used to handle Mongo's object id field.
    """

    def _deserialize(self, val, attr, data):
        return str(val)
