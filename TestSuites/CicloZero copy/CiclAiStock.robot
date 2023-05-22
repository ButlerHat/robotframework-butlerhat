*** Settings ***
Library    ButlerRobot.AIBrowserLibrary  record=${False}  presentation_mode=${True}  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}${/}data  WITH NAME  Browser 
Library    ./robotframework/keywords/count_excel.py
Library    OTP
Library    Collections
Library    OperatingSystem
Resource   ./robotframework/modeling/resources/CrawlOdoo.resource
Resource   ./robotframework/modeling/resources/CrawlAmazon.resource
Variables  ./robotframework/variables/credentials.py
Suite Setup  Browser.Add Task Library    CrawlAmazon  CrawlOdoo


*** Variables ***
${OUTPUT_DIR}  /workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/CicloZero
${DEFAULT_AI_MODE}  Flexible
${BROWSER_WAIT}  2

${URL_AMAZON}  https://sellercentral.amazon.es/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fsellercentral.amazon.es%2Fhome&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=sc_es_amazon_v2&openid.mode=checkid_setup&language=es_ES&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&pageId=sc_es_amazon_v2&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&ssoResponse=eyJ6aXAiOiJERUYiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiQTI1NktXIn0.u8j_3kfAPRO9oea7TATYwCAdOKehZfRhKktBjgJlntMm6nulCn1qEg.B2O2NQ1GNLUmz9NH.cjghNVWhLvzDMxogLdKHIvb87caY5OMLYZheHT6HHz3k088JtfZnEGHu8fk8e_IFDIpVNxqqHzR8JcyQjX1b5SwxquNbOpmt5cnMPZ5pgqpf0pbcHi8-TrhHtZ2XJjSDaSwqYkPTP6oEJKgc6fDOGcJsXOPPXTJc6ZT71ZHEX1R8j94ipHBM6qer4vruZRBYMAdZVaFP.K5bI5NZ7lJG0ObtQQymgtA

${RESULT_EXCEL_PATH_ODOO}  ${OUTPUT_DIR}${/}downloads${/}stock.quant.result.xlsx
${RESULT_EXCEL_PATH_AMZ_UNSHIPPED}  ${OUTPUT_DIR}${/}downloads${/}stock.quant.amz.unshipped.result.xlsx
${RESULT_EXCEL_PATH}  ${OUTPUT_DIR}${/}downloads${/}stock.quant.full.result.xlsx


*** Test Cases ***
CiclAI Stock
    [Documentation]  Creacion de excel para hacer el control de stock. Se usan las páginas de Odoo y Amazon.
    # ================== Odoo ==================
    ${return_excel}  Get Stocks Odoo
    Create Excel    ${return_excel}    ${RESULT_EXCEL_PATH_ODOO}
    Log  Excel creado satisfactoriamente en ${RESULT_EXCEL_PATH_ODOO}  console=${TRUE}
    
    # ================== Amazon Unshipped ==================
    ${amazon_tsv_obj}  Get Unshipped Amazon
    IF  "${amazon_tsv_obj}" == "False"
        Log To Console    message=No hay pedidos pendientes de envío en Amazon
        Copy File    ${RESULT_EXCEL_PATH_ODOO}    ${RESULT_EXCEL_PATH_AMZ_UNSHIPPED}
    ELSE
        Append Tsv To Main Excel    ${amazon_tsv_obj.saveAs}    ${RESULT_EXCEL_PATH_ODOO}    ${RESULT_EXCEL_PATH_AMZ_UNSHIPPED}
    END
    Log  Excel creado satisfactoriamente en ${RESULT_EXCEL_PATH_AMZ_UNSHIPPED}  console=${TRUE}

    # ================== Amazon Unshipped ==================
    ${amazon_dict_obj}  Get Pending Amazon
    Append Dict To Main Excel    ${amazon_dict_obj}    ${RESULT_EXCEL_PATH_AMZ_UNSHIPPED}    ${RESULT_EXCEL_PATH}
    Log  Excel creado satisfactoriamente en ${RESULT_EXCEL_PATH}  console=${TRUE}
    

