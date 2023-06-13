*** Settings ***
Library           ButlerRobot.AIDesktopLibrary  WITH NAME  Desktop

*** Variables ***
${name}    Alvaro
${surname}    Baños
${email_prefix}  albanos19909

*** Tasks ***
Open google
    Desktop.Open Application    google-chrome
    AI.Type text Crear cuenta in google on Search google or type a URL

    Keyboard Input    Crear cuenta google
    Press Keys    ENTER

Book gym
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
    Click   coordinates:605,305
    AI.Click on Junio
    Click   coordinates:755,305
    Keyboard input  1992
    AI.Click on Género  # Entrenar
    AI.Click on "Hombre"
    AI.Click on Siguiente

    Keyboard input  ${email_prefix}
    AI.Click on Siguiente

    Keyboard input  mecagoenlaleche0101
    AI.Click on "Confirmación"
    Keyboard input  mecagoenlaleche0101
    AI.Click on Siguiente



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




    
    