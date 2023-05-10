*** Settings ***
Library  OTP
Library    Collections
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  console=${False}  output_path=${OUTPUT_DIR}/crawl_amazon_data  WITH NAME  Browser
Library   ButlerRobot.AILanguageLibrary
Library   ../keywords/utils.py
Library   ../keywords/count_excel.py
Resource  ./resources/CrawlAmazon.resource
Variables  ../variables/credentials.py
Suite Setup  Browser.Add Task Library    CrawlAmazon


*** Variables ***
${OUTPUT_DIR}  /workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/CicloZero/data
${URL_AMAZON}  https://sellercentral.amazon.es/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fsellercentral.amazon.es%2Fhome&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=sc_es_amazon_v2&openid.mode=checkid_setup&language=es_ES&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&pageId=sc_es_amazon_v2&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&ssoResponse=eyJ6aXAiOiJERUYiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiQTI1NktXIn0.u8j_3kfAPRO9oea7TATYwCAdOKehZfRhKktBjgJlntMm6nulCn1qEg.B2O2NQ1GNLUmz9NH.cjghNVWhLvzDMxogLdKHIvb87caY5OMLYZheHT6HHz3k088JtfZnEGHu8fk8e_IFDIpVNxqqHzR8JcyQjX1b5SwxquNbOpmt5cnMPZ5pgqpf0pbcHi8-TrhHtZ2XJjSDaSwqYkPTP6oEJKgc6fDOGcJsXOPPXTJc6ZT71ZHEX1R8j94ipHBM6qer4vruZRBYMAdZVaFP.K5bI5NZ7lJG0ObtQQymgtA


*** Test Cases ***
CiclAI Amazon Pendientes
    Comment  Obtener inventario de Odoo
    New Browser    chromium    headless=false  downloadsPath=${OUTPUT_DIR}${/}downloads
    New Context    acceptDownloads=${TRUE}
    Wait New Page   ${URL_AMAZON}  wait=${1}

    Login with user ${amazon_user} and pass ${amazon_pass}
    AI Strict.Click on Indicar contraseña de un solo uso desde la app de verificación
    AI Strict.Click on "Enviar contraseña de un solo uso"
    
    ${otp_key}=    Get OTP    ${otp_amazon}
    Should Match Regexp       ${otp_key}        \\d{6}
    Type number "${otp_key}" in field Indicar contraseña de un solo uso
    Check "No vuelvas a pedir un codigo en este navegador"
    Click on "Iniciar sesion"
    Scroll in Select Account until "Spain" is visible and click
    Click on "Select Account"

    Click on menu icon at top left
    Click on "Orders" menu at the left
    Click "Manage orders" submenu

    Click on "Pending" tab
    Change Results per page to 100
    ${num_pending}  How many orders are Pending?

    Comment  Count number of times that appears each SKU
    &{orders_sku}  Create Dictionary
    ${NEXT_OBSERVATION}  Set Variable
    Set Global Variable    ${NEXT_OBSERVATION}
    ${num_pending}  Evaluate  ${num_pending} +1
    FOR  ${i}  IN RANGE  1  ${num_pending}
        ${ord_num}  Get Ordinal    number=${i}
        ${sku}  Which is the SKU of the ${ord_num} order?
        ${qty_sku}  Which quantity has the order with sku ${sku}?

        ${NEXT_OBSERVATION}  Set Variable  The order is under the order with SKU ${sku}
        ${sku_count}  Get From Dictionary  ${orders_sku}  ${sku}  0
        ${new_sku_count}  Evaluate  ${sku_count} + ${qty_sku}
        Set To Dictionary    ${orders_sku}    ${sku}    ${new_sku_count}
    END

    # ${excel_path}  Set Variable  ${/}workspaces${/}ai-butlerhat${/}data-butlerhat${/}robotframework-butlerhat${/}TestSuites${/}CicloZero${/}downloads${/}result.xlsx
    # ${output_path}  Set Variable  ${/}workspaces${/}ai-butlerhat${/}data-butlerhat${/}robotframework-butlerhat${/}TestSuites${/}CicloZero${/}downloads${/}full.xlsx
    # Append Dict To Main Excel    ${orders_sku}    ${excel_path}    ${output_path}

SelectAMerchant
    Open Browser  ${URL_AMAZON}  pause_on_failure=${FALSE}
    Login with user ${amazon_user} and pass ${amazon_pass}
    ${otp_key}=    Get OTP    ${otp_amazon}
    Should Match Regexp       ${otp_key}        \\d{6}
    Type number "${otp_key}" in field Indicar contraseña de un solo uso
    Check "No vuelvas a pedir un codigo en este navegador"
    Click on "Iniciar sesion"

    FOR  ${country}  IN  Spain  Germany  France  Italy  United Kingdom  United States  Japan  Canada  Mexico  Belgium  Australia  Netherlands  Sweden  Poland
        Scroll in Select Account until "${country}" is visible and click
        No Record Scroll Up
    END

