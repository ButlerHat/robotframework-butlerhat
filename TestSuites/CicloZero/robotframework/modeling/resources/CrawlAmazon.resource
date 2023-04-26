*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}/crawl_amazon_data  WITH NAME  Browser
Library   ../../keywords/utils.py


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

# ====== Pendiente Keywords ======
Click "Manage orders" submenu
    Click  //html/body/div/div[1]/div/div[1]/div[3]/div[3]/div/div[1]/div[2]/div/div[4]/div[2]/div[2]/a/div[1]

Click on "Pending" tab
    Click  //div[@class='myo-spa-tab '][.//a[@data-test-id='tab-/mfn/pending']]

Change Results per page to ${num}
    Change Results per page
    Set Results per page to ${num}

Change Results per page
    Click  //*[@id='a-autoid-1-announce']

Set Results per page to ${num}
    &{num_dict}  Create Dictionary   15=0  25=1  50=2  100=3
    Click  //*[@id='myo-table-results-per-page_${num_dict["${num}"]}']

How many orders are Pending?
    [Documentation]  The pending tab must be active
    ${bbox}  Get Element Bounding Box of the "Pending" tab    
    ${txt}  Get Text From Bbox    selector_bbox=${bbox}
    RETURN  ${txt.split('\n')[0].strip()}

Get Element Bounding Box of the "Pending" tab
    ${bbox}  Element Bbox  //div[contains(@class, 'active')]
    RETURN  ${bbox}

Which is the SKU of the ${ord_num} order?
    [Documentation]  The pending tab must be active. Obtain text with the locator, not AI
    ${sku_bbox}  Get element bounding box of the sku of the ${ord_num} order
    ${sku}  Get Text From Bbox    selector_bbox=${sku_bbox}
    # Remove the "SKU: " part
    RETURN  ${sku.replace('SKU', "").replace(':', "").strip()}

Get element bounding box of the sku of the ${ord_num} order
    [Documentation]  Get the element sku bounding box. If you want to give a clue to the AI you can set "${NEXT_OBSERVATION}" variable.
    IF  "${NEXT_OBSERVATION}"  Observation  ${NEXT_OBSERVATION}
    ${num}  Get Cardinal  ${ord_num}
    ${bbox}  Element Bbox  //*[@id='orders-table']//tr[${num}]//span[contains(text(), 'SKU')]/..
    RETURN  ${bbox}

Which quantity has the order with sku ${sku}?
    [Documentation]  The pending tab must be active. Obtain text with the locator, not AI
    ${qty_bbox}  Get element bounding box of the quantity of the order with SKU ${sku}
    ${qty}   Get Text From Bbox    selector_bbox=${qty_bbox}
    # Remove the "Quantity: " part
    RETURN  ${qty.split(':')[-1].strip()}

Get element bounding box of the quantity of the order with SKU ${sku}
    ${bbox}  Element Bbox  //*[@id='orders-table']//tr[.//*[contains(., '${sku}')]]//span[contains(text(), 'Quantity')]/..
    RETURN  ${bbox}


# ===== No record Keywords =====
No Record Scroll Up
    [Tags]  no_record
    Scroll Up At Bbox    //*[@id="picker-container"]/div/div[2]/div/div[3]  1000

No Record Scroll Down
    [Tags]  no_record
    Scroll Down  pixels_selector=10000