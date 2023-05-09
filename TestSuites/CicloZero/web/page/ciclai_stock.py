import asyncio
import os
import datetime
import streamlit as st
import utils.cron as cron
import utils.robot_handler as robot_handler
import utils.vnc as vnc

## Create a function to display a title of "Ciclai Stock", a Run button and a cron field to schedule the task
def ciclai_stock():
    # Title
    main_color = st.secrets.theme.primaryColor
    st.markdown(f'# <span style="color:{main_color}">CiclAI</span> Stock', unsafe_allow_html=True)

    default_command = "robot -d results CiclAiStock.robot"

    # Set cron
    st.markdown("## Program time")
    with st.expander("Schedule the job", expanded=True):
        col1, col2 = st.columns(2)

        col1.markdown(" ### Time")
        cron_str = col1.text_input("Cron", "0 0 * * *"),
        nl_cron = cron.cron_to_natural_language(cron_str[0])
        col1.markdown(f"Next run: {nl_cron}")
        
        # List jobs
        col2.markdown(" ### Jobs list")

        col2.code("\n".join(cron.get_cron_jobs()))

        # Run button
        if st.button("Schedule", type="secondary"):
            success = cron.insert_cron_job(cron_str[0], default_command)
            if success:
                col1.success("Job scheduled successfully")
            else:
                col1.warning("Job already scheduled")

        if st.button("Delete", type="primary"):
            if cron.delete_cron_job(cron_str[0], default_command):
                col1.success("Job deleted successfully")
            else:
                col1.warning("Job not found")

    # Run button
    st.markdown("## Run the job")
    col1, col2 = st.columns([1, 2])

    # VNC
    with col2:
        vnc.vnc("http://localhost:6081/")
        st.caption("VNC password: vscode")
    
    with col1:
        stock_path = st.secrets.paths.stock_excel
        with st.form("Run Robot with args"):
            url = st.text_input("URL_AMAZON", r"https://sellercentral.amazon.es/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fsellercentral.amazon.es%2Fhome&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=sc_es_amazon_v2&openid.mode=checkid_setup&language=es_ES&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&pageId=sc_es_amazon_v2&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&ssoResponse=eyJ6aXAiOiJERUYiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiQTI1NktXIn0.u8j_3kfAPRO9oea7TATYwCAdOKehZfRhKktBjgJlntMm6nulCn1qEg.B2O2NQ1GNLUmz9NH.cjghNVWhLvzDMxogLdKHIvb87caY5OMLYZheHT6HHz3k088JtfZnEGHu8fk8e_IFDIpVNxqqHzR8JcyQjX1b5SwxquNbOpmt5cnMPZ5pgqpf0pbcHi8-TrhHtZ2XJjSDaSwqYkPTP6oEJKgc6fDOGcJsXOPPXTJc6ZT71ZHEX1R8j94ipHBM6qer4vruZRBYMAdZVaFP.K5bI5NZ7lJG0ObtQQymgtA")
            # Add date to excel name
            excel_name = st.text_input("EXEL_NAME", f"CiclAiStock_{datetime.datetime.now().strftime('%H-%M_%d-%m-%Y')}.xlsx")
            if st.form_submit_button("Run", type="primary"):
                
                args = [
                    f"RESULT_EXCEL_PATH:{os.path.join(stock_path, excel_name)}",
                    f"URL_AMAZON:{repr(url)}"
                ]
                asyncio.run(robot_handler.run_robot('stock', args, "CiclAiStock.robot"))

        # Download excel
        if os.path.exists(os.path.join(stock_path, excel_name)):
            st.markdown(f'### Download <span style="color:{excel_name}">CiclAI</span>', unsafe_allow_html=True)
            with open(os.path.join(stock_path, excel_name), 'rb') as f:
                st.download_button(label=excel_name, data=f, file_name=excel_name)
        else:
            st.info(f"Excel not generated")
