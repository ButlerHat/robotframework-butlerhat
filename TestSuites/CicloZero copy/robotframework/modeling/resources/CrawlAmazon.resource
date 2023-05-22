*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  fix_bbox=${TRUE}  output_path=${OUTPUT_DIR}/crawl_amazon_data  WITH NAME  Browser
Library   Collections
Library   ../../keywords/utils.py
Library    OperatingSystem


*** Keywords ***
# ===========================================================
# ======================== Pendiente ========================
# ===========================================================

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
    Click  //*[@id="picker-container"]//div[contains(text(), "${country}")]

Click on "Select Account"
    Click  //button[contains(text(),'Select Account')]

Click on menu icon at top left
    Click  //div[@role='button']

Click on "Orders" menu at the left
    AI.Click on "Orders" menu at the left
    # Only works in flendu
    # Click  //html/body/div/div[1]/div/div[1]/div[3]/div[3]/div/div[1]/div[2]/div/div[4]

Click on "Order Reports" submenu
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

# ==================================================================
# ======================== Pendiente envios ========================
# ==================================================================
Click "Manage orders" submenu
    AI.Click "Manage orders" submenu
    # Click  //html/body/div/div[1]/div/div[1]/div[3]/div[3]/div/div[1]/div[2]/div/div[4]/div[2]/div[2]/a/div[1]

Click on "Pending" tab
    Click  //div[@class='myo-spa-tab '][.//a[@data-test-id='tab-/mfn/pending']]

Change Results per page to ${num}
    Change Results per page
    Set Results per page to ${num}

Change Results per page
    Sleep  2
    Click  //*[@id='a-autoid-1-announce']

Set Results per page to ${num}
    &{num_dict}  Create Dictionary   15=0  25=1  50=2  100=3
    Click  //*[@id='myo-table-results-per-page_${num_dict["${num}"]}']

How many orders are Pending?
    [Documentation]  The pending tab must be active
    ${bbox}  Get Element Bounding Box of the "Pending" tab    
    ${txt}  Get Text From Bbox    selector_bbox=${bbox}
    RETURN  ${txt.split(' ')[0].strip()}

Get Element Bounding Box of the "Pending" tab
    ${bbox}  Element Bbox  //div[contains(@class, 'active')]
    RETURN  ${bbox}

Remove Warnings In Table
    [Tags]  no_record
    Evaluate JavaScript  ${None}    const table = document.getElementById('orders-table');
    ...  // Get a list of all table rows with the class 'myo-table-row warning'
    ...  const rowsToDelete = table.querySelectorAll('.myo-table-row.warning');
    ...    // Loop through each row and remove it from the table
    ...    rowsToDelete.forEach(row => {
    ...    const tdCount = row.getElementsByTagName('td').length;
    ...    if (tdCount < 2) {
    ...    row.parentNode.removeChild(row);
    ...    }});


Which is the number of the second column of the ${ord_num} row?
    [Documentation]  The pending tab must be active. Obtain text with the locator, not AI
    ${num_bbox}  Get element bounding box of the second column of the ${ord_num} order
    ${asin_num}  Get Text From Bbox    selector_bbox=${num_bbox}
    RETURN  ${asin_num.split('\n')[0].strip()}

Get element bounding box of the second column of the ${ord_num} order
    [Documentation]  Get the element second column bounding box. If you want to give a clue to the AI you can set "${NEXT_OBSERVATION}" variable.
    IF  "${NEXT_OBSERVATION}"  Observation  ${NEXT_OBSERVATION}
    ${num}  Get Cardinal  ${ord_num}
    ${bbox}  Element Bbox  //*[@id='orders-table']//tr[${num}]//td[3]
    RETURN  ${bbox}

