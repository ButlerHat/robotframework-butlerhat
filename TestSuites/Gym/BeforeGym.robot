*** Settings ***
# Variables  variables/variables.py
Library  utils/function.py
Library  SeleniumLibrary
Library    Collections

*** Variables ***
${IS_REMOTE}  False

@{MESES}  enero  febrero  marzo  abril  mayo  junio  julio  agosto  septiembre  octubre  noviembre  diciembre
${RELATIVE_DAY}  %{RELATIVE_DAY}  # 2 days later
${DIA}  %{DAY}  # 2
${MES}  %{MONTH}  # 9
${HOUR}  %{HOUR}  # 18:30
${GYM}  %{GYM}    # Cruces

${USER}  %{USER_GYM}  # variables.py
${PASS}  %{PASS}
${NAME}  %{NAME}
${SURNAME}  %{SURNAME}


*** Test Cases ***
PillarClase
    Calcular Dia
    Login
    Acceder SalaMultitrabajo
    Coger Clase  ${dia_}
    Confirmar Compra


*** Keywords ***
Calcular Dia
    ${dia_rel}  Get Variable Value  ${RELATIVE_DAY}
    IF  '${dia_rel}'=='None'
        RETURN
    ELSE
        Log to console  ${dia_rel}
        ${FECHA}  Get Date  ${dia_rel}
        Log to console  ${FECHA}
        ${DIA}  Set Variable  ${FECHA}[day]
        Set Global Variable    ${DIA}
        ${MES}  Set Variable  ${FECHA}[month]
        Set Global Variable    ${MES}
    END


Login 
    IF  '${IS_REMOTE}'=='True'
        Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login  chrome  remote_url=http://localhost:4444
    ELSE
        Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login  chrome
    END
    Maximize Browser Window
    Wait Until Element Is Visible    //*[contains(text(),'Usuario y contraseña')]
    Click Element    //*[contains(text(),'Usuario y contraseña')]
    
    Wait Until Element Is Visible    id=acceso_pass
    Click Element    id=acceso_pass

    Wait Until Element Is Visible    id=correoelectronico
    Input Text  id=correoelectronico  ${USER}
    Input Password    id=contrasenia    ${PASS}
    Click Element    (//div[@id='user-pass']//button)[1]

Acceder SalaMultitrabajo
    Wait Until Element Is Visible  //*[text()='Sala multitrabajo']  30
    Click Element  //*[text()='Sala multitrabajo']  
    
    Wait Until Element Is Visible    //input[@type='text']
    Input Text  //input[@type='text']  ${GYM}

    Wait Until Element Is Visible    //a[contains(.,'${GYM}')]
    Click Element    //a[contains(.,'${GYM}')]

Coger Clase
    [Arguments]  ${dia_}
    Comment  Cambiar mes
    Wait Until Element Is Visible    (//div[@class='datepicker']//table)[1]//th[@class='picker-switch']
    ${index_month}  Evaluate  ${MES} - 1
    Log to console  mes ${mes}
    Log to console  index ${index_month}
    ${target_month}  Get From List  ${MESES}  ${index_month}

    FOR  ${i}  IN RANGE      12
        TRY
            ${current_month}  Get Text    (//div[@class='datepicker']//table)[1]//th[@class='picker-switch']
            Log to console  ${i} ${current_month} ${MESES}[${index_month}]
            Should Contain    ${current_month}    ${MESES}[${index_month}]
            BREAK
        EXCEPT
            Wait Until Element Is Visible    (//div[@class='datepicker']//th[@class='next'])[1]
            Click Element  (//div[@class='datepicker']//th[@class='next'])[1]
            Sleep  1
            CONTINUE            
        END
    END

    # Dia
    Wait Until Element Is Visible  (//td[text()='${dia_}'][not(contains(@class,'disabled'))])[1]
    Click Element  (//td[text()='${dia_}'][not(contains(@class,'disabled'))])[1]

    # Hora
    Wait Until Element Is Visible    //ul[@class='media-list clearfix']//h4[text()='${HOUR}']  10
    Click Element    //ul[@class='media-list clearfix']//h4[text()='${HOUR}']

Confirmar Compra
    Wait Until Element Is Visible  //button[@id='ContentFixedSection_uCarritoConfirmar_btnConfirmCart']

    Sleep   1
    Click Element  //button[@id='ContentFixedSection_uCarritoConfirmar_btnConfirmCart']
    Capture Page Screenshot