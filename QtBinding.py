
# In Python source files where we want to use Qt facilities, do the following:
#
# from QtBinding import QtCore, QtGui, QtSignal, QtSlot
#
# ... then, use the QtSlot() decorator for slots, and the QtSignal() function to declare signals.

import sys, logging

usePySide = ("--pyside" in sys.argv[1:])

if usePySide:
    from PySide import QtCore, QtGui
    QtSignal         = QtCore.Signal
    QtSlot_Unchecked = QtCore.Slot
else:
    from PyQt4 import QtCore, QtGui
    QtSignal         = QtCore.pyqtSignal
    QtSlot_Unchecked = QtCore.pyqtSlot

def QtSlot_Checked(*args, **kwargs):

    # The QtSlot_Checked decorator function wraps the functionality of the QtSlot_Unchecked decorator function,
    # and verifies that (1) the function being decorated does not throw an exception and (2) that it returns None.

    def check_slot_function_result(f):
        def check_slot_function_result_wrapper(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                if result is not None:
                    raise ValueError("Value returned from slot function '{}' is not None as required, but '{}', of type {}.".format(f, result, type(result)))
            except BaseException as exception:
                logging.exception("intercepted an exception: {}".format(exception))
                sys.exit(1)
            return None # this is the expected behavior for a slot function.
        # The __name__ assignment is needed to allow the Qt binding to work properly (at least in PySide).
        # If this is omitted, slots are executed in the incorrect thread when using PySide.
        check_slot_function_result_wrapper.__name__ = f.__name__
        return check_slot_function_result_wrapper

    decorator = QtSlot_Unchecked(*args, **kwargs)
    def wrapped_qtslot_decorator(f):
        return decorator(check_slot_function_result(f))
    return wrapped_qtslot_decorator

# Use the "checked" variant of QtSlot.
QtSlot = QtSlot_Checked
