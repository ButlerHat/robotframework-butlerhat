*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  WITH NAME  Browser 


*** Variables ***
${PHONE}  iphone 12 Negro

*** Test Cases ***
Get Phone Price
    Open Browser  https://amazon.es
    Accept Cookies

*** Keywords ***
Accept cookies
    Record Click

