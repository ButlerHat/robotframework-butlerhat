*** Settings ***
Library   ButlerRobot.AIBrowserLibrary   strict=${False}  fix_bbox=${TRUE}  presentation_mode=${True}  console=${False}  record=${True}  output_path=${OUTPUT_DIR}/data_gym  AS  Browser
Variables  variables/credentials.py


*** Variables ***
${DEFAULT_AI_MODE}  Flexible
${ROBOT_GYM_PASS}  butlerhat


*** Test Cases ***
Demo
    Open Browser  https://deportesweb.madrid.es/DeportesWeb/Login
    Record Test  Demo

    