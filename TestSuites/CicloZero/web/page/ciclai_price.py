import os
import datetime
import asyncio
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import utils.vnc as vnc
import utils.robot_handler as robot_handler
import utils.excel as excel
from urllib.request import urlopen


def ciclai_price():
    # Title
    main_color = st.secrets.theme.primaryColor
    st.markdown(f'# <span style="color:{main_color}">CiclAI</span> Price', unsafe_allow_html=True)

    # Upload file
    st.markdown("## Upload stock excel")
    
    uploaded_file = st.file_uploader("Choose a excel")
    if uploaded_file is None:
        st.warning("Please upload a file. The robot won't work without it")
        
        # TODO: Remove this
        uploaded_file = "/workspaces/CicloZero/downloads/stock/stock.quant.full.result.xlsx"

    # Get last file in stock folder
    stock_path = st.secrets.paths.stock_excel
    stock_excels = [os.path.join(stock_path, f) for f in os.listdir(stock_path) if os.path.isfile(os.path.join(stock_path, f))]
    stock_excels = [f for f in stock_excels if f.endswith(".xlsx")]
    stock_excels.sort(key=os.path.getmtime, reverse=True)
    stock_names = [os.path.basename(f) for f in stock_excels]

    option = st.selectbox("Select a stock excel", stock_names)
    if option is not None:
        uploaded_file = os.path.join(stock_path, option)
        
    # SKUs table
    st.markdown("# Select SKUs")
    if uploaded_file is not None:
        skus_df = excel.get_skus_df(uploaded_file)
        edited_df = st.experimental_data_editor(skus_df, use_container_width=True)
    else:
        edited_df = None
        st.warning("Please upload a file.")
    
    # Run button
    st.markdown("# Search prices in Amazon")
    col1, col2 = st.columns([1, 2])

    # VNC
    with col2:
        vnc.vnc("http://localhost:6081/")
        st.caption("VNC password: vscode")
    
    with col1:
        with st.form("Run Robot with args"):

            if edited_df is None:
                st.warning("Please upload a file.")
                return
            
            skus = edited_df[edited_df["compute price"]]["sku"].tolist()
            st.markdown(f"### SKUs: {len(skus)}")
            if st.form_submit_button("Run", type="primary"):
                with st.spinner("Running robot, launching every 40 seconds to avoid OTP conflicts..."):
                    asyncio.run(run_robots(uploaded_file, skus))
    
    # Show prices
    st.markdown("# Show prices")
    df_prices = None
    if edited_df is not None:
        df_prices = show_prices(edited_df)

    # Show statistics
    st.markdown("# Show statistics")
    if df_prices is not None:
        st.markdown("## Rise the price")
        st.info("The following statistics are calculated only for products where the best price is greater than the self price")
        show_statistics_pie(df_prices)
        show_statistics_pie_per_sku(df_prices)
        
        st.markdown("## Prices per SKU")
        show_statistics_plot(df_prices)


async def run_robots(uploaded_file, skus):
    price_path = st.secrets.paths.price_excel
    tasks = []
    for sku in skus:
        args = [
            f'SKU:"{sku}"',
            f'STOCK_EXCEL_PATH:"{uploaded_file}"',
            f'SKU_EXCEL_PATH:"{os.path.join(price_path, sku + ".xlsx")}"',
        ]
        tasks.append(asyncio.create_task(robot_handler.run_robot(sku, args, "CiclAiPrices.robot", msg=f"Running {sku}")))
        await asyncio.sleep(40)

    await asyncio.gather(*tasks)

