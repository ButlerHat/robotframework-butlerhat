*** Settings ***
Library   ButlerRobot.AIBrowserLibrary  ai_url=http://localhost:5000/predict_rf  console=False  record=${True}  output_path=/workspaces/ai-butlerhat/ai-butlerhat-projects/default/upload  WITH NAME  Browser


*** Tasks ***
ManualFindAndGreets
    New Stealth Persistent Context  /tmp/telegram  headless=${False}  url=https://web.telegram.org/k/
    Sleep  1
    AI.Search HolaBot
    AI.Click under chats on chat @HolaBot
    AI.Click Start
    AI.Write Hola on messages
    AI.Click on send
    AI.Click on three dots at the top right corner
    AI.Click on delete chat
    AI.Click also delete HolaBot
    AI.Click on delete chat popup
