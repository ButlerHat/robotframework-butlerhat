import os
import streamlit as st
import asyncio

async def run_robot(id: str, vars: list, robot: str, msg=None):
    robot_path = st.secrets.paths.robot
    robot_script = os.path.join(robot_path, robot)
    robot_command = "conda run -n base /opt/conda/bin/robot " + \
        f'-d "{robot_path}" ' + \
        f'-v OUTPUT_DIR:"{robot_path}" {"-v " if len(vars) > 0 else ""}{" -v ".join(vars)} ' + \
        f"{robot_script}"

    # Move to robot directory
    print(f"Running {robot_command}")
    msg_ = f"Running {robot}" if not msg else msg

    with st.spinner(msg_):
        with open(f'logfile_out_{id}.txt', 'w') as f2:
            proc = await asyncio.create_subprocess_shell(
                f"{robot_command}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            f2.write(stdout.decode())
            f2.write(stderr.decode())
            ret_val = proc.returncode
    if ret_val != 0:
        msg_ = f"Robot failed with return code {ret_val}" if not msg else f'Fail {ret_val}: {id}'
        st.error(msg_)
    else:
        msg_ = f"Robot finished successfully" if not msg else f'Success: {id}'
        st.success(msg_)