def show_prices(stock_df: pd.DataFrame):
    # Get excels from price folder
    price_path = st.secrets.paths.price_excel
    price_excels = [os.path.join(price_path, f) for f in os.listdir(price_path) if os.path.isfile(os.path.join(price_path, f))]
    price_excels = [f for f in price_excels if f.endswith(".xlsx")]

    # Delete compute price column
    df = stock_df.drop(columns=["compute price"])
    for price_excel in price_excels:
        try:
            df = excel.append_prices_to_df(df, price_excel)
        except Exception as e:
            st.error(f"Error appending prices from {price_excel}: {e}")
            continue
    
    # Show df
    st.dataframe(df)

    # Save excel
    excel_name = f"CiclAiPrice_{datetime.datetime.now().strftime('%H-%M_%d-%m-%Y')}.xlsx"
    df.to_excel(os.path.join('/tmp', excel_name), index=False)
    with open(os.path.join('/tmp', excel_name), 'rb') as f:
        st.download_button(label=f'Download {excel_name}', data=f, file_name=excel_name)

    return df
    

def show_statistics_plot(df):
    df = excel.clean_df_for_statistics(df)

    # Define a list of countries
    countries = ['Germany', 'Netherlands', 'Italy', 'Spain', 'France']
    # Loop through each country
    for country in countries:
        # Define the self price and best price column names
        self_price_col = f'{country} self price'
        best_price_col = f'{country} best price'
        best_seller_col = f'{country} best seller'
        second_price_col = f'{country} second price'
        second_seller_col = f'{country} second seller'
        third_price_col = f'{country} third price'
        third_seller_col = f'{country} third seller'
        url_col = f'{country} url'

        # Create the plot
        fig = go.FigureWidget()

        def generate_hover_template(name, url):
            template = '<b>' + name + '</b><br>' + \
                    '<a href="' + url + '" target="_blank">Amazon web page</a>' + '<extra></extra>'
            return template

        # Add a scatter trace for the third prices
        fig.add_trace(
            go.Scatter(
                x=df['prod'],
                y=df[third_price_col],
                name=f'{country} third price',
                mode='markers',
                marker=dict(
                    color='green'
                ),
                text=df[third_seller_col] + ': €' + df[third_price_col].astype(str),
                customdata=df[url_col],
                hovertemplate=generate_hover_template('%{text}', '%{customdata}')
            )
        )

        # Add a scatter trace for the second prices
        fig.add_trace(
            go.Scatter(
                x=df['prod'],
                y=df[second_price_col],
                name=f'{country} second price',
                mode='markers',
                marker=dict(
                    color='yellow'
                ),
                text=df[second_seller_col] + ': €' + df[second_price_col].astype(str),
                customdata=df[url_col],
                hovertemplate=generate_hover_template('%{text}', '%{customdata}')
            )
        )

        # Add a scatter trace for the best prices
        fig.add_trace(
            go.Scatter(
                x=df['prod'],
                y=df[best_price_col],
                name=f'{country} best price',
                mode='markers',
                marker=dict(
                    color='red'
                ),
                text=df[best_seller_col] + ': €' + df[best_price_col].astype(str),
                customdata=df[url_col],
                hovertemplate=generate_hover_template('%{text}', '%{customdata}')
            )
        )

        # Add a scatter trace for the self prices
        fig.add_trace(
            go.Scatter(
                x=df['prod'],
                y=df[self_price_col],
                name=f'{country} self price',
                mode='markers',
                marker=dict(
                    color='white'
                ),
                text='Self: €' + df[self_price_col].astype(str),
                customdata=df[url_col],
                hovertemplate=generate_hover_template('%{text}', '%{customdata}')
            )
        )

        # Update the layout
        fig.update_layout(
            title=f'Comparison of Self Prices and Best Prices in {country}',
            xaxis_title='Product',
            yaxis_title='Price (€)',
            legend_title='Price Type',
            hovermode='closest'
        )

        st.plotly_chart(fig, use_container_width=True)


