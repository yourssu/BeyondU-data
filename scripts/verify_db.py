import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.load.database import DatabaseLoader
import pandas as pd
from sqlalchemy import create_engine

def main():
    loader = DatabaseLoader()
    engine = loader.engine
    
    query = """
    SELECT name_eng, min_gpa, remark
    FROM university
    WHERE name_eng LIKE '%Baden-Wuerttemberg%'
       OR name_eng LIKE '%Changshu%'
       OR name_eng LIKE '%Rostov%'
       OR remark IS NOT NULL AND remark != ''
    LIMIT 10;
    """
    
    df = pd.read_sql(query, engine)
    print("Database Query Results:")
    print(df.to_string())
    
    # Let's count how many have min_gpa > 5 and how many have remark
    count_query = """
    SELECT 
        SUM(CASE WHEN min_gpa > 5.0 THEN 1 ELSE 0 END) as weird_gpa_count,
        SUM(CASE WHEN remark IS NOT NULL AND remark != '' THEN 1 ELSE 0 END) as non_empty_remark_count
    FROM university;
    """
    counts = pd.read_sql(count_query, engine)
    print("\nSummary Counts:")
    print(counts.to_string())

if __name__ == "__main__":
    main()
