*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}/data  WITH NAME  Browser
Variables  ../variables/credentials.py
Resource   ./resources/CrawlOdoo.resource
Suite Setup  Browser.Add Task Library    CrawlOdoo


*** Variables ***
${OUTPUT_DIR}  /workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/CicloZero/data


*** Test Cases ***
Crawl_Odoo
    Open Browser  https://backoffice.ciclozero.com/  pause_on_failure=${FALSE}
    Click on "Identificarse"
    Login with user ${odoo_user} and pass ${odoo_pass}
    Go to menu icon at the top left
    Go to inventario
    Click on "informes" in the top menu
    Click on "Informe de inventario" in informes submenu
    Select view pivot icon at the top right of the table
    Click on "Total" in the first row
    Click on left right arrow icon under actualizar la cantidad
    Click on cell in the Alm/Stock venta row and column Total
    Click on select all box in the table
    Click to download icon above the table
