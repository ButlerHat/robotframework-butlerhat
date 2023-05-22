#!/bin/bash
export DEVELOPMENT_SERVER=1
export ROBOT_CICLOZERO_PASS='V6#hYk$3YkAWs5XrJnbG$Z!ue#s'
export PYTHONPATH=
export PATH=/vscode/vscode-server/bin/linux-x64/b3e4e68a0bc097f0ae7907b217c1119af9e03435/bin/remote-cli:/opt/conda/envs/web_env/bin:/opt/conda/condabin:/usr/local/python/current/bin:/usr/local/py-utils/bin:/usr/local/share/nvm/current/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/vscode/.local/bin
/opt/conda/condabin/conda run -n base /opt/conda/bin/robot -d "/workspaces/CicloZero/results/stock" -v OUTPUT_DIR:"/workspaces/CicloZero/results/stock" -v RESULT_EXCEL_PATH:/workspaces/CicloZero/downloads/stock/CiclAiStock_$(date +"%H-%M_%d-%m-%Y").xlsx /workspaces/CicloZero/CiclAiStock.robot > /workspaces/CicloZero/jobs/cron.log 2>&1