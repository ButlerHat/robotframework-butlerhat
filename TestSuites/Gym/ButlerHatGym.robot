*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  AS  Browser


*** Variables ***
${day}  3
${hour}  21:00


*** Test Cases ***
Book Gym
    Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login
    AI.Go to "Acceso identificado"
    AI.Click on "Continue con correo electrónico"
    AI.Login with user "davidestu77@gmail.com" and password "A.Mena69"
    AI.Access "Sala multitrabajo"
    AI.Search and select "Cruces"
    AI.Select day ${day}
    AI.Click on hour ${hour}
    AI.Click on "Confirma la compra"
    Close Browser



































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
    
    
    

    