Modelate Table
    Open Browser  ${URL_AMAZON}  pause_on_failure=${FALSE}
    Login with user ${amazon_user} and pass ${amazon_pass}
    ${otp_key}=    Get OTP    ${otp_amazon}
    Should Match Regexp       ${otp_key}        \\d{6}
    Type number "${otp_key}" in field Indicar contraseña de un solo uso
    Check "No vuelvas a pedir un codigo en este navegador"
    Click on "Iniciar sesion"
    Scroll in Select Account until "Spain" is visible and click
    Click on "Select Account"

    Click on menu icon at top left
    Click on "Orders" menu at the left
    Click on "Order Reports" submenu

    Click on "Unshipped Orders" in the menu
    Click on "Request" yellow button
    Click at "Refresh" button at the top right of the table

    FOR  ${ord_num}  IN  first  second  third  fourth  fifth  sixth  seventh  eighth  ninth  tenth
        FOR  ${column}  IN  Report Type  Batch ID  Date Range Covered  Date and Time Requested  Date and Time Completed  Report Status  Download
            ${bbox}  Get element bouding box at ${ord_num} row and "${column}" column at Download Report table
            ${txt}  Get Text From Bbox    selector_bbox=${bbox}
            Log To Console    ${txt}
        END
    END


CiclAI Amazon Unshipped
    Comment  Obtener inventario de Odoo
    New Browser    chromium    headless=false  downloadsPath=${OUTPUT_DIR}${/}downloads
    New Context    acceptDownloads=${TRUE}
    Wait New Page   ${URL_AMAZON}  wait=${1}

    Login with user ${amazon_user} and pass ${amazon_pass}
    AI Strict.Click on Indicar contraseña de un solo uso desde la app de verificación
    AI Strict.Click on "Enviar contraseña de un solo uso"
    
    ${otp_key}=    Get OTP    ${otp_amazon}
    Should Match Regexp       ${otp_key}        \\d{6}
    Type number "${otp_key}" in field Indicar contraseña de un solo uso
    Check "No vuelvas a pedir un codigo en este navegador"
    Click on "Iniciar sesion"
    Scroll in Select Account until "Spain" is visible and click
    Click on "Select Account"

    Click on menu icon at top left
    Click on "Orders" menu at the left
    Click on "Order Reports" submenu

    Click on "Unshipped Orders" in the menu
    # Click on "Request" yellow button

    Set Browser Timeout    timeout=16m
    ${dl_promise}  Promise To Wait For Download    saveAs=${OUTPUT_DIR}${/}downloads${/}unshipped.xlsx
    ${init_time}  Evaluate  time.time()
    WHILE  ${TRUE}
        Click at "Refresh" button at the top right of the table
        ${bbox}  Get element bouding box at first row and "download" column at Download Report table
        ${txt}  Get Text From Bbox    selector_bbox=${bbox}
        ${contains}  Evaluate  "download" in "${txt.lower()}"
        # Check if download is in text
        IF  ${contains}
            ${dl_promise}  Promise To Wait For Download    saveAs=${OUTPUT_DIR}${/}downloads${/}unshipped.tsv
            Click at "download" button at first row at Download Report table
            BREAK
        END
        
        ${contains_no_new}  Evaluate  "no new" in "${txt.lower()}"
        IF  ${contains_no_new}
            FOR  ${ord_num}  IN  first  second  third  fourth  fifth  sixth  seventh  eighth  ninth  tenth
                ${bbox}  Get element bouding box at ${ord_num} row and "download" column at Download Report table
                ${txt}  Get Text From Bbox    selector_bbox=${bbox}
                ${contains}  Evaluate  "download" in "${txt.lower()}"
                # Check if no new is in text
                IF  ${contains}
                    ${dl_promise}  Promise To Wait For Download    saveAs=${OUTPUT_DIR}${/}downloads${/}unshipped.tsv
                    Click at "download" button at ${ord_num} row at Download Report table
                    BREAK
                END
            END
            BREAK
        END

        Sleep  30

        # Check timeout
        ${curr_time}  Evaluate  time.time()
        ${diff_time}  Evaluate  ${curr_time} - ${init_time}
        IF  ${diff_time} > 960  # 16 minutes
            FAIL  Timeout
        END
    END

    Comment  Descargar tsv. Esperar a que se descargue
    ${file_obj}  Wait For  ${dl_promise}
