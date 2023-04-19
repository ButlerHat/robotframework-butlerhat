*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}/data  WITH NAME  Browser
Variables  ./variables/credentials.py


*** Variables ***
${OUTPUT_DIR}  /workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/CicloZero/data


*** Test Cases ***
Crawl_Odoo
    Open Browser  https://backoffice.ciclozero.com/  pause_on_failure=${FALSE}
    

*** Keywords ***
Click on "Identificarse"
    Record Click

Login with user ${user} and pass ${password}
    Record Click
    Keyboard Input    type    ${user}
    Record Click
    Keyboard Input    type    ${password}
    Record Click

Go to menu icon at the top left
    Record Click

Go to inventario
    Record Click

Click on "informes" in the top menu
    Record Click

Click on "Informe de inventario" in informes submenu
    Record Click

Select view pivot icon at the top right of the table
    Record Click

Click on "Total" in the first row
    Record Click

Click on left right arrow icon under actualizar la cantidad
    Record Click

Click on cell in the Alm/Stock venta row and column Total
    Record Click

Click on select all box in the table
    Record Click

Click to download icon above the table
    Record Click