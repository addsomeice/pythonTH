import pandas as pd
import math

# 读取完整的 distance_matrix.csv 文件
df = pd.read_csv('distance_matrix.csv')

# 将数据切分为 20 个较小的 DataFrame
num_rows = len(df)
chunk_size = math.ceil(num_rows / 20)

for i, chunk in enumerate(range(0, num_rows, chunk_size)):
    # 构造每个切分的文件名
    output_file = f'./data/distance_matrix_{i}.csv'

    # 切分并保存 DataFrame 到文件
    df_chunk = df.iloc[chunk:chunk+chunk_size]
    df_chunk.to_csv(output_file, index=False)
