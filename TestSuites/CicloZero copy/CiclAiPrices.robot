*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  presentation_mode=${True}  console=${False}  record=${True}  output_path=${OUTPUT_DIR}/crawl_amazon_data  WITH NAME  Browser
Library   OTP
Library   Collections
Library   ./robotframework/keywords/count_excel.py
Resource   ./robotframework/modeling/resources/CrawlAmazon.resource
Variables  ./robotframework/variables/credentials.py
Suite Setup  Browser.Add Task Library    CrawlAmazon


*** Variables ***
${OUTPUT_DIR}  /workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/CicloZero/robotframework/modeling
${URL_AMAZON}  https://sellercentral.amazon.es/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fsellercentral.amazon.es%2Fhome&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=sc_es_amazon_v2&openid.mode=checkid_setup&language=es_ES&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&pageId=sc_es_amazon_v2&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&ssoResponse=eyJ6aXAiOiJERUYiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiQTI1NktXIn0.u8j_3kfAPRO9oea7TATYwCAdOKehZfRhKktBjgJlntMm6nulCn1qEg.B2O2NQ1GNLUmz9NH.cjghNVWhLvzDMxogLdKHIvb87caY5OMLYZheHT6HHz3k088JtfZnEGHu8fk8e_IFDIpVNxqqHzR8JcyQjX1b5SwxquNbOpmt5cnMPZ5pgqpf0pbcHi8-TrhHtZ2XJjSDaSwqYkPTP6oEJKgc6fDOGcJsXOPPXTJc6ZT71ZHEX1R8j94ipHBM6qer4vruZRBYMAdZVaFP.K5bI5NZ7lJG0ObtQQymgtA
${DEFAULT_AI_MODE}  Flexible
${ROBOT_BROWSER_WAIT}  1

${RETURN_FILE}  ${OUTPUT_DIR}${/}return_msg.txt

${SKU}  iP13-MD-128-B+ -R
${STOCK_EXCEL_PATH}  ${OUTPUT_DIR}${/}downloads${/}stock.quant.full.result.xlsx
${SKU_EXCEL_PATH}  ${OUTPUT_DIR}${/}downloads${/}stock.${SKU}.xlsx


*** Test Cases ***

ComparePrices
    Comment  Obtener inventario de Odoo
    New Browser    chromium    headless=false  downloadsPath=${OUTPUT_DIR}${/}downloads
    New Context    acceptDownloads=${TRUE}
    New Page   ${URL_AMAZON}

    Login with user ${amazon_user} and pass ${amazon_pass}
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
    Go to "Inventory" at the left
    Go to "Manage All Inventory" submenu
    
    Create Sheet For Sku  ${SKU}  ${SKU_EXCEL_PATH} 
    Search for SKU ${sku}
    TRY
        Click at marketplaces button for sku ${sku}
    EXCEPT
        Add Label By Sku  ${SKU_EXCEL_PATH}    ${sku}  Spain  Not Add In Amazon  Not Add In Amazon  Not Add In Amazon  Not Add In Amazon
        Create File    path=${RETURN_FILE}    content=Warning: SKU ${sku} not in Amazon inventory
        Fail  Skipping: SKU ${sku} Not in Amazon inventory
    END
    
    @{marketplaces}  In which marketplaces is it being sold?
    &{attribtue}  Get Attributes From Sku    sku=${sku}
    ${status}  Get From Dictionary    ${attribtue}  estado
    ${filter_dict}  Create Dictionary  NUEVO=Renewed  MEDIO=Good  BAJO=Acceptable
    ${filter_val}  Get From Dictionary  ${filter_dict}  ${status}
    
    Comment  Get markets for sku
    &{markets_prices}  Create Dictionary 
    Create File    path=${RETURN_FILE}    content=Success: SKU ${sku}.


    FOR  ${market}  IN   @{marketplaces}
        ${status}  Get status for ${market}
        ${self_price}  Get price for ${market}

        ${url}  Go to page of the ${market} row
        Run Keyword And Ignore Error    Accept cookies
        
        TRY
            See Renewed at the right above sell on Amazon
        EXCEPT
            Add Label By Sku  ${SKU_EXCEL_PATH}    ${sku}  ${market}  ${status}  Not Found  ${self_price}  ${url}
            Create File    path=${RETURN_FILE}    content= Warning ${sku} captcha: Check ${market} manually.
            Close Page
            CONTINUE
        END
        
        TRY
            Wait Until Keyword Succeeds    30s    5s    Filter with condition ${filter_val}
        EXCEPT
            Add Label By Sku  ${SKU_EXCEL_PATH}    ${sku}  ${market}  ${status}  Not Found  ${self_price}  ${url}
            Append To File    path=${RETURN_FILE}    content= Check ${market} manually.
            Close Page
            CONTINUE
        END
        
        &{market_prices}  Get three first lowest price
        Add Prices By Sku And Market    ${SKU_EXCEL_PATH}    ${sku}    ${market}    ${status}    ${self_price}    ${market_prices}    ${url}

        Close Page
    END


*** Keywords ***
Filter with condition ${filter_val}
    Open filter at the right
    Check ${filter_val} condition checkbox
    Close filter if not open
