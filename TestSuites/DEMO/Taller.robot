*** Settings ***
Library           Browser

*** Tasks ***
Click a button
    New Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/
    Click  //ul/a[contains(.,'userinfobot')]

