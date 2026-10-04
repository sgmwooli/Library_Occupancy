import pandas as pd

df1 = pd.read_csv("/Users/maxwooliscroft/Library/CloudStorage/GoogleDrive-maxiwool8@gmail.com/My Drive/Uni/Final Downloads/OneDrive/Uni/Python/Other_Python/Library_Occupancy/occupancy_log.csv")
df2 = pd.read_csv("/Users/maxwooliscroft/Library/CloudStorage/GoogleDrive-maxiwool8@gmail.com/My Drive/Uni/Final Downloads/OneDrive/Uni/Python/Other_Python/Library_Occupancy/occupancy_log_OLD.csv")
df3 = pd.read_csv("/Users/maxwooliscroft/Library/CloudStorage/GoogleDrive-maxiwool8@gmail.com/My Drive/Uni/Final Downloads/OneDrive/Uni/Python/Other Python/Library_Occupancy/occupancy_log.csv")
df4 = pd.read_csv("/Users/maxwooliscroft/Library/CloudStorage/GoogleDrive-maxiwool8@gmail.com/My Drive/Uni/Final Downloads/OneDrive/Uni/Python/Other Python/Library Occupancy/occupancy_log2.csv")
df5 = pd.read_csv("/Users/maxwooliscroft/Library/CloudStorage/GoogleDrive-maxiwool8@gmail.com/My Drive/Uni/Final Downloads/OneDrive/Uni/Python/Other Python/Library Occupancy/merged.csv")

merged = pd.concat([df1, df2, df3, df4, df5], ignore_index=True)

merged = merged.drop_duplicates()

merged.to_csv("all_data_4-10-26.csv", index=False)
