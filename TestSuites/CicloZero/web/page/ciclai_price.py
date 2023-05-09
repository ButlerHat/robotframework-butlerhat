import os
import asyncio
import streamlit as st
import utils.vnc as vnc
import utils.robot_handler as robot_handler
import utils.excel as excel


def ciclai_price():
    # Title
    main_color = st.secrets.theme.primaryColor
    st.markdown(f'# <span style="color:{main_color}">CiclAI</span> Price', unsafe_allow_html=True)

    # Upload file
    st.markdown("## Upload stock excel")
    col1, _ = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader("Choose a excel")
        if uploaded_file is None:
            st.warning("Please upload a file. The robot won't work without it")
            
            # TODO: Remove this
            uploaded_file = "/workspaces/CicloZero/downloads/stock/stock.quant.full.result.xlsx"
        
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
                    asyncio.run(run_robots(uploaded_file, skus[:2]))


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
