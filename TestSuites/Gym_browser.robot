*** Settings ***
# Variables  variables/variables.py
Library  utils/function.py
Library  ButlerRobot.keywords.data_generator
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  strict=${FALSE}  AS  Browser
Library    Collections

*** Variables ***
${IS_REMOTE}  False

@{MESES}  enero  febrero  marzo  abril  mayo  junio  julio  agosto  septiembre  octubre  noviembre  diciembre
${RELATIVE_DAY}  tomorrow
${DAY}  4
${MONTH}  3
${HOUR}  19:30
${SPORT}  Sala multitrabajo
${GYM}  Cruces

${USER}  davidestu77@gmail.com
${PASS}  A.Mena69
${NAME}  David
${SURNAME}  Correas


*** Test Cases ***
New Gym
    Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login
    Record Selector
    Click  .navigation-section-widget-collection-item:nth-child(1) > .navigation-section-widget-collection-item-title
    Log  Hola

Delete - Class
    Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login
    Login
    Go to "Pablo David Correas" account
    Go to "Compras"
    FOR  ${i}  IN RANGE  3
        Start at random Scroll
        View "22/03/2023" details
        Back
        Start at random Scroll
        View "20/03/2023" details
        Back
        Start at random Scroll
        View "16/03/2023" details
        Back
        Start at random Scroll
        View 14/03/2023 and Carrito 8048619885 details
        Back
        Start at random Scroll
        View 14/03/2023 and Carrito 8048602861 details
        Back
        Start at random Scroll
        View 13/03/2023 and Carrito 8048560433 details
        Back
        Start at random Scroll
        View 13/03/2023 and Carrito 8048547511 details
        Back
        Start at random Scroll
        View 12/03/2023 details
        Back
        Start at random Scroll
        View 11/03/2023 and Carrito 8048470551 details
        Back
        Start at random Scroll
        View 10/03/2023 and Carrito 8048452342 details
        Back
    END
    View 10/03/2023 and Carrito 8048452342 details
    Click on "Anular"
    Click on "Si" in popup


*** Keywords ***
Start at random Scroll
    [Tags]  task  no_record
    [Arguments]  ${max}=100
    ${pixels}  Evaluate  random.randint(0, ${max})  modules=random
    Scroll by  vertical=-100%
    Scroll Down  ${pixels}

Login
    [Tags]  task  no_record
    AI.Go to "Acceso identificado"
    AI.Select "Continue con correo electrónico y contraseña"
    AI.Login with user "${USER}" and password "${PASS}"
    

Go to "${USER}" account
    [Tags]  task
    Click  //*[@id="liPersonas"]/a  position_x=121.53125  position_y=54
    Click  //*[@id="ulPersonas"]/li/a  position_x=67.015625  position_y=16

Go to "Compras"
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uSecciones_divSections"]/section[3]/div[2]/div/div/div[2]/article[2]  position_x=138.5  position_y=70

View "22/03/2023" details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[1]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[1]/td[1]/ul/li/button  position_x=11  position_y=11

View "20/03/2023" details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[2]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[2]/td[1]/ul/li/button  position_x=11  position_y=11

View "16/03/2023" details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[3]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[3]/td[1]/ul/li/button  position_x=11  position_y=11

View 14/03/2023 and Carrito 8048619885 details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[4]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[4]/td[1]/ul/li/button  position_x=11  position_y=11

View 14/03/2023 and Carrito 8048602861 details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[5]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[5]/td[1]/ul/li/button  position_x=11  position_y=11

View 13/03/2023 and Carrito 8048560433 details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[6]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[6]/td[1]/ul/li/button  position_x=11  position_y=11

View 13/03/2023 and Carrito 8048547511 details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[7]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[7]/td[1]/ul/li/button  position_x=11  position_y=11

View 12/03/2023 details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[8]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[8]/td[1]/ul/li/button  position_x=11  position_y=11

View 11/03/2023 and Carrito 8048470551 details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[9]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[9]/td[1]/ul/li/button  position_x=11  position_y=11

View 10/03/2023 and Carrito 8048452342 details
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[10]/td[2]  position_x=15  position_y=32
    Click  //*[@id="ContentFixedSection_uCarritos_tblGrid"]/tbody/tr[10]/td[1]/ul/li/button  position_x=11  position_y=11


Back
    [Tags]  task  no_record
    Click  //*[@id="ContentFixedSection_uCarritos_uCarritosFicha_divCart"]/div[1]/div[1]/span  position_x=13  position_y=13


Click on "Anular"
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_uCarritosFicha_btnRefundCart"]  position_x=26.46875  position_y=29.9375
    
Click on "Si" in popup
    [Tags]  task
    Click  //*[@id="ContentFixedSection_uCarritos_uCarritosFicha_uWarningModal_btnYes"]  position_x=14.03125  position_y=24.296875