Which is the SKU of the order ${2nd_col_num}?
    [Documentation]  The pending tab must be active. Obtain text with the locator, not AI
    ${sku_bbox}  Get element bounding box of the sku of the ${2nd_col_num} order
    ${sku}  Get Text From Bbox    selector_bbox=${sku_bbox}
    # Remove the "SKU: " part
    RETURN  ${sku.split(':')[-1].strip()}

Get element bounding box of the sku of the ${2nd_col_num} order
    [Documentation]  Get the element sku bounding box. 
    ${bbox}  Element Bbox  //*[@id='orders-table']//tr[contains(.,'${2nd_col_num}')]//span[contains(text(), 'SKU')]/..
    RETURN  ${bbox}

Which quantity has the order ${2nd_col_num}?
    [Documentation]  The pending tab must be active. Obtain text with the locator, not AI
    ${qty_bbox}  Get element bounding box of the quantity of the order ${2nd_col_num}
    ${qty}   Get Text From Bbox    selector_bbox=${qty_bbox}
    # Remove the "Quantity: " part
    RETURN  ${qty.split(':')[-1].strip()}

Get element bounding box of the quantity of the order ${2nd_col_num}
    ${bbox}  Element Bbox  //*[@id='orders-table']//tr[contains(.,'${2nd_col_num}')]//span[contains(text(), 'Quantity')]/..
    RETURN  ${bbox}


# ===== No record Keywords =====
No Record Scroll Up
    [Tags]  no_record
    Scroll Up At Bbox    //*[@id="picker-container"]/div/div[2]/div/div[3]  1000

No Record Scroll Down
    [Tags]  no_record
    Scroll Down  pixels_selector=10000


# ==================================================================
# ======================== Price ========================
# ==================================================================

Go to "Inventory" at the left
    Click  //*[text()='Inventory']

Go to "Manage All Inventory" submenu
    Click  //*[text()='Manage All Inventory']

Search for SKU ${sku}
    Click  //*[@id='myitable-search']
    Keyboard Input    type    ${sku}
    Click  //*[@id='myitable-search-button-announce']

Click at marketplaces button for sku ${sku}
    Click  //table//tr[contains(.,"${sku}")]//input[./..//span[contains(text(),'marketplaces')]]

In which marketplaces is it being sold?
    ${bbox}  Get Element Bounding Box of marketplaces
    ${marketplaces}  Get Text From Bbox    selector_bbox=${bbox}
    @{marketplaces}  Set Variable   ${marketplaces.split('\n')[-1].split(',')}
    ${strip_marketplaces}  Evaluate  [x.strip() for x in ${marketplaces}]
    RETURN  ${strip_marketplaces}

Get Element Bounding Box of marketplaces
    ${bbox}  Element Bbox  //*[@id="losg-modal-iframe"] >>> //*[@id='janusTableContent']/div[1]/div[1]
    RETURN  ${bbox}

Go to page of the ${marketplace} row
    [Documentation]  This keyword cannot be recorded because when click does not work
    Get Bounding box of the link in the ${marketplace} row
    ${href}  NoRec Get Attribute    //*[@id="losg-modal-iframe"] >>> //*[@id='janusTableContent']/div[contains(., '${marketplace}')][2]/div[4]//a    href
    New Page  ${href}

    RETURN  ${href}

NoRec Get Attribute
    [Arguments]  ${selector}  ${attribute}
    [Tags]  no_record
    ${attr}  Get Attribute  ${selector}  ${attribute}
    RETURN  ${attr}


Get Bounding box of the link in the ${marketplace} row
    [Documentation]  This keyword is only for teaching purposes. When click does not work
    Element Bbox   //*[@id="losg-modal-iframe"] >>> //*[@id='janusTableContent']/div[contains(., '${marketplace}')][2]/div[4]

Get status for ${market}
    ${bbox}  Get Element Bounding Box of the status of the ${market} row
    ${status}  Get Text From Bbox    selector_bbox=${bbox}
    RETURN  ${status}

