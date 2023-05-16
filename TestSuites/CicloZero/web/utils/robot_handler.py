import os
import streamlit as st
import asyncio

def get_robot_command(id, vars, robot):
    robot_path = st.secrets.paths.robot
    robot_script = os.path.join(robot_path, robot)
    result_path = os.path.join(robot_path, "results", id)
    robot_command = "/opt/conda/condabin/conda run -n base /opt/conda/bin/robot " + \
        f'-d "{result_path}" ' + \
        f'-v OUTPUT_DIR:"{result_path}" {"-v " if len(vars) > 0 else ""}{" -v ".join(vars)} ' + \
        f"{robot_script}"
    return robot_command


async def run_robot(id: str, vars: list, robot: str, msg=None):
    robot_path = st.secrets.paths.robot
    result_path = os.path.join(robot_path, "results", id)
    # If directory does not exist, create it
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    robot_command = get_robot_command(id, vars, robot)

    # Move to robot directory
    print(f"Running {robot_command} \n")
    msg_ = f"Running {robot}" if not msg else msg

    with st.spinner(msg_):
        proc = await asyncio.create_subprocess_shell(
            f"{robot_command}",
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        ret_val = proc.returncode
        with open(os.sep.join([robot_path, "results", id, f'logfile_out_{id}.txt']), 'w') as f2:
            f2.write(stdout.decode())
            f2.write(stderr.decode())

    # Check if there is a msg file
    msg_path = os.path.join(result_path, "return_msg.txt")
    if os.path.exists(msg_path):
        with open(msg_path, 'r') as f:
            msg_ = f.read()
            if 'warn' in msg_.lower():
                st.warning(msg_)
            elif 'success' in msg_.lower():
                st.success(msg_)
            else:
                st.error(msg_)
        # Delete the file
        os.remove(msg_path)
        return

    if ret_val != 0:
        msg_ = f"Robot failed with return code {ret_val}" if not msg else f'Fail {ret_val}: {id}'
        st.error(msg_)
        
    else:
        msg_ = f"Robot finished successfully" if not msg else f'Success: {id}'
        st.success(msg_)
