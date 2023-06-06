*** Settings ***
Library   ButlerRobot.AIBrowserLibrary   strict=${False}  fix_bbox=${TRUE}  presentation_mode=${True}  console=${False}  record=${True}  output_path=${OUTPUT_DIR}/data_gym  WITH NAME  Browser
Variables  variables/credentials.py


*** Variables ***
${day}  3
${hour}  21:00
${DEFAULT_AI_MODE}  Flexible
${ROBOT_GYM_PASS}  butlerhat


*** Test Cases ***
Book Gym
    Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login
    AI Wait 2.Click on Acepto
    Access with "Usuario y contraseña" 
    AI.Click on "Continue con correo electrónico y contraseña"
    AI Wait 2.Login with user "davidestu77@gmail.com" and password "${gym_pass}"
    AI Wait 3.Access "Sala multitrabajo"
    AI.Search and select "Cruces"
    AI wait 1.Select day ${day}
    AI.Click on hour 21:00
    AI.Click on "Confirma la compra"
    Close Browser


Delete Gym
    Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login
    AI.Wait 2.Click on Acepto
    Access with "Usuario y contraseña" 
    AI.Click on "Continue con correo electrónico y contraseña"
    AI Wait 2.Login with user "davidestu77@gmail.com" and password "${gym_pass}"
    AI.Click on "Pablo David Correas Oliver"
    AI.Click on "Mi cuenta" at the top
    AI.Go to "Compras"
    View "26/05/2023" details
    Click on "Anular" red button
    Click on Si at the popup
    Sleep  5
    



*** Keywords ***
Access with "Usuario y contraseña" 
    Click  //*[text()='Usuario y contraseña']

View "${date}" details
    Click  (//tr[.//*[text()='${date}']])[1]
    Click  (//tr[.//*[text()='${date}']])[1]/td[1]/ul/li/button

Click on "Anular" red button
    Click  (//*[text()='Anular'])[1]

Click on Si at the popup
    Click  (//*[text()='Sí'])[1]


































# Delete Gym
#     Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login
#     AI.Go to "Acceso identificado"
#     AI.Click on "Continue con correo electrónico"
#     Ai.Login with user "davidestu77@gmail.com" and password "A.Mena69"
#     AI.Click on "David Correas Oliver"
#     AI.Click on "Mi cuenta"
#     AI.Go to "Compras
#     AI.View "24/03/2023" details
#     AI.Click on "Anular"
#     AI.Click on "Si" at the top
    
    
    

    