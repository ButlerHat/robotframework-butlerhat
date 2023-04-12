*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}/data  WITH NAME  Browser 


*** Variables ***
${OUTPUT_DIR}  /workspaces/udop/i-Code-Doc/IA4RobotFramework/robotframework-butlerhat/TestSuites/CicloZero

*** Test Cases ***
Get Phone Price
    Open Browser  https://amazon.es
    AI.Click "Cesta"

*** Keywords ***
Accept cookies
    Record Click

