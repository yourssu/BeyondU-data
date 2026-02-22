import pandas as pd
import sys
import pathlib
from sqlalchemy import create_engine

sys.path.insert(0, str(pathlib.Path('c:/Users/yyc/dev/BeyondU-Data')))
engine = create_engine('mysql+mysqlconnector://root:392766yyc%40%21@localhost:3306/beyondu_test')

query = "SELECT u.name_kor, u.language_score, l.exam_type, l.min_score, l.level_code FROM university u JOIN language_requirement l ON u.id = l.university_id WHERE u.name_eng LIKE '%Nanjing%'"
df = pd.read_sql(query, engine)
print(df.to_string())
