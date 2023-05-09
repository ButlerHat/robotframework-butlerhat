*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}/data  WITH NAME  Browser


*** Keywords ***
Click on "Identificarse"
    Click  (//b[text()='Identificarse'])[1]

Login with user ${user} and pass ${password}
    Click  //*[@id='login']
    Keyboard Input    type    ${user}
    Click  //*[@id='password']
    Keyboard Input    type    ${password}
    Click  //button[@type='submit']

Go to menu icon at the top left
    Click  //a[@class='full']

Go to inventario
    AI.Go to inventario

Click on "informes" in the top menu
    Click  //a[@data-menu-xmlid='stock.menu_warehouse_report']

Click on "Informe de inventario" in informes submenu
    Click  //a[@data-menu='120']

Select view pivot icon at the top right of the table
    Click  //button[@data-view-type='pivot']

Click on "Total" in the first row
    Click  //th[@style='padding-left: 5px;']

Click on left right arrow icon under actualizar la cantidad
    Click  //button[@aria-label='Invertir ejes']

Click on cell in the Alm/Stock venta row and column Total
    Click  //table/tbody/tr[contains(., 'Stock venta')]/td

Click on select all box in the table
    Click  //th[@style='width: 48px;']

Click to download icon above the table
    Click  //button[@title='Exportar Todo']