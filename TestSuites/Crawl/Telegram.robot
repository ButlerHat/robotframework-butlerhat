*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  console=False  record=${True}  output_path=/workspaces/ai-butlerhat/ai-butlerhat-projects/default/upload  WITH NAME  Browser


*** Tasks ***
ManualFindAndGreets
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/
    Sleep  1
    Search HolaBot
    Click under chats on chat @HolaBot
    Click Start
    Write Hola on messages
    Click on send
    Click on three dots at the top right corner
    Click on delete chat button
    Click also delete checkbox in the popup
    Click on delete chat red button in popup


*** Keywords ***
Write ${message} on messages
    [Tags]  no_record
    Click  //div[@class='input-message-container']
    Keyboard Input    type   ${message}

Click on search
    [Tags]  no_record
    Click  //*[@class='input-search']/input

Search ${text}
    [Tags]  no_record
    Click    //*[@class='input-search']/Input
    Keyboard Input    type   ${text}

Click on chat ${name}
    [Tags]  no_record
    Click  //ul[contains(@data-autonomous, '0')]/a[contains(.,'${name}')]

Click under chats on chat ${name}
    [Tags]  no_record
    Click  //ul[contains(@data-autonomous, '1')]//a[contains(.,'${name}')]

Click start
    [Tags]  no_record
    Click  //button[@class='btn-primary btn-transparent text-bold chat-input-control-button rp']

Click on send
    [Tags]  no_record
    Click  //button[contains(@class, 'send')]

Click on three dots at the top right corner
    Click  //button[@class='btn-icon rp btn-menu-toggle']

Click on delete chat button
    Click  //div[@class="btn-menu-item rp-overflow danger"][contains(.,'Delete Chat')]

Click also delete checkbox in the popup
    Click  //*[contains(text(), 'Also delete')]/../div[1]  # this is a bit tricky, but it works

Click on delete chat red button in popup
    Click  //button[@class="popup-button btn danger rp"]
