*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}/data  WITH NAME  Browser
Library   Dialogs


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

Go to Ventas
    Click  //*[contains(text(),'Ventas')]

Click on "Confirmar"
    Click  (//*[text()='Confirmar'])[2]

Click on Entrega
    Click  (//*[text()='Entrega'])[1]

Click on "Editar" at the top left
    Click  //button[./*[text()='Editar']]

Check if table operaciones detalladas only has one row
    ${num}  Get Element Count  (//table[.//th[contains(., 'de serie')]])[2]//tbody//tr[2]/td
    IF  ${NUM} > 3
        Pause Execution  En la tabla "Operaciones detalladas" solo debe de haber una fila. Hacer pedido de forma manual.
        Fail  En la tabla "Operaciones detalladas" solo debe de haber una fila. Hacer pedido de forma manual.
    END

Click on table operaciones detalladas in the third column
    Click  (//table[.//th[contains(., 'de serie')]])[2]//tbody//tr[1]//td[3]

Click on "Buscar más..." in the dropdown
    Click  //*[text()='Buscar más...']

Input ${imei} in 'Buscar...' input
    Click  //input[@placeholder='Buscar…']
    Keyboard Input    type   ${imei}

Click on the first row of the table
    Click  //div[@class="modal-content"]//table//tbody//tr[1]

Click on "Aceptar Reserva" in the first row
    Click  //td//button[.='Aceptar reserva']

Click on "Validar" purple button
    Click  (//button[.='Validar'])[1]

Click on "Guardar" at the top left
    Click  //button//*[.='Guardar']

Click on "Crear factura"
    Click  (//button//*[text()='Crear Factura'])[1]

Click on "Crear y ver factura" in the popup
    Click  //button//*[text()='Crear y ver factura']

Click on "Publicar" at the top
    Click  //button//*[text()='Publicar']

Click on "Registrar pago" at the top
    Click  //button//*[text()='Registrar pago']

Click on "Validar" on the popup
    Click  //button//*[text()='Validar']

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

