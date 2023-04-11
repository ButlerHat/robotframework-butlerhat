*** Settings ***
Library     ButlerRobot.DataBrowserLibrary  AS  Browser
Library     ../test/test_data_wrapper.py
Suite Setup     Set Library Search Order  Browser


*** Test Cases ***
Test
    [Tags]  json
    Set Library Search Order  Browser
    Browser.Open Browser  https://www.amazon.com  pause_on_failure=False
    Click    //input[@id="nav-search-submit-button"]
    Accept Cookies
    Keyword With No Steps
    Search samsung galaxy s21 product

*** Keywords ***
Open 
    Browser.Open Browser  https://www.amazon.com  pause_on_failure=False
    
Keyword With No Steps
    BuiltIn.Log  esto es una prueba

Accept Cookies
    Run Keyword And Ignore Error   Click  //*[@id="sp-cc-accept"]  

Search Product
    [Arguments]  ${product}
    Type Text    //input[@name="field-keywords"]    ${product}
    Click    //input[@id="nav-search-submit-button"]
    
    