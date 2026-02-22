import pandas as pd
from src.transform.cleaner import DataCleaner

df = pd.DataFrame({"nation": ["  미국  ", "일본"], "name_kor": ["Harvard   University", "Tokyo  University"]})
cleaner = DataCleaner(df)
result = cleaner.clean()
print("Whitespace result:", result.to_dict())

df2 = pd.DataFrame({"nation": ["미국", None, "일본"], "name_kor": ["Harvard", None, "Tokyo"]})
cleaner2 = DataCleaner(df2)
result2 = cleaner2.clean()
print("Empty rows result:", result2.to_dict())
