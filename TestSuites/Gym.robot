*** Settings ***
# Variables  variables/variables.py
Library  utils/function.py
Library  ButlerRobot.keywords.data_generator
Library  ButlerRobot.DataSeleniumLibrary  AS   SeleniumLibrary
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

${USER}  ****
${PASS}  ****
${NAME}  ****
${SURNAME}  ****


*** Test Cases ***
Book day in the gym
    ${day}  ${month}  Calculate day
    Open Chrome
    Access with "Usuario y contraseña"
    Pass Execution    message=No se puede ejecutar el test case
    Select "Continue con correo"
    Login with user "${USER}" and password "${PASS}"
    Access "${SPORT}"
    Search and select "${GYM}"
    Select month "${month}"
    Select day "${day}"
    Click on hour "${HOUR}"
    Start at random Scroll  200
    Confirm booking

Train-Login
    [Tags]  no_exec
    @{USERS}  Get Random Words  10
    @{PASS}  Get Random Words  10
    Open Chrome
    Access with "Usuario y contraseña"
    Select "Continue con correo"
    FOR  ${i}  IN RANGE  10
        Start at random Scroll  200
        Login with user "${USERS[${i}]}" and password "${PASS[${i}]}"
        Clear user and password
    END

Train - Access
    [Tags]  exec
    @{SPORTS}  Create List  BMX  Pista de squash   Pista de tenis  
    ...  Pista de voleibol  Pista de pádel  Pista de bádminton  Oferta de actividades por día y centro
    ...  Tenis de mesa  Pista de patinaje / hockey
    ...  Barcas de recreo  Uso sauna  Oferta de alquileres por actividad y centro
    Open Chrome
    Access with "Usuario y contraseña"
    Select "Continue con correo"
    Login with user "${USER}" and password "${PASS}"
    FOR  ${i}  IN RANGE  3
        FOR  ${sport}  IN  @{SPORTS}
            TRY
                Start at random Scroll
                Access "${sport}"
            EXCEPT
                Log to console  Sport ${sport} not found
            FINALLY
                Go to  https://deportesweb.madrid.es/DeportesWeb/Home
            END
        END
    END

