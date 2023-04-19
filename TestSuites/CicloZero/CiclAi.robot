*** Settings ***
Library    ButlerRobot.AIBrowserLibrary  record=${False}  output_path=${OUTPUT_DIR}/../data  WITH NAME  Browser 
Library    ./robotframework/keywords/count_excel.py
Variables  ./robotframework/variables/credentials.py


*** Variables ***
# ${ROBOT_DIR}  /workspaces/ia-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/CicloZero/robotframework
# ${OUTPUT_DIR}  ${ROBOT_DIR}/output
${DEFAULT_AI_MODE}  Flexible

${RESULT_EXCEL_PATH}  ${OUTPUT_DIR}/stock.quant.xlsx


*** Test Cases ***
CiclAI Stock
    [Documentation]  Creacion de excel para hacer el control de stock. Se usan las páginas de Odoo y Amazon.

    Comment  Obtener inventario de Odoo
    New Browser    chromium    headless=false  downloadsPath=${OUTPUT_DIR}/downloads
    New Context    acceptDownloads=${TRUE}
    Wait New Page       https://backoffice.ciclozero.com/  wait=${3}
    
    Comment  Acceder a informe de inventario
    AI Critical.Click on "Identificarse"
    AI.Login with user ${user} and pass ${pass}
    AI.Go to menu icon at the top left
    AI Critical.Go to inventario
    AI Critical.Click on "informes" in the top menu
    AI Critical.Click on "Informe de inventario" in informes submenu
    
    Comment  Marcar todos los registros de la tabla
    AI.Select view pivot icon at the top right of the table
    AI Critical.Click on "Total" in the first row
    AI.Click on left right arrow icon under actualizar la cantidad
    AI.Click on cell in the Alm/Stock venta row and column Total
    AI.Click on select all box in the table

    Comment  Descargar excel
    ${dl_promise}  Promise To Wait For Download    saveAs=${OUTPUT_DIR}/downloads/stock.quant.xlsx
    AI.Click to download icon above the table
    ${file_obj}  Wait For  ${dl_promise}

    Comment  Contar numero de veces que se repite cada modelo
    Create Excel    ${file_obj.saveAs}    ${RESULT_EXCEL_PATH}
    Log  Excel creado satisfactoriamente en ${RESULT_EXCEL_PATH}  console=${TRUE}
