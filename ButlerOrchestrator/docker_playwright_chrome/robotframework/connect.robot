*** Settings ***
Library       ButlerRobot.AIBrowserLibrary  fix_bbox=${False}  presentation_mode=${True}  console=${False}  record=${False}  WITH NAME  Browser


*** Test Cases ***
Test
    Connect To Browser  ws://172.17.0.2:4445/my_endpoint    
    New Context
    New Page  https://www.google.com
    Click  (//*[contains(text(),'Iniciar')])[2]
