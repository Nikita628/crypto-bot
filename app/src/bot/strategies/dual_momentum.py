from .base import Base
from ..technical_indicators import DataFrameDecorator
from ..deal import Deal, DealDirection

# Strategy description in comments ...
#
#

class DualMomentum(Base):
    def __init__(self):
        self.strategy = 'dual_momentum'

    def get_entry_direction(self, df: DataFrameDecorator) -> DealDirection or None:
        pass

    def is_exit(self, df: DataFrameDecorator, deal: Deal) -> bool:
        pass