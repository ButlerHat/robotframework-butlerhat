*** Settings ***
Documentation     Crawl most used websites in EU
Library   ButlerRobot.AIBrowserLibrary  console=False  output_path=/workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat/TestSuites/Crawl/telegram  WITH NAME  Browser
Library      ButlerRobot.CrawlLibrary  supervise_crop=${False}  WITH NAME  CrawlLibrary

*** Tasks ***
TelegramHome
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    # Open Browser  https://web.telegram.org/a/  pause_on_failure=False
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/a/
    @{recorders}  Create List  click
    CrawlLibrary.Crawl  https://web.telegram.org/a/  1  recorders=${recorders}  max_elements=5

TelegramChatClicks
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    # Open Browser  https://web.telegram.org/a/  pause_on_failure=False
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/a/
    CrawlLibrary.Crawl Clicks  https://web.telegram.org/k/#@userinfobot  max_number_of_page_to_crawl=1

TelegramChatType
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    # Open Browser  https://web.telegram.org/a/  pause_on_failure=False
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/a/
    CrawlLibrary.Crawl Type  https://web.telegram.org/k/#@userinfobot  max_number_of_page_to_crawl=1

TelegramChatTypeMessage
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    # Open Browser  https://web.telegram.org/a/  pause_on_failure=False
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/a/
    @{elements_xpath}  Create List  //div[@contenteditable="true"]
    CrawlLibrary.Crawl Type  https://web.telegram.org/k/#@userinfobot  max_number_of_page_to_crawl=1  max_elements=5  elements_xpath=${elements_xpath}

TelegramSearch
    [Documentation]    Crawl the data browser
    [Tags]    data_browser

    # Open Browser  https://web.telegram.org/a/  pause_on_failure=False
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/a/
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@userinfobot    Click on search

    # Record tabs
    @{tabs_xpath}  Create List  (//*[@class="search-super-tabs menu-horizontal-div"])[1]/div
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@userinfobot    Click on search  elements_xpath=${tabs_xpath}

TelemgramChat
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/a/
    @{elements_xpath}  Create List  //input[@dir='auto']
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

    
    @{element_after_input}  Create List  //button[contains(@class, 'is-visible')]
    CrawlLibrary.Crawl Clicks After Keyword    https://web.telegram.org/k/#@userinfobot    Write on messages  max_number_of_page_to_crawl=1  elements_xpath=${element_after_input}



*** Keywords ***
Click on search
    [Tags]  no_record
    Click  //*[@class='input-search']/input
    
Write on messages
    [Tags]  no_record
    Type Text    (//div[contains(@class, 'input-field-input-fake')])[1]    hola