Get Element Bounding Box of the status of the ${market} row
    # Make sure the row is visible
    ${bbox}  Element Bbox  //*[@id="losg-modal-iframe"] >>> //*[@id='janusTableContent']/div[contains(., '${market}')][2]/div[1]
    RETURN  ${bbox}

Get price for ${market}
    ${bbox}  Get Element Bounding Box of the price of the ${market} row
    ${price}  Get Text From Bbox    selector_bbox=${bbox}
    RETURN  ${price.replace('\n', '').split(' ')[-1]}

Get Element Bounding Box of the price of the ${market} row
    ${loc}  Set Variable  //*[@id="losg-modal-iframe"] >>> //*[@id='janusTableContent']/div[contains(., '${market}')][2]/div[6]//kat-input-group//kat-input
    ${bbox}  Element Bbox  ${loc}
    RETURN  ${bbox}


# ========== Amazon Public ==========
Accept cookies
    Click  //*[@id='sp-cc-accept']

Search ${product}
    Click  //*[@id='twotabsearchtextbox']
    Keyboard Input    type    ${product}

Click on search icon
    Click  //*[@id='nav-search-submit-button']

See Renewed at the right above sell on Amazon
    Click  //div[@class='a-box-inner'][.//div[@class='olp-text-box']]

Open filter at the right
    Click  //*[@id='aod-filter-string']
    # Check if the filter is open
    ${STATUS}  ${MSG}  Run keyword and ignore error  Wait For Elements State   //*[@id="new"]/div/label/input  visible  1
    IF  '${STATUS}' == 'FAIL'  Run Keyword And Ignore Error  Click  //*[@id='aod-filter-string']

Close filter if not open
    ${STATUS}  ${MSG}  Run keyword and ignore error  Wait For Elements State   //*[@id="new"]/div/label/input  visible  1
    IF  '${STATUS}' == 'PASS'  Click  //*[@id='aod-filter-string']

Check ${condition} condition checkbox
    &{types_dict}  Create Dictionary  Renewed=new  Used=used  Like New=usedLikeNew  Very Good=usedVeryGood  Good=usedGood  Acceptable=usedAcceptable
    ${value}  Get From Dictionary    ${types_dict}  ${condition}
    Click  //*[@id="${value}"]/div/label/input

Get three first lowest price
    # Create dict to store prices
    &{prices}  Create Dictionary
    ${num_elements}  Get Element Count  //*[@id='aod-offer']
    ${num_elements}  Evaluate  min(5, ${num_elements})

    FOR  ${i}  IN RANGE  ${num_elements}
        ${ord_num}  Get Ordinal    number=${i+1}

        # Get best price
        ${bbox_price}  ${text}  Get element bounding box of the price of the ${ord_num} option
        ${text_bbox}  IF  not "${text}"  Get Text From Bbox    ${bbox_price}
        ${price}  Set Variable If  not "${text}"  ${text_bbox}  ${text}
        ${bbox}  Get element bounding box of the seller of the ${ord_num} option
        ${seller}  Get Text From Bbox    ${bbox}

        # Add to dict
        Set To Dictionary   ${prices}  ${seller}  ${price}  
    END

    RETURN  ${prices}

Get element bounding box of the price of the ${ord_num} option
    ${num}  Get Cardinal  ${ord_num} 
    ${bbox}  Element Bbox  (//*[@id='aod-offer'][${num}]//*[contains(text(),'€')][not(contains(text(),'no'))])[1]
    
    # This is to get a better text, but Element BBox still here for IA training
    ${text}  Get Text  (//*[@id='aod-offer'][${num}]//*[contains(text(),'€')][not(contains(text(),'no'))])[1]
    RETURN  ${bbox}  ${text}

Get element bounding box of the seller of the ${ord_num} option
    ${num}  Get Cardinal  ${ord_num}
    ${bbox}  Element Bbox  (//*[@id='aod-offer'][${num}]//*[@id='aod-offer-shipsFrom']//span)[2]
    RETURN  ${bbox}


