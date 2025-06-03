# from .general import setup as setup_general
# from .core import setup as setup_core
# from .marriage import setup as setup_marriage
# from .verification import setup as setup_verification

# def setup_commands(bot):
#     setup_general(bot)
#     setup_core(bot)
#     setup_marriage(bot)
#     setup_verification(bot)

from .core import setup as core_setup
from .general import setup as general_setup

def setup(bot):
    core_setup(bot)
    general_setup(bot)
