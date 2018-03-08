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

from marshmallow.fields import *  # noqa


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
