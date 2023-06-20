*** Settings ***
Library           ButlerRobot.AIDesktopLibrary  WITH NAME  Desktop


*** Variables ***
${name}    Sofea
${surname}    Blazquez
${email_prefix}  albanos19909

*** Tasks ***
Create Google account
    Desktop.Open Application    firefox  
    Sleep  3
    # AI.Click on Search 
    Keyboard input  text=https://support.google.com/accounts/answer/27441?hl=en
    Press Keys    ENTER
    Sleep    2s
    AI.Click For myself
    Keyboard Input    text=${name}
    Click    coordinates:605,400
    Keyboard Input    ${surname}
    AI.Click on "Next"
    AI.Click on Year
    Keyboard input  1992
    AI.Click on "Gender"
    AI.Click on "Male"
    AI.Click on "Month"
    AI.Click on "May"
    AI.Click on "Day"
    Keyboard input  23
    AI.Click on "Next"
    AI.Click on "Create your own Gmail address"
    Keyboard Input    sofeaeres
    Ai.Click on "Next"
    Keyboard Input    mecagoenlaleche0101
    AI.Click on "Confirm"
    Keyboard Input    mecagoenlaleche0101
    Ai.Click on "Next"


Open google
    Desktop.Open Application    google-chrome
    AI.Type text Crear cuenta in google on Search google or type a URL

    Keyboard Input    Crear cuenta google
    Press Keys    ENTER

pBook gym
    AI.Access Sala multitrabajo

Create Google account
    AI.Click on Iniciar sesión
    AI.Click on "Crear cuenta"  # Entrenar
    AI.Click on "Para mi uso personal"
    Keyboard input  ${name}
    AI.Click on Apellidos field
    Keyboard input  ${surname}
    AI.Click on Siguiente

    AI.Click on dia
    Keyboard input  4
    AI.Click on "Mes"
    AI.Click on "Junio"
    Click   coordinates:755,305
    Keyboard input  1992
    AI.Click on "Género"  # Entrenar
    AI.Click on "Hombre"
    AI.Click on "Siguiente"

    AI.Click on "Crear dirección de Gmail"

    Keyboard input  ${email_prefix}9
    AI.Click on "Siguiente"

    Keyboard input  mecagoenlaleche0101
    AI.Click on "Confirmación"
    Keyboard input  mecagoenlaleche0101
    AI.Click on "Siguiente"


Create Google account
    Desktop.Open Application    google-chrome
    AI.Click on Search google or type a URL
    Keyboard input  https://accounts.google.com/signup/v2/createaccount?flowName=GlifWebSignIn&flowEntry=SignUp
    Press Keys    ENTER
    AI.Click on Nombre field
    Keyboard input  ${name}
    AI.Click on Apellidos field
    Keyboard input  ${surname}
    AI.Click on Siguiente

    AI.Click on dia
    Keyboard input  4
    Click   coordinates:605,305
    AI.Click on Junio
    Click   coordinates:755,305
    Keyboard input  1992
    AI.Click on Género
    AI.Click on "Hombre"
    AI.Click on Siguiente

    AI.Click on "Crear dirección de Gmail"
    Keyboard input  ${email_prefix}
    AI.Click on Siguiente

    Keyboard input  mecagoenlaleche0101
    AI.Click on "Confirmación"
    Keyboard input  mecagoenlaleche0101
    AI.Click on Siguiente

# *** Keyboards ***
# Hacer login
#     Clicar en usuario
#     Escribir contraseña
#     Clicar en siguiente

# Clicar en usuario
#     Click  coordinates:100,100

# Escribir contraseña
#     Keyboard input  mecagoenlaleche0101

# Clicar en siguiente
#     Press Keys  ENTER


    
    