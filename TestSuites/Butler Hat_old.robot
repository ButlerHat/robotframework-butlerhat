*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  AS  Browser
Library  utils/function.py


*** Variables ***
@{MESES}  enero  febrero  marzo  abril  mayo  junio  julio  agosto  septiembre  octubre  noviembre  diciembre
${RELATIVE_DAY}  tomorrow
${DAY}  4
${MONTH}  3
${HOUR}  21:00
${SPORT}  Sala multitrabajo
${GYM}  Cruces

${USER}  davidestu77@gmail.com
${PASS}  A.Mena69
${NAME}  David
${SURNAME}  Correas

*** Test Cases ***

Linkedin
    Open Browser  http://www.linkedin.com  chromium
    AI.Click on accept cookies
    AI.Click on join now
    AI.Type text "****" on email
    AI.Click on Agree & Join

Gym
    ${day}  ${month}  Calculate day
    Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login
    AI.Go to "Acceso identificado"
    AI.Select "Continue con correo electrónico y contraseña"
    AI.Login with user "${USER}" and password "${PASS}"
    AI.Access "${SPORT}"
    AI.Search and select "${GYM}"
    # AI.Select month "${month}"
    AI.Select day "${day}"
    AI.Click on hour "${HOUR}"
    AI.Confirm booking

*** Keywords ***
Accept Cookies
    [Tags]  task
    AI.Click on accept cookies


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