def show_statistics_pie(df):
    df = excel.clean_df_for_statistics(df)
    
    # Select only the relevant columns
    df = df[['prod', 'Spain self price', 'Spain best price', 'Italy self price', 'Italy best price', 'France self price', 'France best price', 'Germany self price', 'Germany best price', 'Netherlands self price', 'Netherlands best price']]

    # Create a new column to calculate the differences between best price and self price for each marketplace
    df['Spain diff'] = df['Spain best price'] - df['Spain self price']
    df['Italy diff'] = df['Italy best price'] - df['Italy self price']
    df['France diff'] = df['France best price'] - df['France self price']
    df['Germany diff'] = df['Germany best price'] - df['Germany self price']
    df['Netherlands diff'] = df['Netherlands best price'] - df['Netherlands self price']

    # Differences greater than 200 set to 0
    df['Spain diff'] = df['Spain diff'].apply(lambda x: 0 if x > 200 else x)
    df['Italy diff'] = df['Italy diff'].apply(lambda x: 0 if x > 200 else x)
    df['France diff'] = df['France diff'].apply(lambda x: 0 if x > 200 else x)
    df['Germany diff'] = df['Germany diff'].apply(lambda x: 0 if x > 200 else x)
    df['Netherlands diff'] = df['Netherlands diff'].apply(lambda x: 0 if x > 200 else x)

    # Create a new dataframe to hold the sum of the differences for each marketplace
    diff_df = pd.DataFrame(columns=['marketplace', 'diff_sum'])
    diff_df['marketplace'] = ['Spain', 'Italy', 'France', 'Germany', 'Netherlands']
    diff_df.set_index('marketplace', inplace=True)

    # Calculate the sum of differences for each marketplace
    for column in df.columns:
        if 'diff' in column:
            marketplace = column.split()[0]
            diff_df.loc[marketplace, 'diff_sum'] = df[column].clip(lower=0).sum()

    # Create the pie chart
    fig = go.Figure(data=[go.Pie(labels=diff_df.index, values=diff_df['diff_sum'])])
    fig.update_layout(title='Sum of Differences between Best Price and Self Price')

    st.plotly_chart(fig, use_container_width=True)


def show_statistics_pie_per_sku(df):
    df = excel.clean_df_for_statistics(df)
    
    # Select only the relevant columns
    df = df[['prod', 'Spain self price', 'Spain best price', 'Italy self price', 'Italy best price', 'France self price', 'France best price', 'Germany self price', 'Germany best price', 'Netherlands self price', 'Netherlands best price']]

    # Create a new column to calculate the differences between best price and self price for each marketplace
    df['Spain diff'] = df['Spain best price'] - df['Spain self price']
    df['Italy diff'] = df['Italy best price'] - df['Italy self price']
    df['France diff'] = df['France best price'] - df['France self price']
    df['Germany diff'] = df['Germany best price'] - df['Germany self price']
    df['Netherlands diff'] = df['Netherlands best price'] - df['Netherlands self price']

    # Differences greater than 200 set to 0
    df['Spain diff'] = df['Spain diff'].apply(lambda x: 0 if x > 200 else x)
    df['Italy diff'] = df['Italy diff'].apply(lambda x: 0 if x > 200 else x)
    df['France diff'] = df['France diff'].apply(lambda x: 0 if x > 200 else x)
    df['Germany diff'] = df['Germany diff'].apply(lambda x: 0 if x > 200 else x)
    df['Netherlands diff'] = df['Netherlands diff'].apply(lambda x: 0 if x > 200 else x)

    # Create a pie chart per marketplace
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    col5 = st.columns([1, 2, 1])[1]

    for col, marketplace in zip((col1, col2, col3, col4, col5), ['Spain', 'Italy', 'France', 'Germany', 'Netherlands']):
        # Create a new dataframe to hold the sum of the differences for each marketplace
        diff_df = df[['prod', f'{marketplace} diff']]
        diff_df.set_index('prod', inplace=True)

        # Clip the differences to 0
        diff_df[f'{marketplace} diff'] = diff_df[f'{marketplace} diff'].clip(lower=0)

        # Filter out products with no difference
        diff_df = diff_df[diff_df[f'{marketplace} diff'] > 0]

        # Create the pie chart
        fig = go.Figure(data=[go.Pie(labels=diff_df.index, values=diff_df[f'{marketplace} diff'])])
        fig.update_layout(title=f'Sum of Differences between Best Price and Self Price in {marketplace}')

        col.plotly_chart(fig, use_container_width=True)
