*** Settings ***
Documentation     Crawl most used websites in EU
Library   ButlerRobot.AIBrowserLibrary  console=${True}  output_path=/workspaces/ai-butlerhat/ai-butlerhat-projects/default/upload  WITH NAME  Browser
Library   ButlerRobot.CrawlLibrary  supervise_crop=${False}  WITH NAME  CrawlLibrary

*** Tasks ***

TelegramChatClicks
    [Documentation]    Crawl the data browser. DONE
    [Tags]    data_browser

    # Open Browser  https://web.telegram.org/k/  pause_on_failure=False
    Set Supervise Crop    ${True}
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/
    CrawlLibrary.Crawl Clicks  https://web.telegram.org/k/#@userinfobot  max_number_of_page_to_crawl=1

TelegramChatType
    [Documentation]    Crawl the data browser. DONE (Only search field)
    [Tags]    data_browser

    # Open Browser  https://web.telegram.org/k/  pause_on_failure=False
    Set Supervise Crop    ${False}
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/
    CrawlLibrary.Crawl Type  https://web.telegram.org/k/#@userinfobot  max_number_of_page_to_crawl=1

TelegramChatTypeMessage
    [Documentation]    Crawl the data browser. DONE
    [Tags]    data_browser

    # Open Browser  https://web.telegram.org/k/  pause_on_failure=False
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/
    @{elements_xpath}  Create List  //div[@contenteditable="true"]
    CrawlLibrary.Crawl Type  https://web.telegram.org/k/#@userinfobot  max_number_of_page_to_crawl=1  max_elements=5  elements_xpath=${elements_xpath}

