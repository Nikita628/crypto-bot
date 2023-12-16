from .base import Base
import pandas as pd

# Strategy description in comments ...
#
#

class DualMomentum(Base):
    def get_entry_direction(self, df: pd.DataFrame) -> DealDirection or None:
        pass

    def is_exit(self, df: pd.DataFrame, deal: Deal) -> bool:
        pass