"""
Load and create a pandas dataframe from an excel file
"""
import pandas as pd


def _load_excel_file(file_path: str) -> pd.DataFrame:
    """
    Load an excel file and return a pandas dataframe. The first row is used as the header
    """
    return pd.read_excel(file_path, header=0)

def _load_tsv_file(file_path: str) -> pd.DataFrame:
    """
    Load a tsv file and return a pandas dataframe. The first row is used as the header
    """
    return pd.read_csv(file_path, sep="\t", header=0)

def _count_number_of_same_values_in_column(dataframe: pd.DataFrame, column_name: str) -> pd.Series:
    """
    Count the number of same values in a column
    """
    return dataframe[column_name].value_counts()

def _add_empty_column_to_dataframe(dataframe: pd.DataFrame, column_name: str):
    """
    Add an empty column to a pandas dataframe
    """
    dataframe[column_name] = ""

def _save_dataframe_to_excel(dataframe: pd.DataFrame, file_path: str):
    """
    Save a pandas dataframe to an excel file
    """
    dataframe.to_excel(file_path, index=False)

def _add_total_column_to_dataframe(dataframe: pd.DataFrame, column_name: str):
    """
    Add a column to a pandas dataframe with the formula "=B2-C2-D2-E2"
    """
    for i in range(len(dataframe)):
        dataframe.loc[i, column_name] = f"=B{i+2}-C{i+2}-D{i+2}-E{i+2}"


def create_excel(count_excel_path: str, output_excel_path: str):
    df = _load_excel_file(count_excel_path)
    model_count = _count_number_of_same_values_in_column(df, "Producto")

    # Convert Series[int] to DataFrame[int] with columns "Producto" and "Cantidad"
    model_count = model_count.to_frame().reset_index()
    model_count.columns = ["prod", "count"]

    # Add empty column "Amzn pend", "Amzn pend env" "flend"
    _add_empty_column_to_dataframe(model_count, "amzn pend")
    _add_empty_column_to_dataframe(model_count, "amzn pend env")
    _add_empty_column_to_dataframe(model_count, "flend")

    # Add column "Total" with "Cantidad" - "Amzn pend" - "Amzn pend env" - "flend". Values must be calculated with excel formulas (=Bi-Ci-Di-Ei)
    _add_total_column_to_dataframe(model_count, "Total")

    _save_dataframe_to_excel(model_count, output_excel_path)


def append_tsv_to_main_excel(tsv_path: str, excel_path:str, output_excel_path: str):
    excel_df = _load_excel_file(excel_path)
    tsv_df = _load_tsv_file(tsv_path)

    # Count the number of same values in the "sku" column
    model_count = _count_number_of_same_values_in_column(tsv_df, "sku")

    # Convert Series[int] to DataFrame[int] with columns "prod" and "count"
    model_count = model_count.to_frame().reset_index()
    model_count.columns = ["prod", "count"]

    # Insert the values in the "Amzn pend env" column with the same "prod" value. If the product is not in the excel, add it to the end of the list
    for i in range(len(model_count)):
        # Search for the product in the excel which contains the model_count prod
        prod = model_count.loc[i, "prod"]
        # Get the excel row where is the substring of the model_count prod
        excel_row = excel_df[excel_df["prod"].str.contains(str(prod))]
        # Check if the excel row is empty
        if excel_row.empty:
            # If the excel row is empty, add the model_count prod to the end of the excel
            excel_df.loc[len(excel_df)] = [prod, "", "", model_count.loc[i, "count"], "", ""] # type: ignore
        else:
            # If the excel row is not empty, add the model_count count to the excel row
            excel_df.loc[excel_row.index, "amzn pend env"] = model_count.loc[i, "count"] # type: ignore

    # Add column "Total" with "Cantidad" - "Amzn pend" - "Amzn pend env" - "flend". Values must be calculated with excel formulas (=Bi-Ci-Di-Ei)
    _add_total_column_to_dataframe(excel_df, "Total")

    _save_dataframe_to_excel(excel_df, output_excel_path)


def append_dict_to_main_excel(order_count_dict: dict, excel_path:str, output_excel_path: str):
    excel_df = _load_excel_file(excel_path)

    # Insert the values in the "Amzn pend" column with the same "prod" value. If the product is not in the excel, add it to the end of the list
    for prod, count in order_count_dict.items():
        # Search for the product in the excel which contains the model_count prod
        excel_row = excel_df[excel_df["prod"].str.contains(str(prod))]
        # Check if the excel row is empty
        if excel_row.empty:
            # If the excel row is empty, add the model_count prod to the end of the excel
            excel_df.loc[len(excel_df)] = [prod, "", "", count, "", ""] # type: ignore
        else:
            # If the excel row is not empty, add the model_count count to the excel row
            excel_df.loc[excel_row.index, "amzn pend"] = count # type: ignore

    # Add column "Total" with "Cantidad" - "Amzn pend" - "Amzn pend env" - "flend". Values must be calculated with excel formulas (=Bi-Ci-Di-Ei)
    _add_total_column_to_dataframe(excel_df, "Total")

    _save_dataframe_to_excel(excel_df, output_excel_path)

