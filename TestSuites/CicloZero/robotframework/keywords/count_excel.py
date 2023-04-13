"""
Load and create a pandas dataframe from an excel file
"""
import pandas as pd


def _load_excel_file(file_path: str) -> pd.DataFrame:
    """
    Load an excel file and return a pandas dataframe. The first row is used as the header
    """
    return pd.read_excel(file_path, header=0)

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
    for i in range(len(model_count)):
        model_count.loc[i, "Total"] = f"=B{i+2}-C{i+2}-D{i+2}-E{i+2}"

    _save_dataframe_to_excel(model_count, output_excel_path)

