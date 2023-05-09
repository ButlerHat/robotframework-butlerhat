"""
Load and create a pandas dataframe from an excel file
"""
import pandas as pd

def load_excel_file(file_path: str) -> pd.DataFrame:
    """
    Load an excel file and return a pandas dataframe. The first row is used as the header
    """
    return pd.read_excel(file_path, header=0)

# Get the list of prod rows
def get_skus(excel_path) -> list[str]:
    """
    Get the list of products from the excel file
    """
    df = load_excel_file(excel_path)
    # Get sku wich is iPXS-SL-64-B -R in string: [iPXS-SL-64-B -R] iPhone XS (Silver, 64 GB, B, REBU)
    return [product.split("]")[0].split("[")[-1] for product in df["prod"].tolist() if "[" in product and "]" in product]

def get_skus_df(excel_path) -> pd.DataFrame:
    """
    Get the list of products from the excel file. 
    """
    df = load_excel_file(excel_path)

    # Get sku wich is iPXS-SL-64-B -R in string: [iPXS-SL-64-B -R] iPhone XS (Silver, 64 GB, B, REBU)
    ret_df = df[df["prod"].str.contains(r"\[.*\]")].copy()
    ret_df["sku"] = ret_df["prod"].str.split("]").str[0].str.split("[").str[-1]
    ret_df["compute price"] = True

    # Remove sku from prod
    ret_df["prod"] = ret_df["prod"].str.split("]").str[-1].str.strip()

    # If NaN, set to 0
    ret_df["amz unshipped"] = ret_df["amz unshipped"].fillna(0)
    ret_df["amz pending"] = ret_df["amz pending"].fillna(0)
    ret_df["flend"] = ret_df["flend"].fillna(0)

    get_total = lambda count, amz_unshipped, amz_pending, flendu: count - amz_unshipped - amz_pending - flendu
    ret_df['Total'] = ret_df.apply(lambda row: get_total(row['count'], row['amz unshipped'], row['amz pending'], row['flend']), axis=1)

    # Return columns: sku, count, amz_unshipped, amz_pending, flendu, Total, compute_price
    return ret_df[["prod", "sku", "count", "amz unshipped", "amz pending", "flend", "Total", "compute price"]]


def append_prices_to_df(df: pd.DataFrame, prices_excel: str) -> pd.DataFrame:
    """
    Append the prices to the dataframe
    """
    prices_df = load_excel_file(prices_excel)
    # Get SKU with 

    # Merge the two dataframes
    return pd.merge(df, prices_df, how="left", on="sku")

