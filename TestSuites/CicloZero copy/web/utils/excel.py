"""
Load and create a pandas dataframe from an excel file
"""
import re
import pandas as pd
import openpyxl


def load_excel_file(file_path: str, sheet: str | int = 0) -> pd.DataFrame:
    """
    Load an excel file and return a pandas dataframe. The first row is used as the header
    """
    return pd.read_excel(file_path, header=0, sheet_name=sheet)

# Get the list of prod rows
def get_skus(excel_path) -> list[str]:
    """
    Get the list of products from the excel file
    """
    df = load_excel_file(excel_path)
    # Get sku wich is iPXS-SL-64-B -R in string: [iPXS-SL-64-B -R] iPhone XS (Silver, 64 GB, B, REBU)
    return [product.split("]")[0].split("[")[-1] for product in df["prod"].tolist() if "[" in product and "]" in product]

def get_skus_df(excel_path, compute_all) -> pd.DataFrame:
    """
    Get the list of products from the excel file. 
    """
    df = load_excel_file(excel_path)

    # Get sku wich is iPXS-SL-64-B -R in string: [iPXS-SL-64-B -R] iPhone XS (Silver, 64 GB, B, REBU)
    ret_df = df[df["prod"].str.contains(r"\[.*\]")].copy()
    ret_df["sku"] = ret_df["prod"].str.split("]").str[0].str.split("[").str[-1]
    ret_df["compute price"] = compute_all

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
    # Get SKU with the sheet name
    sku = openpyxl.load_workbook(prices_excel).sheetnames[-1]

    # Load the excel file
    prices_df = load_excel_file(prices_excel, sku)
    
    # prices_df columns: marketplace status, self price, best price, best seller, second price, second seller, third price, third seller, url
    # For every sku in df, append the columns if not exists with (marketplace value) status, (marketplace value) price, (marketplace value) seller...
    assert 'marketplace' in prices_df.columns, 'marketplace column not found in prices excel'
    
    for marketplace in prices_df['marketplace'].unique():
        for col in [c for c in prices_df.columns if c != 'marketplace']:
            col_name = f"{marketplace} {col}"
            if col_name not in df.columns:
                df[col_name] = None

            sku_row = df[df["sku"] == sku]
            df.loc[sku_row.index, col_name] = prices_df[prices_df["marketplace"] == marketplace][col].values[0]

    return df

def clean_df_for_statistics(df):
    """
    Get the price columns from the dataframe. Clean df first
    """
    # Define a list of price column names
    price_cols = [col for col in df.columns if 'price' in col]

    # Loop through each price column
    for col in price_cols:
        # Replace empty strings and NaN with 0
        df[col] = df[col].replace('', 0)
        df[col] = df[col].fillna(0)

        # Apply the str.replace() method only to columns with string values
        def convert_str(x):
            if isinstance(x, str):
                # Check if string contains any numbre in 3.000,00 format
                if re.search(r'\d{1,3}\.\d{3},\d{2}', x):
                    x = x.replace('.', '')
                if re.search(r'\d{1,3}\,\d{3}.\d{2}', x):
                    x = x.replace(',', '')

                s = re.sub(r'[^\d.,]','',x.replace('\xa0','').replace(',','.')).strip()
                if s == '':
                    return 0
                else:
                    return float(s)
            return float(x)

        df[col] = df[col].apply(convert_str)

        # Replace empty strings and NaN with 0
        df[col] = df[col].replace('', 0)
        df[col] = df[col].fillna(0)

        # Convert the column to float
        df[col] = df[col].astype(float)

    return df