*** Keywords ***
Get Stocks Odoo
    Comment  Obtener inventario de Odoo
    New Browser    chromium    headless=false  downloadsPath=${OUTPUT_DIR}${/}downloads
    New Context    acceptDownloads=${TRUE}
    Wait New Page       https://backoffice.ciclozero.com/  wait=${3}
    
    Comment  Acceder a informe de inventario
    Click on "Identificarse"
    CrawlOdoo.Login with user ${odoo_user} and pass ${odoo_pass}
    Go to menu icon at the top left
    Go to inventario
    Click on "informes" in the top menu
    Click on "Informe de inventario" in informes submenu
    
    Comment  Marcar todos los registros de la tabla
    Select view pivot icon at the top right of the table
    Click on "Total" in the first row
    Click on left right arrow icon under actualizar la cantidad
    Click on cell in the Alm/Stock venta row and column Total
    Click on select all box in the table

    Comment  Descargar excel
    ${dl_promise}  Promise To Wait For Download    saveAs=${OUTPUT_DIR}${/}downloads${/}stock.quant.xlsx
    Click to download icon above the table
    ${odoo_excel_obj}  Wait For  ${dl_promise}

    RETURN  ${odoo_excel_obj.saveAs}


Get Unshipped Amazon
    New Browser    chromium    headless=false  downloadsPath=${OUTPUT_DIR}${/}downloads
    New Context    acceptDownloads=${TRUE}
    Wait New Page   ${URL_AMAZON}  wait=${1}

    CrawlAmazon.Login with user ${amazon_user} and pass ${amazon_pass}
    AI.Click on Indicar contraseña de un solo uso desde la app de verificación
    AI.Click on "Enviar contraseña de un solo uso"

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

    ${dl_promise}  Promise To Wait For Download    saveAs=${OUTPUT_DIR}${/}downloads${/}unshipped.xlsx
    ${init_time}  Evaluate  time.time()
    WHILE  ${TRUE}
        Click at "Refresh" button at the top right of the table
        Sleep  3
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
        IF  ${contains_no_new}  RETURN  False

        Sleep  30
        # Check timeout
        ${curr_time}  Evaluate  time.time()
        ${diff_time}  Evaluate  ${curr_time} - ${init_time}
        IF  ${diff_time} > 960  # 16 minutes
            FAIL  Timeout
        END
    END

    Comment  Descargar tsv. Esperar a que se descargue
    ${amazon_tsv_obj}  Wait For  ${dl_promise}

    RETURN  ${amazon_tsv_obj}


Get Pending Amazon
    Comment  Obtener inventario de Odoo
    New Browser    chromium    headless=false  downloadsPath=${OUTPUT_DIR}${/}downloads
    New Context    acceptDownloads=${TRUE}
    Wait New Page   ${URL_AMAZON}  wait=${1}

    CrawlAmazon.Login with user ${amazon_user} and pass ${amazon_pass}
    AI.Click on Indicar contraseña de un solo uso desde la app de verificación
    AI.Click on "Enviar contraseña de un solo uso"
    
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
    
    Set Browser Wait Time  0
    ${num_pending}  How many orders are Pending?

    Comment  Count number of times that appears each SKU
    &{orders_sku}  Create Dictionary
    ${NEXT_OBSERVATION}  Set Variable
    Set Global Variable    ${NEXT_OBSERVATION}
    ${num_pending}  Evaluate  ${num_pending} +1

    # This Javascript is for removing warning in the table
    Remove Warnings In Table

    FOR  ${i}  IN RANGE  1  ${num_pending}
        ${ord_num}  Get Ordinal    number=${i}
        ${2nd_col_num}  Which is the number of the second column of the ${ord_num} row?
        ${sku}  Which is the SKU of the order ${2nd_col_num}?
        ${qty_sku}  Which quantity has the order ${2nd_col_num}?

        ${NEXT_OBSERVATION}  Set Variable  The order is under the ${2nd_col_num} order
        Set Global Variable    ${NEXT_OBSERVATION}
        ${sku_count}  Get From Dictionary  ${orders_sku}  ${sku}  0
        ${new_sku_count}  Evaluate  ${sku_count} + ${qty_sku}
        Set To Dictionary    ${orders_sku}    ${sku}    ${new_sku_count}
    END

    RETURN  ${orders_sku}