TelegramSearch
    [Documentation]    Crawl the data browser. DONE. No tabs done
    [Tags]    data_browser

    # Open Browser  https://web.telegram.org/k/  pause_on_failure=False
    Set Supervise Crop    ${True}
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@userinfobot    Click on search

    # Record tabs
    @{tabs_xpath}  Create List  (//*[@class="search-super-tabs menu-horizontal-div"])[1]/div
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@userinfobot    Click on search  elements_xpath=${tabs_xpath}  max_number_of_page_to_crawl=1

TelemgramChatXpath
    [Documentation]    Crawl the data browser. DONE
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/
    @{element_after_input}  Create List  //input[@dir='auto']
    ...  //button[contains(@class, 'is-visible')]
    ...  //ul/a[1]
    ...  //ul/a[2]
    ...  //ul/a[3]
    ...  //ul/a[4]
    ...  //ul/a[5]
    ...  //ul/a[6]
    ...  //ul/a[7]
    ...  //ul/a[8]
    ...  //*[@id='new-menu']
    ...  //button[@class='btn-icon toggle-emoticons']
    ...  //div[contains(@class, 'input-field-input-fake')]
    ...  //div[contains(@class, 'attach-file')]
    ...  //button[contains(@class, 'btn-send')]
    
    # CrawlLibrary.Crawl Clicks  https://web.telegram.org/k/#@userinfobot  max_number_of_page_to_crawl=1  elements_xpath=${elements_xpath}
    Set Supervise Crop    ${True}
    # @{element_after_input}  Create List  //button[contains(@class, 'is-visible')]
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@userinfobot    Write on messages   max_number_of_page_to_crawl=1  elements_xpath=${element_after_input}

TelemgramSend
    [Documentation]    Crawl the data browser. DONE
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/
    @{element_after_input}  Create List  //button[contains(@class, 'btn-send')]
    
    # CrawlLibrary.Crawl Clicks  https://web.telegram.org/k/#@userinfobot  max_number_of_page_to_crawl=1  elements_xpath=${elements_xpath}
    Set Supervise Crop    ${False}
    # @{element_after_input}  Create List  //button[contains(@class, 'is-visible')]
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@userinfobot    Write on messages   max_number_of_page_to_crawl=1  elements_xpath=${element_after_input}

Telegram Scroll
    [Documentation]    Crawl the data browser.
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/#@userinfobot
    Sleep  1
    # Scroll in chats
    Scroll in chats
    Scroll down in chats
    Do Scroll in chats
    Scroll at the left
    Make scroll to see unread chats
    Scroll down in column left

    # Scroll up
    Scroll up in chats
    Do Scroll up in chats
    Scroll up in column left
    Scroll to the top in chats
    Scroll to the top in column left

    # Scroll in messages
    Scroll in messages
    Scroll down in messages
    Do Scroll in messages
    Scroll at the main column
    Make scroll to see unread messages

    # Scroll up
    Go up in messages
    I want to see more messages avobe
    Scroll up in messages
    Scroll to the top in messages
    Scroll to the top in column center

ButtonAddModal
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/#@userinfobot
    Sleep  1

    @{buttons_after_mas}  Create List  (//button[@class="btn-icon popup-close"])[1]  # cerrar
    ...  //button[contains(.,'Add')]  # add
    
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@HolaBot    No Record Click on mas  max_number_of_page_to_crawl=1  elements_xpath=${buttons_after_mas}

    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@HolaBot    No Record Click on mas  max_number_of_page_to_crawl=1  elements_xpath=${buttons_after_mas}

ClickOnMas
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/#@userinfobot
    Sleep  1

    Set Supervise Crop    ${True}

    @{buttons_after_private_chat}  Create List  (//button[@class="btn-icon sidebar-close-button"])[1]  # atras
    ...  (//button[@class="btn-circle btn-corner z-depth-1 is-visible rp"])[1]  # Mas
    ...  (//button[@class="btn-icon rp"])[1]  # lupa izquierda
    
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@HolaBot    No Record Click on new private chat  max_number_of_page_to_crawl=1  elements_xpath=${buttons_after_private_chat}

CreateChats
    [Documentation]    Crawl the data browser.
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/#@userinfobot
    Sleep  1

    @{element}  Create List  //*[@id="new-menu"]

    CrawlLibrary.Crawl Clicks  https://web.telegram.org/k/#@userinfobot  max_number_of_page_to_crawl=1  elements_xpath=${element}


    Close Browser
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/#@userinfobot
    Sleep  1

    @{buttons_after_click}  Create List  //*[text()="New Channel"]/..
    ...  //*[text()="New Group"]/..
    ...  //*[text()="New Private Chat"]/..
    
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@HolaBot    No Record Pencil  max_number_of_page_to_crawl=1  elements_xpath=${buttons_after_click}

    Close Browser
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/#@userinfobot
    Sleep  1

    @{buttons_after_private_chat}  Create List  (//button[@class="btn-icon sidebar-close-button"])[1]  # atras
    ...  (//button[@class="btn-circle btn-corner z-depth-1 is-visible rp"])[1]  # Mas
    ...  (//button[@class="btn-icon rp"])[1]  # lupa izquierda
    
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@HolaBot    No Record Click on new private chat  max_number_of_page_to_crawl=1  elements_xpath=${buttons_after_private_chat}

    Close Browser
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/#@userinfobot
    Sleep  1

    @{buttons_after_mas}  Create List  (//button[@class="btn-icon popup-close"])[1]  # cerrar
    ...  (//button[@class="btn-primary btn-color-primary"])[1]  # add
    
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@HolaBot    No Record Click on mas  max_number_of_page_to_crawl=1  elements_xpath=${buttons_after_mas}
    
    
    Close Browser
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/#@userinfobot
    Sleep  1

    @{texts_after_mas}  Create List  (//div[@class="input-field-input is-empty"])[1]  # first name
    ...  (//div[@class="input-field-input is-empty"])[2]  # last name
    ...  (//div[@class="input-field-input"])[1]  # number
    
    CrawlLibrary.Crawl Type After Keyword   https://web.telegram.org/k/#@HolaBot    No Record Click on mas  max_number_of_page_to_crawl=1  elements_xpath=${texts_after_mas}



*** Keywords ***
No Record Pencil
    [Tags]  no_record
    Click  //*[@id="new-menu"]
    Sleep  1

No Record Click on new private chat
    [Tags]  no_record
    No Record Pencil
    Click  //*[text()="New Private Chat"]/..
    Sleep  1

No Record Click on mas
    [Tags]  no_record
    No Record Click on new private chat
    Click  (//button[@class="btn-circle btn-corner z-depth-1 is-visible rp"])[1]
    Sleep  1


Click on search
    [Tags]  no_record
    Click  //*[@class='input-search']/input
    
Write on messages
    [Tags]  no_record
    ${random_words}  Generate Random Words
    Click  //div[@class='input-message-container']
    Keyboard Key    Control+A+Delete
    Keyboard Input    type   ${random_words}


# Scroll keywords
No Record Get BBox Chats
    [Tags]  no_record
    ${bbox}  Get Bounding Box  //*[@id='column-left']
    RETURN  ${bbox}

No Record Get BBox Messages
    [Tags]  no_record
    ${bbox}  Get Bounding Box  //*[@id='column-center']
    RETURN  ${bbox}

# Chats
# DOWN
Scroll in chats
    Scroll Down At Bbox    //*[@id='column-left']

Scroll down in chats
    Scroll Down At Bbox    //*[@id='column-left']

Do Scroll in chats
    Scroll Down At Bbox    //*[@id='column-left']

Scroll at the left
    Scroll Down At Bbox    //*[@id='column-left']

Make scroll to see unread chats
    Scroll Down At Bbox    //*[@id='column-left']

Scroll down in column left
    Scroll Down At Bbox    //*[@id='column-left']


# UP
Scroll up in chats
    Scroll Up At Bbox    //*[@id='column-left']

Do Scroll up in chats
    Scroll Up At Bbox    //*[@id='column-left']

Scroll up in column left
    Scroll Up At Bbox    //*[@id='column-left']

Scroll to the top in chats
    Scroll Up At Bbox    //*[@id='column-left']

Scroll to the top in column left
    Scroll Up At Bbox    //*[@id='column-left']

# Messages
# DOWN
Scroll in messages
    Scroll Down At Bbox    //*[@id='column-center']

Scroll down in messages
    Scroll Down At Bbox    //*[@id='column-center']

Do Scroll in messages
    Scroll Down At Bbox    //*[@id='column-center']

Scroll at the main column
    Scroll Down At Bbox    //*[@id='column-center'] 

Make scroll to see unread messages
    Scroll Down At Bbox    //*[@id='column-center']

# UP
Go up in messages
    Scroll Up At Bbox    //*[@id='column-center']

I want to see more messages avobe
    Scroll Up At Bbox    //*[@id='column-center']

Scroll up in messages
    Scroll Up At Bbox    //*[@id='column-center']

Scroll to the top in messages
    Scroll Up At Bbox    //*[@id='column-center']

Scroll to the top in column center
    Scroll Up At Bbox    //*[@id='column-center']