Train-gym
    @{GYMS}  Create List  

    Open Chrome
    Access with "Usuario y contraseña"
    Select "Continue con correo"
    Login with user "${USER}" and password "${PASS}"
    Access "${SPORT}"

    FOR  ${I}  IN RANGE  1  44
        ${text}  Get text  (//*[@id="ContentFixedSection_uAltaEventos_uCentrosSeleccionar_divCentros"]/ul/li//h4)[${I}]
        Append To List    ${GYMS}  ${text}
    END

    FOR  ${gym}  IN  @{GYMS}
        Start at random Scroll  200
        Search and select "${gym}"
        Clear Search
    END

Train - Month
    @{SHUFFLED_MONTHS}  Evaluate  random.sample(${MESES}, 12)  modules=random
    Open Chrome
    Access with "Usuario y contraseña"
    Select "Continue con correo"
    Login with user "${USER}" and password "${PASS}"
    Access "${SPORT}"
    Search and select "${GYM}"
    FOR  ${month}  IN  @{SHUFFLED_MONTHS}
        Start at random Scroll  200
        TRY
            Select month "${month}"
        EXCEPT
            Log to console  Month ${month} not found
        FINALLY
            Reset month
        END
    END

Train - Day
    # Random list
    @{DAYS}  Evaluate  random.sample(range(1, 31), 30)  modules=random
    @{MONTHS}  Create list  abril  mayo  junio
    Open Chrome
    Access with "Usuario y contraseña"
    Select "Continue con correo"
    Login with user "${USER}" and password "${PASS}"
    Access "${SPORT}"
    Search and select "${GYM}"
    FOR  ${month}  IN  @{MONTHS}
        Select month "${month}"
        FOR  ${day}  IN  @{DAYS}
            Start at random Scroll  200
            Select day "${day}"
        END
    END

Train - Hour
    [Documentation]  Only works if 'Book day in the gym' test case has been executed
    @{HOURS}  Create List  07:30  09:00  10:30  12:30  14:00  16:00  17:30  19:30  21:00
    ${day}  ${month}  Calculate day
    Open Chrome
    Access with "Usuario y contraseña"
    Select "Continue con correo"
    Login with user "${USER}" and password "${PASS}"
    Access "${SPORT}"
    Search and select "${GYM}"
    Select month "${MONTH}"
    ${top}  Set Variable  ${false}
    FOR  ${d}  IN  24  27
        Select day "${d}"
        FOR  ${hour}  IN  @{HOURS}
            TRY
                IF  ${top}
                    Execute JavaScript  window.scrollTo(0, 0)
                END
                Start at random Scroll  200
                Click on hour "${hour}"
            FINALLY
                Reset Hour  ${d}
            END
        END
        ${top}  Set Variable  ${True}
    END


*** Keywords ***
Calculate day
    ${dia_rel}  Get Variable Value  ${RELATIVE_DAY}
    IF  '${dia_rel}'=='None'
        RETURN
    ELSE
        Log to console  ${dia_rel}
        ${DATE}  Get Date  ${dia_rel}
        Log to console  ${DATE}
        ${DAY}  Set Variable  ${DATE}[day]
        ${index_month}  Evaluate  ${DATE}[month] -1
        ${MONTH}  Set Variable  ${MESES}[${index_month}]
    END
    RETURN  ${DAY}  ${MONTH}

Open Chrome
    [Tags]  task  no_record
    IF  '${IS_REMOTE}'=='True'
        Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login  chrome  remote_url=http://localhost:4444
    ELSE
        Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login  chrome
    END

Access with "Usuario y contraseña"
    Wait Until Element Is Visible    //*[text()='Usuario y contraseña']/..
    Click Element    //*[text()='Usuario y contraseña']/..
    
Select "Continue con correo"
    Wait Until Element Is Visible    id=acceso_pass
    Click Element    id=acceso_pass

Login with user "${USER_}" and password "${PASS_}"
    Wait Until Element Is Visible    id=correoelectronico
    Input Text  id=correoelectronico  ${USER_}
    Input Password    id=contrasenia    ${PASS_}
    Click Element    (//div[@id='user-pass']//button)[1]

Access "${SPORT_}"
    Wait Until Element Is Visible  //*[text()='${SPORT_}']  30
    Click Element  //*[text()='${SPORT_}']/..
    
Search and select "${GYM_}" 
    Wait Until Element Is Visible    //input[@type='text']
    Input Text  //input[@type='text']  ${GYM_}

    Wait Until Element Is Visible    //a[contains(.,'${GYM_}')]
    Click Element    //a[contains(.,'${GYM_}')]/..

Select month "${month_}"
    ${index_month}  Set Variable  ${MESES.index('${month_}')}

    Comment  Cambiar mes
    Wait Until Element Is Visible    (//div[@class='datepicker']//table)[5]//th[@class='picker-switch']
    Log to console  mes ${month_}
    Log to console  index ${index_month}
    ${target_month}  Get From List  ${MESES}  ${index_month}

    FOR  ${i}  IN RANGE   12
        TRY
            ${current_month}  Get Text    (//div[@class='datepicker']//table)[5]//th[@class='picker-switch']
            Log to console  ${i} ${current_month} ${MESES}[${index_month}]
            Should Contain    ${current_month}    ${MESES}[${index_month}]
            BREAK
        EXCEPT
            Wait Until Element Is Visible    xpath:((//div[@class='datepicker']//table)[5]//th[@class='next'])[1]
            Click Element  xpath:((//div[@class='datepicker']//table)[5]//th[@class='next'])[1]
            Sleep  1
            CONTINUE            
        END
    END

Select day "${day_}"
    # Dia
    Wait Until Element Is Visible  xpath:((//div[@class='datepicker']//table)[5]//td[text()='${day_}'][not(contains(@class,'old'))][not(contains(@class,'new'))])[1]
    Click Element  xpath:((//div[@class='datepicker']//table)[5]//td[text()='${day_}'][not(contains(@class,'old'))][not(contains(@class,'new'))])[1]

Click on hour "${hour_}"
    # Hora
    Wait Until Element Is Visible    //ul[@class='media-list clearfix']//h4[text()='${hour_}']  10
    Click Element    //ul[@class='media-list clearfix']//h4[text()='${hour_}']

Confirm booking
    Wait Until Element Is Visible  //button[@id='ContentFixedSection_uCarritoConfirmar_btnConfirmCart']

    Sleep   1
    Click Element  //button[@id='ContentFixedSection_uCarritoConfirmar_btnConfirmCart']
    Capture Page Screenshot
    Sleep  5

Clear user and password
    [Tags]  no_record
    Clear Element Text    id=correoelectronico
    Clear Element Text    id=contrasenia

Back
    [Tags]  task  no_record
    # Check element is visible
    Go Back
    ${STATUS}  Run Keyword And Return Status  Wait Until Element Is Visible    id=acceso_pass  timeout=2
    IF  '${STATUS}'=='${True}'
        Go Back
    END
    Scroll Element Into View    //header

Clear Search
    [Tags]  task  no_record
    Reload Page

Reset Hour
    [Tags]  task  no_record
    [Arguments]  ${day}
    ${day2}  evaluate  ${day} + 1
    Select day "${day2}"
    Select day "${day}"

Reset month
    [Tags]  task  no_record
    Reload Page
    Search and select "${GYM}"

Start at random Scroll
    [Tags]  task  no_record
    [Arguments]  ${max}=200
    Execute Javascript  window.scrollTo(0, Math.floor(Math.random() * ${max}))
