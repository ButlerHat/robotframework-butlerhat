*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}/crawl_amazon_data  WITH NAME  Browser


*** Keywords ***

Login with user ${user} and pass ${password}
    Click  //*[@id='ap_email']
    Keyboard Input    type    ${user}
    Click  //*[@id='ap_password']
    Keyboard Input    type    ${password}
    CLick  //*[@id='signInSubmit']

Type number "${number}" in field Indicar contraseña de un solo uso
    Click  //*[@id='auth-mfa-otpcode']
    Keyboard Input    type    ${number}

Check "No vuelvas a pedir un codigo en este navegador"
    Click  //*[@id='auth-mfa-remember-device']

Click on "Iniciar sesion"
    Click  //*[@id='auth-signin-button']

Scroll in Select Account until "${country}" is visible and click
    ${result}  Is Text Visible  ${country}
    IF    ${result}
        Sleep  0.1
        Click  //*[@id="picker-container"]//div[contains(text(), "${country}")]
        RETURN
    END
    WHILE    ${True}
        Sleep  0.1
        Scroll Down At Bbox    //*[@id="picker-container"]/div/div[2]/div/div[3]
        # Ask if ${country} is visible
        ${result}  Is Text Visible  ${country}
        IF    ${result}
            BREAK
        END
    END
    Sleep  0.1
    Click  //*[@id="picker-container"]//div[contains(text(), "${country}")]

Click on "Select Account"
    Click  //button[contains(text(),'Select Account')]

Click on menu icon at top left
    Click  //div[@role='button']

Click on "Orders" menu at the left
    Click  //html/body/div/div[1]/div/div[1]/div[3]/div[3]/div/div[1]/div[2]/div/div[4]

Click on "Orders Report" submenu
    Click  //a[@href='/order-reports-and-feeds/reports/ref=xx_orderrpt_dnav_xx']

Click on "Unshipped Orders" in the menu
    Click  //*[text()='Unshipped Orders']

Click on "Request" yellow button
    Click  //input[@name='request']

Click at "Refresh" button at the top right of the table
    Click  //input[@name='refresh']

Get element bouding box at ${ordinal_num} row and "${column}" column at Download Report table
    &{num_dict}  Create Dictionary   first=2  second=3  third=4  fourth=5  fifth=6  sixth=7  seventh=8  eighth=9  ninth=10  tenth=11
    &{column_dict}  Create Dictionary   report type=1  batch id=2  date range covered=3  date and time requested=4  date and time completed=5  report status=6  download=7
    ${bbox}  Element Bbox    //html/body/div[1]/div[2]/div[1]/div/div/div[2]/div[2]/div/div/div[4]/table/tr[${num_dict["${ordinal_num.lower()}"]}]/td[${column_dict["${column.lower()}"]}]
    RETURN  ${bbox}

Click at "download" button at ${ordinal_num} row at Download Report table
    &{num_dict}  Create Dictionary   first=2  second=3  third=4  fourth=5  fifth=6  sixth=7  seventh=8  eighth=9  ninth=10  tenth=11
    Click  //html/body/div[1]/div[2]/div[1]/div/div/div[2]/div[2]/div/div/div[4]/table/tr[${num_dict["${ordinal_num}"]}]/td[7]//a

# ===== No record Keywords =====

No Record Scroll Up
    [Tags]  no_record
    Scroll Up At Bbox    //*[@id="picker-container"]/div/div[2]/div/div[3]  1000

No Record Scroll Down
    [Tags]  no_record
    Scroll Down  pixels_selector=10000